---
phase: 05-ci-e2-rerun
fixed_at: 2026-10-10T12:56:28Z
review_path: .planning/phases/05-ci-e2-rerun/05-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 5: Code Review Fix Report

**Fixed at:** 2026-10-10T12:56:28Z
**Source review:** .planning/phases/05-ci-e2-rerun/05-REVIEW.md (commit ba2fa99)
**Iteration:** 1

**Summary:**
- Findings in scope for this run: 4 — the 3 warnings (WR-01..WR-03, per the
  disposition directive: all FIX) plus IN-04 (the orchestrator's carve-out for
  a trivial documentation one-liner fully inside a phase-5-touched file)
- Fixed: 4
- Skipped: 0

IN-01..IN-03 are **info-open by disposition** (no code changes this run) and
are recorded in `05-REVIEW-DISPOSITION.md` — matching the phase 3/4 pattern
where info findings carry an explicit ledger verdict rather than a silent
drop. No critical findings existed (review frontmatter: 0 critical).

## Fixed Issues

### WR-01: Published permutation artifact does not disclose the paired-test semantics

**Files modified:** `script/permutation_tests.py`, `dnallm-mark/data/permutation_tests.json` (regenerated)
**Commit:** 87d10b3
**Applied fix:** Reworded the `info.axis` constant in `build_artifact` (script/permutation_tests.py:192)
from `"per-task zscore, aggregate view (score-vector permutation across tasks)"` — which reads
closest to an independent-samples between-task shuffle — to:

> `"per-task zscore, aggregate view; paired permutation test (scipy permutation_type='samples') — per-task difference signs flipped under the null"`

Schema-compatible as-is: `schemas/permutation_tests.json` types `axis` as a
free string (`additionalProperties: false` only forbids new keys, and no
`permutation_type` info key was added, so the contract file is untouched).
No test pinned the old string (grep over `tests/` for `axis` — zero
assertions on it), so the "+test" component of the atomic commit is a no-op.
The artifact was regenerated via the sanctioned chain (`make data`, whose
data target runs the permutation recipe from the repo root): the diff is the
single `info.axis` line; all 861 pair rows and their p-values are
byte-identical, and the other six derived files regenerated as no-ops.
`CHANGELOG.md` already discloses "paired permutation test
(`permutation_type='samples'`)" at its [1.1.0] methodology bullet (line 60),
so it was left untouched — the artifact now matches the disclosure that
already existed, rather than duplicating it. Post-commit `make data` re-run
is a no-op (drift gate, see Verification).

### WR-02: --priority-file/--from-failures accept non-trainable task names

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commit:** d41a7db
**Applied fix:** `_load_registry_key_sets` now returns a third set — the
Train-falsy dataset keys (`{task for task, row in datasets_info.items() if
not row.get("Train")}`) — and both operator-JSON validators append a named
problem to their existing collect-all-problems list when an entry names such
a task: `load_priority_tiers` refuses a `{model, task}` spec's task
(`"--priority-file task has no train split (Train is falsy): ..."`;
bare model names are unaffected — task None means "every task the matrix can
run"), and `load_failure_pairs` refuses a failure record's task the same way.
This mirrors `_validate_filters`' refusal (`run_sweep.py:319-331`) exactly:
same message pattern, same collect-all-problems discipline, same pre-output
abort. Two new tests name `task-y` (the fixture's `Train: 0` task) through
`--priority-file` and `--from-failures`, asserting the named refusal
(task name + "Train" in the message) and that no output dir is written.
Latent-only exposure confirmed by the review (all 50 real registry tasks are
Train-truthy); the committed `sweep_priorities.json` continues to validate
cleanly (its e2e-registry test still passes).

### WR-03: --subset_file joins registry KEYS at validation but Dataset_name at the apply seam

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** 39b2021
**Applied fix:** Added the validation-time cross-check the review offered as
its fail-loudly option: inside `validate_subset_file`'s per-task loop, a
subset key whose registry row carries `Dataset_name != key` appends a named
problem (`"...row has Dataset_name 'x' != registry key 'k' — the
--subset_file map is keyed on registry keys but applied by Dataset_name, so
this task's subset would silently no-op"`) and skips that task's ID checks;
the existing `__main__` wiring then exits non-zero with
`[Error] invalid --subset_file` before any model load. A row omitting
`Dataset_name` entirely cannot silently diverge — the dataset loop's
`row["Dataset_name"]` subscript would crash the run first — so the check
treats a missing field as coincident (`.get("Dataset_name", task)`), which
also keeps the exec-extracted test fixture shape working. Tests:
`REGISTRY_5` rows now carry coincident `Dataset_name` fields (the real
registry's shape, exercising the happy path), plus
`test_subset_validator_refuses_dataset_name_divergence` injecting a registry
where `DIVERGENT`'s row has `Dataset_name: "renamed__task"` and asserting
the named refusal. Verified a no-op over the real registry + committed
`pipeline/eval_subsets.json`: 43 tasks loaded, zero problems, zero
divergent rows in `pipeline/datasets_info.json`.

### IN-04: Stale legacy usage line in summarize_comparison.py docstring

**Files modified:** `script/summarize_comparison.py`
**Commit:** d87c0b6
**Applied fix:** The docstring's usage block documented the pre-Makefile
two-step (`cd dnallm-mark/data && python ../../script/...`), which leaves
the derived tree stale relative to the full chain (it omits the permutation
engine and the tasks.json index generator). Replaced with the canonical
repo-root `make data` entry point, keeping the CWD-sensitivity note for the
script itself. Documentation-only change; no code, no artifact, no test
movement (grep confirms nothing pins the old usage text).

## Verification

**Where verification ran:** all fixes were applied and verified in the MAIN
checkout at `/home/forrest/Github/dnallmmark` (sequential mode, ISOLATION=none
— no review-fix worktree was created), so every gate number below is
reproducible as-is from this tree.

- Full suite (`make test`): **310 passed** (Python; baseline 307 + 3 new
  tests: 2 WR-02 sweep cases + 1 WR-03 contracts case) and **node:test JS
  lane 15 passed** — zero failures
- `make lint` (ruff over the full pinned scope, which includes every touched
  file): **All checks passed**
- `make typecheck` (`ty check` over script/, baseline/, tests/, scripts/,
  pipeline/): **All checks passed**
- Per-fix gates before each commit: `ast.parse` syntax check + the touched
  module's pytest run + `ruff check` + `ty check` scoped to the touched
  files — all green (test_permutation+test_schemas: 105; test_sweep: 47;
  test_run_finetune_contracts: 24; test_aggregation: 36)
- **Drift gate:** `make data` re-run AFTER the WR-01 regeneration commit
  (87d10b3) is a **no-op** — exit 0, zero tracked-file changes across
  `script/`, `pipeline/`, `tests/`, `dnallm-mark/data/`, `schemas/`; the
  only working-tree residue is the ambient, pre-existing
  `.planning/state.json` modification, left untouched per the run's hard
  constraints
- WR-03 real-data no-op: the strengthened validator over the committed
  `pipeline/eval_subsets.json` + `pipeline/datasets_info.json` returns zero
  problems (43 tasks) — the guard changes nothing over today's coincident
  registry
- Constraint compliance: `run_finetune` never executed; `run_sweep` exercised
  only via its validator unit tests and `--dry-run` CLI tests;
  `env_smoke.py` never imported or executed; `/home/forrest/Github/DNALLM`
  untouched; no git tags; no installs; no suppression widening (ruff scope
  files pass clean with no new noqa)

## Skipped Issues

None — all four in-scope findings were fixed. IN-01..IN-03 were never in
this run's fix scope (info-open by disposition; see
`05-REVIEW-DISPOSITION.md`).

---

_Fixed: 2026-10-10T12:56:28Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
