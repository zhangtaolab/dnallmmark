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
        "output_dir": "out/" + model + "/" + task + "/seed_42",
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


def test_missing_official_registry_yields_failed_item_not_exception(
        monkeypatch, tmp_path):
    """WR-02 (09 review): a missing/corrupt OFFICIAL registry degrades to
    a failed dry-run item naming the read failure — never an OSError
    crossing the service boundary (the module contract: a timeout or a
    crash yields a failed GauntletItem; an escaping exception would kill
    the wizard's gauntlet worker before any item posts and the panel
    rows would stay in-flight forever)."""
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(result=ok_result())
    # repo_root without pipeline/ registries: _official_registry's bare
    # open() raises FileNotFoundError (an OSError) pre-fix
    service = gauntlet.GauntletService(runner=runner, repo_root=tmp_path)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert item.details[0] == "official_registry_unreadable"
    assert runner.calls == [], "nothing launched when the registry is unreadable"


def test_gbk_official_registry_yields_failed_item_not_exception(
        monkeypatch, tmp_path):
    """WR-06 (09 review): a NON-UTF-8 official registry (GBK bytes)
    degrades to the same failed dry-run item as a missing/corrupt one —
    ``UnicodeDecodeError`` (the ``ValueError`` sibling CR-01 judged
    plausible enough at the loader seam to fix and regression-test) must
    never cross the service boundary: escaping would kill the wizard's
    gauntlet worker and strand the panel rows in-flight forever."""
    pin_config_dir(monkeypatch, tmp_path)
    runner = FakeRunner(result=ok_result())
    pipeline_dir = tmp_path / "pipeline"
    pipeline_dir.mkdir()
    # KIND_MODELS' counterpart reads the OFFICIAL datasets registry; GBK
    # bytes fail the utf-8 decode inside open()/json.load
    (pipeline_dir / gauntlet.registry_loader.DATASETS_INFO_NAME).write_bytes(
        '{"k": "自定义"}'.encode("gbk"))
    service = gauntlet.GauntletService(runner=runner, repo_root=tmp_path)

    item = service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    assert not item.ok
    assert item.details[0] == "official_registry_unreadable"
    assert runner.calls == [], "nothing launched when the registry is unreadable"


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


def test_runner_decode_policy_pins_errors_replace(
        monkeypatch, tmp_path):
    """The download_queue WR-05 twin (review follow-up): every _invoke
    runner call carries ``errors="replace"`` alongside ``text=True`` —
    the gauntlet launches the same CJK/emoji-emitting scripts, and a
    non-UTF-8 LC_CTYPE host must decode their output to replacement
    characters, never raise UnicodeDecodeError into the absorbed
    ``subprocess_error`` (a healthy kernel turning into a failed item)."""
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_task_with_train()
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_manifest(argv, [
            planned_cell(KIND_MODELS, "my-custom-lm", counterpart)]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    service.dry_run_precheck(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="r1")

    kwargs = runner.calls[0]["kwargs"]
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["errors"] == "replace", (
        "the gauntlet _invoke must match the download_queue _invoke "
        "twin's decode policy exactly"
    )


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


# =====================================================================
# Task 3: the audit reconciliation leg (D-07) + Pitfall-1 regression
# =====================================================================

COMMITTED_AUDIT_ARTIFACTS = (
    REPO_ROOT / "dnallm-mark" / "data" / "n_audit.json",
    REPO_ROOT / "dnallm-mark" / "data" / "n_audit.csv",
    REPO_ROOT / "pipeline" / "eval_subsets.json",
    REPO_ROOT / "DATA.md",
)


def sha256_of(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dataset_candidate(tmp_path, rows=(3, 2, 2), non_acgt_label=False):
    """A synthetic dataset candidate over REAL tmp split CSVs.

    Returns ``(entry_with_relative_dataset_path, declared_splits)`` —
    the LANDED form: ``Dataset_path`` relative to ``pipeline/`` (how
    custom_entries.land stores it), which the audit leg must
    re-absolutize (Pitfall 3).
    """
    import os as _os
    dataset_dir = tmp_path / "datasets" / "MyCustom" / "demo_task"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for split, count in zip(("train", "dev", "test"), rows):
        lines = ["sequence,label"]
        lines.extend("ACGT,0" for _ in range(count))
        (dataset_dir / (split + ".csv")).write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
    pipeline_dir = REPO_ROOT / "pipeline"
    relative = _os.path.relpath(dataset_dir, pipeline_dir)
    entry = {
        "Dataset_name": "MyCustom__demo_task",
        "Dataset_path": relative,
        "Train": rows[0], "Dev": rows[1], "Test": rows[2],
        "Category": "Plants", "type": "binary", "metric": "mcc",
    }
    declared = {"Train": rows[0], "Dev": rows[1], "Test": rows[2]}
    return entry, declared


def n_audit_task(rows=(3, 2, 2), unified=2, missing=False, non_acgt=0):
    """One n_audit.json task record in the audit writer's own shape."""
    if missing:
        return {"missing": True, "unified_eval_n": None, "splits": None}
    splits = {}
    for split, count in zip(("train", "dev", "test"), rows):
        splits[split] = {
            "rows": count,
            "total_chars": count * 4,
            "non_acgt_chars": non_acgt,
            "rows_with_non_acgt": 1 if non_acgt else 0,
            "strict_survivors": count,
            "n_tolerant_survivors": count,
        }
    return {"missing": False, "unified_eval_n": unified, "splits": splits}


def write_n_audit(argv, tasks):
    """Write an n_audit.json into the call's --data-dir."""
    data_dir = Path(argv[argv.index("--data-dir") + 1])
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "n_audit.json").write_text(
        json.dumps({"tasks": tasks}), encoding="utf-8")


def capture_audit_staging(captured, tasks):
    """on_call hook for the audit leg: snapshot the candidate-only
    registry + env while the tempdir lives, write the fake n_audit."""
    def hook(argv, kwargs):
        registry_dir = Path(argv[argv.index("--registry-dir") + 1])
        captured["registry_dir"] = registry_dir
        captured["staged_entry"] = json.loads(
            (registry_dir / "datasets_info.json").read_text(
                encoding="utf-8"))
        overlay = Path(kwargs["env"][OVERLAY_ENV])
        captured["overlay"] = overlay
        captured["overlay_files"] = list(overlay.iterdir())
        write_n_audit(argv, {"MyCustom__demo_task": tasks})
    return hook


def test_audit_argv_flags_all_temp_never_committed_defaults(
        monkeypatch, tmp_path):
    """Pitfall 1: --registry-dir/--datasets-root/--data-dir/--subsets-
    out/--data-md ALL carry temp values — the argparse defaults that
    point at committed repo artifacts never fire."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, declared = dataset_candidate(tmp_path)
    captured = {}
    runner = FakeRunner(
        result=ok_result(),
        on_call=capture_audit_staging(captured, n_audit_task()))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry, declared, run_id="r1")

    assert item.ok
    argv = runner.calls[0]["argv"]
    assert argv[0] == sys.executable
    script = Path(argv[1])
    assert script.is_absolute()
    assert script == REPO_ROOT / "script" / "audit_n_frequencies.py"
    for flag in ("--registry-dir", "--datasets-root", "--data-dir",
                 "--subsets-out", "--data-md"):
        value = argv[argv.index(flag) + 1]
        assert Path(value).is_absolute()
        assert not str(value).startswith(str(REPO_ROOT)), (
            flag + " points inside the repo — a committed artifact "
            "would be clobbered (Pitfall 1)")


def test_audit_staging_is_candidate_only_with_absolute_path_and_empty_overlay(
        monkeypatch, tmp_path):
    """The audit leg's double isolation: the temp registry contains ONLY
    the candidate (its ``Dataset_path`` absolutized against pipeline/ —
    Pitfall 3), and the env override pins an EMPTY temp dir so the
    operator's real custom registry is never merged (Pitfall 2)."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, declared = dataset_candidate(tmp_path)
    dataset_dir = (tmp_path / "datasets" / "MyCustom" / "demo_task").resolve()
    captured = {}
    runner = FakeRunner(
        result=ok_result(),
        on_call=capture_audit_staging(captured, n_audit_task()))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    service.audit_reconciliation(
        "MyCustom__demo_task", entry, declared, run_id="r1")

    staged = captured["staged_entry"]
    assert set(staged) == {"MyCustom__demo_task"}   # candidate ONLY
    staged_path = Path(staged["MyCustom__demo_task"]["Dataset_path"])
    assert staged_path.is_absolute()
    assert staged_path == dataset_dir
    assert captured["overlay_files"] == []          # EMPTY overlay dir


def test_audit_pass_yields_ok_item_with_reconciliation_detail(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    entry, declared = dataset_candidate(tmp_path)
    runner = FakeRunner(
        result=ok_result(stdout="Audited 1 registry task(s): 1 present, "
                                "0 missing"),
        on_call=lambda argv, kwargs: write_n_audit(
            argv, {"MyCustom__demo_task": n_audit_task()}))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry, declared, run_id="audit-7")

    assert item.ok
    assert item.leg == gauntlet.LEG_AUDIT
    assert item.run_id == "audit-7"
    assert "train_rows=3" in item.details
    assert "test_rows=2" in item.details
    assert "unified_eval_n=2" in item.details
    assert "test_non_acgt_chars=0" in item.details
    assert "Audited 1 registry task(s)" in item.raw_output


def test_audit_declared_measured_mismatch_fails_naming_both_numbers(
        monkeypatch, tmp_path):
    """The reconciliation core: declared Train 10 vs measured 3 is a
    FAIL whose detail names the split AND both counts (declared vs
    measured)."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, _declared = dataset_candidate(tmp_path)
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_n_audit(
            argv, {"MyCustom__demo_task": n_audit_task()}))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry,
        {"Train": 10, "Dev": 2, "Test": 2}, run_id="r1")

    assert not item.ok
    assert "Train_mismatch_declared=10_measured=3" in item.details


def test_audit_missing_dataset_and_zero_rows_fail(monkeypatch, tmp_path):
    """missing=true (the dir never resolved) is a FAIL even though the
    audit script exits 0 by design — the verdict reads n_audit.json."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, _declared = dataset_candidate(tmp_path)
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_n_audit(
            argv, {"MyCustom__demo_task": n_audit_task(missing=True)}))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry, {"Train": 3}, run_id="r1")

    assert not item.ok
    assert "missing=true" in item.details


def test_audit_zero_unified_eval_n_fails(monkeypatch, tmp_path):
    """unified_eval_n == 0 (subset death — the audit emits no
    eval-subset entry by design) is a FAIL: subset survival is a pass
    criterion."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, _declared = dataset_candidate(tmp_path)
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_n_audit(
            argv, {"MyCustom__demo_task": n_audit_task(unified=0)}))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry, {"Train": 3}, run_id="r1")

    assert not item.ok
    assert "unified_eval_n=0" in item.details


def test_audit_non_acgt_rows_still_pass_with_census_detail(
        monkeypatch, tmp_path):
    """The non-ACGT census is REPORTED DATA, never a failure condition
    (official datasets carry non-ACGT rows by design)."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, declared = dataset_candidate(tmp_path)
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_n_audit(
            argv, {"MyCustom__demo_task": n_audit_task(non_acgt=7)}))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry, declared, run_id="r1")

    assert item.ok
    assert "train_non_acgt_chars=7" in item.details


def test_audit_timeout_uses_its_own_timeout_and_fails_itemly(
        monkeypatch, tmp_path):
    pin_config_dir(monkeypatch, tmp_path)
    entry, declared = dataset_candidate(tmp_path)
    runner = FakeRunner(exc=subprocess.TimeoutExpired(
        cmd=["audit_n_frequencies.py"], timeout=300))
    service = gauntlet.GauntletService(
        runner=runner, timeout_audit=7, repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry, declared, run_id="r1")

    assert runner.calls[0]["kwargs"]["timeout"] == 7   # NOT the dry-run 60
    assert not item.ok
    assert any("timeout" in detail for detail in item.details)


def test_model_kind_reconcile_never_invokes_audit(monkeypatch, tmp_path):
    """Kind gating: a model gauntlet runs the dry-run leg ONLY — n_audit
    is dataset-only by design."""
    pin_config_dir(monkeypatch, tmp_path)
    counterpart = first_official_task_with_train()
    runner = FakeRunner(
        result=ok_result(),
        on_call=lambda argv, kwargs: write_manifest(argv, [
            planned_cell(KIND_MODELS, "my-custom-lm", counterpart)]))
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    items = service.reconcile(
        KIND_MODELS, "my-custom-lm", model_candidate(), run_id="run-m")

    assert len(items) == 1
    assert items[0].leg == gauntlet.LEG_DRY_RUN
    assert len(runner.calls) == 1
    assert runner.calls[0]["argv"][1].endswith("run_sweep.py")


def test_dataset_kind_reconcile_runs_both_legs_same_run_id(
        monkeypatch, tmp_path):
    """A dataset candidate gauntlets BOTH legs sequentially under one
    run_id: dry-run first, then audit."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, declared = dataset_candidate(tmp_path)
    counterpart = first_official_model()

    def hook(argv, kwargs):
        if argv[1].endswith("run_sweep.py"):
            write_manifest(argv, [planned_cell(
                KIND_DATASETS, "MyCustom__demo_task", counterpart)])
        else:
            write_n_audit(
                argv, {"MyCustom__demo_task": n_audit_task()})

    runner = FakeRunner(result=ok_result(), on_call=hook)
    service = gauntlet.GauntletService(runner=runner, repo_root=REPO_ROOT)

    items = service.reconcile(
        KIND_DATASETS, "MyCustom__demo_task", entry, run_id="run-d",
        declared_splits=declared)

    assert [item.leg for item in items] == [
        gauntlet.LEG_DRY_RUN, gauntlet.LEG_AUDIT]
    assert {item.run_id for item in items} == {"run-d"}
    assert all(item.ok for item in items)
    assert len(runner.calls) == 2


# ===== the Pitfall-1 regression gate (real subprocess) =====


@pytest.mark.skipif(
    not (REPO_ROOT / "script" / "audit_n_frequencies.py").is_file(),
    reason="audit script absent (not a repo checkout)")
def test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet(
        monkeypatch, tmp_path):
    """The Pitfall-1 gate: a REAL audit-gauntlet run over a tmp CSV
    dataset leaves the four committed artifacts (n_audit.json,
    n_audit.csv, eval_subsets.json, DATA.md) byte-identical — fails if
    any audit default output path ever fires. Also the live proof: the
    real subprocess reconciles declared-vs-measured over real CSVs
    (CPU/stdlib, sub-second)."""
    pin_config_dir(monkeypatch, tmp_path)
    entry, declared = dataset_candidate(tmp_path)
    before = {path: sha256_of(path) for path in COMMITTED_AUDIT_ARTIFACTS}
    service = gauntlet.GauntletService(repo_root=REPO_ROOT)

    item = service.audit_reconciliation(
        "MyCustom__demo_task", entry, declared, run_id="live-audit")

    assert item.ok, item
    assert "train_rows=3" in item.details
    assert "unified_eval_n=2" in item.details
    after = {path: sha256_of(path) for path in COMMITTED_AUDIT_ARTIFACTS}
    assert after == before, (
        "committed audit artifacts changed — an audit output flag "
        "fired its repo default (Pitfall 1)")
