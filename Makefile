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
#   make lint       ruff over tests/
# =====================================================================

.PHONY: data test test-fast lint check-node

# WR-02: PATH lookup with an overridable default (`make UV=/path/to/uv`) —
# setup-uv/brew/pipx installs live outside ~/.local/bin, and a hardcode
# there breaks every target (incl. CI) with Error 127.
UV ?= uv
DATA_DIR := dnallm-mark/data

# Data chain — one `cd ... && ...` per line: each recipe line is its own
# shell (Pitfall 8), and the Python scripts resolve inputs/outputs against
# CWD. The JS generator is __dirname-relative and runs from repo root as-is.
data:
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/get_task_performance.py
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/summarize_comparison.py
	node scripts/generate-tasks-index.js

# --group dev is REQUIRED: default-groups = ["data"] in pyproject.toml
# replaces uv's ["dev"] default (Pitfall 2). The JS lane runs plain node
# (built-in node:test runner, zero npm deps — no Python env involved).
# check-node (IN-04): node is a hard dependency of this target — without
# the guard a node-less machine dies on a raw FileNotFoundError instead of
# an actionable message. WR-06: the fast-lane escape hatch noted below is
# real only because test_golden.py skips its node-dependent tests via
# skipif — the fast lane is pytest-only AND skips the goldens, so the
# message must say "skips", not imply node was never needed.
check-node:
	@command -v node >/dev/null 2>&1 || { echo "node >=18 required for the JS test lane and the tasks.json goldens — install Node; the pytest-only fast lane (make test-fast) skips node-dependent tests when node is absent"; exit 1; }

test: check-node
	$(UV) run --group dev pytest
	node --test tests/js/

test-fast:
	$(UV) run --group dev pytest -m "not slow"

# Lint scope is tests/ ONLY this phase: D-04 forbids touching pre-existing
# production code, and script/, scripts/, baseline/, pipeline/ carry ~21
# pre-existing ruff findings — widening scope is a deliberate later change,
# not a silent one.
lint:
	$(UV) run --group dev ruff check tests/
