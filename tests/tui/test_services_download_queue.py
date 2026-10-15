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
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from tui.services import download_queue, registries, run_config, settings

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


def test_enqueue_unknown_reasons_yield_their_own_outcome(
        monkeypatch, tmp_path):
    """WR-06: the defensive reasons (no mirror, unreadable registry)
    yield the ``unknown`` action carrying their OWN reason — never the
    shape-D ``disabled`` collapse whose toast claims a mirror layout
    the channel never resolved."""
    repo = tmp_repo_with_registry(
        tmp_path / "repo", {"DemoN__nomirror": synth_entries()[
            "DemoN__nomirror"]})
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        repo_root=repo, cli_path=str(fake_cli(tmp_path)))

    outcome = service.enqueue("DemoN__nomirror")

    assert outcome.action == "unknown", (
        "no_modelscope_mirror is a channel-unavailable state, not the "
        "shape-D mirror-layout copy"
    )
    assert outcome.reason_code == "no_modelscope_mirror"
    assert service.entries() == []

    # a registry that cannot be read: unknown + registry_unreadable
    bare = tmp_path / "bare"
    (bare / "pipeline").mkdir(parents=True)   # NO datasets_info.json
    degraded = download_queue.DownloadQueueService(
        repo_root=bare, cli_path=str(fake_cli(tmp_path)))
    outcome = degraded.enqueue("Any__key")

    assert outcome.action == "unknown"
    assert outcome.reason_code == "registry_unreadable"


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
    """Over a STAGED n_audit view (the R-03 follow-up rule: the
    committed baseline is maintainer-refreshable — 50/50 present today —
    so a missing-set test pins its own missing keys through the
    N_AUDIT_PATH seam, never the baseline): every missing DOWNLOADABLE
    row enqueues, a disabled (shape-D) missing row is skipped, and the
    second call is a no-op count of 0."""
    service, _ = make_service(tmp_path, monkeypatch)
    registry = committed_registry()
    downloadable = sorted(
        key for key in registry
        if service.resolve_channel(key) is not None
        and service.resolve_channel(key).reason_code is None)
    staged = downloadable[:2] + [SHAPE_D_KEY]
    tmp_n_audit_missing(monkeypatch, tmp_path, tasks={
        key: ({"missing": True} if key in staged
              else dict(_PRESENT_TASK_RECORD))
        for key in registry})
    missing_rows = [row.key for row in service.missing_datasets()]
    assert set(missing_rows) == set(staged), (
        "the staged view drives the missing set (2 downloadable + "
        "1 shape-D), never the committed baseline"
    )

    count = service.enqueue_all_missing()

    assert count == 2, "only the downloadable missing rows enqueue"
    assert {e.key for e in service.entries()} == set(downloadable[:2])
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


def test_claim_next_clears_the_interrupted_flag_in01(
        monkeypatch, tmp_path):
    """IN-01: the restart note's flag clears when the resume BEGINS —
    claiming the recovered entry is the moment the note's promise is
    being fulfilled, so downloading/done/failed rows never render the
    stale 'last interrupted — the channel will resume' forever."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_text(json.dumps({
        "schema_version": 1,
        "entries": [{
            "key": "k__midflight", "kind": "dataset",
            "state": "downloading", "attempts": 1,
            "enqueued_at": "2026-10-12T00:00:00+00:00",
            "started_at": "2026-10-12T00:01:00+00:00",
            "finished_at": None, "last_percent": 62,
            "interrupted": False, "log_path": None,
            "problems": [], "reconcile": None}],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    assert service.load() is None
    (entry,) = service.entries()
    assert entry.interrupted is True    # the downgrade set it

    claimed = service.claim_next()

    assert claimed.state == "downloading"
    assert claimed.interrupted is False, (
        "the claim IS the resume — the note's flag must clear here"
    )
    (entry,) = service.entries()
    assert entry.interrupted is False


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
    """Rows exist exactly for official keys whose n_audit presence is
    MISSING (computed in the test from the same registry + view — never
    a hardcoded key list); each row carries the declared total and the
    channel disposition. The R-03 follow-up rule: the presence view is a
    STAGED fixture over real registry keys (the committed baseline is
    maintainer-refreshable — 50/50 present today — so this lane never
    depends on the baseline carrying missing keys)."""
    service, _ = make_service(tmp_path, monkeypatch)
    registry = committed_registry()
    staged_missing = sorted(registry)[:2]
    tmp_n_audit_missing(monkeypatch, tmp_path, tasks={
        key: ({"missing": True} if key in staged_missing
              else dict(_PRESENT_TASK_RECORD))
        for key in registry})

    rows = service.missing_datasets()

    audit_tasks = registries.load_n_audit()
    expected = {
        key for key in registry
        if registries.presence_for(key, audit_tasks).status
        == registries.PRESENCE_MISSING
    }
    assert {row.key for row in rows} == expected == set(staged_missing)
    for row in rows:
        assert isinstance(row, download_queue.MissingInfo)
        entry = registry[row.key]
        declared = sum(
            entry.get(field) or 0 for field in ("Train", "Dev", "Test"))
        assert row.declared_total == declared
        assert row.channel in ("downloadable", "disabled", "unknown")
        assert row.reason_code is None or isinstance(row.reason_code, str)
        assert row.source_url is None or "modelscope.cn" in row.source_url


#: A present n_audit task record — the refresh-stable fixture filler
#: (missing-set lanes stage real registry keys as missing around it;
#: the committed baseline itself is never expected to carry either
#: state — R-03 refreshes it).
_PRESENT_TASK_RECORD = {"missing": False, "splits": {
    "train": {"rows": 1}, "dev": {"rows": 1}, "test": {"rows": 1}}}


def test_missing_datasets_empty_when_n_audit_unavailable(
        monkeypatch, tmp_path):
    service, _ = make_service(tmp_path, monkeypatch)
    monkeypatch.setattr(
        download_queue.registries, "load_n_audit", lambda: None)

    assert service.missing_datasets() == []


def tmp_n_audit_missing(monkeypatch, tmp_path, tasks):
    """Point ``registries.N_AUDIT_PATH`` at a tmp committed view with the
    given tasks mapping — the CR-01 regression lane's presence source
    (the committed file stays read-only; monkeypatch is the seam)."""
    path = tmp_path / "n-audit-view" / "n_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"tasks": tasks}), encoding="utf-8")
    monkeypatch.setattr(registries, "N_AUDIT_PATH", path)
    return path


def done_reconciled_entry(key, verdict="pass"):
    """One persisted-form queue entry: done with a measured reconcile
    (the D-11 overlay source ``reconciled_rows`` reads)."""
    measured = ({"train": 10, "dev": 2, "test": 2}
                if verdict == "pass" else None)
    return {
        "key": key, "kind": "dataset", "state": "done", "attempts": 1,
        "enqueued_at": "2026-10-12T00:00:00+00:00",
        "started_at": "2026-10-12T00:01:00+00:00",
        "finished_at": "2026-10-12T00:02:00+00:00",
        "last_percent": 100, "interrupted": False, "log_path": None,
        "problems": [],
        "reconcile": {"verdict": verdict, "declared": {"Train": 10},
                      "measured": measured, "unified_eval_n": 2},
    }


def test_missing_datasets_flips_over_done_reconciled_entries_cr01(
        monkeypatch, tmp_path):
    """CR-01 (the release-blocking regression): the D-11 flip reaches the
    missing pane — over a SEEDED REAL service + tmp committed n_audit, a
    key whose committed record is missing but whose queue entry is done
    with a measured reconcile LEAVES ``missing_datasets`` (the merged
    view), while a mismatched key never flips (semantic 6)."""
    repo = tmp_repo_with_registry(tmp_path / "repo", {
        "Demo__task": SHAPE_A_ENTRY,
        "DemoM__mm": {
            "Dataset_path": "datasets/DemoM/mm_task",
            "download_url":
                "https://www.modelscope.cn/datasets/lgq12697/GUE",
            "Train": 5, "Dev": 1, "Test": 1},
    })
    tmp_n_audit_missing(monkeypatch, tmp_path, tasks={
        "Demo__task": {"missing": True},
        "DemoM__mm": {"missing": True},
    })
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    state.mkdir(parents=True, exist_ok=True)
    mismatch_entry = done_reconciled_entry("DemoM__mm", verdict="mismatch")
    mismatch_entry["state"] = "mismatch"
    (state / download_queue.QUEUE_FILE_NAME).write_text(json.dumps({
        "schema_version": download_queue.SCHEMA_VERSION,
        "entries": [
            done_reconciled_entry("Demo__task"),
            mismatch_entry,
        ],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        cli_path=str(fake_cli(tmp_path)))

    rows = service.missing_datasets()

    # the done+reconciled key LEFT the missing list; the mismatched key
    # never flips (UI-SPEC semantic 6) — the pane mirrors the selection
    # screen's merged view, not the committed file alone
    assert [row.key for row in rows] == ["DemoM__mm"], (
        "a reconcile-pass (done) key must leave the missing pane "
        "(merge_presence over reconciled_rows); a mismatched key stays"
    )
    # the merged view through the service's OWN state path flips presence
    merged = service.merged_audit_tasks()
    assert registries.presence_for(
        "Demo__task", merged).status == registries.PRESENCE_PRESENT
    assert registries.presence_for(
        "DemoM__mm", merged).status == registries.PRESENCE_MISSING
    # the committed file is read-only to this path (the merge is pure)
    assert registries.load_n_audit()["Demo__task"]["missing"] is True


def test_merged_audit_tasks_overlays_this_services_state_path_cr01(
        monkeypatch, tmp_path):
    """The merged view reads the SERVICE's own state path (an explicit
    ``state_path`` stays authoritative) and is committed-view-only when
    nothing reconciled — the exact substrate the selection screen and
    the data-manager summary both consume."""
    repo = tmp_repo_with_registry(
        tmp_path / "repo", {"Demo__task": SHAPE_A_ENTRY})
    tmp_n_audit_missing(monkeypatch, tmp_path, tasks={
        "Demo__task": {"missing": True}})
    state_a = tmp_path / "state-a"
    state_b = tmp_path / "state-b"
    for state in (state_a, state_b):
        state.mkdir(parents=True, exist_ok=True)
    (state_a / download_queue.QUEUE_FILE_NAME).write_text(json.dumps({
        "schema_version": download_queue.SCHEMA_VERSION,
        "entries": [done_reconciled_entry("Demo__task")],
    }, indent=4, ensure_ascii=False), encoding="utf-8")

    seeded = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state_a / "download_queue.json",
        cli_path=str(fake_cli(tmp_path)))
    empty = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state_b / "download_queue.json",
        cli_path=str(fake_cli(tmp_path)))

    assert download_queue.merge_presence(
        registries.load_n_audit(), {},
    )["Demo__task"]["missing"] is True      # committed view unchanged
    assert seeded.merged_audit_tasks()["Demo__task"]["missing"] is False
    assert empty.merged_audit_tasks()["Demo__task"]["missing"] is True


# =====================================================================
# The full presence view (DCL-03, 261014-dcl — presence_rows, the same
# merged n_audit/reconcile substrate as the missing view; CR-01)
# =====================================================================


def test_presence_rows_covers_every_official_key_with_declared_totals(
        monkeypatch, tmp_path):
    """Every committed official registry key (50) carries exactly one
    row, in registry file order, with statuses inside the registries
    presence vocabulary and ``declared_total`` from the registry entry
    (computed in the test from the same registry — never hardcoded)."""
    service, _ = make_service(tmp_path, monkeypatch)
    registry = committed_registry()

    rows = service.presence_rows()

    assert [row.key for row in rows] == list(registry)
    assert len(rows) == 50
    for row in rows:
        assert isinstance(row, download_queue.PresenceRow)
        entry = registry[row.key]
        assert row.declared_total == sum(
            entry.get(field) or 0 for field in ("Train", "Dev", "Test"))
        assert row.status in (
            registries.PRESENCE_PRESENT, registries.PRESENCE_MISSING,
            registries.PRESENCE_UNKNOWN, registries.PRESENCE_UNAVAILABLE,
        )


def test_presence_rows_missing_set_equals_missing_datasets_keys_cr01(
        monkeypatch, tmp_path):
    """CR-01: the full view's MISSING-status key set equals the missing
    pane's key set EXACTLY (both derive from the same merged view); a
    done-reconciled key flips in BOTH together while a mismatched key
    never flips in either."""
    repo = tmp_repo_with_registry(tmp_path / "repo", {
        "Demo__task": SHAPE_A_ENTRY,
        "DemoM__mm": {
            "Dataset_path": "datasets/DemoM/mm_task",
            "download_url":
                "https://www.modelscope.cn/datasets/lgq12697/GUE",
            "Train": 5, "Dev": 1, "Test": 1},
    })
    tmp_n_audit_missing(monkeypatch, tmp_path, tasks={
        "Demo__task": {"missing": True},
        "DemoM__mm": {"missing": True},
    })
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    state.mkdir(parents=True, exist_ok=True)
    mismatch_entry = done_reconciled_entry("DemoM__mm", verdict="mismatch")
    mismatch_entry["state"] = "mismatch"
    (state / download_queue.QUEUE_FILE_NAME).write_text(json.dumps({
        "schema_version": download_queue.SCHEMA_VERSION,
        "entries": [
            done_reconciled_entry("Demo__task"),
            mismatch_entry,
        ],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        cli_path=str(fake_cli(tmp_path)))

    rows = service.presence_rows()

    statuses = {row.key: row.status for row in rows}
    assert statuses["Demo__task"] == registries.PRESENCE_PRESENT, (
        "the done+reconciled key flipped present in the full view"
    )
    assert statuses["DemoM__mm"] == registries.PRESENCE_MISSING
    missing_keys = {row.key for row in rows
                    if row.status == registries.PRESENCE_MISSING}
    assert missing_keys == {row.key for row in service.missing_datasets()}, (
        "the full view's missing set and the missing pane move together"
    )


def test_presence_rows_absent_n_audit_still_lists_keys_degraded(
        monkeypatch, tmp_path):
    """With the committed n_audit absent, keys still list with degraded
    statuses (overlay-present or unknown), never an exception."""
    service, _ = make_service(tmp_path, monkeypatch)
    monkeypatch.setattr(
        download_queue.registries, "load_n_audit", lambda: None)

    rows = service.presence_rows()

    assert len(rows) == 50
    assert {row.status for row in rows} <= {
        registries.PRESENCE_UNKNOWN, registries.PRESENCE_PRESENT}


def test_presence_rows_unreadable_registry_yields_empty(tmp_path):
    """The missing_datasets tolerance twin: an unreadable official
    registry yields [], never an exception."""
    bare = tmp_path / "bare"
    (bare / "pipeline").mkdir(parents=True)   # NO datasets_info.json
    service = download_queue.DownloadQueueService(
        repo_root=bare, cli_path=str(fake_cli(tmp_path)))

    assert service.presence_rows() == []


# =====================================================================
# Lane 1: module hygiene (services-tier invariants)
# =====================================================================


def test_service_module_carries_zero_inline_chinese_copy():
    source = Path(download_queue.__file__).read_text(encoding="utf-8")
    assert not CJK_RE.search(source), "inline Chinese copy in the service"


def test_service_module_never_imports_modelscope():
    """D-01: modelscope is in NO uv group — the service must stay
    importable (and import-clean) on machines without it. The scan is
    AST-based (261014-mlc): the KIND_MODEL lane's FIXED program constant
    carries the subprocess's own ``from modelscope...`` line as STRING
    data (the -I child is the only place dnallm/modelscope code runs) —
    a raw-text scan would false-positive on it; the AST scan keeps the
    invariant stronger, not weaker (aliased/try-guarded imports surface
    too)."""
    import ast

    tree = ast.parse(
        Path(download_queue.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert not (name == "modelscope"
                        or name.startswith("modelscope.")), (
                f"the service module must never import modelscope: {name}"
            )
            assert not (name == "dnallm"
                        or name.startswith("dnallm.")), (
                f"the service module must never import dnallm: {name}"
            )


# =====================================================================
# Lane 2: R-01/R-02 channel resolution + CLI probe + argv composition
# =====================================================================


def tmp_repo_with_registry(tmp_path, entries):
    """A tmp repo root carrying a synthetic official dataset registry —
    channel resolution is derived from registry fields, so the shape
    pins run over controlled entries with a tmp local_dir."""
    pipeline = tmp_path / "pipeline"
    pipeline.mkdir(parents=True, exist_ok=True)
    (pipeline / "datasets_info.json").write_text(
        json.dumps(entries), encoding="utf-8")
    return tmp_path


def synth_entries():
    """One synthetic entry per disposition (repos from the R-02 table)."""
    return {
        "Demo__task": {
            "Dataset_path": "datasets/Demo/task",
            "download_url":
                "https://www.modelscope.cn/datasets/lgq12697/GUE",
            "download_url_alternates":
                "https://huggingface.co/datasets/whatever",
            "Train": 10, "Dev": 2, "Test": 2},
        "DemoA2__alt": {
            "Dataset_path": "datasets/Demo/alt_task",
            "download_url":
                "https://drive.google.com/file/d/XYZ/view",
            "download_url_alternates":
                "https://www.modelscope.cn/datasets/lgq12697/GUE"},
        "DemoB__leaf": {
            "Dataset_path": "datasets/DemoB/leaf_task",
            "download_url": "https://www.modelscope.cn/datasets/"
                            "zhangtaolab/cross_species_leaf_absolute_"
                            "translation"},
        "PDLLMs_datasets__plant-multi-species-H3K27ac": {
            "Dataset_path":
                "datasets/PDLLMs_datasets/plant-multi-species-H3K27ac",
            "download_url": "https://www.modelscope.cn/datasets/"
                            "zhangtaolab/plant-multi-species-histone-"
                            "modifications"},
        "DemoD__parquet": {
            "Dataset_path": "datasets/DemoD/parquet_task",
            "download_url":
                "https://www.modelscope.cn/datasets/lgq12697/"
                "Genomic_Benchmarks"},
        "DemoU__future": {
            "Dataset_path": "datasets/DemoU/future_task",
            "download_url": "https://www.modelscope.cn/datasets/"
                            "someone/brand_new_repo"},
        "DemoM__bad": {
            "Dataset_path": "datasets/DemoM/bad_task",
            "download_url":
                "https://www.modelscope.cn/datasets/a/b/c"},
        "DemoN__nomirror": {
            "Dataset_path": "datasets/DemoN/nomirror_task",
            "download_url":
                "https://drive.google.com/file/d/ABC/view",
            "download_url_alternates":
                "https://huggingface.co/datasets/other"},
    }


def service_over(tmp_repo, tmp_path):
    return download_queue.DownloadQueueService(
        repo_root=tmp_repo, cli_path=str(fake_cli(tmp_path)))


def is_modelscope(url):
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower()
    return host == "modelscope.cn" or host.endswith(".modelscope.cn")


def test_r02_census_46_downloadable_4_disabled_over_committed_registry(
        monkeypatch, tmp_path):
    """THE R-02 gate: over the committed official registry, exactly 46
    keys resolve downloadable (38 shape A + 5 shape B + 3 shape C) and
    4 are disabled with reason shape_d_layout; every downloadable
    spec's repo_id matches its shape-table row (computed key-by-key —
    registry/mirror drift surfaces here as a loud failure, never a
    silent bad download)."""
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    registry = committed_registry()

    per_shape = {"A": [], "B": [], "C": []}
    disabled = {}
    for key in registry:
        spec = service.resolve_channel(key)
        assert spec is not None, key
        if spec.reason_code is None:
            per_shape[spec.shape].append(key)
        else:
            disabled[key] = spec.reason_code

    assert {shape: len(keys) for shape, keys in per_shape.items()} == {
        "A": 38, "B": 5, "C": 3}
    assert set(disabled) == {
        "Genomic_Benchmarks__coding",
        "Genomic_Benchmarks__human_vs_worm",
        "Genomic_Benchmarks__regulatory_region_type",
        "PDLLMs_datasets__plant-multi-species-open-chromatin"}
    assert {reason for reason in disabled.values()} == {
        download_queue.REASON_SHAPE_D}
    table = {
        "A": download_queue.SHAPE_A_REPOS,
        "B": download_queue.SHAPE_B_REPOS,
        "C": {download_queue.SHAPE_C_REPO},
    }
    for shape, keys in per_shape.items():
        for key in keys:
            spec = service.resolve_channel(key)
            assert spec.repo_id in table[shape], (key, spec.repo_id)
            assert spec.source_url is not None


def test_r01_gue_primary_google_drive_resolves_via_alternates(
        monkeypatch, tmp_path):
    """R-01 pinned: a GUE key's primary is the shared Google Drive
    file, so the modelscope mirror in download_url_alternates wins —
    and the winning URL rides the spec as data."""
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    registry = committed_registry()

    spec = service.resolve_channel("GUE__EPI_GM12878")

    assert spec.reason_code is None
    assert spec.repo_id == "lgq12697/GUE"
    assert spec.source_url == registry["GUE__EPI_GM12878"][
        "download_url_alternates"]
    assert is_modelscope(spec.source_url)


def test_r01_modelscope_primary_ignores_alternates(monkeypatch, tmp_path):
    """R-01 pinned (computed key): a key whose PRIMARY is already the
    modelscope mirror resolves from the primary; the alternates field
    is never consulted."""
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    registry = committed_registry()
    primary_ms = [key for key, entry in registry.items()
                  if is_modelscope(entry.get("download_url", ""))]
    assert primary_ms, "committed registry must carry modelscope primaries"

    key = primary_ms[0]
    spec = service.resolve_channel(key)

    assert spec.reason_code is None
    assert spec.source_url == registry[key]["download_url"]


def test_shape_a_argv_list_absolute_exact_flag_order(monkeypatch,
                                                     tmp_path):
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel("Demo__task")
    argv = download_queue.compose_download_argv(spec, "/fake/cli")

    assert spec.shape == "A"
    assert spec.final_task_dir == "task"
    assert argv == [
        "/fake/cli", "download", "--dataset", "lgq12697/GUE",
        "--local_dir", str(repo / "pipeline" / "datasets" / "Demo"),
        "--include", "task/*", "--exclude", "*.DS_Store"]
    assert isinstance(argv, list)                 # never a shell string
    assert Path(argv[argv.index("--local_dir") + 1]).is_absolute()


def test_shape_b_argv_whole_repo_local_dir_no_include(monkeypatch,
                                                      tmp_path):
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel("DemoB__leaf")
    argv = download_queue.compose_download_argv(spec, "/fake/cli")

    assert spec.shape == "B"
    assert argv == [
        "/fake/cli", "download", "--dataset",
        "zhangtaolab/cross_species_leaf_absolute_translation",
        "--local_dir",
        str(repo / "pipeline" / "datasets" / "DemoB" / "leaf_task"),
        "--exclude", "*.DS_Store"]
    assert "--include" not in argv


def test_shape_c_argv_subtree_include_plus_rename_pair(monkeypatch,
                                                       tmp_path):
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel(
        "PDLLMs_datasets__plant-multi-species-H3K27ac")
    argv = download_queue.compose_download_argv(spec, "/fake/cli")

    assert spec.shape == "C"
    assert argv == [
        "/fake/cli", "download", "--dataset",
        "zhangtaolab/plant-multi-species-histone-modifications",
        "--local_dir",
        str(repo / "pipeline" / "datasets" / "PDLLMs_datasets"),
        "--include", "H3K27ac/*", "--exclude", "*.DS_Store"]
    assert spec.rename == (
        "PDLLMs_datasets/H3K27ac",
        "PDLLMs_datasets/plant-multi-species-H3K27ac")
    assert spec.final_task_dir == "plant-multi-species-H3K27ac"


def test_shape_d_composes_no_argv_carries_reason(monkeypatch, tmp_path):
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel("DemoD__parquet")

    assert spec.reason_code == download_queue.REASON_SHAPE_D
    assert download_queue.channel_state(spec) == "disabled"
    assert download_queue.compose_download_argv(spec, "/fake/cli") \
        is None


def test_malformed_repo_id_degrades_never_reaches_argv(monkeypatch,
                                                       tmp_path):
    """T-10-01-01: a registry URL whose path yields a multi-segment
    repo id fails the allowlist regex — unknown disposition, no argv."""
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel("DemoM__bad")

    assert spec.reason_code == download_queue.REASON_MALFORMED_REPO_ID
    assert download_queue.channel_state(spec) == "unknown"
    assert download_queue.compose_download_argv(spec, "/fake/cli") \
        is None


def test_unknown_repo_degrades_disabled(monkeypatch, tmp_path):
    """Registry/mirror evolution tolerance: a repo absent from the
    R-02 table is disabled with reason unknown_repo_shape, never a
    crash and never a guessed argv."""
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel("DemoU__future")

    assert spec.reason_code == download_queue.REASON_UNKNOWN_REPO
    assert download_queue.channel_state(spec) == "disabled"
    assert download_queue.compose_download_argv(spec, "/fake/cli") \
        is None


def test_no_modelscope_mirror_degrades_unknown(monkeypatch, tmp_path):
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel("DemoN__nomirror")

    assert spec.reason_code == download_queue.REASON_NO_MIRROR
    assert download_queue.channel_state(spec) == "unknown"
    assert spec.source_url is None


# ===== CLI probe resolution order (live-probed; -m never works) =====


def test_cli_probe_explicit_arg_wins(monkeypatch, tmp_path):
    """An explicit cli_path returns verbatim even when a venv sibling
    exists — the seam tests and the sleep-cancel lane inject here."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "modelscope").write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(bin_dir / "python"))

    resolved = download_queue.resolve_modelscope_cli("/explicit/cli")

    assert resolved == Path("/explicit/cli")


def test_cli_probe_venv_sibling(monkeypatch, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "modelscope").write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(bin_dir / "python"))
    monkeypatch.setattr("shutil.which", lambda name: None)

    resolved = download_queue.resolve_modelscope_cli()

    assert resolved == bin_dir / "modelscope"


def test_cli_probe_which_fallback(monkeypatch, tmp_path):
    bin_dir = tmp_path / "elsewhere"        # NO modelscope sibling
    bin_dir.mkdir(parents=True)
    monkeypatch.setattr(sys, "executable", str(bin_dir / "python"))
    monkeypatch.setattr("shutil.which",
                        lambda name: "/usr/local/bin/modelscope")

    resolved = download_queue.resolve_modelscope_cli()

    assert resolved == Path("/usr/local/bin/modelscope")


def test_cli_probe_absent_yields_none(monkeypatch, tmp_path):
    bin_dir = tmp_path / "empty"            # no sibling, which -> None
    bin_dir.mkdir()
    monkeypatch.setattr(sys, "executable", str(bin_dir / "python"))
    monkeypatch.setattr("shutil.which", lambda name: None)

    assert download_queue.resolve_modelscope_cli() is None


# =====================================================================
# Lane 3: the Popen execution engine — spawn/stream/reap/cancel +
# landing check + shape-C rename + the recorded-fixture parser
# =====================================================================

import io
import os
import subprocess
import threading
import time

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SUCCESS_MARKER = "Successfully Downloaded from dataset"
START_MARKER = "Downloading Dataset to directory"


class ChunkedStream:
    """A pipe-like stream that yields pre-scripted byte chunks (the
    reader thread's incremental-parse view of a real stderr)."""

    def __init__(self, chunks):
        self.chunks = [c.encode("utf-8") if isinstance(c, str) else c
                       for c in chunks]

    def read(self, n=-1):
        return self.chunks.pop(0) if self.chunks else b""


class FakePopen:
    """A Popen-shaped object (poll/wait/kill/terminate/pid + pipe
    streams) — the FakeRunner idiom adapted to the Popen seam."""

    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode_value = returncode
        self.pid = 424242

        def as_stream(data):
            if hasattr(data, "read"):
                return data
            if isinstance(data, str):
                data = data.encode("utf-8")
            return io.BytesIO(data)

        self.stdout = as_stream(stdout)
        self.stderr = as_stream(stderr)
        self.killed = False

    def wait(self, timeout=None):
        return self.returncode_value

    def poll(self):
        return self.returncode_value

    def kill(self):
        self.killed = True
        self.returncode_value = -9

    def terminate(self):
        self.returncode_value = -15


class FakeSpawner:
    """The injectable Popen seam recording every spawn."""

    def __init__(self, popen=None, exc=None):
        self.popen = popen if popen is not None else FakePopen()
        self.exc = exc
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "kwargs": dict(kwargs)})
        if self.exc is not None:
            raise self.exc
        return self.popen


SHAPE_A_ENTRY = {
    "Dataset_path": "datasets/Demo/task",
    "download_url": "https://www.modelscope.cn/datasets/lgq12697/GUE",
    "download_url_alternates":
        "https://huggingface.co/datasets/whatever",
    "Train": 10, "Dev": 2, "Test": 2,
}


def engine_service(tmp_path, monkeypatch, spawner, entries=None,
                   cli=None, runner=None):
    """A service over a tmp repo (shape-A synthetic entry) + tmp state
    root + injected spawner — the offline engine lane.

    ``runner`` is the reconcile-leg seam (10-02): None injects the
    default PASSING fake (the landed->done transition now requires a
    passing reconcile — the 10-01 engine tests stay offline); tests of
    the gate itself inject failing/mismatching runners explicitly."""
    repo = tmp_repo_with_registry(
        tmp_path / "repo", entries or {"Demo__task": SHAPE_A_ENTRY})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    cli_path = str(cli) if cli is not None else str(fake_cli(tmp_path))
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        spawner=spawner, runner=(runner if runner is not None
                                 else passing_reconcile_runner()),
        cli_path=cli_path)
    assert service.enqueue("Demo__task").action == "enqueued"
    service.claim_next()
    return service, repo, state


def land_csvs(repo, group, task, splits=("train", "dev", "test")):
    task_dir = repo / "pipeline" / "datasets" / group / task
    task_dir.mkdir(parents=True, exist_ok=True)
    for split in splits:
        (task_dir / (split + ".csv")).write_text(
            "sequence,label\nACGT,0\n", encoding="utf-8")
    return task_dir


# ===== the parser over RECORDED captures (never synthetic ideals) =====


def test_success_fixture_parses_to_full_completion():
    text = (FIXTURES_DIR / "modelscope_stderr_success.txt").read_text(
        encoding="utf-8")

    files, items = download_queue.parse_progress(text)

    assert items == 100
    assert files["emp_H3/train.csv"] == 100
    assert files["emp_H3/dev.csv"] == 100
    assert len(files) == 4


def test_interrupted_fixture_parses_midflight_and_strips_ansi():
    """ANSI [A escapes + CR churn parse to the mid-file percent; no
    completion percent exists anywhere in the capture."""
    text = (FIXTURES_DIR / "modelscope_stderr_interrupted.txt").read_text(
        encoding="utf-8")

    files, items = download_queue.parse_progress(text)

    assert items == 50
    assert files["emp_H3/train.csv"] == 41
    clean = download_queue.clean_chunk(text)
    assert "\x1b" not in clean
    assert "\r" not in clean


def test_unparseable_chunk_yields_indeterminate_none():
    files, items = download_queue.parse_progress("nothing to see here\n")
    assert files == {}
    assert items is None


def test_first_real_error_line_skips_pkg_resources_noise():
    text = ("UserWarning: pkg_resources is deprecated as an API. x\n"
            "import pkg_resources\n"
            "Traceback (most recent call last):\n"
            "OSError: [Errno 2] boom")
    assert download_queue.first_real_error_line(text) == \
        "Traceback (most recent call last):"


def test_first_real_error_line_none_on_noise_only():
    text = "UserWarning: pkg_resources is deprecated as an API. x\n" \
           "import pkg_resources\n\n"
    assert download_queue.first_real_error_line(text) is None


# ===== spawn discipline (argv/env/pipe pins over the fake spawner) =====


def test_spawn_pins_list_argv_env_passthrough_pipes_session(
        monkeypatch, tmp_path):
    spawner = FakeSpawner(FakePopen(returncode=0))
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner)
    land_csvs(repo, "Demo", "task")

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "done"
    (call,) = spawner.calls
    argv = call["argv"]
    assert isinstance(argv, list)               # never a shell string
    assert argv[0].endswith("modelscope-fake")  # the injected CLI
    assert argv[argv.index("--dataset") + 1] == "lgq12697/GUE"
    assert Path(argv[argv.index("--local_dir") + 1]).is_absolute()
    kwargs = call["kwargs"]
    assert kwargs["env"] == dict(os.environ)    # EXACTLY, zero overrides
    assert kwargs["start_new_session"] is True
    assert kwargs["stdout"] == subprocess.PIPE
    assert kwargs["stderr"] == subprocess.PIPE


def test_progress_callback_fires_once_per_integer_change(
        monkeypatch, tmp_path):
    """Duplicates never re-fire; the indeterminate-until-parsed contract
    holds (nothing fires before the first parseable percent)."""
    line = "Downloading [a/train.csv]: {p}%|x| y/y [00:00<00:00]\n"
    stderr = ChunkedStream([
        "some unparseable chatter\n",
        line.format(p=0), line.format(p=0),
        line.format(p=25), line.format(p=25),
        line.format(p=50),
        line.format(p=100), line.format(p=100),
    ])
    spawner = FakeSpawner(FakePopen(returncode=0, stderr=stderr))
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner)
    land_csvs(repo, "Demo", "task")
    fired = []

    event = service.run_task(
        "Demo__task", run_id="r1",
        progress_cb=lambda key, pct: fired.append((key, pct)))

    assert fired == [("Demo__task", 0), ("Demo__task", 25),
                     ("Demo__task", 50), ("Demo__task", 100)]
    assert event.last_percent == 100


def test_stdout_markers_detected_as_data_booleans(monkeypatch, tmp_path):
    stdout = ("Downloading Dataset to directory: /tmp/x\n"
              "Successfully Downloaded from dataset lgq12697/GUE.\n")
    spawner = FakeSpawner(FakePopen(returncode=0, stdout=stdout))
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner)
    land_csvs(repo, "Demo", "task")

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "done"
    assert "start_marker=true" in event.details
    assert "success_marker=true" in event.details


# ===== exit classification + the Pitfall-3 landing gate =====


def test_exit_zero_with_success_marker_but_no_files_fails_landing(
        monkeypatch, tmp_path):
    """THE exit-0-but-empty trap: the CLI reports success for an empty
    filtered include set — exit 0 + the success marker still fails
    unless every split CSV landed (Pitfall 3)."""
    stdout = ("Downloading Dataset to directory: /tmp/x\n"
              "Successfully Downloaded from dataset lgq12697/GUE.\n")
    spawner = FakeSpawner(FakePopen(returncode=0, stdout=stdout))
    service, _, _ = engine_service(tmp_path, monkeypatch, spawner)
    # NOTE: no CSVs landed under pipeline/datasets/Demo/task

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    assert event.problems == ("landing_incomplete",)
    assert "missing=Demo/task/train.csv" in event.details
    assert "missing=Demo/task/dev.csv" in event.details
    assert "missing=Demo/task/test.csv" in event.details
    (entry,) = service.entries()
    assert entry.state == "failed"
    assert entry.log_path == "logs/Demo__task.log"


def test_partial_landing_missing_one_split_fails_naming_it(
        monkeypatch, tmp_path):
    spawner = FakeSpawner(FakePopen(returncode=0))
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner)
    land_csvs(repo, "Demo", "task", splits=("train", "dev"))

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    assert event.problems == ("landing_incomplete",)
    assert "missing=Demo/task/test.csv" in event.details


def test_nonzero_exit_fails_with_code_and_log(monkeypatch, tmp_path):
    spawner = FakeSpawner(FakePopen(returncode=7))
    service, _, state = engine_service(tmp_path, monkeypatch, spawner)

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    assert event.problems == ("exit_7",)
    assert "exit_code=7" in event.details
    log_file = state / "logs" / "Demo__task.log"
    assert log_file.is_file()
    assert event.log_path == "logs/Demo__task.log"


def test_cli_absent_at_run_time_fails_without_spawning(
        monkeypatch, tmp_path):
    spawner = FakeSpawner()
    # enqueue through the existing fake CLI, THEN take the CLI away —
    # a nowhere-pointing explicit path now refuses at enqueue time too
    # (the 10-06 availability gate), so the run-time absence is staged
    # by clearing the explicit pointer after the enqueue
    service, _, _ = engine_service(tmp_path, monkeypatch, spawner)
    service._cli_path = None
    force_cli_absent(monkeypatch, tmp_path)

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    assert event.problems == ("cli_unavailable",)
    assert spawner.calls == []


def test_spawner_launch_failure_absorbed_as_failed_event(
        monkeypatch, tmp_path):
    spawner = FakeSpawner(exc=OSError("[Errno 13] Permission denied"))
    service, _, _ = engine_service(tmp_path, monkeypatch, spawner)

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    assert event.problems == ("subprocess_error",)
    assert "Permission denied" in " ".join(event.details)


# ===== the shape-C post-landing rename (four cases) =====


SHAPE_C_ENTRY = {
    "Dataset_path": "datasets/PDLLMs_datasets/plant-multi-species-H3K27ac",
    "download_url": "https://www.modelscope.cn/datasets/zhangtaolab/"
                    "plant-multi-species-histone-modifications",
}


SHAPE_C_KEY = "PDLLMs_datasets__plant-multi-species-H3K27ac"


def c_service(tmp_path, monkeypatch, spawner):
    repo = tmp_repo_with_registry(
        tmp_path / "repo", {SHAPE_C_KEY: SHAPE_C_ENTRY})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        spawner=spawner,
        runner=passing_reconcile_runner(key=SHAPE_C_KEY),
        cli_path=str(fake_cli(tmp_path)))
    assert service.enqueue(SHAPE_C_KEY).action == "enqueued"
    service.claim_next()
    return service, repo


def test_shape_c_rename_source_present_target_absent(monkeypatch,
                                                     tmp_path):
    """Case 1: the repo subtree landed; rename to the registry dir name
    then the landing check passes -> done."""
    service, repo = c_service(tmp_path, monkeypatch, FakeSpawner())
    land_csvs(repo, "PDLLMs_datasets", "H3K27ac")

    event = service.run_task(SHAPE_C_KEY, run_id="r1")

    assert event.state == "done"
    assert not (repo / "pipeline" / "datasets" / "PDLLMs_datasets"
                / "H3K27ac").exists()          # source moved
    land_csvs(repo, "PDLLMs_datasets", "plant-multi-species-H3K27ac")


def test_shape_c_rename_target_already_complete_skips(monkeypatch,
                                                      tmp_path):
    """Case 2: the target already carries all three CSVs (a prior run's
    rename) — skip, idempotent done."""
    service, repo = c_service(tmp_path, monkeypatch, FakeSpawner())
    land_csvs(repo, "PDLLMs_datasets", "plant-multi-species-H3K27ac")

    event = service.run_task(SHAPE_C_KEY, run_id="r1")

    assert event.state == "done"


def test_shape_c_rename_target_incomplete_source_present_fails(
        monkeypatch, tmp_path):
    """Case 3: an incomplete target exists while the source also exists
    — operator data is NEVER overwritten; the failure names it."""
    service, repo = c_service(tmp_path, monkeypatch, FakeSpawner())
    land_csvs(repo, "PDLLMs_datasets", "H3K27ac")            # source
    land_csvs(repo, "PDLLMs_datasets", "plant-multi-species-H3K27ac",
              splits=("train",))                             # partial

    event = service.run_task(SHAPE_C_KEY, run_id="r1")

    assert event.state == "failed"
    assert event.problems == ("rename_target_exists",)
    # nothing was overwritten: both trees intact
    assert (repo / "pipeline" / "datasets" / "PDLLMs_datasets"
            / "H3K27ac" / "train.csv").is_file()
    target = (repo / "pipeline" / "datasets" / "PDLLMs_datasets"
              / "plant-multi-species-H3K27ac")
    assert (target / "train.csv").is_file()
    assert not (target / "dev.csv").exists()


def test_shape_c_rename_source_absent_falls_to_landing_check(
        monkeypatch, tmp_path):
    """Case 4: neither source nor target — the rename is a no-op and
    the landing check fails with the missing files named."""
    service, _repo = c_service(tmp_path, monkeypatch, FakeSpawner())

    event = service.run_task(SHAPE_C_KEY, run_id="r1")

    assert event.state == "failed"
    assert event.problems == ("landing_incomplete",)
    assert "missing=PDLLMs_datasets/plant-multi-species-H3K27ac/train.csv" \
        in event.details


# ===== log capture (D-03) =====


def test_log_file_round_trip_verbatim_with_pkg_resources_skip(
        monkeypatch, tmp_path):
    stdout = ("Downloading Dataset to directory: /tmp/x\n"
              "Successfully Downloaded from dataset lgq12697/GUE.\n")
    stderr = ("UserWarning: pkg_resources is deprecated as an API. x\n"
              "import pkg_resources\n"
              "some real stderr failure line\n")
    spawner = FakeSpawner(FakePopen(returncode=1, stdout=stdout,
                                    stderr=stderr))
    service, _, state = engine_service(tmp_path, monkeypatch, spawner)

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    log_file = state / event.log_path
    text = log_file.read_text(encoding="utf-8")
    assert "Downloading Dataset to directory: /tmp/x" in text   # verbatim
    assert "UserWarning: pkg_resources is deprecated" in text   # verbatim
    assert download_queue.first_real_error_line(text.split("[stderr]\n")[-1]) \
        == "some real stderr failure line"
    (entry,) = service.entries()
    assert entry.log_path == "logs/Demo__task.log"


# ===== claim_next (D-04) =====


def test_claim_next_claims_head_pending_in_file_order(monkeypatch,
                                                      tmp_path):
    service, _ = make_service(tmp_path, monkeypatch)
    service.enqueue(DOWNLOADABLE_KEY)
    service.enqueue("GUE__fungi_species_20")

    first = service.claim_next()
    second = service.claim_next()
    third = service.claim_next()

    assert first.key == DOWNLOADABLE_KEY
    assert first.state == "downloading"
    assert first.attempts == 1
    assert first.started_at is not None
    assert second.key == "GUE__fungi_species_20"
    assert third is None
    # persisted: the file carries both downloading rows
    doc = json.loads(
        (service._state_path).read_text(encoding="utf-8"))
    assert [e["state"] for e in doc["entries"]] == [
        "downloading", "downloading"]


# ===== the REAL-subprocess cancel lane (killpg, no modelscope) =====


def test_cancel_mid_run_terminates_process_group_real_subprocess(
        monkeypatch, tmp_path):
    """A spawner-default run against an inline sleep script (injected
    CLI + tmp local_dir) proves the killpg termination, the
    cancelled_by_operator classification, and partials-retained
    semantics — no modelscope dependency."""
    repo = tmp_repo_with_registry(
        tmp_path / "repo", {"Demo__task": SHAPE_A_ENTRY})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    sleep_cli = tmp_path / "modelscope"
    sleep_cli.write_text("#!/bin/sh\nexec sleep 60\n", encoding="utf-8")
    sleep_cli.chmod(0o755)
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        cli_path=str(sleep_cli))
    assert service.enqueue("Demo__task").action == "enqueued"
    service.claim_next()

    result = {}
    worker = threading.Thread(
        target=lambda: result.__setitem__(
            "event", service.run_task("Demo__task", run_id="cancel-1")))
    worker.start()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline \
            and "Demo__task" not in service._active:
        time.sleep(0.02)
    assert "Demo__task" in service._active, "spawn never became active"
    proc = service._active["Demo__task"]
    pgid = proc.pid          # start_new_session: pgid == child pid

    outcome = service.cancel("Demo__task")

    assert outcome == "signalled"
    worker.join(timeout=20)
    assert not worker.is_alive(), "run_task did not return after cancel"
    event = result["event"]
    assert event.state == "failed"
    assert event.problems == ("cancelled_by_operator",)
    assert "exit_code=" in " ".join(event.details)
    (entry,) = service.entries()
    assert entry.state == "failed"
    assert entry.problems == ("cancelled_by_operator",)
    # the WHOLE process group is gone (killpg reached sleep too — a
    # bare terminate() would have orphaned it holding the group open)
    assert proc.poll() is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(pgid, 0)
    # partials retained: the service wrote nothing into the repo tree
    datasets_tree = repo / "pipeline" / "datasets"
    assert not datasets_tree.exists() or not any(
        datasets_tree.rglob("*"))


# =====================================================================
# Lane 4: the D-09/D-10 reconcile kernel (10-02 Task 1) — the audit
# subprocess leg, the verdict semantics, and the run_task done gate
# =====================================================================

import shutil
from types import SimpleNamespace

#: The whole-dir overlay override env name (the registry_loader
#: contract; the reconcile/reaudit legs pin it to an EMPTY temp dir).
OVERLAY_ENV = "DNALLMMARK_CUSTOM_REGISTRY_DIR"

#: The four flags the reconcile leg MUST carry on every invocation (the
#: anti-clobber boundary, T-10-02-01 — with all four at temp values the
#: audit subprocess can never reach its committed default outputs).
RECONCILE_OUTPUT_FLAGS = ("--registry-dir", "--datasets-root",
                          "--data-dir", "--subsets-out", "--data-md")


class FakeReconcileRunner:
    """The gauntlet FakeRunner idiom at the runner seam: records every
    call; ``on_call`` executes while the service's staging tempdir is
    still ALIVE, so tests capture the staged registry content and write
    the temp n_audit.json the service will parse."""

    def __init__(self, on_call=None, exc=None, result=None):
        self.calls = []
        self.on_call = on_call
        self.exc = exc
        self.result = result

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "kwargs": dict(kwargs)})
        if self.exc is not None:
            raise self.exc
        if self.on_call is not None:
            self.on_call(list(argv), kwargs)
        return (self.result if self.result is not None
                else SimpleNamespace(returncode=0, stdout="", stderr=""))


def write_temp_n_audit(argv, tasks):
    """Write a tasks-shaped n_audit.json into the call's --data-dir (the
    temp output the service parses)."""
    data_dir = Path(argv[argv.index("--data-dir") + 1])
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "n_audit.json").write_text(
        json.dumps({"tasks": tasks}), encoding="utf-8")


def audit_record(train, dev, test):
    """One present n_audit task record with the given measured rows."""
    def split(rows):
        return {"rows": rows, "non_acgt_chars": 0, "strict_survivors": rows,
                "n_tolerant_survivors": rows}
    return {
        "missing": False,
        "unified_eval_n": test,
        "splits": {"train": split(train), "dev": split(dev),
                   "test": split(test)},
    }


def passing_reconcile_runner(key="Demo__task", train=10, dev=2, test=2):
    """The default engine-lane runner: writes a PASSING temp n_audit for
    ``key`` with rows matching the synthetic entry's declarations."""
    return FakeReconcileRunner(
        on_call=lambda argv, kwargs: write_temp_n_audit(
            argv, {key: audit_record(train, dev, test)}))


def reconcile_service(tmp_path, monkeypatch, runner, entries=None):
    """A service over a tmp repo + tmp state root with the reconcile
    runner injected (reconcile_dataset never touches queue state — the
    tmp state root exists only for constructor parity)."""
    repo = tmp_repo_with_registry(
        tmp_path / "rrepo", entries or {"Demo__task": SHAPE_A_ENTRY})
    state = tmp_path / "rstate"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        runner=runner, cli_path=str(fake_cli(tmp_path)))
    return service, repo


# ===== vocabulary + constructor knobs =====


def test_reconcile_vocabulary_verdicts_env_and_default_timeout():
    """The verdict vocabulary, the overlay env constant, and the 300s
    default reconcile timeout (T-10-02-05)."""
    assert download_queue.VERDICT_PASS == "pass"
    assert download_queue.VERDICT_MISMATCH == "mismatch"
    assert download_queue.VERDICT_FAILED == "failed"
    assert download_queue.CUSTOM_DIR_ENV == OVERLAY_ENV
    assert download_queue.DEFAULT_TIMEOUT_RECONCILE == 300


def test_default_runner_replaces_undecodable_stdout_bytes(tmp_path):
    """WR-05 behavioral proof: with the pinned kwargs (text=True +
    errors="replace"), a subprocess emitting non-UTF-8 bytes decodes to
    replacement characters — never a UnicodeDecodeError out of
    communicate() (the GBK-locale failure class)."""
    script = tmp_path / "emit.py"
    script.write_text(
        "import sys\n"
        "sys.stdout.buffer.write(b'\\xff\\xfe mojibake\\n')\n",
        encoding="utf-8")

    proc = download_queue._default_runner(
        [sys.executable, str(script)],
        capture_output=True, text=True, errors="replace",
        timeout=30, env=dict(os.environ))

    assert proc.returncode == 0
    assert "�" in proc.stdout, (
        "the undecodable byte must decode to the replacement char"
    )


def test_reconcile_timeout_knob_overridable(tmp_path, monkeypatch):
    captured = {}
    runner = FakeReconcileRunner(on_call=lambda argv, kwargs:
                                 captured.update(kwargs))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)
    service._timeout_reconcile = 7

    service.reconcile_dataset("Demo__task", run_id="r1")

    assert captured["timeout"] == 7


# ===== the staging discipline (T-10-02-01: four temp outputs, one env
# override, candidate-only registry, ABSOLUTE Dataset_path) =====


def capture_staging(captured, key="Demo__task"):
    """on_call hook: snapshot argv/env/kwargs + the staged registry
    while the tempdir is alive, then write a passing temp n_audit."""
    def hook(argv, kwargs):
        captured["argv"] = list(argv)
        captured["env"] = kwargs["env"]
        captured["kwargs"] = dict(kwargs)
        registry_dir = Path(argv[argv.index("--registry-dir") + 1])
        captured["registry_dir"] = registry_dir
        captured["staged"] = json.loads(
            (registry_dir / "datasets_info.json").read_text(
                encoding="utf-8"))
        write_temp_n_audit(argv, {key: audit_record(10, 2, 2)})
    return hook


def test_reconcile_argv_pins_all_output_flags_at_temp_paths(
        tmp_path, monkeypatch):
    """Every reconcile invocation carries ALL four output flags with
    values under the service's own staging temp root — never the
    script's committed repo defaults (the clobber boundary)."""
    captured = {}
    runner = FakeReconcileRunner(on_call=capture_staging(captured))
    service, repo = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "pass"
    argv = captured["argv"]
    assert argv[0] == sys.executable                      # never a shell
    assert argv[1] == str(repo / "script" / "audit_n_frequencies.py")
    assert Path(argv[1]).is_absolute()
    for flag in RECONCILE_OUTPUT_FLAGS:
        assert flag in argv, flag
    data_dir = Path(argv[argv.index("--data-dir") + 1])
    registry_dir = captured["registry_dir"]
    datasets_root = Path(argv[argv.index("--datasets-root") + 1])
    staging_root = data_dir.parent
    # all four outputs live under ONE staging temp root, outside the repo
    assert registry_dir.parent == staging_root
    assert datasets_root.parent == staging_root
    assert Path(argv[argv.index("--subsets-out") + 1]).parent == data_dir
    assert Path(argv[argv.index("--data-md") + 1]).parent == data_dir
    for flag in RECONCILE_OUTPUT_FLAGS:
        assert REPO_ROOT not in \
            Path(argv[argv.index(flag) + 1]).parents, flag
    # the runner-call kwargs (the gauntlet _invoke shape)
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["timeout"] == 300
    # WR-05: the reconcile leg's decode policy matches _pump's
    assert captured["kwargs"]["errors"] == "replace"


def test_reconcile_env_exactly_one_override_pinned_to_empty_dir(
        tmp_path, monkeypatch):
    """env == os.environ plus EXACTLY the CUSTOM_DIR_ENV override, and
    the pinned dir exists and is EMPTY at call time (the operator's real
    custom overlay can never leak into a reconcile, T-10-02-02). The
    existence/emptiness pins run INSIDE the hook — the staging tempdir
    is cleaned before reconcile_dataset returns (by design)."""
    captured = {}

    def hook(argv, kwargs):
        overlay = Path(kwargs["env"][OVERLAY_ENV])
        captured["env"] = kwargs["env"]
        captured["overlay_is_dir"] = overlay.is_dir()
        captured["overlay_empty"] = list(overlay.iterdir()) == []
        write_temp_n_audit(argv, {"Demo__task": audit_record(10, 2, 2)})

    runner = FakeReconcileRunner(on_call=hook)
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    service.reconcile_dataset("Demo__task", run_id="r1")

    assert captured["overlay_is_dir"] is True
    assert captured["overlay_empty"] is True       # EMPTY at call time
    expected = dict(os.environ)
    expected[OVERLAY_ENV] = captured["env"][OVERLAY_ENV]
    assert captured["env"] == expected             # exactly one override


def test_reconcile_stages_candidate_only_registry_absolute_path(
        tmp_path, monkeypatch):
    """The staged temp registry contains EXACTLY the one key, with its
    Dataset_path ABSOLUTIZED against the pipeline dir (the pathlib join
    replaces --datasets-root, making that root inert — gauntlet Pitfall
    3)."""
    captured = {}
    runner = FakeReconcileRunner(on_call=capture_staging(captured))
    service, repo = reconcile_service(tmp_path, monkeypatch, runner)

    service.reconcile_dataset("Demo__task", run_id="r1")

    staged = captured["staged"]
    assert set(staged) == {"Demo__task"}          # candidate-only
    staged_path = staged["Demo__task"]["Dataset_path"]
    assert Path(staged_path).is_absolute()
    assert staged_path == str(
        (repo / "pipeline" / "datasets" / "Demo" / "task").resolve())
    # the staged registry lives under the staging temp root, not the repo
    assert captured["registry_dir"] not in repo.parents
    assert (repo / "pipeline" / "datasets_info.json").read_text(
        encoding="utf-8") != json.dumps(staged)   # official file untouched


# ===== the failure edges (never an exception, never a done) =====


def test_reconcile_timeout_absorbed_as_failed(tmp_path, monkeypatch):
    runner = FakeReconcileRunner(
        exc=subprocess.TimeoutExpired(cmd="audit", timeout=300))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.ok is False
    assert outcome.verdict == "failed"
    assert outcome.problems[0] == "timeout"
    assert "timeout_seconds=300" in outcome.problems
    assert outcome.measured is None


def test_reconcile_nonzero_exit_failed_with_verbatim_raw(tmp_path,
                                                         monkeypatch):
    result = SimpleNamespace(returncode=2, stdout="partial out\n",
                             stderr="boom traceback\n")
    runner = FakeReconcileRunner(result=result)
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "failed"
    assert "exit_nonzero" in outcome.problems
    assert "exit_code=2" in outcome.problems
    assert outcome.raw_output == "partial out\nboom traceback\n"


def test_reconcile_launch_exception_absorbed(tmp_path, monkeypatch):
    runner = FakeReconcileRunner(exc=OSError("[Errno 2] No such file"))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "failed"
    assert "subprocess_error" in outcome.problems[0]
    assert "No such file" in outcome.problems[1]


def test_reconcile_unparseable_n_audit_failed(tmp_path, monkeypatch):
    def write_garbage(argv, kwargs):
        data_dir = Path(argv[argv.index("--data-dir") + 1])
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "n_audit.json").write_text("{not json", encoding="utf-8")
    runner = FakeReconcileRunner(on_call=write_garbage)
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "failed"
    assert "n_audit_unreadable" in outcome.problems


def test_reconcile_key_absent_from_tasks_failed(tmp_path, monkeypatch):
    runner = FakeReconcileRunner(on_call=lambda argv, kwargs:
                                 write_temp_n_audit(
                                     argv, {"Other__key": audit_record(1, 1, 1)}))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "failed"
    assert "key_absent_from_n_audit" in outcome.problems


def test_reconcile_registry_unreadable_failed_never_raises(
        tmp_path, monkeypatch):
    """A repo without a readable official registry is a failed outcome
    (absorbed), never an exception across the service boundary."""
    repo = tmp_path / "bare-repo"
    (repo / "pipeline").mkdir(parents=True)      # NO datasets_info.json
    state = tmp_path / "rstate"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    service = download_queue.DownloadQueueService(
        repo_root=repo, runner=FakeReconcileRunner(),
        cli_path=str(fake_cli(tmp_path)))

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "failed"
    assert "registry_unreadable" in outcome.problems


def test_reconcile_unknown_key_failed(tmp_path, monkeypatch):
    service, _ = reconcile_service(tmp_path, monkeypatch,
                                   FakeReconcileRunner())

    outcome = service.reconcile_dataset("NotInRegistry__x", run_id="r1")

    assert outcome.verdict == "failed"
    assert "unknown_key" in outcome.problems


# ===== the verdict semantics (the gauntlet _audit_verdict, official
# declared side from the registry Train/Dev/Test) =====


def test_reconcile_verdict_pass_carries_declared_and_measured(
        tmp_path, monkeypatch):
    runner = passing_reconcile_runner()          # rows 10/2/2 == declared
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.ok is True
    assert outcome.verdict == "pass"
    assert outcome.problems == ()
    assert outcome.declared == {"Train": 10, "Dev": 2, "Test": 2}
    assert outcome.measured == {"train": 10, "dev": 2, "test": 2}
    assert outcome.unified_eval_n == 2


def test_reconcile_verdict_mismatch_names_split_and_both_numbers(
        tmp_path, monkeypatch):
    """A declared-vs-measured inequality is a MISMATCH verdict whose
    problem names the split and BOTH numbers (the banner's {n}/{m})."""
    runner = passing_reconcile_runner(train=3)   # declared 10, measured 3
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.ok is False
    assert outcome.verdict == "mismatch"
    assert "Train_mismatch_declared=10_measured=3" in outcome.problems
    assert outcome.declared == {"Train": 10, "Dev": 2, "Test": 2}
    assert outcome.measured == {"train": 3, "dev": 2, "test": 2}


def test_reconcile_verdict_missing_true_is_mismatch(tmp_path, monkeypatch):
    runner = FakeReconcileRunner(
        on_call=lambda argv, kwargs: write_temp_n_audit(
            argv, {"Demo__task": {"missing": True, "unified_eval_n": None,
                                  "splits": None}}))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "mismatch"
    assert "missing=true" in outcome.problems


def test_reconcile_verdict_zero_rows_is_mismatch_with_data(
        tmp_path, monkeypatch):
    record = audit_record(0, 2, 2)               # train measured zero
    runner = FakeReconcileRunner(
        on_call=lambda argv, kwargs: write_temp_n_audit(
            argv, {"Demo__task": record}))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "mismatch"
    assert "train_rows=0" in outcome.problems
    assert outcome.measured["train"] == 0        # the banner's data


def test_reconcile_verdict_bool_rows_rejected(tmp_path, monkeypatch):
    record = audit_record(10, 2, 2)
    record["splits"]["dev"]["rows"] = True       # bool is NOT an int
    runner = FakeReconcileRunner(
        on_call=lambda argv, kwargs: write_temp_n_audit(
            argv, {"Demo__task": record}))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "mismatch"
    assert "dev_rows=True" in outcome.problems


def test_reconcile_verdict_zero_unified_eval_n_is_mismatch(
        tmp_path, monkeypatch):
    record = audit_record(10, 2, 2)
    record["unified_eval_n"] = 0
    runner = FakeReconcileRunner(
        on_call=lambda argv, kwargs: write_temp_n_audit(
            argv, {"Demo__task": record}))
    service, _ = reconcile_service(tmp_path, monkeypatch, runner)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.verdict == "mismatch"
    assert "unified_eval_n=0" in outcome.problems


def test_reconcile_absent_declaration_skips_that_split(
        tmp_path, monkeypatch):
    """The gauntlet rule: an entry with NO Train declaration skips the
    train comparison entirely — a differing measured train still PASSES
    (rows>0 and unified_eval_n>0 are the only gates for that split)."""
    entry = dict(SHAPE_A_ENTRY)
    entry.pop("Train")                            # absent declaration
    runner = passing_reconcile_runner(train=99)   # measured 99, declared absent
    service, _ = reconcile_service(
        tmp_path, monkeypatch, runner, entries={"Demo__task": entry})

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.ok is True
    assert outcome.verdict == "pass"
    assert outcome.declared == {"Dev": 2, "Test": 2}
    assert outcome.measured == {"train": 99, "dev": 2, "test": 2}


# ===== the REAL audit subprocess lane (CPU, sub-second, no GPU/dnallm;
# the test_services_gauntlet.py precedent — the script + registry_loader
# copied into a tmp repo so a controlled registry + fixture CSVs feed
# the REAL kernels) =====


def real_audit_repo(tmp_path, declared, rows=None):
    """A tmp repo carrying the REAL audit script + registry_loader, a
    synthetic one-key registry with the given DECLARED counts, and
    fixture CSVs whose actual row counts are ``rows`` (default = the
    declared counts; pure-ACGT sequences so every row survives
    strict)."""
    repo = tmp_path / "real-repo"
    (repo / "script").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "script" / "audit_n_frequencies.py",
                repo / "script" / "audit_n_frequencies.py")
    (repo / "pipeline").mkdir()
    shutil.copy(REPO_ROOT / "pipeline" / "registry_loader.py",
                repo / "pipeline" / "registry_loader.py")
    train, dev, test = declared
    if rows is None:
        rows = declared
    (repo / "pipeline" / "datasets_info.json").write_text(json.dumps({
        "Demo__task": {
            "Dataset_path": "datasets/Demo/task",
            "download_url":
                "https://www.modelscope.cn/datasets/lgq12697/GUE",
            "download_url_alternates":
                "https://huggingface.co/datasets/whatever",
            "Train": train, "Dev": dev, "Test": test,
        }}), encoding="utf-8")
    task_dir = repo / "pipeline" / "datasets" / "Demo" / "task"
    task_dir.mkdir(parents=True)
    for split, count in (("train", rows[0]), ("dev", rows[1]),
                         ("test", rows[2])):
        lines = ["sequence,label"]
        lines += [f"ACGTACGTAC,{index}" for index in range(count)]
        (task_dir / (split + ".csv")).write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
    return repo


def real_reconcile_service(tmp_path, monkeypatch, repo):
    state = tmp_path / "real-state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    return download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        cli_path=str(fake_cli(tmp_path)))         # default REAL runner


def test_reconcile_real_subprocess_pass_over_fixture_csvs(
        tmp_path, monkeypatch):
    """D-09 end-to-end: the real audit script counts the fixture CSVs;
    matching declarations reconcile to PASS with the measured ints."""
    repo = real_audit_repo(tmp_path, declared=(4, 2, 2))
    service = real_reconcile_service(tmp_path, monkeypatch, repo)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.ok is True
    assert outcome.verdict == "pass"
    assert outcome.problems == ()
    assert outcome.measured == {"train": 4, "dev": 2, "test": 2}
    assert outcome.unified_eval_n == 2
    assert outcome.raw_output                        # verbatim captured


def test_reconcile_real_subprocess_mismatch_names_numbers_no_deletion(
        tmp_path, monkeypatch):
    """A deliberately wrong declared count is a MISMATCH naming the split
    and both numbers — and NOTHING is deleted (D-07)."""
    repo = real_audit_repo(tmp_path, declared=(999, 2, 2), rows=(4, 2, 2))
    service = real_reconcile_service(tmp_path, monkeypatch, repo)

    outcome = service.reconcile_dataset("Demo__task", run_id="r1")

    assert outcome.ok is False
    assert outcome.verdict == "mismatch"
    assert "Train_mismatch_declared=999_measured=4" in outcome.problems
    assert outcome.measured == {"train": 4, "dev": 2, "test": 2}
    task_dir = repo / "pipeline" / "datasets" / "Demo" / "task"
    for split in ("train", "dev", "test"):
        assert (task_dir / (split + ".csv")).is_file()   # D-07: intact


# ===== the run_task done gate (the 10-01 amendment: done = landed AND
# reconcile pass) =====


def test_run_task_done_populates_entry_reconcile(monkeypatch, tmp_path):
    """done now requires the reconcile pass; the entry's reconcile field
    carries declared/measured/unified_eval_n/verdict (the overlay source
    10-05 consumes via reconciled_rows)."""
    spawner = FakeSpawner(FakePopen(returncode=0))
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner)
    land_csvs(repo, "Demo", "task")

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "done"
    assert "reconcile_verdict=pass" in event.details
    (entry,) = service.entries()
    assert entry.state == "done"
    assert entry.reconcile == {
        "verdict": "pass",
        "declared": {"Train": 10, "Dev": 2, "Test": 2},
        "measured": {"train": 10, "dev": 2, "test": 2},
        "unified_eval_n": 2,
    }


def test_run_task_reconcile_mismatch_lands_mismatch_state(
        monkeypatch, tmp_path):
    """A reconcile mismatch lands the entry in state mismatch carrying
    declared and measured numbers — and deletes nothing (D-07)."""
    spawner = FakeSpawner(FakePopen(returncode=0))
    runner = passing_reconcile_runner(train=3)    # declared 10, measured 3
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner,
                                      runner=runner)
    landed = land_csvs(repo, "Demo", "task")

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "mismatch"
    assert "Train_mismatch_declared=10_measured=3" in event.problems
    assert "reconcile_verdict=mismatch" in event.details
    (entry,) = service.entries()
    assert entry.state == "mismatch"
    assert entry.reconcile["verdict"] == "mismatch"
    assert entry.reconcile["declared"] == {"Train": 10, "Dev": 2, "Test": 2}
    assert entry.reconcile["measured"] == {"train": 3, "dev": 2, "test": 2}
    for split in ("train", "dev", "test"):
        assert (landed / (split + ".csv")).is_file()   # D-07: intact


def test_run_task_reconcile_failed_lands_failed_state(monkeypatch,
                                                      tmp_path):
    """A failed reconcile (timeout here) can never produce done — the
    entry lands failed with the reconcile problem codes."""
    spawner = FakeSpawner(FakePopen(returncode=0))
    runner = FakeReconcileRunner(
        exc=subprocess.TimeoutExpired(cmd="audit", timeout=300))
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner,
                                      runner=runner)
    land_csvs(repo, "Demo", "task")

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    assert "timeout" in event.problems
    (entry,) = service.entries()
    assert entry.state == "failed"
    assert entry.reconcile is None


def test_run_task_log_carries_reconcile_section(monkeypatch, tmp_path):
    """The verbatim log gains a [reconcile] section carrying the audit
    subprocess output (D-03 drill-down completeness)."""
    result = SimpleNamespace(returncode=2, stdout="", stderr="audit blew up")
    spawner = FakeSpawner(FakePopen(returncode=0))
    service, repo, state = engine_service(
        tmp_path, monkeypatch, spawner,
        runner=FakeReconcileRunner(result=result))
    land_csvs(repo, "Demo", "task")

    service.run_task("Demo__task", run_id="r1")

    log_text = (state / "logs" / "Demo__task.log").read_text(
        encoding="utf-8")
    assert "[reconcile]" in log_text
    assert "audit blew up" in log_text


# =====================================================================
# The D-11 presence overlay (10-02 Task 2) — merge_presence +
# reconciled_rows, the pure substrate the unchanged Phase 8
# presence_for consumes (semantic 6: only reconcile-PASS keys flip)
# =====================================================================


def committed_tasks_shape():
    """A tasks-shaped dict in the committed n_audit form: one present
    key with real splits, one missing key (splits null)."""
    return {
        "GUE__present_task": {
            "missing": False,
            "unified_eval_n": 2000,
            "splits": {
                "train": {"rows": 10000, "non_acgt_chars": 0},
                "dev": {"rows": 2000, "non_acgt_chars": 0},
                "test": {"rows": 2000, "non_acgt_chars": 0},
            },
        },
        "GUE__missing_task": {
            "missing": True, "unified_eval_n": None, "splits": None},
    }


def test_merge_presence_flips_missing_to_present_with_measured_ints():
    """THE flip (semantic 6): a reconcile-pass key overlaid onto the
    committed view reads PRESENCE_PRESENT through the UNCHANGED
    presence_for, with the exact measured integers."""
    merged = download_queue.merge_presence(
        committed_tasks_shape(), {"GUE__missing_task": (7, 3, 3)})

    presence = registries.presence_for("GUE__missing_task", merged)

    assert presence.status == registries.PRESENCE_PRESENT
    assert presence.rows == (7, 3, 3)


def test_merge_presence_non_overlaid_keys_read_exactly_as_before():
    audit_tasks = committed_tasks_shape()
    before = json.loads(json.dumps(audit_tasks["GUE__present_task"]))

    merged = download_queue.merge_presence(
        audit_tasks, {"GUE__missing_task": (7, 3, 3)})

    assert merged["GUE__present_task"] == before
    assert registries.presence_for(
        "GUE__present_task", merged).rows == (10000, 2000, 2000)
    assert set(merged) == {"GUE__present_task", "GUE__missing_task"}


def test_merge_presence_none_audit_tasks_overlay_only_serves_presence():
    """A missing/corrupt committed n_audit + a non-empty overlay still
    serves presence_for (the column stays usable from live truth
    alone)."""
    merged = download_queue.merge_presence(None, {"K__x": (5, 2, 2)})

    assert merged == {"K__x": {
        "missing": False,
        "splits": {"train": {"rows": 5}, "dev": {"rows": 2},
                   "test": {"rows": 2}},
    }}
    assert registries.presence_for(
        "K__x", merged).status == registries.PRESENCE_PRESENT


def test_merge_presence_registry_drift_key_absent_from_audit_appears():
    """An overlay key the committed audit never carried simply appears —
    the overlay IS the newer truth (drift tolerance)."""
    merged = download_queue.merge_presence(
        committed_tasks_shape(), {"Brand__new_key": (9, 1, 1)})

    assert registries.presence_for(
        "Brand__new_key", merged).rows == (9, 1, 1)


def test_merge_presence_is_pure_no_mutation_no_io():
    """Pure data composition: the inputs are never mutated (deep copy
    compare), and an empty overlay returns an equal-but-new dict."""
    audit_tasks = committed_tasks_shape()
    snapshot = json.loads(json.dumps(audit_tasks))
    overlay = {"GUE__missing_task": (7, 3, 3)}

    merged = download_queue.merge_presence(audit_tasks, overlay)

    assert audit_tasks == snapshot                    # input untouched
    assert overlay == {"GUE__missing_task": (7, 3, 3)}
    assert merged is not audit_tasks                  # a NEW dict
    empty = download_queue.merge_presence(audit_tasks, {})
    assert empty == audit_tasks and empty is not audit_tasks


def test_merge_presence_overlaid_value_shape_is_tasks_shaped():
    """The overlaid record carries exactly the fields presence_for
    reads: missing False + splits.{train,dev,test}.rows."""
    merged = download_queue.merge_presence({}, {"K__y": (1, 2, 3)})
    record = merged["K__y"]
    assert record["missing"] is False
    assert set(record["splits"]) == {"train", "dev", "test"}
    assert [record["splits"][s]["rows"] for s in ("train", "dev", "test")] \
        == [1, 2, 3]


# ===== reconciled_rows (the overlay source; read-only + tolerant) =====


def queue_doc(entries):
    return {"schema_version": 1, "entries": entries}


def entry_raw(key, state, measured=None, verdict="pass"):
    reconcile = (None if measured is None else {
        "verdict": verdict,
        "declared": {"Train": measured[0], "Dev": measured[1],
                     "Test": measured[2]},
        "measured": {"train": measured[0], "dev": measured[1],
                     "test": measured[2]},
        "unified_eval_n": measured[2],
    })
    return {"key": key, "kind": "dataset", "state": state,
            "attempts": 1, "enqueued_at": "2026-10-12T00:00:00+00:00",
            "started_at": None, "finished_at": None, "last_percent": 100,
            "interrupted": False, "log_path": None, "problems": [],
            "reconcile": reconcile}


def write_queue_state(state, doc):
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_text(
        json.dumps(doc, indent=4, ensure_ascii=False), encoding="utf-8")


def test_reconciled_rows_derives_from_done_entries_only(
        monkeypatch, tmp_path):
    """Only state-done entries with a populated reconcile.measured
    contribute {key: (train, dev, test)} — mismatch and failed entries
    NEVER enter the overlay (semantic 6), and done-without-reconcile is
    skipped."""
    state = pin_state_dir(monkeypatch, tmp_path)
    write_queue_state(state, queue_doc([
        entry_raw("K__done", "done", measured=(10, 2, 2)),
        entry_raw("K__mismatch", "mismatch", measured=(3, 2, 2),
                  verdict="mismatch"),
        entry_raw("K__failed_reconcile", "failed"),
        entry_raw("K__done_no_reconcile", "done", measured=None),
        entry_raw("K__pending", "pending"),
    ]))

    rows = download_queue.reconciled_rows()

    assert rows == {"K__done": (10, 2, 2)}


def test_reconciled_rows_skips_non_integer_measured(
        monkeypatch, tmp_path):
    """Degrade, never crash: a measured split that is not a non-bool
    int disqualifies that entry (presence_for would read UNKNOWN
    anyway)."""
    state = pin_state_dir(monkeypatch, tmp_path)
    doc = queue_doc([entry_raw("K__ok", "done", measured=(4, 2, 2))])
    bad = entry_raw("K__bad", "done", measured=(4, 2, 2))
    bad["reconcile"]["measured"]["dev"] = "2"
    doc["entries"].append(bad)
    write_queue_state(state, doc)

    rows = download_queue.reconciled_rows()

    assert rows == {"K__ok": (4, 2, 2)}


def test_reconciled_rows_corrupt_file_yields_empty(
        monkeypatch, tmp_path):
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_bytes(b"{garbage")

    assert download_queue.reconciled_rows() == {}


def test_reconciled_rows_absent_file_yields_empty(
        monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)

    assert download_queue.reconciled_rows() == {}


def test_reconciled_rows_explicit_path_overrides_state_dir(
        monkeypatch, tmp_path):
    """The state_path argument reads exactly that file (the 10-05
    screens/other callers may point at a snapshot)."""
    explicit = tmp_path / "elsewhere" / "download_queue.json"
    explicit.parent.mkdir(parents=True)
    explicit.write_text(json.dumps(
        queue_doc([entry_raw("K__elsewhere", "done", measured=(6, 3, 3))]),
        indent=4), encoding="utf-8")

    rows = download_queue.reconciled_rows(state_path=explicit)

    assert rows == {"K__elsewhere": (6, 3, 3)}


def test_reconciled_rows_feeds_merge_presence_end_to_end(
        monkeypatch, tmp_path):
    """The substrate chain: persisted done entries -> reconciled_rows ->
    merge_presence -> the UNCHANGED presence_for flips to PRESENT."""
    state = pin_state_dir(monkeypatch, tmp_path)
    write_queue_state(state, queue_doc([
        entry_raw("GUE__missing_task", "done", measured=(7, 3, 3))]))

    merged = download_queue.merge_presence(
        committed_tasks_shape(), download_queue.reconciled_rows())

    presence = registries.presence_for("GUE__missing_task", merged)
    assert presence.status == registries.PRESENCE_PRESENT
    assert presence.rows == (7, 3, 3)



# =====================================================================
# The R-03 g re-audit (10-02 Task 3) — the audit script's DEFAULT
# outputs write the four worktree artifacts (maintainer review/commit);
# every automatic path is pinned to temp outputs + byte-unchanged
# =====================================================================

import hashlib

#: The four committed artifacts the audit script's DEFAULT outputs
#: write (Pitfall 6) — byte-unchanged across every automatic path.
COMMITTED_AUDIT_ARTIFACTS = (
    REPO_ROOT / "dnallm-mark" / "data" / "n_audit.json",
    REPO_ROOT / "dnallm-mark" / "data" / "n_audit.csv",
    REPO_ROOT / "pipeline" / "eval_subsets.json",
    REPO_ROOT / "DATA.md",
)


def artifact_hashes():
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in COMMITTED_AUDIT_ARTIFACTS}


def reaudit_service(tmp_path, monkeypatch, runner,
                    timeout_reaudit=None):
    repo = tmp_repo_with_registry(
        tmp_path / "arepo", {"Demo__task": SHAPE_A_ENTRY})
    state = tmp_path / "astate"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    kwargs = {}
    if timeout_reaudit is not None:
        kwargs["timeout_reaudit"] = timeout_reaudit
    return download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        runner=runner, cli_path=str(fake_cli(tmp_path)), **kwargs)


def reaudit_ok_result():
    return SimpleNamespace(
        returncode=0,
        stdout="Audited 50 registry task(s): 43 present, 7 missing\n",
        stderr="")


def test_reaudit_outcome_shape_and_default_timeout():
    """ReauditOutcome exists with the ok/details/raw_output shape
    (frozen dataclass — the QueueEntry line-195 test pins the decorator
    behavior); the reaudit timeout default is 300 (T-10-02-05)."""
    outcome = download_queue.ReauditOutcome(
        ok=True, details=("exit_code=0",), raw_output="x")
    assert outcome.ok is True
    assert outcome.details == ("exit_code=0",)
    assert outcome.raw_output == "x"
    assert download_queue.DEFAULT_TIMEOUT_REAUDIT == 300


def test_reaudit_argv_exactly_interpreter_and_script_no_flags(
        tmp_path, monkeypatch):
    """R-03 pinned: argv is EXACTLY [sys.executable, <absolute script
    path>] — NO output flags, so the script's own defaults write the
    four worktree artifacts for maintainer review (never temp+replace
    narrow writes)."""
    captured = {}

    def hook(argv, kwargs):
        captured["argv"] = list(argv)
        captured["kwargs"] = dict(kwargs)

    runner = FakeReconcileRunner(on_call=hook, result=reaudit_ok_result())
    service = reaudit_service(tmp_path, monkeypatch, runner)

    outcome = service.reaudit_baseline(run_id="r1")

    assert outcome.ok is True
    assert captured["argv"] == [
        sys.executable,
        str(service._repo_root / "script" / "audit_n_frequencies.py")]
    for flag in RECONCILE_OUTPUT_FLAGS:
        assert flag not in captured["argv"], flag
    assert captured["kwargs"]["timeout"] == 300
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    # WR-05: the decode policy — errors="replace" rides every runner
    # call (the audit script emits CJK/emoji markers; a non-UTF-8
    # LC_CTYPE must decode them, never raise UnicodeDecodeError and
    # turn a healthy audit into a spurious failed verdict)
    assert captured["kwargs"]["errors"] == "replace"


def test_reaudit_env_exactly_one_override_empty_overlay(
        tmp_path, monkeypatch):
    """T-10-02-03: env == os.environ plus EXACTLY the CUSTOM_DIR_ENV
    override pinned at an EMPTY temp dir while the subprocess runs — a
    colliding local custom overlay can never leak into the refreshed
    committed baseline. The existence pins run inside the hook (the
    tempdir lives only for the subprocess's lifetime)."""
    captured = {}

    def hook(argv, kwargs):
        overlay = Path(kwargs["env"][OVERLAY_ENV])
        captured["env"] = kwargs["env"]
        captured["overlay_is_dir"] = overlay.is_dir()
        captured["overlay_empty"] = list(overlay.iterdir()) == []

    runner = FakeReconcileRunner(on_call=hook, result=reaudit_ok_result())
    service = reaudit_service(tmp_path, monkeypatch, runner)

    service.reaudit_baseline(run_id="r1")

    assert captured["overlay_is_dir"] is True
    assert captured["overlay_empty"] is True
    expected = dict(os.environ)
    expected[OVERLAY_ENV] = captured["env"][OVERLAY_ENV]
    assert captured["env"] == expected


def test_reaudit_ok_carries_verbatim_raw(tmp_path, monkeypatch):
    runner = FakeReconcileRunner(result=reaudit_ok_result())
    service = reaudit_service(tmp_path, monkeypatch, runner)

    outcome = service.reaudit_baseline(run_id="r1")

    assert outcome.ok is True
    assert outcome.details == ("exit_code=0",)
    assert outcome.raw_output == reaudit_ok_result().stdout


def test_reaudit_nonzero_exit_not_ok_verbatim_raw(tmp_path, monkeypatch):
    result = SimpleNamespace(returncode=1, stdout="", stderr="boom\n")
    runner = FakeReconcileRunner(result=result)
    service = reaudit_service(tmp_path, monkeypatch, runner)

    outcome = service.reaudit_baseline(run_id="r1")

    assert outcome.ok is False
    assert "exit_nonzero" in outcome.details
    assert "exit_code=1" in outcome.details
    assert outcome.raw_output == "boom\n"


def test_reaudit_timeout_absorbed_not_ok(tmp_path, monkeypatch):
    runner = FakeReconcileRunner(
        exc=subprocess.TimeoutExpired(cmd="audit", timeout=300))
    service = reaudit_service(tmp_path, monkeypatch, runner)

    outcome = service.reaudit_baseline(run_id="r1")

    assert outcome.ok is False
    assert "timeout" in outcome.details
    assert "timeout_seconds=300" in outcome.details


def test_reaudit_launch_error_absorbed_not_ok(tmp_path, monkeypatch):
    runner = FakeReconcileRunner(exc=OSError("[Errno 13] denied"))
    service = reaudit_service(tmp_path, monkeypatch, runner)

    outcome = service.reaudit_baseline(run_id="r1")

    assert outcome.ok is False
    assert any("subprocess_error" in token for token in outcome.details)
    assert any("denied" in token for token in outcome.details)


def test_reaudit_timeout_knob_overridable(tmp_path, monkeypatch):
    captured = {}
    runner = FakeReconcileRunner(
        on_call=lambda argv, kwargs: captured.update(kwargs),
        result=reaudit_ok_result())
    service = reaudit_service(tmp_path, monkeypatch, runner,
                              timeout_reaudit=7)

    service.reaudit_baseline(run_id="r1")

    assert captured["timeout"] == 7


def test_no_automatic_path_ever_constructs_a_no_flag_audit_argv(
        monkeypatch, tmp_path):
    """The reachability invariant: ONLY reaudit_baseline invokes the
    audit script without output flags — the automatic reconcile inside
    run_task carries ALL FOUR output flags at temp values (recorded by
    the shared runner seam; the reaudit call is the only no-flag one)."""
    spawner = FakeSpawner(FakePopen(returncode=0))
    runner = FakeReconcileRunner(on_call=lambda argv, kwargs:
                                 write_temp_n_audit(
                                     argv, {"Demo__task":
                                            audit_record(10, 2, 2)})
                                 if "--data-dir" in argv else None)
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner,
                                      runner=runner)
    land_csvs(repo, "Demo", "task")

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "done"
    (reconcile_call,) = runner.calls
    for flag in RECONCILE_OUTPUT_FLAGS:
        assert flag in reconcile_call["argv"], flag

    outcome = service.reaudit_baseline(run_id="r2")

    assert outcome.ok is True
    assert len(runner.calls) == 2
    reaudit_argv = runner.calls[1]["argv"]
    for flag in RECONCILE_OUTPUT_FLAGS:
        assert flag not in reaudit_argv, flag


def test_committed_artifacts_byte_unchanged_across_real_reconcile_run(
        monkeypatch, tmp_path):
    """THE anti-clobber gate (T-10-02-01): one full run_task whose
    reconcile runs the REAL audit subprocess leaves the four committed
    artifacts sha256-identical before/after (the reconcile path's
    outputs are temp-only)."""
    before = artifact_hashes()

    repo = real_audit_repo(tmp_path, declared=(4, 2, 2))
    state = tmp_path / "byte-state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    cli = tmp_path / "modelscope"
    cli.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    cli.chmod(0o755)
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        cli_path=str(cli))                  # default REAL runner
    assert service.enqueue("Demo__task").action == "enqueued"
    service.claim_next()

    event = service.run_task("Demo__task", run_id="byte-1")

    assert event.state == "done"           # the real reconcile passed
    (entry,) = service.entries()
    assert entry.reconcile["measured"] == {"train": 4, "dev": 2,
                                           "test": 2}
    assert artifact_hashes() == before     # all four byte-unchanged


# =====================================================================
# The DATA-04 zenodo-kind queue lane (10-03 Task 2) — fully offline:
# a URL-router fetch seam (probe + record + file downloads), a fixture
# record, and a locally-built zip through the REAL extraction and the
# REAL reconcile subprocess over a tmp repo.
# =====================================================================

import email.message
import urllib.error
import zipfile

from tui.services import zenodo_bundle

#: A realistic Zenodo file URL (the links.self spelling) for fixtures.
BUNDLE_ZIP_URL = (
    "https://zenodo.org/api/records/19135551/files/Demo.zip/content")


def test_zenodo_kind_and_queue_key_constants_pinned():
    """The bundle entry's kind + queue identity (the only Zenodo string
    constants in the source beside the record id/URL)."""
    assert download_queue.KIND_ZENODO_BUNDLE == "zenodo_bundle"
    assert download_queue.ZENODO_BUNDLE_KEY == "zenodo-19135551"


def test_enqueue_zenodo_appends_without_any_cli(tmp_path, monkeypatch):
    """The bundle lane is stdlib HTTP — enqueue succeeds on a machine
    with NO modelscope CLI (the dataset lane's probed unavailable state
    does not apply here)."""
    force_cli_absent(monkeypatch, tmp_path)
    state = pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService()

    outcome = service.enqueue_zenodo()

    assert outcome.action == "enqueued"
    assert outcome.key == download_queue.ZENODO_BUNDLE_KEY
    (entry,) = service.entries()
    assert entry.kind == download_queue.KIND_ZENODO_BUNDLE
    assert entry.key == download_queue.ZENODO_BUNDLE_KEY
    assert entry.state == "pending"
    assert state_file(state).is_file()          # persisted immediately


def test_enqueue_zenodo_dedupes_like_any_enqueue(tmp_path, monkeypatch):
    make_service(tmp_path, monkeypatch)
    service = download_queue.DownloadQueueService()

    first = service.enqueue_zenodo()
    second = service.enqueue_zenodo()

    assert first.action == "enqueued"
    assert second.action == "already_queued"
    assert len(service.entries()) == 1


def test_claim_next_treats_the_bundle_entry_like_any_pending(
        tmp_path, monkeypatch):
    make_service(tmp_path, monkeypatch)
    service = download_queue.DownloadQueueService()
    service.enqueue_zenodo()

    claimed = service.claim_next()

    assert claimed is not None
    assert claimed.key == download_queue.ZENODO_BUNDLE_KEY
    assert claimed.kind == download_queue.KIND_ZENODO_BUNDLE
    assert claimed.state == "downloading"


class FakeUrlResponse:
    """A urlopen-shaped context manager for the router seam."""

    def __init__(self, status=200, payload=b""):
        self.status = status
        self._payload = payload

    def read(self, size=-1):
        payload, self._payload = self._payload, b""
        return payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class UrlRouter:
    """The offline zenodo seam: ``url -> response | exception``."""

    def __init__(self, table):
        self.table = table
        self.calls = []

    def __call__(self, url, timeout=None):
        self.calls.append(url)
        entry = self.table[url]
        if isinstance(entry, Exception):
            raise entry
        return entry


def bundle_repo(tmp_path, declared=(4, 2, 2)):
    """A tmp repo (the real_audit_repo shape) whose registry declares
    Demo__task with NO datasets on disk — the CSVs arrive ONLY via the
    bundle zip extraction (the real audit script + registry_loader are
    copies, so the reconcile leg runs the REAL kernels)."""
    repo = tmp_path / "bundle-repo"
    (repo / "script").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "script" / "audit_n_frequencies.py",
                repo / "script" / "audit_n_frequencies.py")
    (repo / "pipeline").mkdir()
    shutil.copy(REPO_ROOT / "pipeline" / "registry_loader.py",
                repo / "pipeline" / "registry_loader.py")
    train, dev, test = declared
    (repo / "pipeline" / "datasets_info.json").write_text(json.dumps({
        "Demo__task": {
            "Dataset_path": "datasets/Demo/task",
            "download_url":
                "https://www.modelscope.cn/datasets/lgq12697/GUE",
            "download_url_alternates":
                "https://huggingface.co/datasets/whatever",
            "Train": train, "Dev": dev, "Test": test,
        }}), encoding="utf-8")
    return repo


def pin_n_audit_missing(monkeypatch, tmp_path, missing=True):
    """Point ``registries.N_AUDIT_PATH`` at a tmp artifact declaring
    Demo__task missing — the missing-set source the bundle branch's
    landing check iterates (the committed n_audit.json stays
    read-only; monkeypatch is the seam, never a file rewrite)."""
    path = tmp_path / "n-audit" / "n_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"tasks": {"Demo__task": {"missing": missing}}}),
        encoding="utf-8")
    monkeypatch.setattr(registries, "N_AUDIT_PATH", path)
    return path


def bundle_zip_bytes(rows=(4, 2, 2), extra=None):
    """A synthetic group archive: ``Demo/task/{train,dev,test}.csv``
    with pure-ACGT rows (``rows=None`` builds only the extra members —
    the nothing-lands fixture)."""
    members = {}
    if rows is not None:
        for split, count in zip(("train", "dev", "test"), rows):
            lines = ["sequence,label"]
            lines += [f"ACGTACGTAC,{index}" for index in range(count)]
            members[f"Demo/task/{split}.csv"] = (
                "\n".join(lines) + "\n")
    if extra:
        members.update(extra)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in members.items():
            archive.writestr(name, text)
    return buffer.getvalue()


def public_record_table(zip_value, files=None):
    """The URL table for a PUBLIC record serving the given zip bytes
    (``files`` overrides the record's file list)."""
    if files is None:
        files = [{"key": "Demo.zip", "size": len(zip_value),
                  "links": {"self": BUNDLE_ZIP_URL}}]
    record = {"files": files}
    return {
        zenodo_bundle.ZENODO_API_URL: FakeUrlResponse(
            200, json.dumps(record).encode("utf-8")),
        BUNDLE_ZIP_URL: FakeUrlResponse(200, zip_value),
    }


def bundle_service(tmp_path, monkeypatch, fetch, repo):
    """A service over the tmp repo + tmp state root with the zenodo
    fetch seam injected and NO CLI anywhere near the lane."""
    state = tmp_path / "bundle-state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        zenodo_fetch=fetch)
    return service, state


def test_run_task_zenodo_not_public_fails_record_not_public(
        tmp_path, monkeypatch):
    """THE live-today state: the record 404s at run time -> failed
    ``record_not_public`` with the probe state in details; activation
    is exactly this answer flipping — zero code change."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path)
    fetch = UrlRouter({zenodo_bundle.ZENODO_API_URL: urllib.error.HTTPError(
        zenodo_bundle.ZENODO_API_URL, 404, "NOT FOUND",
        email.message.Message(), None)})
    service, _state = bundle_service(tmp_path, monkeypatch, fetch, repo)
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z1")

    assert event.state == "failed"
    assert "record_not_public" in event.problems
    assert "probe=not_public" in event.details
    (entry,) = service.entries()
    assert entry.state == "failed"
    assert entry.reconcile is None
    # nothing landed, nothing extracted (the datasets dir never formed)
    assert not (repo / "pipeline" / "datasets").exists()


def test_run_task_zenodo_bundle_offline_end_to_end_done(
        tmp_path, monkeypatch):
    """The whole bundle path offline: fixture record -> zip through the
    REAL extraction -> landing check -> REAL reconcile subprocess over
    the tmp repo -> done carrying the per-key verdict map."""
    repo = bundle_repo(tmp_path, declared=(4, 2, 2))
    pin_n_audit_missing(monkeypatch, tmp_path)
    fetch = UrlRouter(public_record_table(bundle_zip_bytes((4, 2, 2))))
    service, state = bundle_service(tmp_path, monkeypatch, fetch, repo)
    assert service.enqueue_zenodo().action == "enqueued"
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z2")

    assert event.state == "done"
    assert event.problems == ()
    (entry,) = service.entries()
    assert entry.reconcile == {"per_key": {"Demo__task": "pass"}}
    # the CSVs landed through the real extraction...
    task_dir = repo / "pipeline" / "datasets" / "Demo" / "task"
    for split in ("train", "dev", "test"):
        assert (task_dir / (split + ".csv")).is_file()
    # ...only into the datasets tree (the branch writes nowhere else)
    assert sorted(path.name for path in
                  (repo / "pipeline" / "datasets").iterdir()) == ["Demo"]
    # staging lives under the state root; the log carries the
    # reconcile section (the REAL subprocess output, D-03 drill-down)
    assert (state / "zenodo-19135551" / "Demo.zip").is_file()
    log_text = (state / entry.log_path).read_text(encoding="utf-8")
    assert "[reconcile]" in log_text


def test_run_task_zenodo_zero_conforming_files_fails_unreadable(
        tmp_path, monkeypatch):
    """A record shape the defensive parser does not recognize is an
    explicit failure — never a guess, never a hardcoded list."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path)
    table = public_record_table(
        b"", files=[{"nonsense": True}])
    del table[BUNDLE_ZIP_URL]           # never reached
    fetch = UrlRouter(table)
    service, _state = bundle_service(tmp_path, monkeypatch, fetch, repo)
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z3")

    assert event.state == "failed"
    assert "record_file_list_unreadable" in event.problems
    assert "bundle_files=0" in event.details


def test_run_task_zenodo_mid_download_failure_fails_with_diagnostics(
        tmp_path, monkeypatch):
    """A mid-download network failure fails the task with verbatim
    diagnostics; the partial staging dir never affects presence (no
    reconcile pass without the full landing check)."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path)
    table = public_record_table(b"")
    table[BUNDLE_ZIP_URL] = urllib.error.URLError(
        "connection reset mid-file")
    fetch = UrlRouter(table)
    service, state = bundle_service(tmp_path, monkeypatch, fetch, repo)
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z4")

    assert event.state == "failed"
    assert "bundle_download_failed" in event.problems
    assert any("connection reset mid-file" in token
               for token in event.details)
    (entry,) = service.entries()
    assert entry.state == "failed"
    assert entry.reconcile is None
    # verbatim diagnostics reach the drill-down log
    log_text = (state / entry.log_path).read_text(encoding="utf-8")
    assert "connection reset mid-file" in log_text
    # nothing landed — presence untouched
    assert not (repo / "pipeline" / "datasets" / "Demo").exists()


def test_run_task_zenodo_zip_slip_member_skipped_run_still_lands(
        tmp_path, monkeypatch):
    """T-10-03-01 through the queue: a traversal member is skipped
    with a problem and NOTHING appears outside the datasets root,
    while the conforming tree still lands and reconciles."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path)
    zip_value = bundle_zip_bytes(
        (4, 2, 2), extra={"../evil.txt": "pwned"})
    fetch = UrlRouter(public_record_table(zip_value))
    service, _state = bundle_service(tmp_path, monkeypatch, fetch, repo)
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z5")

    assert event.state == "done"
    assert "zip_slip_skipped=../evil.txt" in event.details
    assert not (repo / "pipeline" / "evil.txt").exists()
    assert (repo / "pipeline" / "datasets" / "Demo" / "task"
            / "train.csv").is_file()


def test_run_task_zenodo_mismatch_lands_mismatch_state_no_deletion(
        tmp_path, monkeypatch):
    """A landed key whose real count disproves the declared shape lands
    the entry in mismatch carrying the per-key verdict — and deletes
    nothing (D-07)."""
    repo = bundle_repo(tmp_path, declared=(999, 2, 2))
    pin_n_audit_missing(monkeypatch, tmp_path)
    fetch = UrlRouter(public_record_table(bundle_zip_bytes((4, 2, 2))))
    service, _state = bundle_service(tmp_path, monkeypatch, fetch, repo)
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z6")

    assert event.state == "mismatch"
    assert any("Train_mismatch_declared=999_measured=4" in problem
               for problem in event.problems)
    (entry,) = service.entries()
    assert entry.reconcile == {"per_key": {"Demo__task": "mismatch"}}
    task_dir = repo / "pipeline" / "datasets" / "Demo" / "task"
    assert (task_dir / "train.csv").is_file()    # nothing deleted


def test_run_task_zenodo_nothing_landed_fails(tmp_path, monkeypatch):
    """A bundle whose content lands no currently-missing key is a
    failed run naming it — never a vacuous done."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path)
    zip_value = bundle_zip_bytes(
        rows=None, extra={"OtherGroup/thing.csv": "sequence,label\n"})
    fetch = UrlRouter(public_record_table(zip_value))
    service, _state = bundle_service(tmp_path, monkeypatch, fetch, repo)
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z7")

    assert event.state == "failed"
    assert "bundle_landed_zero" in event.problems
    assert "landed=0" in event.details


def test_run_task_zenodo_nothing_missing_is_done_nothing_to_do_in08(
        tmp_path, monkeypatch):
    """IN-08: a bundle run on a machine where NOTHING is missing is the
    explicit nothing-to-do outcome — done with a note, ZERO network
    legs — never a multi-GB download followed by a misleading
    failed bundle_landed_zero terminal state."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path, missing=False)
    router = UrlRouter(public_record_table(bundle_zip_bytes((4, 2, 2))))
    service, _state = bundle_service(tmp_path, monkeypatch, router, repo)
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z-noop")

    assert event.state == "done"
    assert event.problems == ()
    assert "missing_keys=0" in event.details
    assert any(detail.startswith("nothing_to_do")
               for detail in event.details), (
        "the empty-missing-set run is the explicit nothing-to-do outcome"
    )
    assert router.calls == [], (
        "the nothing-to-do bundle never probes, downloads, or extracts"
    )
    (entry,) = service.entries()
    assert entry.state == "done"
    assert entry.reconcile == {"per_key": {}}
    assert not (repo / "pipeline" / "datasets").exists()


def test_run_task_zenodo_cancel_before_stages_fails_never_probes(
        tmp_path, monkeypatch):
    """WR-01: a cancel that lands while the bundle entry is downloading
    is honored at the FIRST stage boundary — failed
    ``cancelled_by_operator`` with zero network legs (the probe never
    fires), mirroring the CLI lane's reap-loop contract."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path)
    router = UrlRouter(public_record_table(bundle_zip_bytes((4, 2, 2))))
    service, _state = bundle_service(tmp_path, monkeypatch, router, repo)
    service.enqueue_zenodo()
    service.claim_next()

    assert service.cancel(download_queue.ZENODO_BUNDLE_KEY) == "signalled"
    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z-cancel-0")

    assert event.state == "failed"
    assert event.problems == (download_queue.PROBLEM_CANCELLED,)
    assert router.calls == [], "the cancelled bundle never probes"
    (entry,) = service.entries()
    assert entry.state == "failed"
    assert not (repo / "pipeline" / "datasets").exists()


def test_run_task_zenodo_cancel_mid_download_fails_cancelled(
        tmp_path, monkeypatch):
    """WR-01 end-to-end: the operator's x-cancel lands mid-download (the
    public ``cancel`` API, called from inside the fetch seam while the
    entry is downloading) — the per-file loop STOPS at the should_cancel
    seam, the run finishes failed ``cancelled_by_operator`` (never a
    per-file failure), the partial staging stays retained, and nothing
    extracts."""
    repo = bundle_repo(tmp_path)
    pin_n_audit_missing(monkeypatch, tmp_path)
    second_url = "https://zenodo.org/api/files/record/Second.zip"
    zip_value = bundle_zip_bytes((4, 2, 2))
    router = UrlRouter(public_record_table(zip_value, files=[
        {"key": "Demo.zip", "size": len(zip_value),
         "links": {"self": BUNDLE_ZIP_URL}},
        {"key": "Second.zip", "size": 6,
         "links": {"self": second_url}},
    ]))
    router.table[second_url] = FakeUrlResponse(200, b"second")
    cell: dict = {}

    def cancelling_opener(url, timeout=None):
        if url == BUNDLE_ZIP_URL:
            # the operator presses x-confirm while file 1 streams
            assert cell["service"].cancel(
                download_queue.ZENODO_BUNDLE_KEY) == "signalled"
        return router(url, timeout=timeout)

    service, state = bundle_service(
        tmp_path, monkeypatch, cancelling_opener, repo)
    cell["service"] = service
    service.enqueue_zenodo()
    service.claim_next()

    event = service.run_task(
        download_queue.ZENODO_BUNDLE_KEY, run_id="z-cancel-1")

    assert event.state == "failed"
    assert event.problems == (download_queue.PROBLEM_CANCELLED,), (
        "the cancelled bundle is the operator-cancel problem, never "
        "bundle_download_failed"
    )
    assert "downloaded=1" in event.details, (
        "the in-loop should_cancel seam stopped the loop after file 1"
    )
    (entry,) = service.entries()
    assert entry.state == "failed"
    # the partial staging stays retained (the lane re-runs from scratch
    # on retry — no byte-resume by design); Second.zip never downloaded
    staging = state / "zenodo-19135551"
    assert (staging / "Demo.zip").is_file()
    assert not (staging / "Second.zip").exists()
    # cancelled BEFORE extract: nothing landed under pipeline/datasets
    assert not (repo / "pipeline" / "datasets").exists()
    # the flag is consumed by _finish (a later retry is never poisoned)
    service.retry(download_queue.ZENODO_BUNDLE_KEY)
    assert service.claim_next().state == "downloading"


# =====================================================================
# The DL_/QUEUE_ string block + ENV_ROUTE amendment (10-03 Task 3,
# I18N-01 single home) — the inventory tripwire the 10-04/10-05
# consumers build against: every constant NAME they reference must
# exist here, exactly once, in tui/strings.py.
# =====================================================================

from tui import strings as tui_strings

#: The complete expected DL_ inventory (the screen chrome, the Zenodo
#: four states + toasts/labels, the keycaps, the derived gap-fillers,
#: the full presence view pair DCL-03/261014-dcl added, and the
#: datasets-primary rework additions MLC-03/261014-mlc: the full-list
#: download column + its three status words, and the w wizard keycap).
EXPECTED_DL_CONSTANTS = (
    "DL_SCREEN_TITLE", "DL_MISSING_TITLE", "DL_MISSING_COL_KEY",
    "DL_MISSING_COL_ROWS", "DL_MISSING_EMPTY", "DL_PRESENCE_SUMMARY",
    "DL_PRESENCE_TITLE", "DL_PRESENCE_TOGGLE_LABEL",
    "DL_ZENODO_PROBING", "DL_ZENODO_NOT_PUBLIC", "DL_ZENODO_PUBLIC",
    "DL_ZENODO_FAILED", "DL_ZENODO_DISABLED_TOAST",
    "DL_ZENODO_KEY_LABEL", "DL_BUNDLE_TASK_NAME", "DL_DISABLED_TOAST",
    "DL_UNKNOWN_TOAST",
    "DL_ENQUEUE_LABEL", "DL_RETRY_LABEL", "DL_CANCEL_LABEL",
    "DL_ENQUEUE_ALL_LABEL",
    "DL_COL_DOWNLOAD", "DL_FULL_PRESENT", "DL_FULL_MISSING",
    "DL_FULL_UNKNOWN", "DL_WIZARD_LABEL",
)

#: The complete expected QUEUE_ inventory (title/columns/empty, the
#: five states, reconcile cells, restart note, banner, toasts,
#: confirms, progress, the g label).
EXPECTED_QUEUE_CONSTANTS = (
    "QUEUE_TITLE", "QUEUE_COL_TASK", "QUEUE_COL_STATE",
    "QUEUE_COL_PROGRESS", "QUEUE_COL_RECONCILE", "QUEUE_EMPTY",
    "QUEUE_STATE_PENDING", "QUEUE_STATE_DOWNLOADING",
    "QUEUE_STATE_DONE", "QUEUE_STATE_FAILED", "QUEUE_STATE_MISMATCH",
    "QUEUE_RECONCILE_PASS", "QUEUE_RECONCILE_RUNNING",
    "QUEUE_RECONCILE_MISMATCH", "QUEUE_RESTART_NOTE",
    "QUEUE_BANNER_MISMATCH", "QUEUE_TOAST_ENQUEUED",
    "QUEUE_TOAST_ENQUEUED_ALL", "QUEUE_TOAST_ALREADY_QUEUED",
    "QUEUE_FLIP_TOAST", "QUEUE_RETRY_NOOP", "QUEUE_CANCEL_NOOP",
    "QUEUE_CLI_UNAVAILABLE", "QUEUE_PERSIST_FAILED_TOAST",
    "QUEUE_PERSIST_DRIVER_TOAST", "QUEUE_PROGRESS_INDETERMINATE",
    "QUEUE_CONFIRM_CANCEL_PENDING", "QUEUE_CONFIRM_CANCEL_DOWNLOADING",
    "QUEUE_REAUDIT_LABEL", "QUEUE_FLIP_TOAST_MODEL",
)

#: The selection-screen d amendments (D-14) + the models-column presence
#: pair (DCL-02, 261014-dcl) — this file is the established SEL_
#: registration site (the one-directional defined-check covers them).
#: SEL_ENQUEUE_LABEL was RETIRED at 261014-mlc (slot 2's d is the model
#: download — its own label); SEL_ENQUEUE_PRESENT_TOAST stays (the
#: slot-3 full-list present-row toast).
EXPECTED_SEL_CONSTANTS = (
    "SEL_ENQUEUE_PRESENT_TOAST",
    "SEL_MODEL_PRESENCE_PRESENT", "SEL_MODEL_PRESENCE_MISSING",
)


def test_dl_and_queue_string_inventory_defined():
    """The drift tripwire: every DL_/QUEUE_/SEL_ name the 10-04/10-05
    plans consume exists, non-empty, at module level in tui/strings.py
    (the I18N-01 single home) — a rename or gap fails HERE, before any
    screen lands.

    261015-ehc (EHC-1): the check runs over BOTH languages — the
    registry rebinds its constants per language, so each side must
    carry the full inventory (zh restored for the committed zh-rendering
    test surface)."""
    try:
        for lang in ("zh", "en"):
            tui_strings.set_language(lang)
            for prefix, names in (("DL_", EXPECTED_DL_CONSTANTS),
                                  ("QUEUE_", EXPECTED_QUEUE_CONSTANTS),
                                  ("SEL_", EXPECTED_SEL_CONSTANTS)):
                for name in names:
                    assert hasattr(tui_strings, name), (lang, name)
                    value = getattr(tui_strings, name)
                    assert isinstance(value, str) and value, (lang, name)
                    assert name.startswith(prefix), name
    finally:
        tui_strings.set_language("zh")


def test_dl_queue_inventory_complete_no_unlisted_constants():
    """IN-09: the single-home lock is BIDIRECTIONAL — every DL_/QUEUE_
    constant tui/strings.py defines is listed in the expected tuples, so
    a new toast that skips registration fails here instead of silently
    drifting out of the inventory's coverage."""
    listed = set(EXPECTED_DL_CONSTANTS) | set(EXPECTED_QUEUE_CONSTANTS)
    defined = {name for name in dir(tui_strings)
               if name.startswith(("DL_", "QUEUE_"))}
    assert defined == listed, (
        "the string inventory and the tripwire must match exactly — "
        f"unregistered: {sorted(defined - listed)}; "
        f"stale registrations: {sorted(listed - defined)}"
    )


def test_queue_state_strings_glyph_first_and_distinct():
    """The NO_COLOR redundancy contract: each of the five queue states
    leads with its distinct glyph (◌ ⠋ ✓ ✗ ⚠). 261015-ehc: the glyph
    leads in BOTH languages."""
    try:
        for lang in ("zh", "en"):
            tui_strings.set_language(lang)
            state_glyphs = [
                tui_strings.QUEUE_STATE_PENDING[0],
                tui_strings.QUEUE_STATE_DOWNLOADING[0],
                tui_strings.QUEUE_STATE_DONE[0],
                tui_strings.QUEUE_STATE_FAILED[0],
                tui_strings.QUEUE_STATE_MISMATCH[0],
            ]
            assert state_glyphs == ["◌", "⠋", "✓", "✗", "⚠"], lang
            assert len(set(state_glyphs)) == 5, lang
    finally:
        tui_strings.set_language("zh")


def test_env_route_amendment_carries_keycap_and_cli_command():
    """The ENV_ROUTE amendment (UI-SPEC verbatim hint): the [3] keycap
    segment and the CLI audit command both present, the {n} field
    preserved (the constant-derived env-check test stays green), and
    the retired Phase-10-panel note gone."""
    line = tui_strings.ENV_ROUTE_MISSING_DATASETS
    assert "[3] 前往数据管理" in line
    assert "python script/audit_n_frequencies.py" in line
    assert "{n}" in line
    assert line[0] == "⚠"
    assert "Phase 10 提供" not in line


def test_bundle_task_name_matches_queue_key_identity():
    """The bundle row's task label renders the queue identity (the
    zenodo-19135551 prefix is the shared anchor between strings and
    the service constant)."""
    assert tui_strings.DL_BUNDLE_TASK_NAME.startswith(
        download_queue.ZENODO_BUNDLE_KEY)


# =====================================================================
# Lane 7: the degradation edge sweep (10-06 Task 1) — CLI absent via a
# nowhere-pointing explicit path, registry-evolution entries, and the
# corrupt-diagnostic session memory. Every degradation is a designed
# state, never a crash and never silent loss.
# =====================================================================

#: A registry-evolution fixture key (valid queue identity, absent from
#: the official registry — the D-06 tolerance case).
VANISHED_KEY = "VanishedRepo__gone_task"


def hand_written_state_file(state, entries):
    """Seed the queue state file with hand-written entries (the
    registry-evolution / crash-restart fixtures)."""
    state.mkdir(parents=True, exist_ok=True)
    doc = {"schema_version": download_queue.SCHEMA_VERSION, "entries": [
        {
            "key": key, "kind": "dataset", "state": entry_state,
            "attempts": attempts,
            "enqueued_at": "2026-10-12T00:00:00+00:00",
            "started_at": None, "finished_at": None,
            "last_percent": last_percent, "interrupted": False,
            "log_path": None, "problems": [], "reconcile": None,
        }
        for key, entry_state, attempts, last_percent in entries
    ]}
    state_file(state).write_text(
        json.dumps(doc, indent=4, ensure_ascii=False), encoding="utf-8")
    return state_file(state)


def test_enqueue_cli_absent_via_nonexistent_explicit_path(
        monkeypatch, tmp_path):
    """D-01 degradation (the constructor override needs no PATH games):
    a cli_path pointing NOWHERE is the probed-unavailable state —
    enqueue yields ``cli_unavailable``, NO entry is created, and the
    queue file is byte-identical before and after (an absent file stays
    absent; a populated file keeps its exact bytes)."""
    nowhere = tmp_path / "nowhere" / "modelscope"
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    service = download_queue.DownloadQueueService(cli_path=str(nowhere))

    outcome = service.enqueue(DOWNLOADABLE_KEY)

    assert outcome.action == "cli_unavailable"
    assert outcome.key == DOWNLOADABLE_KEY
    assert service.entries() == []
    assert not state_file(state).exists(), (
        "the refused enqueue must never create the state file"
    )

    # a populated file stays byte-identical across the refused enqueue
    raw = hand_written_state_file(state, [
        ("GUE__fungi_species_20", "done", 1, 100)]).read_text(
        encoding="utf-8")
    fresh = download_queue.DownloadQueueService(cli_path=str(nowhere))
    assert fresh.load() is None

    refused = fresh.enqueue(DOWNLOADABLE_KEY)

    assert refused.action == "cli_unavailable"
    assert state_file(state).read_text(encoding="utf-8") == raw, (
        "the refused enqueue must never rewrite the queue file"
    )
    assert [entry.key for entry in fresh.entries()] == [
        "GUE__fungi_species_20"]


def test_run_task_nonexistent_explicit_cli_fails_cli_unavailable(
        monkeypatch, tmp_path):
    """The run-time availability gate: an explicit CLI path pointing
    nowhere fails as the honest probed ``cli_unavailable`` state —
    never a spawn attempt (which would surface as a confusing
    subprocess_error at best, a wrong-machine exec at worst)."""
    spawner = FakeSpawner()
    service, _, _ = engine_service(tmp_path, monkeypatch, spawner)
    service._cli_path = str(tmp_path / "nowhere" / "modelscope")

    event = service.run_task("Demo__task", run_id="r1")

    assert event.state == "failed"
    assert event.problems == (download_queue.PROBLEM_CLI_UNAVAILABLE,)
    assert spawner.calls == []
    (entry,) = service.entries()
    assert entry.state == "failed"


def test_unknown_registry_key_entry_tolerated_end_to_end(
        monkeypatch, tmp_path):
    """Registry evolution (D-06 tolerance): an entry whose key has
    vanished from the official registry loads, survives ``entries()``,
    never breaks ``missing_datasets``/``enqueue``, resolves to the
    unknown channel, and fails honestly at run time — never a crash,
    never silent loss of the OTHER entries."""
    state = pin_state_dir(monkeypatch, tmp_path)
    hand_written_state_file(state, [
        (VANISHED_KEY, "pending", 0, None),
        (DOWNLOADABLE_KEY, "done", 1, 100)])
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    assert service.load() is None

    by_key = {entry.key: entry for entry in service.entries()}
    assert by_key[VANISHED_KEY].state == "pending"
    assert by_key[DOWNLOADABLE_KEY].state == "done"

    # the channel resolution degrades to unknown (None spec) — the
    # screen's drill-down renders the unknown disposition from it
    assert service.resolve_channel(VANISHED_KEY) is None

    # missing_datasets runs clean over the committed registry and never
    # admits the vanished key (the registry is the only authority)
    rows = service.missing_datasets()
    assert VANISHED_KEY not in {row.key for row in rows}

    # enqueue: the existing entry wins (D-08 idempotence) — no crash
    assert service.enqueue(VANISHED_KEY).action == "already_queued"

    # run_task on the vanished key: the honest failed state, the other
    # entry untouched
    event = service.run_task(VANISHED_KEY, run_id="r1")
    assert event.state == "failed"
    assert "unknown_key" in event.problems
    by_key = {entry.key: entry for entry in service.entries()}
    assert by_key[VANISHED_KEY].state == "failed"
    assert by_key[DOWNLOADABLE_KEY].state == "done"


def test_corrupt_load_diagnostic_remembered_for_the_session(
        monkeypatch, tmp_path):
    """The corrupt-state contract (10-06): the diagnostic returns from
    ``load()`` once AND is remembered on the service for the session —
    the screen's later snapshot reads (its reloads) still surface it;
    the sidecar + the usable empty queue are the 10-01 pins."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    garbage = b"{not json at all"
    state_file(state).write_bytes(garbage)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))

    error = service.load()

    assert isinstance(error, str) and "moved aside" in error
    # a second (now-healthy) load returns None — the diagnostic PERSISTS
    assert service.load() is None
    assert service.last_load_diagnostic() == error
    # the queue stays usable and the memory survives the mutation
    assert service.enqueue(DOWNLOADABLE_KEY).action == "enqueued"
    assert service.last_load_diagnostic() == error
    assert (state / (download_queue.QUEUE_FILE_NAME
                     + ".corrupt")).read_bytes() == garbage
    # a fresh service over the (now quarantined-away) file: no memory
    fresh = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    fresh.load()
    assert fresh.last_load_diagnostic() is None


def test_malformed_entries_dropped_with_diagnostic_in07(
        monkeypatch, tmp_path):
    """IN-07: a hand-edited file whose entries array carries one
    non-dict entry loses THAT row with a diagnostic through the session
    channel — never silent loss (the module contract), and the healthy
    siblings all survive."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_text(json.dumps({
        "schema_version": 1,
        "entries": [
            {"key": "k__fine", "kind": "dataset", "state": "pending",
             "attempts": 0, "enqueued_at": "2026-10-12T00:00:00+00:00",
             "started_at": None, "finished_at": None,
             "last_percent": None, "interrupted": False,
             "log_path": None, "problems": [], "reconcile": None},
            "not-an-entry-at-all",
            42,
        ],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))

    diagnostic = service.load()

    assert isinstance(diagnostic, str) and "2" in diagnostic and (
        "dropped" in diagnostic), (
        "the two malformed entries must be reported, never silently lost"
    )
    assert [entry.key for entry in service.entries()] == ["k__fine"]
    assert service.last_load_diagnostic() == diagnostic, (
        "the drop rides the session channel (the status line surfaces it)"
    )
    assert service.load() is None, (
        "the healthy reload is clean — the diagnostic is remembered"
    )


def test_dropped_rows_load_still_downgrades_downloading_in11(
        monkeypatch, tmp_path):
    """IN-11: the dropped-rows path must not skip the D-06
    downloading->pending downgrade — a compound hand-edited file (one
    non-dict row AND one downloading entry) reports the drop AND
    downgrades the survivor, so boot resume still sees a pending entry
    and kicks."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    state_file(state).write_text(json.dumps({
        "schema_version": 1,
        "entries": [
            "not-an-entry-at-all",
            {"key": "k__midflight", "kind": "dataset",
             "state": "downloading", "attempts": 1,
             "enqueued_at": "2026-10-12T00:00:00+00:00",
             "started_at": "2026-10-12T00:01:00+00:00",
             "finished_at": None, "last_percent": 62,
             "interrupted": False, "log_path": None,
             "problems": [], "reconcile": None},
        ],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))

    diagnostic = service.load()

    assert isinstance(diagnostic, str) and "1" in diagnostic, (
        "the dropped row is still reported (the IN-07 contract)"
    )
    (entry,) = service.entries()
    assert entry.key == "k__midflight"
    assert entry.state == "pending", (
        "the compound load must still downgrade the downloading entry "
        "(D-06) — boot resume kicks off this pending view"
    )
    assert entry.interrupted is True
    # the downgrade persisted alongside the cleaned rows
    on_disk = json.loads(state_file(state).read_text(encoding="utf-8"))
    assert on_disk["entries"][0]["state"] == "pending"
    assert on_disk["entries"][0]["interrupted"] is True


# =====================================================================
# WR-04: persistence failures never cross the never-raises boundary —
# an unwritable state rail (read-only dir, full disk) degrades every
# mutator to an honest outcome instead of an exception.
# =====================================================================


def read_only_state(state):
    """Make the state root unwritable (restored by the caller)."""
    state.chmod(0o500)


def writable_state(state):
    state.chmod(0o700)


def test_enqueue_persist_failure_refused_no_ghost_row(
        tmp_path, monkeypatch):
    """WR-04 (verified-by-execution class): with the state dir
    read-only, ``enqueue`` returns the honest ``persist_failed``
    outcome and rolls the in-memory append back — never a
    PermissionError, never a ghost pending row."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    read_only_state(state)
    try:
        outcome = service.enqueue(DOWNLOADABLE_KEY)

        assert outcome.action == "persist_failed"
        assert outcome.key == DOWNLOADABLE_KEY
        assert service.entries() == [], (
            "the refused enqueue must roll its in-memory append back"
        )
    finally:
        writable_state(state)


def test_claim_next_persist_failure_reverts_returns_none(
        tmp_path, monkeypatch):
    """WR-04: a claim whose downloading transition cannot persist is
    REVERTED (the entry returns to its exact prior shape) and
    ``claim_next`` answers None — never an exception, never a stuck
    in-memory downloading entry with no driver."""
    state = pin_state_dir(monkeypatch, tmp_path)
    hand_written_state_file(state, [(DOWNLOADABLE_KEY, "pending", 1, 40)])
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    assert service.load() is None
    read_only_state(state)
    try:
        claimed = service.claim_next()

        assert claimed is None
        (entry,) = service.entries()
        assert entry.state == "pending"
        assert entry.attempts == 1
        assert entry.started_at is None
    finally:
        writable_state(state)


def test_run_task_persist_failure_still_returns_event(
        tmp_path, monkeypatch):
    """WR-04: a failing ``_finish`` persist never raises out of
    ``run_task`` — the event still fires (the row refreshes), carrying
    a ``persist_error=`` problem so the row and drill-down surface the
    degradation; the in-memory entry holds the terminal state."""
    spawner = FakeSpawner()
    service, _repo, state = engine_service(tmp_path, monkeypatch, spawner)
    service._cli_path = str(tmp_path / "nowhere" / "modelscope")
    read_only_state(state)
    try:
        event = service.run_task("Demo__task", run_id="persist-1")

        assert event.state == "failed"
        assert download_queue.PROBLEM_CLI_UNAVAILABLE in event.problems
        assert any(problem.startswith("persist_error=")
                   for problem in event.problems), (
            "the persist failure rides the event as a problem token"
        )
        (entry,) = service.entries()
        assert entry.state == "failed"
        assert any(problem.startswith("persist_error=")
                   for problem in entry.problems)
    finally:
        writable_state(state)


# =====================================================================
# Lane 8: the exhaustive state-machine transition table + the restart
# rehydration chain (10-06 Task 2) — every legal edge applies, every
# illegal edge is a no-op, and persist -> crash -> reboot -> rehydrate
# -> resume is proven end-to-end at the service tier.
# =====================================================================

#: The exhaustive (from_state, action, expectation) table. expectation
#: is (kind, after_state): ``applied`` transitions, ``refused``/
#: ``noop``/``already`` leave the state untouched with a falsy return,
#: ``removed`` deletes the entry, ``signalled`` flags without a state
#: change (the reap owns that transition).
STATE_MACHINE_TABLE = [
    # claim_next: the ONLY pending -> downloading edge (D-04)
    ("pending", "claim_next", ("applied", "downloading")),
    ("downloading", "claim_next", ("noop", None)),
    ("done", "claim_next", ("noop", None)),
    ("failed", "claim_next", ("noop", None)),
    ("mismatch", "claim_next", ("noop", None)),
    # retry: the ONLY failed/mismatch -> pending edge (D-06)
    ("failed", "retry", ("applied", "pending")),
    ("mismatch", "retry", ("applied", "pending")),
    ("pending", "retry", ("refused", "pending")),
    ("downloading", "retry", ("refused", "downloading")),
    ("done", "retry", ("refused", "done")),
    # cancel: pending removed / downloading signalled / terminal noop
    ("pending", "cancel", ("removed", None)),
    ("downloading", "cancel", ("signalled", "downloading")),
    ("done", "cancel", ("noop", "done")),
    ("failed", "cancel", ("noop", "failed")),
    ("mismatch", "cancel", ("noop", "mismatch")),
    # enqueue: idempotent over ANY existing state (D-08) — never coerces
    ("pending", "enqueue", ("already", "pending")),
    ("downloading", "enqueue", ("already", "downloading")),
    ("done", "enqueue", ("already", "done")),
    ("failed", "enqueue", ("already", "failed")),
    ("mismatch", "enqueue", ("already", "mismatch")),
]


@pytest.mark.parametrize("from_state,action,expected", STATE_MACHINE_TABLE)
def test_state_machine_transition_table_exhaustive(
        monkeypatch, tmp_path, from_state, action, expected):
    """The exhaustive D-02/D-06/D-08 pin: every legal transition
    applies through its owning mutator; every illegal one is a no-op
    with a falsy return and a byte-identical queue file — no action
    silently coerces a state it does not own."""
    state = pin_state_dir(monkeypatch, tmp_path)
    # the downloading state exists ONLY through its owning edge (a
    # seeded downloading entry downgrades to pending at load — D-06),
    # so those rows seed pending and claim first
    seed_state = ("pending" if from_state == "downloading"
                  else from_state)
    path = hand_written_state_file(state, [
        (DOWNLOADABLE_KEY, seed_state, 1, 40)])
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    assert service.load() is None
    if from_state == "downloading":
        assert service.claim_next().state == "downloading"
    before = path.read_text(encoding="utf-8")

    kind, after_state = expected
    if action == "claim_next":
        claimed = service.claim_next()
        if kind == "applied":
            assert claimed is not None
            assert claimed.state == "downloading"
            assert claimed.attempts == 2
            assert service.entries()[0].state == "downloading"
        else:
            assert claimed is None
            assert service.entries()[0].state == from_state
            assert path.read_text(encoding="utf-8") == before, (
                "a refused claim must never rewrite the file")
    elif action == "retry":
        outcome = service.retry(DOWNLOADABLE_KEY)
        if kind == "applied":
            assert outcome is True
            assert service.entries()[0].state == "pending"
        else:
            assert outcome is False
            assert service.entries()[0].state == after_state
            assert path.read_text(encoding="utf-8") == before, (
                "a refused retry must never rewrite the file")
    elif action == "cancel":
        outcome = service.cancel(DOWNLOADABLE_KEY)
        assert outcome == kind
        if kind == "removed":
            assert service.entries() == []
        else:
            assert service.entries()[0].state == after_state
            if kind == "noop":
                assert path.read_text(encoding="utf-8") == before, (
                    "a terminal-state cancel must never rewrite the file")
    else:   # enqueue
        outcome = service.enqueue(DOWNLOADABLE_KEY)
        assert outcome.action == "already_queued"
        assert service.entries()[0].state == after_state
        assert len(service.entries()) == 1
        assert path.read_text(encoding="utf-8") == before, (
            "an already-queued enqueue must never rewrite the file")


@pytest.mark.parametrize("scenario,expected_state,expected_problems", [
    ("pass", "done", ()),
    ("exit_nonzero", "failed", ("exit_7",)),
    ("mismatch_verdict", "mismatch",
     ("Train_mismatch_declared=10_measured=3",)),
])
def test_run_task_terminal_transitions_from_downloading(
        monkeypatch, tmp_path, scenario, expected_state, expected_problems):
    """downloading -> done | failed | mismatch happens ONLY through
    run_task outcomes (the table's terminal leg): the passing verdict
    lands done, a nonzero exit lands failed carrying its code, and a
    mismatching reconcile verdict lands mismatch carrying BOTH
    numbers."""
    stdout = ("Downloading Dataset to directory: /tmp/x\n"
              "Successfully Downloaded from dataset lgq12697/GUE.\n")
    if scenario == "exit_nonzero":
        spawner = FakeSpawner(FakePopen(returncode=7))
        runner = passing_reconcile_runner()
    elif scenario == "mismatch_verdict":
        spawner = FakeSpawner(FakePopen(returncode=0, stdout=stdout))
        runner = FakeReconcileRunner(
            on_call=lambda argv, kwargs: write_temp_n_audit(
                argv, {"Demo__task": audit_record(3, 2, 2)}))
    else:
        spawner = FakeSpawner(FakePopen(returncode=0, stdout=stdout))
        runner = passing_reconcile_runner()
    repo = tmp_repo_with_registry(
        tmp_path / "repo", {"Demo__task": SHAPE_A_ENTRY})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        spawner=spawner, runner=runner,
        cli_path=str(fake_cli(tmp_path)))
    assert service.enqueue("Demo__task").action == "enqueued"
    assert service.claim_next().state == "downloading"
    land_csvs(repo, "Demo", "task")   # the landing gate passes

    event = service.run_task("Demo__task", run_id="t-" + scenario)

    assert event.state == expected_state
    assert event.problems == expected_problems
    assert service.entries()[0].state == expected_state


def test_restart_resume_end_to_end_service_tier(monkeypatch, tmp_path):
    """SC2 at the service tier, the full chain: persisted mid-download
    (state downloading) -> crash -> a fresh service's load() rehydrates
    with the downgrade (pending + interrupted, persisted) -> claim ->
    the channel's own resume fast path (exit 0 + the success marker
    over the ALREADY COMPLETE local dir — the .msc skip, no transfer
    work) -> the landing check passes on the existing tree -> reconcile
    pass -> done."""
    repo = tmp_repo_with_registry(
        tmp_path / "repo", {"Demo__task": SHAPE_A_ENTRY})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    state.mkdir(parents=True, exist_ok=True)
    queue_path = state / download_queue.QUEUE_FILE_NAME
    queue_path.write_text(json.dumps({
        "schema_version": 1,
        "entries": [{
            "key": "Demo__task", "kind": "dataset",
            "state": "downloading", "attempts": 1,
            "enqueued_at": "2026-10-12T00:00:00+00:00",
            "started_at": "2026-10-12T00:01:00+00:00",
            "finished_at": None, "last_percent": 62,
            "interrupted": False, "log_path": None,
            "problems": [], "reconcile": None}],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    # the prior run's progress: the three split CSVs already complete
    land_csvs(repo, "Demo", "task")
    # the resumed CLI invoke returns immediately (the .msc skip)
    stdout = ("Downloading Dataset to directory: /tmp/x\n"
              "Successfully Downloaded from dataset lgq12697/GUE.\n")
    spawner = FakeSpawner(FakePopen(returncode=0, stdout=stdout))
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=queue_path, spawner=spawner,
        runner=passing_reconcile_runner(),
        cli_path=str(fake_cli(tmp_path)))

    assert service.load() is None          # the reboot's tolerant read
    (entry,) = service.entries()
    assert entry.state == "pending"
    assert entry.interrupted is True

    claimed = service.claim_next()         # the driver's re-invoke
    assert claimed.state == "downloading"
    event = service.run_task("Demo__task", run_id="resume-1")

    assert event.state == "done"
    assert "landing=ok" in event.details
    assert "success_marker=true" in event.details
    (entry,) = service.entries()
    assert entry.state == "done"
    assert entry.reconcile is not None
    assert entry.reconcile["verdict"] == "pass"


def test_probe_zenodo_routes_through_the_service_fetch_seam():
    """The D-12 probe rides the service's zenodo_fetch seam (10-06):
    the screen Backend probes THROUGH the queue, so the real adapter —
    not just the Pilot fakes — is offline-injectable; no queue lane can
    ever reach the network by construction."""
    from email.message import Message
    from urllib.error import HTTPError

    from tui.services import zenodo_bundle

    probe_calls = []

    def offline_opener(url, timeout=None):
        probe_calls.append(url)
        raise HTTPError(url, 404, "Not Found", Message(), None)

    service = download_queue.DownloadQueueService(
        zenodo_fetch=offline_opener)

    probe_state = service.probe_zenodo()

    assert probe_state == zenodo_bundle.PROBE_NOT_PUBLIC
    assert probe_calls and "zenodo.org" in probe_calls[0], (
        "the probe must route through the injected seam, never the wire"
    )


# =====================================================================
# L6H-03: the dataset-root landing base (261014-l6h; rerouted 10-07 /
# CR-01) — constructor dataset_root param > the run-config chain
# (resolve_dirs(load_state()).dataset_root_abs — the slot-4 spec,
# seeded from directories.json INSIDE load_state()) > the repo
# pipeline/ default. Every dataset LANDING site resolves through the
# one helper: the ChannelSpec local_dir, the landing gate's relative
# naming, the shape-C rename, the zenodo extract target, the
# landed-keys scan, and the reconcile staged absolute Dataset_path.
# The official REGISTRY read stays repo-anchored — registry is repo
# state, never redirected by user storage config (the deliberate
# not-rerouted list).
# =====================================================================

@pytest.fixture(autouse=True)
def _pin_directories_config(tmp_path_factory, monkeypatch):
    """Every queue test runs against an EMPTY config root AND an EMPTY
    state root — the absent-directories.json + absent-run_config.json
    case — making this whole module the byte-identity proof (and
    hermetic against developer-machine files). The STATE pin is the
    10-07/CR-01 hermeticity requirement: after the reroute every
    ``_datasets_base()`` call reads ``settings.state_dir() /
    run_config.json``, and a live one exists on the maintainer box —
    without the pin it could steer any queue test's landing base.
    tmp_path_FACTORY, never the per-test tmp_path: the
    no-residue/never-persists lanes above assert their tmp_path's
    exact contents (the root-conftest pin's own rule); explicit
    in-test ``pin_state_dir`` calls override the autouse pin and keep
    working."""
    pinned = tmp_path_factory.mktemp("dq-no-directories-config")
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(pinned))
    pinned_state = tmp_path_factory.mktemp("dq-no-run-config-state")
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(pinned_state))


def write_directories_json(config_dir, doc):
    """Place a directories.json under a config root (the file tier)."""
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "directories.json").write_text(
        json.dumps(doc), encoding="utf-8")
    return config_dir


def test_file_dataset_root_redirects_spec_local_dir_and_gate_naming(
        monkeypatch, tmp_path):
    """The file tier: a directories.json carrying dataset_root under an
    injected config dir redirects ChannelSpec.local_dir under
    X/datasets, AND the landing gate names missing paths relative to
    X/datasets (never the repo pipeline form)."""
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)
    root_x = tmp_path / "storage-x"
    config = write_directories_json(
        tmp_path / "cfg-file", {"dataset_root": str(root_x)})
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(config))

    spec = service.resolve_channel("Demo__task")

    assert spec.local_dir == root_x / "datasets" / "Demo"
    problem, details = service._landing_details(spec)
    assert problem == download_queue.PROBLEM_LANDING_INCOMPLETE
    assert details == [
        "missing=Demo/task/train.csv",
        "missing=Demo/task/dev.csv",
        "missing=Demo/task/test.csv",
    ]


def test_constructor_dataset_root_beats_file_key(monkeypatch, tmp_path):
    """The precedence pin: an explicit constructor dataset_root (the
    flag tier) wins over a present-and-set file key."""
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    root_x = tmp_path / "storage-x"
    root_y = tmp_path / "storage-y"
    config = write_directories_json(
        tmp_path / "cfg-both", {"dataset_root": str(root_x)})
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(config))
    service = download_queue.DownloadQueueService(
        repo_root=repo, cli_path=str(fake_cli(tmp_path)),
        dataset_root=str(root_y))

    spec = service.resolve_channel("Demo__task")

    assert spec.local_dir == root_y / "datasets" / "Demo"


def test_absent_param_and_file_keep_repo_pipeline_datasets_form(tmp_path):
    """The byte-identity pin: with neither the param nor a file (the
    module autouse fixture pins the config root empty), local_dir is
    EXACTLY the repo pipeline/datasets form — the 144 pre-existing
    tests prove the same for every other landing site."""
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)

    spec = service.resolve_channel("Demo__task")

    assert spec.local_dir == repo / "pipeline" / "datasets" / "Demo"


def test_corrupt_directories_json_degrades_to_repo_default(
        monkeypatch, tmp_path):
    """The tolerant service-tier seam: a corrupt directories.json
    (invalid JSON) degrades to the repo default — no SystemExit ever
    escapes the service (the strict fail-loud lane belongs to the
    pipeline scripts alone)."""
    repo = tmp_repo_with_registry(tmp_path / "repo", synth_entries())
    service = service_over(repo, tmp_path)
    config = tmp_path / "cfg-corrupt"
    config.mkdir()
    (config / "directories.json").write_text(
        "{not valid json", encoding="utf-8")
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(config))

    spec = service.resolve_channel("Demo__task")

    assert spec.local_dir == repo / "pipeline" / "datasets" / "Demo"


# =====================================================================
# CR-01 (10-07): landing-base/consumption-base AGREEMENT — the queue's
# dataset landing base resolves through the SAME run-config chain every
# consumption side reads (the env-check dataset_dirs kernel,
# env_check.py's resolve_dirs(load_state()) + check_dataset_dirs, and
# compose_argv's --dataset_root), pinned across the verifier's exact
# three-configuration repro matrix (10-VERIFICATION.md). Modes 1 and 2
# were the reproduced divergence; the control pins byte-identity.
# =====================================================================

def test_datasets_base_agrees_with_consumption_spec_without_file_cr01(
        monkeypatch, tmp_path):
    """Mode 1 (spec-without-file, the PRIMARY UI flow): the operator
    set 数据集根 on slot 4 — persisted as session state — and never
    pressed [s] 保存默认, so directories.json is absent. The BARE
    production construction (no param threading, the tui/app.py shape)
    must land at the configured root, and the landing base must EQUAL
    the consumption base (the chain the env kernel and the launched
    sweep read)."""
    state = tmp_path / "state-cr01"
    state.mkdir()
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    root_x = tmp_path / "sweep-data"
    run_config.save_state(
        replace(run_config.DEFAULT_RUN_SPEC, dataset_root=str(root_x)))

    service = download_queue.DownloadQueueService()
    consumption = run_config.resolve_dirs(
        run_config.load_state()).dataset_root_abs

    assert service._datasets_base() == root_x
    assert str(service._datasets_base()) == consumption


def test_datasets_base_agrees_with_consumption_relative_file_value_cr01(
        monkeypatch, tmp_path):
    """Mode 2 (relative file value, TUI CWD != repo root): a
    directories.json carrying a RELATIVE dataset_root and no state
    file. The landing base must anchor against REPO_ROOT exactly like
    the consumption chain (_abs_against_repo_root), never the process
    CWD — the download lands where the configured run reads it."""
    config = write_directories_json(
        tmp_path / "cfg-rel", {"dataset_root": "rel-ds"})
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(config))
    monkeypatch.chdir(tmp_path)

    service = download_queue.DownloadQueueService()
    consumption = run_config.resolve_dirs(
        run_config.load_state()).dataset_root_abs

    assert consumption == str(run_config._abs_against_repo_root("rel-ds"))
    assert service._datasets_base() == Path(consumption)
    assert service._datasets_base() == download_queue.REPO_ROOT / "rel-ds"
    assert service._datasets_base() != tmp_path / "rel-ds"


def test_datasets_base_agrees_with_consumption_default_control_cr01():
    """Control (aligned default): neither spec nor file set (the
    autouse fixture pins both roots empty) — the consumption chain
    answers dataset_root_abs None and the landing base is EXACTLY the
    repo pipeline/ dir. The byte-identity control: passes before AND
    after the reroute, pinning that the reroute changes nothing when
    nothing is configured."""
    service = download_queue.DownloadQueueService()

    dirs = run_config.resolve_dirs(run_config.load_state())

    assert dirs.dataset_root_abs is None
    assert service._datasets_base() == download_queue.REPO_ROOT / "pipeline"


# =====================================================================
# Lane 11: the KIND_MODEL channel (MLC-01, 261014-mlc) — dnallm-authority
# model downloads through the shared queue. Every test stays CI-safe: the
# fake-spawner engine lane writes fixture trees under tmp_path; NO test
# imports dnallm or modelscope or touches the network (the -I subprocess
# is the only place dnallm code ever runs).
# =====================================================================

MODEL_KEY = "DNABERT-2-117M"           # the smallest adapted slot model
MODEL_REPO_ID = "ZhejiangLab-LifeScience/DNABERT-2-117M"
UNADAPTED_MODEL_KEY = "CrossDNA_519M"  # committed, verdict dnllm_adapted false


def tmp_repo_with_models_registry(tmp_path, entries):
    """A tmp repo root carrying a synthetic official MODELS registry (the
    model channel's registry authority — same shape as the dataset
    helper, over models_info.json)."""
    pipeline = tmp_path / "pipeline"
    pipeline.mkdir(parents=True, exist_ok=True)
    (pipeline / "models_info.json").write_text(
        json.dumps(entries), encoding="utf-8")
    return tmp_path


MODEL_ENTRY = {"Model_path": "models/DNABERT-2-117M", "size (M)": 117}


class ModelFakeSpawner:
    """The model lane's injectable spawner: records every spawn and
    optionally stages a modelscope-1.40.2-shaped landing tree under the
    argv landing dir before answering (the normalization fixture)."""

    def __init__(self, returncode=0, writer=None,
                 stderr=b"downloading model ...\n"):
        self.returncode_value = returncode
        self.writer = writer
        self._stderr = stderr
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "kwargs": dict(kwargs)})
        if self.writer is not None:
            self.writer(argv)
        return FakePopen(returncode=self.returncode_value,
                         stdout=b"", stderr=self._stderr)


def write_modelscope_nesting(landing, org_repo=MODEL_REPO_ID, files=None):
    """Stage the live-probed modelscope 1.40.2 cache layout under the
    landing dir: models/<org>--<name>/snapshots/<rev>/<files> plus the
    .lock/ scaffolding dir."""
    slug = org_repo.replace("/", "--")
    snapshot = Path(landing) / "models" / slug / "snapshots" / "master"
    snapshot.mkdir(parents=True, exist_ok=True)
    for name in (files if files is not None
                 else ("config.json", "tokenizer_config.json",
                       "model.safetensors")):
        (snapshot / name).write_text("{}" if name.endswith(".json")
                                     else "weights", encoding="utf-8")
    (Path(landing) / ".lock").mkdir(exist_ok=True)
    return snapshot


def model_engine_service(tmp_path, monkeypatch, spawner,
                         entries=None, model_root=None, writer=None):
    """A model-lane service over a tmp repo + tmp state root + injected
    spawner, with the entry already enqueued (kind=KIND_MODEL) and
    claimed for run_task. ``writer`` optionally arms the spawner's
    landing-tree staging hook (the normalization fixtures)."""
    if writer is not None:
        spawner.writer = writer
    repo = tmp_repo_with_models_registry(
        tmp_path / "repo", entries or {MODEL_KEY: dict(MODEL_ENTRY)})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    root = model_root if model_root is not None else tmp_path / "mstore"
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        spawner=spawner, cli_path=str(fake_cli(tmp_path)),
        model_root=str(root))
    assert service.enqueue_model(MODEL_KEY).action == "enqueued"
    service.claim_next()
    return service, repo, state, Path(root)


# ===== vocabulary + the fixed program constant (T-qt-01) =====


def test_kind_model_vocabulary_and_program_constant_pinned():
    """The model-kind contract: KIND_MODEL beside the dataset kinds, and
    the FIXED module-level program the -I subprocess runs — the L6H-04
    proven invocation (functools.partial-bound modelscope
    snapshot_download with cache_dir riding the partial, because the
    dnallm download_model wrapper does not thread it)."""
    assert download_queue.KIND_MODEL == "model"
    program = download_queue.MODEL_DOWNLOAD_PROGRAM
    for fragment in (
            "from functools import partial",
            ("from modelscope.hub.snapshot_download "
             "import snapshot_download"),
            "from dnallm.models.model import download_model",
            "download_model(repo_id, downloader=partial(",
            "cache_dir="):
        assert fragment in program, fragment


def test_model_reason_codes_are_machine_vocabulary():
    """The model lane's reason/problem codes (the screens render, never
    parse)."""
    assert download_queue.REASON_NOT_DNLLM_ADAPTED == "not_dnllm_adapted"
    assert download_queue.REASON_COMPAT_UNAVAILABLE == "compat_unavailable"
    assert download_queue.REASON_NO_MODEL_PATH == "no_model_path"
    assert download_queue.REASON_ALREADY_PRESENT == "already_present"
    assert download_queue.PROBLEM_MODEL_NESTING == "model_nesting_ambiguous"
    assert download_queue.PROBLEM_MODEL_HOIST_ERROR == "model_hoist_error"


# ===== resolve_model_channel + _models_base =====


def test_model_channel_census_36_clean_23_not_adapted_over_committed(
        monkeypatch, tmp_path):
    """THE compat gate: over the committed 59-key models registry,
    exactly 36 keys resolve a clean spec (repo id == the compat map's
    modelscope id; landing == the model_presence join over the effective
    base; source_url carries the repo id) and 23 degrade with
    not_dnllm_adapted — computed key-by-key, drift surfaces loudly."""
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    registry = json.loads(
        (REPO_ROOT / "pipeline" / "models_info.json").read_text(
            encoding="utf-8"))
    compat = download_queue.registries.load_dnallm_compat()

    clean, degraded = {}, {}
    for key in registry:
        spec = service.resolve_model_channel(key)
        assert spec is not None, key
        if spec.reason_code is None:
            clean[key] = spec
        else:
            degraded[key] = spec.reason_code

    assert len(clean) == 36
    assert len(degraded) == 23
    assert set(degraded.values()) == {"not_dnllm_adapted"}
    base = str(service._models_base()).rstrip(os.sep) + os.sep
    for key, spec in clean.items():
        assert spec.repo_id == compat[key]["modelscope"], key
        expected_landing = base + registry[key]["Model_path"]
        assert str(spec.landing) == expected_landing, key
        assert "modelscope.cn" in spec.source_url
        assert spec.repo_id in spec.source_url


def test_models_base_is_byte_identical_to_the_selection_presence_chain(
        monkeypatch, tmp_path):
    """The MLC-01 landing/presence agreement pin: with no constructor
    param and no configured root, ``_models_base()`` is byte-identical
    to the chain SelectionBackend feeds ``model_presence`` (a landed
    model ALWAYS flips its presence cell)."""
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    from types import SimpleNamespace

    from tui.services import run_config as run_config_service
    dirs = run_config_service.resolve_dirs(
        run_config_service.load_state())
    expected = dirs.model_root_abs or str(
        run_config_service.DEFAULT_REGISTRY_DIR)
    assert str(service._models_base()) == expected

    # the run-config tier: a configured root redirects the base (the
    # seam patched on the module the queue imports)
    root_x = tmp_path / "stor-x"
    monkeypatch.setattr(download_queue.run_config,
                        "load_state", lambda: object())
    monkeypatch.setattr(
        download_queue.run_config, "resolve_dirs",
        lambda spec: SimpleNamespace(model_root_abs=str(root_x)))
    assert str(service._models_base()) == str(root_x)

    # the param tier beats the file tier
    root_y = tmp_path / "stor-y"
    param = download_queue.DownloadQueueService(
        model_root=str(root_y), cli_path=str(fake_cli(tmp_path)))
    assert str(param._models_base()) == str(root_y)


def test_resolve_model_channel_unknown_key_yields_none(
        monkeypatch, tmp_path):
    """A key absent from the official MODELS registry resolves None (the
    caller answers unknown_key) — customs are not download targets."""
    service, _ = make_service(tmp_path, monkeypatch)
    assert service.resolve_model_channel("not-a-model-key") is None


# ===== enqueue_model outcome order =====


def test_enqueue_model_happy_path_appends_kind_model_entry(
        monkeypatch, tmp_path):
    service, state = make_service(tmp_path, monkeypatch)

    outcome = service.enqueue_model(MODEL_KEY)

    assert outcome.action == "enqueued"
    assert outcome.key == MODEL_KEY
    (entry,) = service.entries()
    assert entry.kind == download_queue.KIND_MODEL
    assert entry.state == "pending"
    doc = json.loads(state_file(state).read_text(encoding="utf-8"))
    assert doc["entries"][0]["kind"] == download_queue.KIND_MODEL
    assert set(doc["entries"][0]) == CANONICAL_ENTRY_FIELDS


def test_enqueue_model_is_idempotent_per_key_any_state(
        monkeypatch, tmp_path):
    """An existing entry of ANY state yields already_queued first (the
    D-08 twin — even when the CLI has since gone absent)."""
    service, _ = make_service(tmp_path, monkeypatch)
    assert service.enqueue_model(MODEL_KEY).action == "enqueued"

    again = service.enqueue_model(MODEL_KEY)

    assert again.action == "already_queued"
    assert len(service.entries()) == 1


def test_enqueue_model_unknown_key_never_appends(monkeypatch, tmp_path):
    service, _ = make_service(tmp_path, monkeypatch)

    outcome = service.enqueue_model("NotInRegistry__nope")

    assert outcome.action == "unknown_key"
    assert service.entries() == []


def test_enqueue_model_unadapted_verdict_yields_not_dnllm_adapted(
        monkeypatch, tmp_path):
    """A committed official key whose compat verdict is false enqueues
    to unknown/not_dnllm_adapted — the honest manual-placement class,
    never HF guidance, never a queue row."""
    service, _ = make_service(tmp_path, monkeypatch)

    outcome = service.enqueue_model(UNADAPTED_MODEL_KEY)

    assert outcome.action == "unknown"
    assert outcome.reason_code == "not_dnllm_adapted"
    assert service.entries() == []


def test_enqueue_model_absent_compat_entry_while_loadable_is_not_adapted(
        monkeypatch, tmp_path):
    """A key the (loadable, non-empty) compat map simply lacks reads as
    not_dnllm_adapted — registry evolution, not an outage."""
    service, _ = make_service(tmp_path, monkeypatch)
    committed = download_queue.registries.load_dnallm_compat()
    assert committed  # the map is loadable and non-empty
    monkeypatch.setattr(
        download_queue.registries, "load_dnallm_compat",
        lambda: {k: v for k, v in committed.items() if k != MODEL_KEY})

    outcome = service.enqueue_model(MODEL_KEY)

    assert outcome.action == "unknown"
    assert outcome.reason_code == "not_dnllm_adapted"


def test_enqueue_model_unreadable_compat_map_yields_compat_unavailable(
        monkeypatch, tmp_path):
    """An EMPTY compat mapping is the degraded read (the committed map
    carries all 59 keys — emptiness is the unreadable signal): the
    honest compat_unavailable reason, never a crash."""
    service, _ = make_service(tmp_path, monkeypatch)
    monkeypatch.setattr(
        download_queue.registries, "load_dnallm_compat", dict)

    outcome = service.enqueue_model(MODEL_KEY)

    assert outcome.action == "unknown"
    assert outcome.reason_code == "compat_unavailable"
    assert service.entries() == []


def test_enqueue_model_no_model_path_yields_no_model_path(
        monkeypatch, tmp_path):
    """An adapted key whose REGISTRY entry carries no usable Model_path
    string enqueues to unknown/no_model_path (no landing can be
    composed)."""
    repo = tmp_repo_with_models_registry(
        tmp_path / "repo", {MODEL_KEY: {"size (M)": 117}})
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        repo_root=repo, model_root=str(tmp_path / "mstore"),
        cli_path=str(fake_cli(tmp_path)))

    outcome = service.enqueue_model(MODEL_KEY)

    assert outcome.action == "unknown"
    assert outcome.reason_code == "no_model_path"
    assert service.entries() == []


def test_enqueue_model_existing_landing_yields_already_present(
        monkeypatch, tmp_path):
    """The defensive disk gate: a landing dir that already exists on
    disk refuses with already_present (presence will read it — enqueueing
    a download over a landed card is never the honest action)."""
    repo = tmp_repo_with_models_registry(
        tmp_path / "repo", {MODEL_KEY: dict(MODEL_ENTRY)})
    root = tmp_path / "mstore"
    (root / "models" / MODEL_KEY).mkdir(parents=True)
    pin_state_dir(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService(
        repo_root=repo, model_root=str(root),
        cli_path=str(fake_cli(tmp_path)))

    outcome = service.enqueue_model(MODEL_KEY)

    assert outcome.action == "unknown"
    assert outcome.reason_code == "already_present"
    assert service.entries() == []


def test_enqueue_model_cli_unavailable_outcome(monkeypatch, tmp_path):
    """The CLI probe doubles as the modelscope-package presence proxy
    (the -I program imports modelscope from the same env)."""
    pin_state_dir(monkeypatch, tmp_path)
    force_cli_absent(monkeypatch, tmp_path)
    service = download_queue.DownloadQueueService()

    outcome = service.enqueue_model(MODEL_KEY)

    assert outcome.action == "cli_unavailable"
    assert service.entries() == []


def test_enqueue_model_persist_failure_refused_no_ghost_row(
        tmp_path, monkeypatch):
    """The WR-04 twin: an unwritable state rail refuses with
    persist_failed and rolls the append back — never a ghost row."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    service = download_queue.DownloadQueueService(
        cli_path=str(fake_cli(tmp_path)))
    read_only_state(state)
    try:
        outcome = service.enqueue_model(MODEL_KEY)

        assert outcome.action == "persist_failed"
        assert service.entries() == []
    finally:
        writable_state(state)


# ===== run_task: the KIND_MODEL branch (spawn/normalize/gate) =====


def test_model_run_task_pins_isolated_python_argv_env_and_session(
        monkeypatch, tmp_path):
    """The spawn discipline: LIST argv [sys.executable, -I, -c, the
    FIXED program, landing, repo_id] (T-qt-01: no operator-controlled
    code — only landing dir + repo id cross as argv DATA), env exactly
    dict(os.environ), start_new_session, PIPEs."""
    spawner = ModelFakeSpawner(returncode=0)
    service, _repo, _state, root = model_engine_service(
        tmp_path, monkeypatch, spawner,
        writer=lambda argv: write_modelscope_nesting(argv[4]))

    event = service.run_task(MODEL_KEY, run_id="m1")

    assert event.state == "done"
    (call,) = spawner.calls
    argv = call["argv"]
    assert argv[0] == sys.executable
    assert argv[1:4] == ["-I", "-c", download_queue.MODEL_DOWNLOAD_PROGRAM]
    assert argv[4:] == [str(root / "models" / MODEL_KEY), MODEL_REPO_ID]
    assert call["kwargs"]["env"] == dict(os.environ)
    assert call["kwargs"]["start_new_session"] is True
    assert call["kwargs"]["stdout"] == subprocess.PIPE
    assert call["kwargs"]["stderr"] == subprocess.PIPE


def test_model_run_task_progress_cb_fires_on_integer_change(
        monkeypatch, tmp_path):
    """C4J-1 (261015-c4j): the model lane threads ``progress_cb`` — its
    stderr pump runs the SAME best-effort ``parse_progress`` extraction
    the dataset lane uses (dedupe per integer-percent change, the
    ``run_task`` percent_state closure verbatim); the final event carries
    the last parsed percent. A child emitting nothing parseable fires
    nothing (the neighboring nesting-gate test pins that None path)."""
    line = ("Downloading [models/x/model.safetensors]:"
            " {p}%|x| y/y [00:00<00:00]\n")
    stderr = ChunkedStream([
        "dnallm chatter (no percent)\n",
        line.format(p=0), line.format(p=0),
        line.format(p=50),
        line.format(p=100), line.format(p=100),
    ])
    spawner = ModelFakeSpawner(
        returncode=0, stderr=stderr,
        writer=lambda argv: write_modelscope_nesting(argv[4]))
    service, _repo, _state, _root = model_engine_service(
        tmp_path, monkeypatch, spawner)
    fired = []

    event = service.run_task(
        MODEL_KEY, run_id="m-pct",
        progress_cb=lambda key, pct: fired.append((key, pct)))

    assert fired == [(MODEL_KEY, 0), (MODEL_KEY, 50), (MODEL_KEY, 100)], (
        "dedupe per integer change — the dataset lane's exact closure"
    )
    assert event.state == "done"
    assert event.last_percent == 100, (
        "the last parsed percent lands on the event (slot 2 renders it)"
    )


def test_model_run_task_normalizes_nesting_and_gates_on_config_json(
        monkeypatch, tmp_path):
    """Exit 0 + the modelscope 1.40.2 nesting: the single snapshot dir's
    children hoist to the landing root, the scaffolding (models/ subtree
    + .lock/) is removed, and done REQUIRES config.json to exist
    DIRECTLY in the landing dir — no reconcile leg (models are not
    n_audit subjects)."""
    spawner = ModelFakeSpawner(returncode=0)
    service, _repo, _state, root = model_engine_service(
        tmp_path, monkeypatch, spawner,
        writer=lambda argv: write_modelscope_nesting(argv[4]))

    event = service.run_task(MODEL_KEY, run_id="m2")

    landing = root / "models" / MODEL_KEY
    assert event.state == "done"
    assert event.problems == ()
    assert event.last_percent is None, (
        "this fake child emits no parseable percents — percent None "
        "stays the honest indeterminate (C4J-1 parses best-effort, "
        "never fabricates)"
    )
    assert (landing / "config.json").is_file()
    assert (landing / "tokenizer_config.json").is_file()
    assert not (landing / "models").exists(), "scaffolding removed"
    assert not (landing / ".lock").exists(), "lock dir removed"
    (entry,) = service.entries()
    assert entry.state == "done"
    assert entry.reconcile is None, "the model lane has NO reconcile leg"


def test_model_run_task_zero_snapshot_dirs_fails_ambiguous(
        monkeypatch, tmp_path):
    """A models/ scaffolding with ZERO snapshot dirs fails honestly
    (model_nesting_ambiguous) — the nesting is unreadable, never a
    fabricated done."""

    def writer(argv):
        (Path(argv[4]) / "models").mkdir(parents=True, exist_ok=True)

    spawner = ModelFakeSpawner(returncode=0)
    service, _repo, _state, _root = model_engine_service(
        tmp_path, monkeypatch, spawner, writer=writer)

    event = service.run_task(MODEL_KEY, run_id="m3")

    assert event.state == "failed"
    assert download_queue.PROBLEM_MODEL_NESTING in event.problems


def test_model_run_task_multiple_snapshot_dirs_fails_ambiguous(
        monkeypatch, tmp_path):
    """Two snapshot dirs (an ambiguous hoist) fail honestly — collapsing
    either one silently would be a data decision, never the queue's."""

    def writer(argv):
        for rev in ("master", "v2"):
            write_modelscope_nesting(argv[4], files=("config.json",))
            # second revision under the same slug
            slug = MODEL_REPO_ID.replace("/", "--")
            extra = Path(argv[4]) / "models" / slug / "snapshots" / rev
            extra.mkdir(parents=True, exist_ok=True)
            (extra / "config.json").write_text("{}", encoding="utf-8")

    spawner = ModelFakeSpawner(returncode=0)
    service, _repo, _state, _root = model_engine_service(
        tmp_path, monkeypatch, spawner, writer=writer)

    event = service.run_task(MODEL_KEY, run_id="m4")

    assert event.state == "failed"
    assert download_queue.PROBLEM_MODEL_NESTING in event.problems


def test_model_run_task_empty_landing_fails_honestly(
        monkeypatch, tmp_path):
    """Exit 0 with an EMPTY landing (nothing staged) fails with the
    landing-incomplete gate — exit 0 alone can never mean done."""

    def writer(argv):
        Path(argv[4]).mkdir(parents=True, exist_ok=True)

    spawner = ModelFakeSpawner(returncode=0)
    service, _repo, _state, _root = model_engine_service(
        tmp_path, monkeypatch, spawner, writer=writer)

    event = service.run_task(MODEL_KEY, run_id="m5")

    assert event.state == "failed"
    assert download_queue.PROBLEM_LANDING_INCOMPLETE in event.problems


def test_model_run_task_nonzero_exit_fails_exit_code(
        monkeypatch, tmp_path):
    spawner = ModelFakeSpawner(returncode=3)
    service, _repo, _state, _root = model_engine_service(
        tmp_path, monkeypatch, spawner)

    event = service.run_task(MODEL_KEY, run_id="m6")

    assert event.state == "failed"
    assert "exit_3" in event.problems


def test_model_run_task_degraded_channel_fails_with_reason(
        monkeypatch, tmp_path):
    """A claimed entry whose channel degraded after the claim (the map
    went unreadable) fails carrying the reason — never a spawn."""
    repo = tmp_repo_with_models_registry(
        tmp_path / "repo", {MODEL_KEY: dict(MODEL_ENTRY)})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    spawner = ModelFakeSpawner()
    service = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        spawner=spawner, cli_path=str(fake_cli(tmp_path)),
        model_root=str(tmp_path / "mstore"))
    assert service.enqueue_model(MODEL_KEY).action == "enqueued"
    service.claim_next()
    monkeypatch.setattr(
        download_queue.registries, "load_dnallm_compat", dict)

    event = service.run_task(MODEL_KEY, run_id="m7")

    assert event.state == "failed"
    assert "compat_unavailable" in event.problems
    assert spawner.calls == []


# ===== boot resume: KIND_MODEL entries ride the existing machinery =====


def test_persisted_pending_model_entry_survives_load_and_reclaims(
        monkeypatch, tmp_path):
    """A persisted pending KIND_MODEL entry rehydrates on load() and
    claim_next hands it to the driver with its kind intact (the D-06
    restart downgrade rides the existing machinery unchanged)."""
    repo = tmp_repo_with_models_registry(
        tmp_path / "repo", {MODEL_KEY: dict(MODEL_ENTRY)})
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    first = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        cli_path=str(fake_cli(tmp_path)),
        model_root=str(tmp_path / "mstore"))
    assert first.enqueue_model(MODEL_KEY).action == "enqueued"
    first.claim_next()   # persist as downloading

    fresh = download_queue.DownloadQueueService(
        repo_root=repo, state_path=state / "download_queue.json",
        cli_path=str(fake_cli(tmp_path)),
        model_root=str(tmp_path / "mstore"))
    assert fresh.load() is None

    (entry,) = fresh.entries()
    assert entry.state == "pending", "the D-06 downgrade"
    assert entry.interrupted is True
    claimed = fresh.claim_next()
    assert claimed is not None
    assert claimed.kind == download_queue.KIND_MODEL
    assert claimed.key == MODEL_KEY


# =====================================================================
# EHC-4 (261015-ehc ruling 4) — the parsed download SPEED alongside the
# percent (slots 2 + 3 only; the additive-fake pin holds: the existing
# 2-arg-lambda tests above prove the no-rate path keeps calling the
# callback with TWO arguments)
# =====================================================================


def test_parse_speed_tqdm_and_modelscope_tokens():
    """TQDM-style rates parse verbatim — unspaced, spaced, and the
    binary i-prefix variants."""
    assert download_queue.parse_speed(
        " 42%|x| 1G/2G [00:10<00:10, 892kB/s]") == "892kB/s"
    assert download_queue.parse_speed("1.23MB/s") == "1.23MB/s"
    assert download_queue.parse_speed("5.0 MiB/s") == "5.0 MiB/s"
    assert download_queue.parse_speed("rate=892kB/s tail") == "892kB/s"


def test_parse_speed_last_token_wins_none_without_rate():
    """A multi-line chunk carries the NEWEST rate; chunks without a rate
    token parse None — the honest fallback, never a fabricated speed."""
    assert download_queue.parse_speed(
        "old 1kB/s\nnewest 2.5GB/s") == "2.5GB/s"
    assert download_queue.parse_speed(
        "no rate here [00:10<00:10]") is None
    assert download_queue.parse_speed("") is None


def test_parse_speed_adversarial_garbage_never_raises():
    """T-ehc-01: ANSI-laden, CR-carried, huge-digit garbage never raises
    (regex-only extraction over the cleaned chunk)."""
    for garbage in (
        "\x1b[2K\r  50%\r\x1b[0m laden 892kB/s",
        "\x1b[1A\x1b[2K 999999999999TB/s",
        "B/s kB/s 12/34 5.0.0.0MB/s",
    ):
        result = download_queue.parse_speed(garbage)
        assert result is None or isinstance(result, str)


def test_progress_callback_carries_speed_on_the_pair_dedupe(
        monkeypatch, tmp_path):
    """EHC-4 plumbing: percent WITHOUT a rate fires the 2-ARG call
    (every pre-existing 2-arg fake keeps conforming); a stalled percent
    with a NEW rate still fires (the dedupe is on the (percent, speed)
    PAIR — a big file's percent can stall while the rate streams); an
    unchanged pair never re-fires."""
    rated = ("Downloading [a/train.csv]: {p}%|x| y/y "
             "[00:00<00:00, {s}]\n")
    plain = "Downloading [a/train.csv]: {p}%|x| y/y [00:00<00:00]\n"
    stderr = ChunkedStream([
        plain.format(p=10),               # no rate -> the 2-arg call
        rated.format(p=10, s="892kB/s"),  # stalled pct + new rate -> fires
        rated.format(p=10, s="892kB/s"),  # pair unchanged -> deduped
        rated.format(p=20, s="1.2MB/s"),  # both changed -> fires
    ])
    spawner = FakeSpawner(FakePopen(returncode=0, stderr=stderr))
    service, repo, _ = engine_service(tmp_path, monkeypatch, spawner)
    land_csvs(repo, "Demo", "task")
    fired = []

    event = service.run_task(
        "Demo__task", run_id="r1",
        progress_cb=lambda key, pct, speed=None: fired.append(
            (key, pct, speed)))

    assert fired == [
        ("Demo__task", 10, None),
        ("Demo__task", 10, "892kB/s"),
        ("Demo__task", 20, "1.2MB/s"),
    ], "speed-only changes are real ticks; unchanged pairs dedupe"
    assert event.last_percent == 20


def test_model_lane_progress_callback_carries_speed_identically(
        monkeypatch, tmp_path):
    """The -I model-lane pump behaves IDENTICALLY to the dataset CLI
    lane (EHC-4): the same (percent, speed) pair dedupe and the same
    additive 2-arg/3-arg call discipline."""
    rated = ("Downloading [models/x/model.safetensors]:"
             " {p}%|x| y/y [00:00<00:00, {s}]\n")
    plain = ("Downloading [models/x/model.safetensors]:"
             " {p}%|x| y/y [00:00<00:00]\n")
    stderr = ChunkedStream([
        plain.format(p=0),
        rated.format(p=0, s="512kB/s"),
        rated.format(p=0, s="512kB/s"),
        rated.format(p=99, s="4.5MB/s"),
    ])
    spawner = ModelFakeSpawner(
        returncode=0, stderr=stderr,
        writer=lambda argv: write_modelscope_nesting(argv[4]))
    service, _repo, _state, _root = model_engine_service(
        tmp_path, monkeypatch, spawner)
    fired = []

    event = service.run_task(
        MODEL_KEY, run_id="m-speed",
        progress_cb=lambda key, pct, speed=None: fired.append(
            (key, pct, speed)))

    assert fired == [
        (MODEL_KEY, 0, None),
        (MODEL_KEY, 0, "512kB/s"),
        (MODEL_KEY, 99, "4.5MB/s"),
    ]
    assert event.state == "done"
    assert event.last_percent == 99
