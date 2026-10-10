# =====================================================================
# Makefile — single-command entry points over the uv-managed environment
#
# Replaces the undocumented CWD-sensitive 3-step regeneration procedure
# (REL-04): everything below runs from the repo root with no activation
# step. `uv run` auto-syncs .venv from uv.lock before invoking.
#
#   make data       regenerate the derived data chain (47 task_performance
#                   + 4 models_comparison + tasks.json)
#   make test       full local suite: pytest (slow lane included) plus the
#                   node:test JS suite over tests/js/ (Python + JS lanes)
#   make test-fast  pytest excluding @slow (the real-tree determinism run);
#                   the JS suite is fast and runs in the full test lane
#   make lint       ruff over tests/ + the Phase-authored/edited files
#                   (make_dev_splits.py, summarize_comparison.py,
#                   export_runs.py, run_finetune.py, run_sweep.py,
#                   compare.py)
#   make typecheck  ty type check over script/, baseline/, tests/, scripts/,
#                   and pipeline/ (GPU-side imports replaced with Any — they
#                   are never installed CPU-side, D-05)
# =====================================================================

.PHONY: data test test-fast lint typecheck check-node

# WR-02: PATH lookup with an overridable default (`make UV=/path/to/uv`) —
# setup-uv/brew/pipx installs live outside ~/.local/bin, and a hardcode
# there breaks every target (incl. CI) with Error 127.
UV ?= uv
DATA_DIR := dnallm-mark/data

# Data chain — one `cd ... && ...` per line: each recipe line is its own
# shell (Pitfall 8), and the Python scripts resolve inputs/outputs against
# CWD. The JS generator is __dirname-relative and runs from repo root as-is.
data: check-node
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/get_task_performance.py
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/summarize_comparison.py
	node scripts/generate-tasks-index.js

# --group dev is REQUIRED: default-groups = ["data"] in pyproject.toml
# replaces uv's ["dev"] default (Pitfall 2). The JS lane runs plain node
# (built-in node:test runner, zero npm deps — no Python env involved).
# check-node (IN-04, WR-07): node is a hard dependency of BOTH the `test`
# target (JS suite + tasks.json goldens) and the `data` target (the index
# generator recipe line) — without the guard a node-less machine dies on a
# raw FileNotFoundError / `sh: node: not found` Error 127 instead of an
# actionable message. WR-06: the fast-lane escape hatch noted below is
# real only because test_golden.py skips its node-dependent tests via
# skipif — the fast lane is pytest-only AND skips the goldens, so the
# message must say "skips", not imply node was never needed.
check-node:
	@command -v node >/dev/null 2>&1 || { echo "node >=18 required for the JS test lane, the tasks.json goldens, and 'make data' — install Node; the pytest-only fast lane (make test-fast) skips node-dependent tests when node is absent"; exit 1; }

test: check-node
	$(UV) run --group dev pytest
	node --test tests/js/

test-fast:
	$(UV) run --group dev pytest -m "not slow"

# Lint scope (Phase 3 decision, D-08): tests/ plus the explicit list of
# Phase-authored/edited files whose findings are FIXED — script/make_dev_splits.py
# (03-02), pipeline/run_finetune.py (D-08: all 16 arriving findings resolved,
# 13 genuinely + 3 justified per-line noqa at the designed blind-except
# isolation sites), pipeline/run_sweep.py (03-04), script/summarize_comparison.py
# (04-01: FIX-02 Category grouping + WR-03 isfinite), baseline/compare.py
# (04-01: IN-01 INT label + WR-02 BOOL_CROSS), script/export_runs.py (04-02:
# vendored suite statistics + the exporter core). The pre-existing findings in
# the REMAINING script/, scripts/, baseline/ production files stay deferred
# to their Phase 4/5 routing, so those paths stay OUT of scope deliberately.
# No [tool.ruff] config section exists (D-08: no baseline carry-over, no
# suppression).
lint:
	$(UV) run --group dev ruff check tests/ script/make_dev_splits.py script/summarize_comparison.py script/export_runs.py baseline/compare.py pipeline/run_finetune.py pipeline/run_sweep.py

# Type check (ty, maintainer directive 2026-10-09): zero-diagnostics baseline
# verified empirically at research time. [tool.ty] in pyproject.toml carries
# the config — extra-paths mirrors tests/conftest.py's sys.path contract, and
# GPU-side imports (torch/dnallm/transformers/peft/datasets) are replaced
# with Any because they are never installed CPU-side (D-05). --group dev is
# required for the same default-groups reason as lint/test.
typecheck:
	$(UV) run --group dev ty check
