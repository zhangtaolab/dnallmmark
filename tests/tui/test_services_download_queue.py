"""
Tier-1 service tests for ``tui/services/download_queue.py`` (Phase 10,
10-01 — DATA-01/DATA-02 substrate: the persistent download queue).

Three lanes, per the plan:

- **State-machine suite** — the D-05/D-06 queue persistence contract:
  XDG state file, atomic round-trips, restart downgrade
  (``downloading`` -> ``pending`` + the ``interrupted`` flag), corrupt
  recovery (``.corrupt`` sidecar + diagnostic + a usable empty queue),
  enqueue outcome vocabulary incl. the D-08 per-key idempotence, retry
  gating, and pending-cancel removal. Missing-set derivation
  (``missing_datasets``) is computed over the committed registry + the
  committed n_audit.json (never hardcoded key-by-key).
- **Channel-resolution suite** — the R-01 primary-else-alternate URL
  rule, the R-02 46/4 shape census pinned against the committed
  registry (computed), per-shape argv composition (LIST argv, absolute
  paths, exact flag order), the degraded paths (no mirror / malformed
  repo id / unknown repo shape), and the CLI probe resolution order.
- **Engine/parser suite** — the Task 3 Popen engine over an injectable
  spawner (argv/env/pipe pins, progress parsing with integer-change
  throttling, exit-0-but-empty-include -> ``landing_incomplete``, the
  shape-C rename four cases), the parser over RECORDED stderr fixture
  files (never synthetic ideals), and cancel via a REAL sleep
  subprocess proving the ``os.killpg`` process-group termination.

Every test injects a tmp state root via ``DNALLMMARK_TUI_STATE_DIR`` —
the real ``~/.local/state/dnallmmark`` is never read or written.

See also:
    ``tui/services/download_queue.py`` — the service under test.
    ``tui/services/settings.py`` — the state-root/atomic-write seam.
    ``tui/services/gauntlet.py`` — the subprocess-discipline precedent.
"""

import json
import re
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tui.services import download_queue, registries, settings

REPO_ROOT = Path(__file__).resolve().parents[2]
CJK_RE = re.compile("[一-鿿]")

#: The canonical persisted entry field set (the exact pin — no field may
#: ever appear outside this set; credential-shaped fields are refused by
#: set equality, SC5/T-10-01-02).
CANONICAL_ENTRY_FIELDS = {
    "key", "kind", "state", "attempts", "enqueued_at", "started_at",
    "finished_at", "last_percent", "interrupted", "log_path", "problems",
    "reconcile",
}

#: A committed-registry key per channel disposition (Task 2's census
#: test recomputes the full 46/4 split; these three are stable anchors).
DOWNLOADABLE_KEY = "GUE__EPI_GM12878"        # shape A via alternates (GUE)
SHAPE_D_KEY = "Genomic_Benchmarks__coding"    # disabled with reason


def pin_state_dir(monkeypatch, tmp_path):
    """Point the TUI state root at a tmp dir — the real XDG state home
    is never touched (D-05/D-08 boundary)."""
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    return state


def fake_cli(tmp_path):
    """A present-on-disk CLI stand-in (the enqueue CLI probe just needs
    an existing path; nothing ever executes it in the fake lanes)."""
    cli = tmp_path / "modelscope-fake"
    cli.write_text("#!/bin/sh\n:", encoding="utf-8")
    cli.chmod(0o755)
    return cli


def force_cli_absent(monkeypatch, tmp_path):
    """Make the CLI probe resolve to None: sys.executable points at a
    tmp dir with NO modelscope sibling and shutil.which finds nothing
    (the repo venv DOES carry .venv/bin/modelscope — pinning the
    executable is what makes these tests hermetic)."""
    fake_bin = tmp_path / "no-cli-bin"
    fake_bin.mkdir(exist_ok=True)
    monkeypatch.setattr(sys, "executable", str(fake_bin / "python"))
    monkeypatch.setattr("shutil.which", lambda name: None)


def make_service(tmp_path, monkeypatch, **kwargs):
    """A service over a pinned tmp state root with an available CLI."""
    state = pin_state_dir(monkeypatch, tmp_path)
    kwargs.setdefault("cli_path", str(fake_cli(tmp_path)))
    service = download_queue.DownloadQueueService(**kwargs)
    return service, state


def state_file(state):
    return state / download_queue.QUEUE_FILE_NAME


def committed_registry():
    return json.loads(
        (REPO_ROOT / "pipeline" / "datasets_info.json").read_text(
            encoding="utf-8"))


# =====================================================================
# Lane 1: vocabulary + persistence shape (D-02/D-05/SC5)
# =====================================================================


def test_queue_states_vocabulary_and_schema_version_pinned():
    """D-02 verbatim five states, in order; schema_version is 1."""
    assert download_queue.QUEUE_STATES == (
        "pending", "downloading", "done", "failed", "mismatch")
    assert download_queue.SCHEMA_VERSION == 1
    assert download_queue.QUEUE_FILE_NAME == "download_queue.json"


def test_load_absent_file_yields_empty_queue_without_error(
        monkeypatch, tmp_path):
    state = pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService()

    error = service.load()

    assert error is None
    assert service.entries() == []
    assert not state_file(state).exists()   # no read ever creates it


def test_enqueue_persists_schema_one_entries_shape(
        monkeypatch, tmp_path):
    service, state = make_service(tmp_path, monkeypatch)

    outcome = service.enqueue(DOWNLOADABLE_KEY)

    assert outcome.action == "enqueued"
    doc = json.loads(state_file(state).read_text(encoding="utf-8"))
    assert doc["schema_version"] == download_queue.SCHEMA_VERSION
    assert isinstance(doc["entries"], list)
    assert len(doc["entries"]) == 1
    assert set(doc["entries"][0]) == CANONICAL_ENTRY_FIELDS


def test_persisted_entries_carry_no_credential_fields(monkeypatch, tmp_path):
    """SC5/T-10-01-02: the persisted schema has zero credential surface —
    the entry key set is EXACTLY the canonical fields (set equality
    refuses any token/secret-shaped addition)."""
    service, state = make_service(tmp_path, monkeypatch)
    service.enqueue(DOWNLOADABLE_KEY)
    service.claim_next()   # exercise the downloading transition too

    doc = json.loads(state_file(state).read_text(encoding="utf-8"))
    forbidden = {"token", "password", "credential", "credentials",
                 "api_key", "secret", "auth"}
    for entry in doc["entries"]:
        assert set(entry) == CANONICAL_ENTRY_FIELDS
        assert not (set(entry) & forbidden)
    assert set(doc) == {"schema_version", "entries"}


def test_mutator_round_trip_byte_consistent(monkeypatch, tmp_path):
    """Every mutator leaves a file a fresh load() reads back identically
    (indent=4, ensure_ascii=False via settings.atomic_write)."""
    service, state = make_service(tmp_path, monkeypatch)
    service.enqueue(DOWNLOADABLE_KEY)
    raw_first = state_file(state).read_text(encoding="utf-8")

    fresh = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    assert fresh.load() is None
    assert fresh.entries() == service.entries()

    # byte-stable: rewriting the same state changes nothing
    service.retry(DOWNLOADABLE_KEY) if service.entries()[0].state == \
        "failed" else None
    second = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    second.load()
    second.enqueue(DOWNLOADABLE_KEY)      # already_queued: no rewrite...
    assert state_file(state).read_text(encoding="utf-8") == raw_first


def test_entries_returns_frozen_copies(monkeypatch, tmp_path):
    service, _ = make_service(tmp_path, monkeypatch)
    service.enqueue(DOWNLOADABLE_KEY)

    (entry,) = service.entries()
    assert isinstance(entry, download_queue.QueueEntry)
    with pytest.raises(FrozenInstanceError):
        entry.state = "done"


def test_enqueue_new_entry_fields_and_iso_timestamps(monkeypatch, tmp_path):
    from datetime import datetime
    service, _ = make_service(tmp_path, monkeypatch)

    service.enqueue(DOWNLOADABLE_KEY)

    (entry,) = service.entries()
    assert entry.key == DOWNLOADABLE_KEY
    assert entry.kind == "dataset"
    assert entry.state == "pending"
    assert entry.attempts == 0
    assert entry.problems == ()
    assert entry.reconcile is None
    assert entry.log_path is None
    assert entry.started_at is None
    assert entry.finished_at is None
    assert entry.last_percent is None
    assert entry.interrupted is False
    datetime.fromisoformat(entry.enqueued_at)   # ISO-8601, parses


# =====================================================================
# Lane 1: enqueue outcome vocabulary (D-08 idempotence + gates)
# =====================================================================


def test_enqueue_is_idempotent_per_key_any_state(monkeypatch, tmp_path):
    """D-08: an existing entry of ANY state yields already_queued with
    no state change (even when the CLI has since gone absent)."""
    service, _ = make_service(tmp_path, monkeypatch)
    assert service.enqueue(DOWNLOADABLE_KEY).action == "enqueued"

    again = service.enqueue(DOWNLOADABLE_KEY)

    assert again.action == "already_queued"
    assert again.key == DOWNLOADABLE_KEY
    (entry,) = service.entries()
    assert entry.state == "pending"          # no state change
    assert len(service.entries()) == 1       # no duplicate row

    # an existing entry wins even when the CLI probe now fails
    service._cli_path = None
    force_cli_absent(monkeypatch, tmp_path)
    still = service.enqueue(DOWNLOADABLE_KEY)
    assert still.action == "already_queued"


def test_enqueue_unknown_key_outcome(monkeypatch, tmp_path):
    service, _ = make_service(tmp_path, monkeypatch)

    outcome = service.enqueue("NotInRegistry__nope")

    assert outcome.action == "unknown_key"
    assert outcome.key == "NotInRegistry__nope"
    assert service.entries() == []


def test_enqueue_shape_d_key_yields_disabled_with_reason_and_url(
        monkeypatch, tmp_path):
    """R-02: the 4 shape-D keys enqueue to the disabled outcome carrying
    the machine reason + the drill-down source_url."""
    service, _ = make_service(tmp_path, monkeypatch)

    outcome = service.enqueue(SHAPE_D_KEY)

    assert outcome.action == "disabled"
    assert outcome.key == SHAPE_D_KEY
    assert outcome.reason_code == "shape_d_layout"
    assert outcome.source_url and "modelscope.cn" in outcome.source_url
    assert service.entries() == []


def test_enqueue_cli_unavailable_outcome(monkeypatch, tmp_path):
    """D-01: a CLI-absent machine yields the probed cli_unavailable
    outcome — never an import error, never an exception."""
    pin_state_dir(monkeypatch, tmp_path)
    force_cli_absent(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService()

    outcome = service.enqueue(DOWNLOADABLE_KEY)

    assert outcome.action == "cli_unavailable"
    assert outcome.key == DOWNLOADABLE_KEY
    assert service.entries() == []


def test_enqueue_all_missing_enqueues_downloadable_missing_only(
        monkeypatch, tmp_path):
    """Over the committed n_audit (7 missing GUE keys, all shape A):
    enqueue_all_missing enqueues every one, returns 7, and is a no-op
    count of 0 on the second call."""
    service, _ = make_service(tmp_path, monkeypatch)
    missing = [row.key for row in service.missing_datasets()]
    assert missing, "committed n_audit must carry missing tasks"

    count = service.enqueue_all_missing()

    assert count == len(missing)
    assert {e.key for e in service.entries()} == set(missing)
    assert all(e.state == "pending" for e in service.entries())
    assert service.enqueue_all_missing() == 0   # second call: nothing new


# =====================================================================
# Lane 1: retry gating + cancel semantics (D-06)
# =====================================================================


def test_retry_gates_on_failed_or_mismatch(monkeypatch, tmp_path):
    state = pin_state_dir(monkeypatch, tmp_path)
    doc = {"schema_version": 1, "entries": [
        {"key": "k__failed", "kind": "dataset", "state": "failed",
         "attempts": 2, "enqueued_at": "2026-10-12T00:00:00+00:00",
         "started_at": None, "finished_at": None, "last_percent": 40,
         "interrupted": False, "log_path": None, "problems": ["exit_1"],
         "reconcile": None},
        {"key": "k__mismatch", "kind": "dataset", "state": "mismatch",
         "attempts": 1, "enqueued_at": "2026-10-12T00:00:00+00:00",
         "started_at": None, "finished_at": None, "last_percent": None,
         "interrupted": False, "log_path": None, "problems": [],
         "reconcile": None},
        {"key": "k__done", "kind": "dataset", "state": "done",
         "attempts": 1, "enqueued_at": "2026-10-12T00:00:00+00:00",
         "started_at": None, "finished_at": None, "last_percent": 100,
         "interrupted": False, "log_path": None, "problems": [],
         "reconcile": None},
    ]}
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_text(
        json.dumps(doc, indent=4, ensure_ascii=False), encoding="utf-8")
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    assert service.load() is None

    assert service.retry("k__failed") is True
    assert service.retry("k__mismatch") is True
    assert service.retry("k__done") is False
    assert service.retry("k__absent") is False

    by_key = {e.key: e for e in service.entries()}
    assert by_key["k__failed"].state == "pending"
    assert by_key["k__mismatch"].state == "pending"
    assert by_key["k__done"].state == "done"
    assert by_key["k__failed"].attempts == 2   # preserved across retry
    # persisted: a fresh load sees the retried states
    fresh = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    fresh.load()
    assert {e.key: e.state for e in fresh.entries()} == {
        "k__failed": "pending", "k__mismatch": "pending", "k__done": "done"}


def test_cancel_pending_removes_entry_from_file(monkeypatch, tmp_path):
    service, state = make_service(tmp_path, monkeypatch)
    service.enqueue(DOWNLOADABLE_KEY)
    service.enqueue("GUE__fungi_species_20")

    outcome = service.cancel(DOWNLOADABLE_KEY)

    assert outcome == "removed"
    doc = json.loads(state_file(state).read_text(encoding="utf-8"))
    assert [e["key"] for e in doc["entries"]] == ["GUE__fungi_species_20"]
    assert len(service.entries()) == 1


def test_cancel_absent_and_terminal_states_are_noop(monkeypatch, tmp_path):
    state = pin_state_dir(monkeypatch, tmp_path)
    doc = {"schema_version": 1, "entries": [
        {"key": "k__done", "kind": "dataset", "state": "done",
         "attempts": 1, "enqueued_at": "2026-10-12T00:00:00+00:00",
         "started_at": None, "finished_at": None, "last_percent": 100,
         "interrupted": False, "log_path": None, "problems": [],
         "reconcile": None},
    ]}
    state.mkdir(parents=True, exist_ok=True)
    before = json.dumps(doc, indent=4, ensure_ascii=False)
    state_file(state).write_text(before, encoding="utf-8")
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    service.load()

    assert service.cancel("k__never_enqueued") == "noop"
    assert service.cancel("k__done") == "noop"
    assert state_file(state).read_text(encoding="utf-8") == before


# =====================================================================
# Lane 1: restart + corrupt recovery (D-06, T-10-01-05)
# =====================================================================


def test_restart_downgrades_downloading_to_pending_interrupted(
        monkeypatch, tmp_path):
    """D-06: an entry persisted as downloading loads back as pending
    with interrupted=true; the downgrade itself persists (D-05: every
    transition writes); failed entries survive as failed."""
    state = pin_state_dir(monkeypatch, tmp_path)
    doc = {"schema_version": 1, "entries": [
        {"key": "k__midflight", "kind": "dataset", "state": "downloading",
         "attempts": 1, "enqueued_at": "2026-10-12T00:00:00+00:00",
         "started_at": "2026-10-12T00:01:00+00:00",
         "finished_at": None, "last_percent": 62, "interrupted": False,
         "log_path": None, "problems": [], "reconcile": None},
        {"key": "k__failed", "kind": "dataset", "state": "failed",
         "attempts": 3, "enqueued_at": "2026-10-12T00:00:00+00:00",
         "started_at": "2026-10-12T00:01:00+00:00",
         "finished_at": "2026-10-12T00:02:00+00:00",
         "last_percent": 10, "interrupted": False, "log_path": None,
         "problems": ["exit_1"], "reconcile": None},
    ]}
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_text(
        json.dumps(doc, indent=4, ensure_ascii=False), encoding="utf-8")

    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    error = service.load()

    assert error is None
    by_key = {e.key: e for e in service.entries()}
    assert by_key["k__midflight"].state == "pending"
    assert by_key["k__midflight"].interrupted is True
    assert by_key["k__midflight"].attempts == 1     # preserved
    assert by_key["k__midflight"].started_at == "2026-10-12T00:01:00+00:00"
    assert by_key["k__failed"].state == "failed"    # re-queueable via retry
    assert by_key["k__failed"].interrupted is False
    # the downgrade persists to disk (D-05 every-transition-persists)
    on_disk = json.loads(state_file(state).read_text(encoding="utf-8"))
    disk = {e["key"]: e for e in on_disk["entries"]}
    assert disk["k__midflight"]["state"] == "pending"
    assert disk["k__midflight"]["interrupted"] is True
    # idempotent: a second load changes nothing further
    assert service.load() is None
    assert {e.key: e.state for e in service.entries()} == {
        "k__midflight": "pending", "k__failed": "failed"}


def test_corrupt_file_moved_aside_with_diagnostic_then_usable(
        monkeypatch, tmp_path):
    """T-10-01-05: garbage bytes -> the .corrupt sidecar exists, a
    diagnostic string returns (never an exception), and the queue is
    usable afterwards."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    garbage = b"{not json at all"
    state_file(state).write_bytes(garbage)

    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    error = service.load()

    assert isinstance(error, str) and error            # a diagnostic
    assert service.entries() == []
    sidecar = state / (download_queue.QUEUE_FILE_NAME + ".corrupt")
    assert sidecar.is_file()
    assert sidecar.read_bytes() == garbage
    # usable afterwards: enqueue writes a fresh valid file
    assert service.enqueue(DOWNLOADABLE_KEY).action == "enqueued"
    doc = json.loads(state_file(state).read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1


def test_unknown_schema_version_treated_as_corrupt(monkeypatch, tmp_path):
    """A forward-dated schema (version 2) is moved aside rather than
    misread — the diagnostic names the mismatch."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_text(
        json.dumps({"schema_version": 99, "entries": []}), encoding="utf-8")

    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    error = service.load()

    assert isinstance(error, str) and "99" in error
    assert service.entries() == []
    assert (state / (download_queue.QUEUE_FILE_NAME + ".corrupt")).is_file()


# =====================================================================
# Lane 1: missing-set derivation (D-13 input; the official registry is
# the only authority, presence from the committed n_audit)
# =====================================================================


def test_missing_datasets_computed_over_committed_registry_and_n_audit(
        monkeypatch, tmp_path):
    """Rows exist exactly for official keys whose committed n_audit
    presence is MISSING (computed in the test from the same two
    committed files — never a hardcoded key list); each row carries the
    declared total and the channel disposition."""
    service, _ = make_service(tmp_path, monkeypatch)

    rows = service.missing_datasets()

    audit_tasks = registries.load_n_audit()
    expected = {
        key for key in committed_registry()
        if registries.presence_for(key, audit_tasks).status
        == registries.PRESENCE_MISSING
    }
    assert {row.key for row in rows} == expected
    assert expected, "committed n_audit must carry missing tasks"
    registry = committed_registry()
    for row in rows:
        assert isinstance(row, download_queue.MissingInfo)
        entry = registry[row.key]
        declared = sum(
            entry.get(field) or 0 for field in ("Train", "Dev", "Test"))
        assert row.declared_total == declared
        assert row.channel in ("downloadable", "disabled", "unknown")
        assert row.reason_code is None or isinstance(row.reason_code, str)
        assert row.source_url is None or "modelscope.cn" in row.source_url


def test_missing_datasets_empty_when_n_audit_unavailable(
        monkeypatch, tmp_path):
    service, _ = make_service(tmp_path, monkeypatch)
    monkeypatch.setattr(
        download_queue.registries, "load_n_audit", lambda: None)

    assert service.missing_datasets() == []


# =====================================================================
# Lane 1: module hygiene (services-tier invariants)
# =====================================================================


def test_service_module_carries_zero_inline_chinese_copy():
    source = Path(download_queue.__file__).read_text(encoding="utf-8")
    assert not CJK_RE.search(source), "inline Chinese copy in the service"


def test_service_module_never_imports_modelscope():
    """D-01: modelscope is in NO uv group — the service must stay
    importable (and import-clean) on machines without it."""
    source = Path(download_queue.__file__).read_text(encoding="utf-8")
    for pattern in ("import modelscope", "from modelscope"):
        assert pattern not in source
