# =====================================================================
# Makefile — single-command entry points over the uv-managed environment
#
# Replaces the undocumented CWD-sensitive 3-step regeneration procedure
# (REL-04): everything below runs from the repo root with no activation
# step. `uv run` auto-syncs .venv from uv.lock before invoking.
#
#   make data       regenerate the derived data chain (4 models_comparison
#                   + tasks.json; task_performance/ is committed static
#                   data until E2' regenerates it via script/export_runs.py)
#   make test       full local suite: pytest (slow lane included) plus the
#                   node:test JS suite over tests/js/ (Python + JS lanes)
#   make test-fast  pytest excluding @slow (the real-tree determinism run);
#                   the JS suite is fast and runs in the full test lane
#   make ci         the pinned CI lane (Phase 5, REV-06 Q2): pytest -m ci —
#                   golden replay + metric-key parity + species spot checks
#                   + aggregation units; reuses the existing suite (the ci
#                   marker selects modules, no duplicated tests)
#   make lint       ruff over tests/ + the Phase-authored/edited files
#                   (make_dev_splits.py, summarize_comparison.py,
#                   export_runs.py, freeze_snapshot.py, convert_registry.py,
#                   run_finetune.py, run_sweep.py, env_smoke.py,
#                   compare.py, permutation_tests.py,
#                   run_migration_inventory.py, audit_n_frequencies.py)
#   make typecheck  ty type check over script/, baseline/, tests/, scripts/,
#                   and pipeline/ (GPU-side imports replaced with Any — they
#                   are never installed CPU-side, D-05)
# =====================================================================

.PHONY: data test test-fast ci lint typecheck check-node snapshot

# WR-02: PATH lookup with an overridable default (`make UV=/path/to/uv`) —
# setup-uv/brew/pipx installs live outside ~/.local/bin, and a hardcode
# there breaks every target (incl. CI) with Error 127.
UV ?= uv
DATA_DIR := dnallm-mark/data

# Data chain — one `cd ... && ...` per line: each recipe line is its own
# shell (Pitfall 8), and summarize resolves inputs/outputs against CWD.
# The permutation engine is REPO_ROOT-relative and runs from the repo root
# (F6 Q3: offline at regeneration, never at page render). The JS generator
# is __dirname-relative and runs from repo root as-is. The retired pivot
# step is gone (04-05, SC-2/OQ6): task_performance/ is committed static
# data until E2' regenerates it via script/export_runs.py — this target
# cannot and must not refresh it. The provenance emitter (06-04, DATA-04/
# DATA-05) projects the registry's six provenance columns into
# data/provenance.{json,csv} + the DATA.md appendix — deterministic, so the
# whole chain stays a byte-stable no-op on a clean checkout (the drift
# invariant the CI job replays).
data: check-node
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/summarize_comparison.py
	$(UV) run --group data python script/permutation_tests.py
	$(UV) run --group data python script/build_provenance.py
	node scripts/generate-tasks-index.js

# Snapshot lane (06-04, SC-3 / REV-03 tail): freeze the committed
# derived-data set — everything in dnallm-mark/data/ except
# model_performance/ (an input, not a derived output) — into a tar +
# SHA256 manifest under baseline/snapshots. The frozen commit hash reads
# the committed manifest.json `generated_from` constant: NEVER a live git
# call in the data path (the lane must work from a tarball-exported tree).
# Manual override when re-freezing outside the data chain:
#   --commit-hash "$$(git rev-parse HEAD)"
# Paths are passed relative to baseline/snapshots so re-verification is
# the standard tool one-liner from that directory:
#   cd baseline/snapshots && sha256sum -c snapshot-*.sha256
# The .tar is gitignored; the .sha256 manifest is committed (OQ 2).
SNAPSHOT_FILES := $(patsubst %,../../%,$(wildcard $(DATA_DIR)/*.json $(DATA_DIR)/*.csv)) $(patsubst %,../../%,$(wildcard $(DATA_DIR)/task_performance/*.json))
snapshot:
	@set -e; \
	hash="$$($(UV) run --group data python -c "import json; print(json.load(open('$(DATA_DIR)/manifest.json'))['generated_from'])")"; \
	mkdir -p baseline/snapshots; cd baseline/snapshots; \
	$(UV) run --group data python ../../script/freeze_snapshot.py --paths $(SNAPSHOT_FILES) --output-dir . --commit-hash "$$hash"

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
	node --test tests/js/*.test.js

test-fast:
	$(UV) run --group dev pytest -m "not slow"

# The pinned CI lane (Phase 5, REV-06 Q2): exactly the tests the CI workflow's
# test job replays — the golden replay over the committed e2_replay fixture
# plus the three reused classes (metric-key parity, species spot checks,
# aggregation units) via the `ci` pytest marker registered in pyproject.toml.
ci: check-node
	$(UV) run --group dev pytest -m ci

# Lint scope (Phase 3 decision, D-08): tests/ plus the explicit list of
# Phase-authored/edited files whose findings are FIXED — script/make_dev_splits.py
# (03-02), pipeline/run_finetune.py (D-08: all 16 arriving findings resolved,
# 13 genuinely + 3 justified per-line noqa at the designed blind-except
# isolation sites), pipeline/run_sweep.py (03-04), script/summarize_comparison.py
# (04-01: FIX-02 Category grouping + WR-03 isfinite; 04-05: IN-03 importer),
# baseline/compare.py (04-01: IN-01 INT label + WR-02 BOOL_CROSS),
# script/export_runs.py (04-02: vendored suite statistics + the exporter
# core; 04-05: the legacy dataset-metric translation), script/freeze_snapshot.py
# (04-02: the tar + SHA256 snapshot primitive), script/convert_registry.py
# (04-05, IN-08: the bidirectional registry converter joins scope — clean on
# arrival). The pre-existing findings in the REMAINING script/, scripts/,
# baseline/ production files stay deferred to their later routing, so those
# paths stay OUT of scope deliberately.
# No [tool.ruff] config section exists (D-08: no baseline carry-over, no
# suppression).
# Phase-6 extension (06-04): the new phase-6 scripts join the fixed-findings
# list ONLY when present on disk — a cut lane's script must never be
# referenced by the gate (existence guard; sequential wave order means
# 06-02/06-03 scripts already exist here, and script/doi_swap.py joins
# automatically when it lands later in 06-04).
PHASE6_SCRIPTS := $(foreach s,script/build_frontier.py script/zero_shot_vep.py script/build_provenance.py script/doi_swap.py,$(if $(wildcard $(s)),$(s)))
lint:
	$(UV) run --group dev ruff check tests/ script/make_dev_splits.py script/summarize_comparison.py script/export_runs.py script/freeze_snapshot.py script/convert_registry.py script/permutation_tests.py script/run_migration_inventory.py script/audit_n_frequencies.py baseline/compare.py pipeline/run_finetune.py pipeline/run_sweep.py pipeline/env_smoke.py $(PHASE6_SCRIPTS)

# Type check (ty, maintainer directive 2026-10-09): zero-diagnostics baseline
# verified empirically at research time. [tool.ty] in pyproject.toml carries
# the config — extra-paths mirrors tests/conftest.py's sys.path contract, and
# GPU-side imports (torch/dnallm/transformers/peft/datasets) are replaced
# with Any because they are never installed CPU-side (D-05). --group dev is
# required for the same default-groups reason as lint/test.
typecheck:
	$(UV) run --group dev ty check
