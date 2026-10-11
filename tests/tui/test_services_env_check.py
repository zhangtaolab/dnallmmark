"""
Tier-1 service tests for ``tui/services/env_check.py`` (Phase 8, 08-04).

Pinned decisions:

- ENV-01/D-02: the service imports the env_smoke kernels and consumes
  their structured ``CheckResult`` returns — never subprocess, never
  stdout parsing, never a re-implemented check.
- ENV-02/D-05 (cache): a same-LOCAL-calendar-day restart is a cache hit
  (the 08-06 screen's zero-kernel signal); yesterday is a miss; a
  torn/corrupt/missing state file is a cache miss (None sentinel through
  ``artifact_loader``), never a crash.
- D-05 (persistence): partial failures persist whole (every item's
  status and detail lines); persisting twice is idempotent through the
  atomic tmp+os.replace write (no residue, single valid file).
- Pitfall 8: the same-day comparison runs in LOCAL calendar time —
  ``checked_at`` is the local naive display value and
  ``checked_at_iso`` the ISO instant of the same moment.
- D-03: NO real GPU kernel executes in any test here — injected fakes
  and monkeypatched ``env_smoke`` kernel attributes only (the CI
  discipline; real kernels run only on the GB10 host).

See also:
    ``tui/services/env_check.py`` — the service under test.
    ``pipeline/env_smoke.py`` — the kernels (main() order authority).
    ``tests/test_env_smoke_bytes.py`` — the CLI byte contract.
"""

import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import env_smoke  # conftest puts pipeline/ on sys.path (D-02/D-19)
from env_smoke import CheckResult

from tui.services import env_check
from tui.services.env_check import (
    default_state_path,
    is_same_local_day,
    load_cached,
    persist,
    run_full_check,
)

# main()'s result-list order — the row/serialization vocabulary (08-01).
MAIN_KERNEL_ORDER = (
    "version_pins",
    "dnallm",
    "peft",
    "cuda",
    "matmul",
    "numpy",
    "dataset_dirs",
)


def _local(year, month, day, hour=0, minute=0):
    """A naive LOCAL datetime — the service's display basis (Pitfall 8).

    Deliberately naive (single justified noqa): the service contract
    reads naive values as local wall-clock time, and these fixtures pin
    exactly that path — an aware fixture would test a different branch.
    """
    return datetime(year, month, day, hour, minute)  # noqa: DTZ001


def _pass(name):
    """A fake passing kernel result."""
    return CheckResult(name=name, ok=True, lines=(f"PASS: fake {name}",))


def _fail(name):
    """A fake failing kernel result carrying a detail line."""
    return CheckResult(name=name, ok=False, lines=(f"FAIL: fake {name} detail",))


# ===== Cache semantics (D-05) =====


def test_same_day_state_is_a_cache_hit(tmp_path):
    """checked_at on today's LOCAL calendar day -> same-day hit."""
    path = tmp_path / "env_check.json"
    now = _local(2026, 10, 11, 9, 30)
    persist(path, [_pass("numpy")], now=now)
    state = load_cached(path)
    assert state is not None
    # The 08-06 on_mount composition: a same-day hit means ZERO kernels
    # run — the screen renders the cached items instead.
    assert is_same_local_day(state, now=now) is True


def test_yesterday_state_is_a_cache_miss(tmp_path):
    """checked_at yesterday -> the cache does not satisfy startup (D-05)."""
    path = tmp_path / "env_check.json"
    now = _local(2026, 10, 11, 9, 30)
    persist(path, [_pass("numpy")], now=now - timedelta(days=1))
    state = load_cached(path)
    assert is_same_local_day(state, now=now) is False


def test_corrupt_state_file_is_a_none_cache_miss_without_raising(tmp_path):
    """A torn/truncated state file loads as None — full re-run, no crash."""
    path = tmp_path / "env_check.json"
    path.write_text('{"schema_version": 1, "checked_at": "2026-10-1',
                    encoding="utf-8")
    assert load_cached(path) is None


def test_missing_state_file_is_a_none_cache_miss(tmp_path):
    """An absent state file is a cache miss, never an exception."""
    assert load_cached(tmp_path / "absent.json") is None


def test_none_state_is_never_a_same_day_hit():
    """The None sentinel (corrupt/missing) can never read as a cache hit."""
    assert is_same_local_day(None) is False


# ===== Persistence (D-05, T-08-03) =====


def test_persist_writes_schema_and_both_timestamps(tmp_path):
    """State shape: schema_version 1 + local naive + ISO + full items."""
    path = tmp_path / "env_check.json"
    now = _local(2026, 10, 11, 16, 20)
    persist(path, [_pass("version_pins"), _fail("cuda")], now=now)
    state = load_cached(path)
    assert state["schema_version"] == 1
    assert state["checked_at"] == "2026-10-11 16:20"  # local naive display
    assert isinstance(state["checked_at_iso"], str)
    assert "T" in state["checked_at_iso"]  # ISO-8601 instant form
    assert [item["name"] for item in state["items"]] == [
        "version_pins",
        "cuda",
    ]
    assert state["items"][1] == {
        "name": "cuda",
        "ok": False,
        "lines": ["FAIL: fake cuda detail"],
    }


def test_persist_twice_leaves_single_valid_file_no_tmp_residue(tmp_path):
    """Idempotent persistence: one valid file, zero .tmp siblings."""
    path = tmp_path / "env_check.json"
    now = _local(2026, 10, 11, 16, 20)
    persist(path, [_pass("numpy")], now=now)
    persist(path, [_pass("numpy"), _pass("peft")], now=now)
    assert list(tmp_path.iterdir()) == [path]
    state = load_cached(path)
    assert [item["name"] for item in state["items"]] == ["numpy", "peft"]


def test_partial_failure_persists_whole(tmp_path):
    """A partial-failure run persists EVERY item incl. FAIL detail lines."""
    path = tmp_path / "env_check.json"
    results = [
        _pass("version_pins"),
        _pass("dnallm"),
        _pass("peft"),
        _fail("cuda"),
        _pass("matmul"),
        _pass("numpy"),
        _fail("dataset_dirs"),
    ]
    persist(path, results, now=_local(2026, 10, 11, 8, 0))
    state = load_cached(path)
    assert len(state["items"]) == 7
    assert state["items"][3] == {
        "name": "cuda",
        "ok": False,
        "lines": ["FAIL: fake cuda detail"],
    }
    assert state["items"][6] == {
        "name": "dataset_dirs",
        "ok": False,
        "lines": ["FAIL: fake dataset_dirs detail"],
    }


# ===== Orchestration (ENV-01, D-02, D-03) =====


def test_run_full_check_injected_kernels_return_in_order_and_persist_once(
        tmp_path, monkeypatch):
    """Injected fake kernels: results in given order, persisted exactly once."""
    path = tmp_path / "env_check.json"
    calls = []
    persist_calls = []
    real_persist = env_check.persist

    def counting_persist(path_, results_, now=None):
        persist_calls.append(path_)
        return real_persist(path_, results_, now=now)

    monkeypatch.setattr(env_check, "persist", counting_persist)

    def kernel_a():
        calls.append("a")
        return _pass("version_pins")

    def kernel_b():
        calls.append("b")
        return _fail("cuda")

    results = run_full_check(
        kernels=[kernel_a, kernel_b],
        state_path=path,
        now=_local(2026, 10, 11, 10, 0),
    )
    assert [result.name for result in results] == ["version_pins", "cuda"]
    assert calls == ["a", "b"]  # every kernel executed exactly once
    assert persist_calls == [path]  # persisted exactly once
    state = load_cached(path)
    assert [item["name"] for item in state["items"]] == [
        "version_pins",
        "cuda",
    ]


def _patch_env_smoke_kernels(monkeypatch, order, cuda_fn=None, matmul_fn=None):
    """Replace every env_smoke kernel with a recording fake (D-03: no real
    kernel ever executes; the service's import seam is what's under test).

    ``order`` is the shared recording list every fake appends its kernel
    id to; custom cuda/matmul fakes must do their own appends (they own
    the recording).
    """

    def fake_version_pins(pins):
        order.append("version_pins")
        return _pass("version_pins")

    def fake_dnallm():
        order.append("dnallm")
        return _pass("dnallm")

    def fake_peft():
        order.append("peft")
        return _pass("peft")

    def default_cuda(torch_module):
        order.append("cuda")
        return _pass("cuda")

    def default_matmul(torch_module):
        order.append("matmul")
        return _pass("matmul")

    def fake_numpy(floor_major):
        order.append("numpy")
        return _pass("numpy")

    def fake_dataset_dirs():
        order.append("dataset_dirs")
        return _pass("dataset_dirs")

    monkeypatch.setattr(env_smoke, "check_version_pins", fake_version_pins)
    monkeypatch.setattr(env_smoke, "check_dnallm", fake_dnallm)
    monkeypatch.setattr(env_smoke, "check_peft", fake_peft)
    monkeypatch.setattr(env_smoke, "check_cuda", cuda_fn or default_cuda)
    monkeypatch.setattr(env_smoke, "check_matmul", matmul_fn or default_matmul)
    monkeypatch.setattr(env_smoke, "check_numpy", fake_numpy)
    monkeypatch.setattr(env_smoke, "check_dataset_dirs", fake_dataset_dirs)
    return order


def test_run_full_check_default_sequence_mirrors_main_order(
        tmp_path, monkeypatch):
    """No injection -> the REAL env_smoke kernels, imported, in main() order.

    The kernel bodies are monkeypatched to recording fakes (D-03 — no GPU
    kernel executes in CI), but the SEQUENCE the service builds is the
    real one: version_pins, dnallm, peft, cuda, matmul, numpy,
    dataset_dirs, with the torch module passed through to cuda/matmul.
    """
    path = tmp_path / "env_check.json"
    fake_torch = types.ModuleType("torch")
    order = []
    received = []

    def recording_cuda(torch_module):
        order.append("cuda")
        received.append(("cuda", torch_module))
        return _pass("cuda")

    def recording_matmul(torch_module):
        order.append("matmul")
        received.append(("matmul", torch_module))
        return _pass("matmul")

    _patch_env_smoke_kernels(
        monkeypatch, order=order, cuda_fn=recording_cuda,
        matmul_fn=recording_matmul,
    )
    # torch PRESENT: a fake module in sys.modules (the 08-01 injection seam)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    results = run_full_check(
        state_path=path, now=_local(2026, 10, 11, 10, 0)
    )
    assert order == list(MAIN_KERNEL_ORDER)
    assert received == [("cuda", fake_torch), ("matmul", fake_torch)]
    assert [result.name for result in results] == list(MAIN_KERNEL_ORDER)
    # the run persisted under the injected state path
    state = load_cached(path)
    assert [item["name"] for item in state["items"]] == list(
        MAIN_KERNEL_ORDER
    )


def test_default_sequence_torch_gate_appends_two_false_results(
        tmp_path, monkeypatch):
    """Torch import fails -> cuda+matmul become the two ok=False empties.

    The fallback mirrors main()'s torch-unavailable branch exactly: two
    failed CheckResult placeholders with zero lines of their own.
    """
    path = tmp_path / "env_check.json"
    order = []
    _patch_env_smoke_kernels(monkeypatch, order=order)
    # torch MISSING: the None halt sentinel in sys.modules (08-01 seam) —
    # deterministic regardless of whether the host really has torch.
    monkeypatch.setitem(sys.modules, "torch", None)

    results = run_full_check(
        state_path=path, now=_local(2026, 10, 11, 10, 0)
    )
    assert order == ["version_pins", "dnallm", "peft", "numpy", "dataset_dirs"]
    assert [result.name for result in results] == list(MAIN_KERNEL_ORDER)
    assert results[3] == CheckResult(name="cuda", ok=False, lines=())
    assert results[4] == CheckResult(name="matmul", ok=False, lines=())


# ===== Default state location (D-04) =====


def test_default_state_path_lives_under_the_state_root(tmp_path, monkeypatch):
    """The state file lives under the STATE root — never the config root."""
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", str(tmp_path))
    assert default_state_path() == tmp_path / "env_check.json"


# ===== D-02 prohibitions =====


def test_service_never_subprocesses_or_parses_env_smoke_stdout():
    """D-02: no subprocess, no stdout parsing anywhere in the service."""
    source = Path(env_check.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "check_output" not in source
