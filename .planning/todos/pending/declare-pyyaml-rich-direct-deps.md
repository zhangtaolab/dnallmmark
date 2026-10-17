---
title: Declare direct imports pyyaml + rich in dependency groups (post-v1.2)
created: 2026-10-13T21:23:00+08:00
source: dependency-completeness audit during phase-12 execution (session 2026-10-13)
milestone_scope: v1.2 (post-milestone; blocked by phase-12 zero-pyproject/lock constraint)
---

# Declare pyyaml + rich as direct dependencies

Dependency audit (2026-10-13, phase-12 execution window) found two packages that are
**directly imported by repo code but not declared in any `[dependency-group]** — they resolve
only through transitive closure. This violates the project's own stated convention
(pyproject.toml platformdirs comment: *"declared directly to stop transitive-luck imports"*).

## Finding 1 — pyyaml (real risk)

- **Direct import:** `script/export_runs.py:118` (`import yaml`); exercised by
  `tests/test_export_runs.py` and the `make data` lane.
- **Current coverage (luck):** `data → evaluate v0.4.6 → datasets v5.1.0 → pyyaml v6.0.3`
  (also `huggingface-hub → pyyaml`). Every lane inherits it only because
  `default-groups = ["data"]` rides all `uv run` invocations.
- **Break scenario:** evaluate (or datasets) drops its pyyaml dependency → data scripts +
  the test lane fail at import with no pyproject change on our side.
- **Fix:** add `"pyyaml>=6"` to the `data` group; `uv lock`; verify
  `uv export --group data --no-emit-project` diff is pyyaml-only and regenerate
  `requirements.txt`.

## Finding 2 — rich (weak risk)

- **Direct imports:** `from rich.text import Text` in 11 tui modules
  (`tui/app.py`, `tui/screens/*.py`) + 9 Pilot test files (`tests/tui/test_pilot_*.py`).
- **Current coverage:** `tui → textual v8.2.8 → rich v15.0.0` — textual's hard runtime
  dependency, pinned in `uv.lock`; all rich-importing code runs under `--group tui`.
- **Break scenario:** textual vendoring/replacing rich (remote), or a tui-lane-without-textual
  ever existing (none does today).
- **Fix:** add `"rich>=13"` (floor matching textual's own requirement) to the `tui` group.

## Verified complete (no action)

- `uv lock --check` fresh (93 packages, zero drift); `requirements.txt` byte-identical to
  live `uv export --group data --no-emit-project` (header comment line differs only by the
  `-o requirements.txt` flag spelling).
- CI lanes match declarations: `make test` = dev+tui(+data default) + node:test zero-dep JS
  lane; static-js uses exact-version npx pins; gpu group + dnallm never enter CI (REL-02).
- dnallm: deliberately outside all groups (not on PyPI; manual editable install from
  ../DNALLM branch `revision`) — recorded decision, not a gap. GB10 venv is currently
  CPU-state (no torch/dnallm); next pipeline run needs `uv sync --group tui --group gpu`
  + dnallm reinstall.
- peft/datasets: no direct repo imports (datasets transitive via data group; peft only
  relevant at runtime through dnallm's trainer under `--peft`).

## Constraints

- **Do not land during phase 12** (standing zero-pyproject/uv.lock-change constraint).
- When landing: single commit (pyproject + uv.lock + requirements.txt regen), full
  `make test && make lint && make typecheck` gate, note in CHANGELOG if maintained then.
