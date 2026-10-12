"""
Tier-1 service tests for ``tui/services/gauntlet.py`` (Phase 9, 09-02 —
CUST-04 / D-06 dry-run precheck leg).

Two lanes, per the plan:

- **Fake-runner suite** — an injected runner records
  ``(argv, env, timeout)`` and returns configured results; these tests
  pin the argv shape (LIST, ``sys.executable``, ABSOLUTE script path —
  registry values never reach a shell, T-09-05), the env construction
  (``os.environ`` plus EXACTLY one override), the staging content
  (existing customs + candidate forced ``enabled: true``), and every
  verdict path (pass / nonzero exit / exit-0-but-absent manifest
  (Pitfall 5) / unreadable manifest / timeout / runner crash).
- **Real-subprocess lane** — ``run_sweep.py --dry-run`` as a REAL
  subprocess over the committed official registries (stdlib, CPU,
  sub-second — live-proven in the Phase 9 research): a synthetic model
  candidate passes end-to-end, proving the leg with zero GPU/dnallm.

Every test injects tmp env roots — the real ``~/.config/dnallmmark``
(this machine HAS one) is never read or written (D-08 boundary).

See also:
    ``tui/services/gauntlet.py`` — the service under test.
    ``tui/services/custom_entries.py`` — the existing-custom read seam.
    ``pipeline/run_sweep.py`` — the dry-run subprocess target.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tui.services import gauntlet, settings
from tui.services.custom_entries import KIND_DATASETS, KIND_MODELS

CONFIG_ENV = settings.CONFIG_DIR_ENV
OVERLAY_ENV = gauntlet.CUSTOM_DIR_ENV
REPO_ROOT = Path(__file__).resolve().parents[2]
CJK_RE = re.compile("[一-鿿]")


def pin_config_dir(monkeypatch, tmp_path):
    """Point the TUI config root (the existing-custom read) at a tmp
    dir — the operator's real custom registry is never staged."""
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    return tmp_path


def first_official_task_with_train():
    """The deterministic dry-run counterpart rule for MODEL candidates:
    the first official datasets_info.json key in FILE ORDER with truthy
    ``Train`` (computed from the committed registry, never hardcoded)."""
    registry = json.loads(
        (REPO_ROOT / "pipeline" / "datasets_info.json").read_text(
            encoding="utf-8"))
    for key, entry in registry.items():
        if isinstance(entry, dict) and entry.get("Train"):
            return key
    raise AssertionError("committed registry has no Train-truthy task")


def first_official_model():
    """The deterministic dry-run counterpart rule for DATASET
    candidates: the first official models_info.json key in file order."""
    registry = json.loads(
        (REPO_ROOT / "pipeline" / "models_info.json").read_text(
            encoding="utf-8"))
    return next(iter(registry))


class FakeRunner:
    """Injectable subprocess seam recording every call.

    ``on_call(argv, kwargs)`` runs while the service's staging tempdir
    is still ALIVE (it executes inside the runner call), so tests can
    both capture the staged registry content and write the fake
    manifest into the ``--output-root`` the service passed.
    """

    def __init__(self, result=None, on_call=None, exc=None):
        self.calls = []
        self.result = result
        self.on_call = on_call
        self.exc = exc

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "kwargs": dict(kwargs)})
        if self.exc is not None:
            raise self.exc
        if self.on_call is not None:
            self.on_call(list(argv), kwargs)
        return self.result


def write_manifest(argv, cells):
    """Write a sweep_manifest.json into the call's --output-root."""
    out = Path(argv[argv.index("--output-root") + 1])
    out.mkdir(parents=True, exist_ok=True)
    (out / gauntlet.MANIFEST_NAME).write_text(
        json.dumps({"matrix": {}, "cells": cells}), encoding="utf-8")


def ok_result(stdout="[Dry-run] 1 planned cell(s) over 1 model(s) x "
                     "1 task(s) x 1 seed(s)"):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def planned_cell(kind, candidate_key, counterpart, status="planned"):
    """One manifest cell naming the candidate on its axis."""
    model = candidate_key if kind == KIND_MODELS else counterpart
    task = counterpart if kind == KIND_MODELS else candidate_key
    return {
        "model": model,
        "task": task,
        "seed": 42,
        "status": status,
        "output_dir": "out/{}/{}/seed_42".format(model, task),
    }


def model_candidate():
    return {
        "Model_name": "my-custom-lm",
        "Model_path": "models/my-custom-lm",
        "architecture": "Bert",
        "type": "MLM",
    }


def capture_staging(captured, filename):
    """on_call hook: snapshot the staged overlay registry + env while
    the tempdir is alive, then write a passing manifest."""
    def hook(argv, kwargs):
        staging = Path(kwargs["env"][OVERLAY_ENV])
        captured["staging"] = staging
        captured["staged"] = json.loads(
            (staging / filename).read_text(encoding="utf-8"))
        captured["env"] = kwargs["env"]
        write_manifest(argv, [planned_cell(
            KIND_MODELS, "my-custom-lm",
            first_official_task_with_train())])
    return hook


# ===== argv discipline (T-09-05: LIST, executable, absolute, no shell) =====


def test_model_dry_run_argv_is_list_with_executable_and_absolute_script(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(result=ok_result(),
                        on_call=lambda argv, kwargs: write_manifest(
                            argv, [planned_cell(
                                KIND_MODELS, "my-custom-lm",
                                first_official_task_with_train())]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert item.ok
    argv = runner.calls[0]["argv"]
    assert isinstance(argv, list)          # never a shell string
    assert argv[0] == sys.executable       # the same interpreter
    script = Path(argv[1])
    assert script.is_absolute()            # never CWD-relative
    assert script == REPO_ROOT / "pipeline" / "run_sweep.py"
    assert "--dry-run" in argv


def test_model_dry_run_flags_candidate_and_official_counterpart(
        monkeypatch, tmp_path):
    """--models <candidate> --tasks <first official Train-truthy task>
    --seeds 42 --output-root <temp> — the counterpart derived at read
    time, never a hardcoded key constant."""
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_task_with_train()
    runner = FakeRunner(result=ok_result(),
                        on_call=lambda argv, kwargs: write_manifest(
                            argv, [planned_cell(
                                KIND_MODELS, "my-custom-lm", counterpart)]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    argv = runner.calls[0]["argv"]
    assert argv[argv.index("--models") + 1] == "my-custom-lm"
    assert argv[argv.index("--tasks") + 1] == counterpart
    assert argv[argv.index("--seeds") + 1] == "42"
    out_root = Path(argv[argv.index("--output-root") + 1])
    assert out_root.is_absolute()
    assert str(REPO_ROOT) not in str(out_root)   # never inside the repo


def test_dataset_dry_run_uses_first_official_model_counterpart(
        monkeypatch, tmp_path):
    """Dataset candidates gauntlet on the OTHER axis: --models <first
    official model key> --tasks <candidate>."""
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_model()
    runner = FakeRunner(result=ok_result(),
                        on_call=lambda argv, kwargs: write_manifest(
                            argv, [planned_cell(
                                KIND_DATASETS, "my-custom-ds", counterpart)]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_DATASETS, "my-custom-ds",
        {"Dataset_name": "my-custom-ds", "Train": 3, "Dev": 1, "Test": 2},
        run_id="r9")

    assert item.ok
    argv = runner.calls[0]["argv"]
    assert argv[argv.index("--models") + 1] == counterpart
    assert argv[argv.index("--tasks") + 1] == "my-custom-ds"


# ===== env isolation + staging content (Pitfall 2 / D-08) =====


def test_env_is_os_environ_plus_exactly_one_override(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    captured = {}
    runner = FakeRunner(
        result=ok_result(),
        on_call=capture_staging(captured, "custom_models.json"))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    env = captured["env"]
    expected = dict(os.environ)
    expected[OVERLAY_ENV] = env[OVERLAY_ENV]
    assert env == expected          # exactly one override, rest passthrough
    staging = captured["staging"]
    assert staging.name == "overlay"
    assert staging.parent.name.startswith("dnallmmark-gauntlet-")


def test_staging_contains_existing_customs_and_candidate_enabled_true(
        monkeypatch, tmp_path):
    """The overlay stages the operator's EXISTING customs + the
    candidate forced to enabled true (the env var replaces the whole
    dir — a candidate-only file would drop existing customs from the
    merged view)."""
    config = pin_config_dir(monkeypatch, tmp_path)
    existing = {
        "existing-custom": {"Model_name": "existing-custom",
                            "enabled": False},
    }
    (config / "custom_models.json").write_text(
        json.dumps(existing), encoding="utf-8")
    captured = {}
    runner = FakeRunner(
        result=ok_result(),
        on_call=capture_staging(captured, "custom_models.json"))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    staged = captured["staged"]
    assert set(staged) == {"existing-custom", "my-custom-lm"}
    assert staged["existing-custom"] == existing["existing-custom"]
    assert staged["my-custom-lm"]["enabled"] is True   # forced, D-09


def test_unreadable_existing_custom_registry_yields_failed_item(
        monkeypatch, tmp_path):
    """A corrupt user-owned registry cannot be silently dropped from
    the staging view (the pipeline would fail loud on it) — the
    gauntlet surfaces the read failure as a failed item, and the
    subprocess is never launched."""
    config = pin_config_dir(monkeypatch, tmp_path)
    (config / "custom_models.json").write_text(
        "{corrupt", encoding="utf-8")
    runner = FakeRunner()
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert item.run_id == "r1"
    assert runner.calls == []          # no subprocess on a staging failure


# ===== verdicts from parsed artifacts, never exit codes alone (Pitfall 5) =====


def test_pass_yields_ok_item_with_planned_cell_count_and_stdout(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_task_with_train()
    runner = FakeRunner(
        result=ok_result(stdout="[Dry-run] 2 planned cell(s)"),
        on_call=lambda argv, kwargs: write_manifest(argv, [
            planned_cell(KIND_MODELS, "my-custom-lm", counterpart),
            planned_cell(KIND_MODELS, "my-custom-lm", counterpart),
        ]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="run-42")

    assert item.ok
    assert "planned_cells=2" in item.details
    assert "[Dry-run] 2 planned cell(s)" in item.raw_output
    assert item.run_id == "run-42"
    assert item.leg == gauntlet.LEG_DRY_RUN
    assert item.kind == KIND_MODELS
    assert item.name == "my-custom-lm"


def test_nonzero_exit_yields_failed_item_with_verbatim_output(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(result=SimpleNamespace(
        returncode=1,
        stdout="[Error] --models names not in registry: ['my-custom-lm']",
        stderr="traceback tail"))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert "[Error] --models names not in registry" in item.raw_output
    assert "traceback tail" in item.raw_output
    assert "exit_nonzero" in item.details


def test_exit_zero_with_candidate_absent_manifest_fails(
        monkeypatch, tmp_path):
    """Pitfall 5: exit 0 with a manifest that never names the candidate
    (zero-cell / candidate-absent) is a FAIL — the verdict reads the
    parsed cells, not the exit code."""
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_manifest(argv, []))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert "planned_cells=0" in item.details


def test_planned_cells_with_non_planned_status_fail(monkeypatch, tmp_path):
    """A cell naming the candidate with any status other than planned
    (e.g. failed/skipped) is not a pass."""
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_task_with_train()
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_manifest(argv, [
            planned_cell(KIND_MODELS, "my-custom-lm", counterpart,
                         status="failed")]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok


def test_unreadable_manifest_yields_failed_item_with_stdout(
        monkeypatch, tmp_path):
    """Exit 0 but no parseable manifest at the output root (a None
    artifact_loader sentinel) is a failed item with the verbatim stdout
    — never a crash, never an exit-0 pass."""
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(result=ok_result())   # writes no manifest at all
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert "manifest_unreadable" in item.details
    assert "[Dry-run]" in item.raw_output


# ===== timeouts, crashes, and the service boundary (T-09-07) =====


def test_default_and_overridden_timeouts_reach_the_runner(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_task_with_train()
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_manifest(argv, [
            planned_cell(KIND_MODELS, "my-custom-lm", counterpart)]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)
    service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")
    assert runner.calls[0]["kwargs"]["timeout"] == 60   # default

    faster = gauntlet.GauntletService(
        runner=runner, timeout_dry_run=5, repo_root=REPO_ROOT)
    faster.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r2")
    assert runner.calls[1]["kwargs"]["timeout"] == 5    # overridable


def test_runner_timeout_yields_failed_item_naming_timeout(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(
        exc=subprocess.TimeoutExpired(cmd=["run_sweep.py"], timeout=60))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert any("timeout" in detail for detail in item.details)
    assert item.run_id == "r1"


def test_runner_crash_yields_failed_item_never_an_exception(
        monkeypatch, tmp_path):
    """A crashed runner (OSError — script missing, spawn failure)
    crosses NO exception boundary: the item carries the error text."""
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(exc=OSError("[Errno 2] No such file or directory"))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert "No such file" in item.raw_output + " ".join(item.details)


def test_every_item_carries_run_id_and_service_is_stateless(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_task_with_train()
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_manifest(argv, [
            planned_cell(KIND_MODELS, "my-custom-lm", counterpart)]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    first = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="run-a")
    second = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="run-b")

    assert first.run_id == "run-a"
    assert second.run_id == "run-b"     # never mixed, never the previous
    assert len(runner.calls) == 2


# ===== module hygiene (services-tier invariants) =====


def test_service_module_carries_zero_inline_chinese_copy():
    """All gauntlet copy lives in tui/strings.py (GAUNTLET_*) — the
    service carries structured data only."""
    source = Path(gauntlet.__file__).read_text(encoding="utf-8")
    assert not CJK_RE.search(source), "inline Chinese copy in the service"


def test_service_module_has_no_shell_invocation_patterns():
    """T-09-05 pin: no shell=True, no os.system, no argv string-joins."""
    source = Path(gauntlet.__file__).read_text(encoding="utf-8")
    for pattern in ("shell=True", "os.system", '" ".join'):
        assert pattern not in source, "forbidden subprocess pattern"


# ===== the real-subprocess lane (D-06 live proof; CPU/stdlib/sub-second) =====


@pytest.mark.skipif(
    not (REPO_ROOT / "pipeline" / "models_info.json").is_file()
    or not (REPO_ROOT / "pipeline" / "datasets_info.json").is_file(),
    reason="committed official registries absent (not a repo checkout)")
def test_real_subprocess_dry_run_passes_for_synthetic_model_candidate(
        monkeypatch, tmp_path):
    """The REAL leg: run_sweep.py --dry-run as an actual subprocess over
    the committed official 62/50 registries with the candidate staged
    through the temp overlay — exit 0 AND the parsed manifest's cells
    carry the candidate with status planned (Pitfall 5). The subprocess
    is fully isolated from the operator's real custom dir (the env
    override replaces it); nothing lands anywhere (D-08)."""
    pin_config_dir(monkeypatch, tmp_path)
    service = gauntlet.GauntletService(repo_root=REPO_ROOT)

    item = service.dry_run_precheck(
        KIND_MODELS, "gauntlet-probe-lm",
        {"Model_name": "gauntlet-probe-lm",
         "Model_path": "models/gauntlet-probe-lm",
         "architecture": "Bert", "type": "MLM"},
        run_id="live-1")

    assert item.ok
    assert item.run_id == "live-1"
    assert "planned_cells=1" in item.details
    assert "[Dry-run]" in item.raw_output
