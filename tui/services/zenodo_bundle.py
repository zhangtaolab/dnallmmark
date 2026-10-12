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
``tests/tui/test_import_lock.py``). Dependencies: stdlib urllib only at
this task; Task 2 adds the zipfile/json driver surface.
"""

import urllib.error
import urllib.request

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
