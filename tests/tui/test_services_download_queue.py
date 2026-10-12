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
    service, _, _ = engine_service(tmp_path, monkeypatch, spawner,
                                   cli=tmp_path / "absent-cli")
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
