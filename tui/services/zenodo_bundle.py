"""
zenodo_bundle — the DATA-04 Zenodo whole-package lane (Phase 10, 10-03;
D-12): the record public probe and the bundle download/extract driver.

Contract (locked decisions + research rulings):

- D-12: record ``19135551`` is probed for publication with ONE stdlib
  GET against the frozen module constant ``ZENODO_API_URL`` (~15s
  timeout): 200 -> ``public``; HTTP 404 -> ``not_public`` (live today:
  the record is not registered); any other HTTPError, URLError,
  timeout, or unexpected exception -> ``failed``. The probe result is
  a PURE state string, session-memory only — zero persisted probe
  state (UI-SPEC auto-default 6: every mount re-probes, so the
  publication moment can never go stale). Activation of the whole
  bundle entry is exactly this answer flipping — zero code change.
- Pitfall 7 (live-probed 2026-10-12): HEAD against the records CDN
  times out while the API GET answers instantly — HEAD is NEVER used.
  The probe URL is a frozen constant; no caller input ever reaches it.
- A4: a future restricted-published record could 403; that maps to
  ``failed`` (disabled + explanation) — safe degradation, verified at
  activation time.
- Derive-never-hardcode: the bundle file list derives from the record
  API response at activation time via ``parse_record_files`` — a shape
  the defensive parser does not recognize is an explicit empty outcome
  the caller turns into a failed run, never a hardcoded filename list.
- The bundle lane has NO byte-resume machinery BY DESIGN (a re-run
  starts from scratch; per-key dataset downloads are the resumable
  path). Downloaded archives extract only into ``pipeline/datasets``
  with a zip-slip guard: every member must resolve under the datasets
  root or it is skipped with a problem, never extracted (T-10-03-01).
- ZERO new dependencies: stdlib urllib + zipfile only. requests/httpx
  are modelscope's dependencies, never the TUI's.

ZERO textual imports (the services-tier invariant, locked by
``tests/tui/test_import_lock.py``). Dependencies: stdlib (json/shutil/
urllib/zipfile/dataclasses/pathlib).
"""

import json
import shutil
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

# ===== The frozen probe target (D-12) =====

#: The record under watch — never a parameter, never recomposed.
ZENODO_RECORD_ID = "19135551"

#: The full frozen API URL (the records CDN answers GET; HEAD hangs).
ZENODO_API_URL = "https://zenodo.org/api/records/19135551"

#: The four probe states (probing itself is a screen-side transient;
#: this service answers one of these three terminal strings).
PROBE_PUBLIC = "public"
PROBE_NOT_PUBLIC = "not_public"
PROBE_FAILED = "failed"

#: The probe/download budget (T-10-03-03: a hang is a failed state,
#: never a frozen worker).
PROBE_TIMEOUT_SECONDS = 15.0

#: The staging directory name under the XDG state root (derived from
#: the record id — the only other Zenodo string constant in the repo
#: is the queue key, owned by ``download_queue``).
STAGING_DIR_NAME = "zenodo-" + ZENODO_RECORD_ID

#: The streamed copy chunk (64 KiB — bounded memory over any archive).
DOWNLOAD_CHUNK_BYTES = 65536


def probe_zenodo_public(timeout=PROBE_TIMEOUT_SECONDS, opener=None):
    """One stdlib GET against the frozen record URL (D-12).

    Pure I/O — no state, no persistence, no retries. The mapping:

    - 200 -> ``PROBE_PUBLIC``;
    - HTTPError 404 -> ``PROBE_NOT_PUBLIC`` (the live-today
      not-registered answer);
    - any other HTTPError, URLError, timeout, or unexpected exception
      -> ``PROBE_FAILED`` (the service boundary: degrade, never crash).

    Args:
        timeout (float): the per-request budget in seconds (default
            ~15; a hang maps to ``PROBE_FAILED``).
        opener: the injectable urlopen-shaped seam (``url,
            timeout=...`` -> a context manager with ``.read``); None
            wraps ``urllib.request.urlopen``.

    Returns:
        str: one of ``PROBE_PUBLIC`` / ``PROBE_NOT_PUBLIC`` /
        ``PROBE_FAILED``.
    """
    fetch = opener if opener is not None else urllib.request.urlopen
    try:
        with fetch(ZENODO_API_URL, timeout=timeout) as resp:
            status = getattr(resp, "status", None)
            return PROBE_PUBLIC if status == 200 else PROBE_FAILED
    except urllib.error.HTTPError as exc:
        return PROBE_NOT_PUBLIC if exc.code == 404 else PROBE_FAILED
    except Exception:               # noqa: BLE001 — service boundary
        return PROBE_FAILED


def fetch_record_json(timeout=PROBE_TIMEOUT_SECONDS, fetch=None):
    """GET + parse the record document (the bundle file-list source).

    Runs only after ``probe_zenodo_public`` answered ``public`` — the
    same frozen URL, the same injectable seam. Defensive by contract:
    ANY failure (network, unparseable JSON, a non-object document)
    yields ``(None, diagnostic)`` — never an exception, never a guessed
    layout.

    Args:
        timeout (float): the per-request budget in seconds.
        fetch: the urlopen-shaped seam (``url, timeout=...`` -> a
            context manager with ``.read``); None wraps
            ``urllib.request.urlopen``.

    Returns:
        tuple: ``(record, error)`` — the parsed record dict and None on
        success, or ``(None, diagnostic)`` on every failure edge.
    """
    opener = fetch if fetch is not None else urllib.request.urlopen
    try:
        with opener(ZENODO_API_URL, timeout=timeout) as resp:
            payload = resp.read()
        record = json.loads(payload.decode("utf-8", errors="replace"))
        if not isinstance(record, dict):
            return None, "record_not_an_object"
        return record, None
    except Exception as exc:        # noqa: BLE001 — service boundary
        return None, repr(exc)


@dataclass(frozen=True)
class BundleFile:
    """One conforming entry from the record's file list — pure data.

    Attributes:
        name: the bare file name (no path separators — the staging
            write refuses anything else).
        url: the download URL (``links.self`` or ``links.download``).
        size: the declared size in bytes (int or None — advisory
            only, never a gate).
    """

    name: str
    url: str
    size: int | None


def parse_record_files(record):
    """Defensively extract the file list from one record document.

    Accepts BOTH documented entry spellings per field — name from
    ``key`` or ``filename``; url from ``links.self`` or
    ``links.download`` (A4/T-10-03-02: the shape is verified at
    activation, never assumed). Non-conforming entries are skipped; a
    record with zero conforming entries yields an EMPTY tuple the
    caller turns into a failed ``record_file_list_unreadable`` run —
    never a hardcoded filename list, never a guess.

    Args:
        record (dict): the parsed record document.

    Returns:
        tuple[BundleFile, ...]: the conforming entries in record
        order (possibly empty).
    """
    if not isinstance(record, dict):
        return ()
    raw_files = record.get("files")
    if not isinstance(raw_files, list):
        return ()
    parsed = []
    for raw in raw_files:
        if not isinstance(raw, dict):
            continue
        name = raw.get("key")
        if not isinstance(name, str) or not name:
            name = raw.get("filename")
        if not isinstance(name, str) or not name:
            continue
        links = raw.get("links")
        url = None
        if isinstance(links, dict):
            url = links.get("self")
            if not isinstance(url, str) or not url:
                url = links.get("download")
        if not isinstance(url, str) or not url:
            continue
        size = raw.get("size")
        size = (size if isinstance(size, int)
                and not isinstance(size, bool) else None)
        parsed.append(BundleFile(name=name, url=url, size=size))
    return tuple(parsed)


def download_bundle_files(files, dest_dir, fetch=None):
    """Stream every bundle file into the staging dir (never raises).

    Each file copies through the injectable fetch seam in
    ``DOWNLOAD_CHUNK_BYTES`` chunks (bounded memory); per-file failures
    are collected and the run continues to the next file — the CALLER
    decides that any failure fails the whole task (the bundle lane has
    no byte-resume machinery by design; a re-run starts from scratch).
    A file name carrying path separators is refused (staging is one
    flat directory; anything else would be a traversal write).

    Args:
        files (iterable[BundleFile]): the parsed file list.
        dest_dir: the staging directory (created on demand; the caller
            resolves it under the XDG state root).
        fetch: the urlopen-shaped seam; None wraps
            ``urllib.request.urlopen``.

    Returns:
        tuple: ``(downloaded, failures)`` — the landed file paths
        (list of Path) and per-file diagnostics (list of str,
        ``"<name>:<repr>"`` shapes), either possibly empty.
    """
    opener = fetch if fetch is not None else urllib.request.urlopen
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    failures: list[str] = []
    for item in files:
        if Path(item.name).name != item.name or item.name in (".", ".."):
            failures.append(item.name + ":unsafe_staging_name")
            continue
        target = dest / item.name
        try:
            with opener(item.url, timeout=PROBE_TIMEOUT_SECONDS) as src, \
                    open(target, "wb") as dst:
                while True:
                    chunk = src.read(DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    dst.write(chunk)
        except Exception as exc:    # noqa: BLE001 — service boundary
            failures.append(item.name + ":" + repr(exc))
            continue
        downloaded.append(target)
    return downloaded, failures


def extract_bundle_archives(archives, datasets_root):
    """Extract the zip archives into the datasets tree, zip-slip
    guarded (T-10-03-01).

    Every member path resolves under ``datasets_root.resolve()`` —
    anything else (``../`` traversal, absolute paths) is SKIPPED with
    a problem, never extracted. Non-zip files are ignored (the record
    may carry READMEs); parent directories are created on demand; the
    extraction is a plain per-member copy, so a zipfile member can
    never become a symlink here.

    Args:
        archives (iterable[Path]): the downloaded file paths.
        datasets_root: the extraction root (``pipeline/datasets``).

    Returns:
        tuple: ``(extracted, problems)`` — the number of members
        extracted (int) and the skip/failure diagnostics (list of
        str, ``zip_slip_skipped=<member>`` / ``<archive>:<repr>``
        shapes).
    """
    root = Path(datasets_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    extracted = 0
    problems: list[str] = []
    for archive in archives:
        path = Path(archive)
        try:
            if not zipfile.is_zipfile(path):
                continue        # non-zip bundle members are ignored
            with zipfile.ZipFile(path) as bundle:
                for member in bundle.infolist():
                    if member.is_dir():
                        continue
                    target = (root / member.filename).resolve()
                    if not target.is_relative_to(root):
                        problems.append(
                            "zip_slip_skipped=" + member.filename)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.open(member) as src, \
                            open(target, "wb") as dst:
                        shutil.copyfileobj(
                            src, dst, DOWNLOAD_CHUNK_BYTES)
                    extracted += 1
        except (zipfile.BadZipFile, OSError) as exc:
            problems.append(path.name + ":" + repr(exc))
    return extracted, problems
