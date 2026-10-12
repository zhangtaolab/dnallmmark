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

import inspect
import re
import time
import urllib.error
from pathlib import Path

from tui.services import zenodo_bundle

CJK_RE = re.compile("[一-鿿]")

#: The live-today 404 body, verbatim from the research capture — carried
#: by the fake so the not-public row documents the exact live state.
NOT_REGISTERED_BODY = (
    b'{"status": 404, "message": "The persistent identifier is not '
    b'registered."}')


class FakeResponse:
    """A urlopen-shaped context manager (``.status`` + chunked ``read``)."""

    def __init__(self, status=200, payload=b""):
        self.status = status
        self._payload = payload
        self.read_calls = []

    def read(self, size=-1):
        self.read_calls.append(size)
        payload, self._consumed = self._payload, True
        return payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def recording_opener(response=None, exc=None):
    """An opener fake recording ``(url, timeout)`` per call."""
    calls = []

    def opener(url, timeout=None):
        calls.append({"url": url, "timeout": timeout})
        if exc is not None:
            raise exc
        return response

    opener.calls = calls
    return opener


def http_error(code, reason):
    """A urlopen-raised HTTPError shape (fp unused — the probe reads
    only ``.code`` before the with-block ever opens)."""
    return urllib.error.HTTPError(
        zenodo_bundle.ZENODO_API_URL, code, reason, None, None)


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
