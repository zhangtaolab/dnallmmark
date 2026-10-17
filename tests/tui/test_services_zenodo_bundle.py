"""
Tier-1 service tests for ``tui/services/zenodo_bundle.py`` (Phase 10,
10-03 — DATA-04/D-12: the Zenodo record public probe; Task 2 appends
the bundle-driver + queue-integration suites below).

Single lane: **mocked-opener** — every probe-state mapping is pinned
fully offline (CI never touches zenodo.org; the research's live probes
are the SOURCE of the mapping, these tests are its pin). The fakes are
urlopen-shaped (``url, timeout=...`` -> a context manager carrying
``.status`` and ``.read``), the exact seam the service injects.

Live-probed facts pinned here (10-RESEARCH, 2026-10-12):

- GET ``https://zenodo.org/api/records/19135551`` answers instantly;
  HEAD against the records CDN TIMES OUT (Pitfall 7) — HEAD is never
  used.
- The record is NOT registered today: the API answers 404 with body
  ``{"status": 404, "message": "The persistent identifier is not
  registered."}`` — the exact live-today not-public mapping.
- A future restricted-published record could 403 (A4); it maps to
  probe-FAILED (disabled + explanation) — safe degradation, verified
  at activation time.

See also:
    ``tui/services/zenodo_bundle.py`` — the service under test.
    ``tui/services/download_queue.py`` — the zenodo-kind queue branch.
"""

import email.message
import inspect
import io
import json
import re
import struct
import time
import urllib.error
import zipfile
from pathlib import Path

from tui.services import zenodo_bundle

CJK_RE = re.compile("[一-鿿]")

#: The live-today 404 body, verbatim from the research capture — carried
#: by the fake so the not-public row documents the exact live state.
NOT_REGISTERED_BODY = (
    b'{"status": 404, "message": "The persistent identifier is not '
    b'registered."}')


class FakeResponse:
    """A urlopen-shaped context manager (``.status`` + ``.read``).

    ``read`` honours the chunk-size argument with a cursor so the
    streamed-download tests can pin the 64 KiB chunking contract.
    """

    def __init__(self, status=200, payload=b""):
        self.status = status
        self._payload = payload
        self._offset = 0
        self.read_calls = []

    def read(self, size=-1):
        self.read_calls.append(size)
        if size is None or size < 0:
            chunk = self._payload[self._offset:]
        else:
            chunk = self._payload[self._offset:self._offset + size]
        self._offset += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class RecordingOpener:
    """An opener fake recording ``(url, timeout)`` per call (the last
    response is exposed for read-pattern assertions)."""

    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []
        self.last_response = None

    def __call__(self, url, timeout=None):
        self.calls.append({"url": url, "timeout": timeout})
        if self.exc is not None:
            raise self.exc
        self.last_response = self.response
        return self.response


def recording_opener(response=None, exc=None):
    """The RecordingOpener factory (ty-clean attribute access)."""
    return RecordingOpener(response=response, exc=exc)


def http_error(code, reason):
    """A urlopen-raised HTTPError shape (fp unused — the probe reads
    only ``.code`` before the with-block ever opens)."""
    return urllib.error.HTTPError(
        zenodo_bundle.ZENODO_API_URL, code, reason,
        email.message.Message(), None)


# =====================================================================
# Task 1: the four-state probe (D-12) — every row offline
# =====================================================================


def test_constants_frozen_record_id_and_api_url():
    """The probe target is a frozen module constant pair — no input
    ever reaches the URL (the SSRF-ish misuse guard, T-10-03 family)."""
    assert zenodo_bundle.ZENODO_RECORD_ID == "19135551"
    assert zenodo_bundle.ZENODO_API_URL == (
        "https://zenodo.org/api/records/19135551")
    assert zenodo_bundle.PROBE_PUBLIC == "public"
    assert zenodo_bundle.PROBE_NOT_PUBLIC == "not_public"
    assert zenodo_bundle.PROBE_FAILED == "failed"
    assert zenodo_bundle.PROBE_TIMEOUT_SECONDS == 15.0


def test_probe_200_maps_public_and_passes_the_seam_kwargs():
    """A 200 record answers PUBLIC; the opener receives the frozen URL
    and the default ~15s timeout (the DoS bound, T-10-03-03)."""
    opener = recording_opener(response=FakeResponse(200, b"{}"))

    state = zenodo_bundle.probe_zenodo_public(opener=opener)

    assert state == zenodo_bundle.PROBE_PUBLIC
    assert opener.calls == [{
        "url": zenodo_bundle.ZENODO_API_URL,
        "timeout": zenodo_bundle.PROBE_TIMEOUT_SECONDS,
    }]


def test_probe_404_maps_not_public_the_live_today_state():
    """THE live-today mapping: the record is not registered — the API
    answers 404 with the verbatim body below — and 404 means NOT PUBLIC
    (D-12's disabled-with-explanation state; the activation flip is
    exactly this answer changing)."""
    opener = recording_opener(
        exc=http_error(404, "NOT FOUND"))    # body: NOT_REGISTERED_BODY
    assert NOT_REGISTERED_BODY.startswith(b'{"status": 404')

    state = zenodo_bundle.probe_zenodo_public(opener=opener)

    assert state == zenodo_bundle.PROBE_NOT_PUBLIC


def test_probe_other_http_error_maps_failed():
    """A 500 is neither public nor the not-registered answer -> FAILED
    (a pure probe-state string; the screen renders the error copy)."""
    opener = recording_opener(exc=http_error(500, "Internal Server Error"))

    state = zenodo_bundle.probe_zenodo_public(opener=opener)

    assert state == zenodo_bundle.PROBE_FAILED


def test_probe_403_restricted_maps_failed_safe_degradation():
    """A4 pin: a future restricted-published record 403s; the mapping
    degrades to FAILED (disabled + explanation), never a false public
    and never a crash — verified again at activation time."""
    opener = recording_opener(exc=http_error(403, "Forbidden"))

    state = zenodo_bundle.probe_zenodo_public(opener=opener)

    assert state == zenodo_bundle.PROBE_FAILED


def test_probe_urlerror_network_failure_maps_failed():
    """A network failure (URLError) is FAILED — distinct from NOT
    PUBLIC: an unreachable API is never read as 'record absent'."""
    opener = recording_opener(
        exc=urllib.error.URLError("connection refused"))

    state = zenodo_bundle.probe_zenodo_public(opener=opener)

    assert state == zenodo_bundle.PROBE_FAILED


def test_probe_timeout_honours_the_injected_contract():
    """T-10-03-03: the timeout parameter reaches the seam AND a hang
    past it is a FAILED outcome — the fake emulates urlopen's socket
    timeout by sleeping past the tiny injected budget, then raising."""
    tiny = 0.05
    opener = recording_opener()       # raises nothing by itself
    started = time.monotonic()

    def slow_opener(url, timeout=None):
        opener.calls.append({"url": url, "timeout": timeout})
        time.sleep((timeout or 0) + tiny)   # past the budget...
        raise TimeoutError("timed out")     # ...as urlopen would

    state = zenodo_bundle.probe_zenodo_public(
        timeout=tiny, opener=slow_opener)

    assert state == zenodo_bundle.PROBE_FAILED
    assert opener.calls[0]["timeout"] == tiny    # the seam honoured
    assert time.monotonic() - started >= tiny


def test_probe_unexpected_exception_maps_failed():
    """The service boundary: ANY unexpected exception absorbs to FAILED
    — a probe may degrade, never crash the worker."""
    opener = recording_opener(exc=ValueError("bogus response object"))

    state = zenodo_bundle.probe_zenodo_public(opener=opener)

    assert state == zenodo_bundle.PROBE_FAILED


def test_probe_accepts_no_url_or_shape_parameter():
    """The URL is never a parameter — no caller input can retarget the
    probe (frozen-constant contract, verbatim from Task 1's spec)."""
    parameters = inspect.signature(
        zenodo_bundle.probe_zenodo_public).parameters
    assert set(parameters) <= {"timeout", "opener"}


# ===== module hygiene (the services-tier invariants) =====


def test_service_module_carries_zero_inline_chinese_copy():
    """Operator copy lives in tui/strings.py (DL_ZENODO_*) — the service
    carries machine states only (the whole-services CJK lock's
    per-module mirror)."""
    source = Path(zenodo_bundle.__file__).read_text(encoding="utf-8")
    assert not CJK_RE.search(source), "inline Chinese copy in the service"


def test_service_module_never_composes_or_heads_the_probe_url():
    """The frozen URL is greppable as one literal; no HEAD request and
    no string composition ever builds a request target (Pitfall 7 +
    the frozen-constant contract)."""
    source = Path(zenodo_bundle.__file__).read_text(encoding="utf-8")
    assert "https://zenodo.org/api/records/19135551" in source
    assert "method=\"HEAD\"" not in source
    assert "method='HEAD'" not in source
    assert ".head(" not in source


# =====================================================================
# Task 2: the bundle driver (parse / download / extract) — offline
# through the injected seams; the queue-integration lane lives in
# test_services_download_queue.py (it needs the service + tmp repo).
# =====================================================================

#: A realistic Zenodo file URL (the links.self shape) for fixtures.
ZIP_FILE_URL = (
    "https://zenodo.org/api/records/19135551/files/Demo.zip/content")
README_FILE_URL = (
    "https://zenodo.org/api/records/19135551/files/README.md/content")


def record_doc():
    """The fixture record: BOTH documented spellings present in
    different entries (A4 — the parser must accept either), plus three
    non-conforming shapes that are skipped."""
    return {
        "files": [
            # spelling 1: name from `key`, url from links.self
            {"key": "Demo.zip", "size": 4096,
             "links": {"self": ZIP_FILE_URL}},
            # spelling 2: name from `filename`, url from links.download
            {"filename": "README.md", "size": 12,
             "links": {"download": README_FILE_URL}},
            {"size": 5, "links": {"self": README_FILE_URL}},  # no name
            {"key": "no-url.bin"},                          # no url
            "not-a-dict",                                   # not a dict
        ],
    }


def build_zip_bytes(members):
    """Build one real zip archive in memory: ``{name: text}``."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in members.items():
            archive.writestr(name, text)
    return buffer.getvalue()


def test_fetch_record_json_parses_the_document():
    payload = json.dumps(record_doc()).encode("utf-8")
    fetch = recording_opener(response=FakeResponse(200, payload))

    record, error = zenodo_bundle.fetch_record_json(fetch=fetch)

    assert error is None
    assert record["files"][0]["key"] == "Demo.zip"
    assert fetch.calls[0]["url"] == zenodo_bundle.ZENODO_API_URL


def test_fetch_record_json_non_object_json_is_a_failure():
    fetch = recording_opener(response=FakeResponse(200, b"[1, 2, 3]"))

    record, error = zenodo_bundle.fetch_record_json(fetch=fetch)

    assert record is None
    assert error


def test_fetch_record_json_absorbs_network_failure():
    fetch = recording_opener(
        exc=urllib.error.URLError("connection reset"))

    record, error = zenodo_bundle.fetch_record_json(fetch=fetch)

    assert record is None
    assert "URLError" in error


def test_parse_record_files_accepts_both_spellings_and_skips_junk():
    files = zenodo_bundle.parse_record_files(record_doc())

    assert files == (
        zenodo_bundle.BundleFile(
            name="Demo.zip", url=ZIP_FILE_URL, size=4096),
        zenodo_bundle.BundleFile(
            name="README.md", url=README_FILE_URL, size=12),
    )


def test_parse_record_files_zero_conforming_yields_empty():
    """The explicit unreadable outcome the caller turns into a failed
    run — never a guess, never a hardcoded list (T-10-03-02)."""
    assert zenodo_bundle.parse_record_files({"files": []}) == ()
    assert zenodo_bundle.parse_record_files({}) == ()
    assert zenodo_bundle.parse_record_files(
        {"files": [{"nonsense": True}]}) == ()
    assert zenodo_bundle.parse_record_files(None) == ()
    assert zenodo_bundle.parse_record_files(
        {"files": "not-a-list"}) == ()


def test_download_bundle_files_streams_in_64k_chunks(tmp_path):
    payload = b"x" * (zenodo_bundle.DOWNLOAD_CHUNK_BYTES + 100)
    fetch = recording_opener(response=FakeResponse(200, payload))
    staging = tmp_path / "staging"

    downloaded, failures = zenodo_bundle.download_bundle_files(
        (zenodo_bundle.BundleFile(
            name="Demo.zip", url=ZIP_FILE_URL, size=len(payload)),),
        staging, fetch=fetch)

    assert failures == []
    assert downloaded == [staging / "Demo.zip"]
    assert (staging / "Demo.zip").read_bytes() == payload
    # the streaming contract: bounded 64 KiB reads, not one blob read
    assert fetch.last_response.read_calls[:2] == [
        zenodo_bundle.DOWNLOAD_CHUNK_BYTES,
        zenodo_bundle.DOWNLOAD_CHUNK_BYTES]


def test_download_bundle_files_collects_per_file_failures(tmp_path):
    """A mid-download network failure is collected verbatim and the run
    continues — the CALLER (queue branch) fails the whole task (no
    byte-resume machinery in this lane by design)."""
    state = {"n": 0}

    def fetch(url, timeout=None):
        state["n"] += 1
        if state["n"] == 1:
            return FakeResponse(200, b"good bytes")
        raise urllib.error.URLError("connection reset mid-file")

    staging = tmp_path / "staging"
    files = (
        zenodo_bundle.BundleFile(name="a.zip", url=ZIP_FILE_URL,
                                 size=None),
        zenodo_bundle.BundleFile(name="b.zip", url=README_FILE_URL,
                                 size=None),
    )

    downloaded, failures = zenodo_bundle.download_bundle_files(
        files, staging, fetch=fetch)

    assert [path.name for path in downloaded] == ["a.zip"]
    assert len(failures) == 1
    assert failures[0].startswith("b.zip:")
    assert "connection reset mid-file" in failures[0]


def test_download_bundle_files_refuses_traversal_names(tmp_path):
    """A record-sourced name carrying separators never writes outside
    the staging dir (the download-side zip-slip class)."""
    fetch = recording_opener(response=FakeResponse(200, b"evil"))
    staging = tmp_path / "staging"

    downloaded, failures = zenodo_bundle.download_bundle_files(
        (zenodo_bundle.BundleFile(
            name="../escape.zip", url=ZIP_FILE_URL, size=None),),
        staging, fetch=fetch)

    assert downloaded == []
    assert failures == ["../escape.zip:unsafe_staging_name"]
    assert list(staging.iterdir()) == []


def test_download_bundle_files_should_cancel_stops_the_loop(tmp_path):
    """WR-01: the ``should_cancel`` seam — checked before each file, a
    truthy answer STOPS the loop (the partial list is the caller's to
    classify as cancelled, never a per-file failure)."""
    fetch = recording_opener(response=FakeResponse(200, b"bytes"))
    staging = tmp_path / "staging"
    files = (
        zenodo_bundle.BundleFile(name="a.zip", url=ZIP_FILE_URL,
                                 size=None),
        zenodo_bundle.BundleFile(name="b.zip", url=README_FILE_URL,
                                 size=None),
    )
    # cancel becomes visible after the FIRST file completes
    checks = {"n": 0}

    def should_cancel():
        checks["n"] += 1
        return checks["n"] > 1

    downloaded, failures = zenodo_bundle.download_bundle_files(
        files, staging, fetch=fetch, should_cancel=should_cancel)

    assert [path.name for path in downloaded] == ["a.zip"]
    assert failures == [], "the in-loop stop is never a per-file failure"
    assert [path.name for path in staging.iterdir()] == ["a.zip"]


def test_extract_bundle_archives_lands_the_tree_under_root(tmp_path):
    zip_path = tmp_path / "Demo.zip"
    zip_path.write_bytes(build_zip_bytes({
        "Demo/task/train.csv": "sequence,label\nACGT,0\n",
        "Demo/task/dev.csv": "sequence,label\nACGT,0\n",
        "Demo/task/test.csv": "sequence,label\nACGT,0\n",
    }))
    datasets_root = tmp_path / "datasets"

    extracted, problems = zenodo_bundle.extract_bundle_archives(
        [zip_path], datasets_root)

    assert (extracted, problems) == (3, [])
    assert (datasets_root / "Demo" / "task" / "train.csv").is_file()
    assert (datasets_root / "Demo" / "task" / "dev.csv").is_file()
    assert (datasets_root / "Demo" / "task" / "test.csv").is_file()


def test_extract_bundle_archives_zip_slip_guard_skips_traversal(
        tmp_path):
    """T-10-03-01 pin: a ``../`` member is skipped with a problem and
    NOTHING is written outside the datasets root."""
    zip_path = tmp_path / "slip.zip"
    zip_path.write_bytes(build_zip_bytes({
        "Demo/task/train.csv": "sequence,label\nACGT,0\n",
        "../evil.txt": "pwned",
        "/absolute-evil.txt": "pwned",
    }))
    datasets_root = tmp_path / "datasets"

    extracted, problems = zenodo_bundle.extract_bundle_archives(
        [zip_path], datasets_root)

    assert extracted == 1
    assert "zip_slip_skipped=../evil.txt" in problems
    assert "zip_slip_skipped=/absolute-evil.txt" in problems
    assert not (tmp_path / "evil.txt").exists()
    assert not Path("/absolute-evil.txt").exists()
    assert (datasets_root / "Demo" / "task" / "train.csv").is_file()


def test_extract_bundle_archives_ignores_non_zip_and_reports_corrupt(
        tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("not a zip", encoding="utf-8")
    # a STRUCTURALLY VALID zip whose member data is corrupt: consistent
    # local-header/central-directory/EOCD skeleton (is_zipfile accepts it
    # on every CPython — the old lying-EOCD fixture gambled on
    # is_zipfile internals and Python 3.14's tightened EOCD validation
    # reclassified it as non-zip), but the local file header is garbage
    # so extraction always raises BadZipFile — the corrupt-archive edge
    name = b"evil.csv"
    local = (
        b"PK\x03\x04"
        + struct.pack(
            "<5H3I2H", 20, 0, 8, 0, 0, 0, 1, 1, len(name), 0)
        + name + b"BROKEN-DATA")
    central = (
        b"PK\x01\x02"
        + struct.pack(
            "<6H3I5H2I",
            20, 20, 0, 8, 0, 0, 0, 1, 1, len(name), 0, 0, 0, 0, 0,
            len(local))
        + name)
    eocd = (
        b"PK\x05\x06"
        + struct.pack("<4H2IH", 0, 0, 1, 1, len(central), len(local), 0))
    corrupt = tmp_path / "corrupt.zip"
    corrupt.write_bytes(local + central + eocd)
    datasets_root = tmp_path / "datasets"

    extracted, problems = zenodo_bundle.extract_bundle_archives(
        [readme, corrupt], datasets_root)

    assert extracted == 0
    assert len(problems) == 1
    assert problems[0].startswith("corrupt.zip:")
    assert not list(datasets_root.rglob("*"))
