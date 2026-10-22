---
phase: 18-docs-authoring
plan: 02
subsystem: docs
tags: [documentation, multi-gpu, dispatch, subset-datasets, readme, onboarding]
requires:
  - "18-01 (docs/multi-gpu.md dispatch-first restructure — the runbook this plan points into)"
provides:
  - "DOCS-02: README/ONBOARDING/GETTING-STARTED carry the dispatch + 5% subset content; zero stale static-only instructions"
affects:
  - README.md
  - docs/ONBOARDING.md
  - docs/GETTING-STARTED.md
tech-stack:
  added: []
  patterns:
    - "entry-point summary links to the full runbook instead of duplicating it"
    - "every expected-output block pasted from one named executed artifact"
key-files:
  created: []
  modified:
    - README.md
    - docs/ONBOARDING.md
    - docs/GETTING-STARTED.md
decisions:
  - "README dispatch block uses the executed r2 flag set with a deliberately generalized run root (finetuned-sweep-5pct) — the 12-cell/2-model/2-task matrix and its counts are the executed Phase-15 numbers; only the root name differs so a reader's verbatim run never collides with the machine's r2 root markers"
  - "ONBOARDING §5 'To validate a subset, add --tasks' line left untouched — the mandatory disambiguation lives in the appended §6 note which names §5's --tasks filter explicitly (surgical scope: plan action says extend §6 only)"
metrics:
  duration: 7 min
  completed: 2026-10-22
status: complete
commits: 3
plan_head_before: cc26bb722053ad0e6d920d237354ea3c813fc7ae
plan_head_after: 81ff1acd95b6fe01e9d1528cadc6905b7bfc5a6c
actuals:
  tokens: 1948   # chars/4 over the realized diff (7790 diff chars across the three files)
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count cc26bb7..HEAD
---

# Phase 18 Plan 02: Entry-document dispatch + 5% subset landing Summary

**One-liner:** README gained a copy-paste "Multi-GPU sweeps (dispatch mode) and 5% subset datasets" subsection (executed Phase-15 commands and row counts) plus a dispatch-first docs-index bullet; ONBOARDING §6 gained the dispatch pointer, the generate→configure→run→consume subset summary, and the mandatory task-filter-vs-subset-dataset disambiguation; GETTING-STARTED's pointer went dispatch-first.

## What Was Executed

### Task 1 — README subsection + docs-index descriptor (commit b1d7833)

- New level-3 subsection "Multi-GPU sweeps (dispatch mode) and 5% subset datasets" inserted in the Benchmark Pipeline flow between the Run Pipeline closing prose and "### Export Runs to the Leaderboard".
- Three-sentence orientation: dispatch = one dispatcher feeding idle per-GPU workers under ONE shared root (no merge step); legacy static sharding coexists behind `--mode static`; full runbook at docs/multi-gpu.md.
- Command block (a) subset generation: `python script/make_subset_datasets.py` with the exact flag set verified at `script/make_subset_datasets.py:140-175` (`--dataset-root`, `--output-root pipeline/datasets-smoke`, `--registry-dir pipeline/registry-smoke`, `--models`, `--tasks`, `--fraction 0.05`, `--seed 42`) and the executed expected-output lines quoted verbatim from `/root/autodl-tmp/phase15-evidence/subset-generation.log` (5mC 105/11/117 from source 2110/234/2344; emp_H3 598/74/74 from source 11971/1497/1497).
- Command block (b) dispatch launch: dry-run first, real minus `--dry-run`, generalizing the executed Phase-15 r2 argv (`--mode dispatch --workers 2 --gpus 0,1`, offline env exports, explicit absolute `--output-root`/`--log_dir`, subset pair `--registry-dir`/`--dataset_root`) with expected `[Dry-run] [Dispatch] 12 planned cell(s)`; plus the export consumption one-liner with its executed record-count line (`[Dry-run] 12 run record(s) across 2 model(s) / 2 task(s)` — the executed r2 matrix counts, from `15-VERIFICATION.md:163`).
- Close: VAL-02 isolation one-liner (subset roots/registries never shared with real runs; generator refuses registry dirs overlapping official `pipeline/`).
- Docs-index bullet (README line ~624 post-edit) rewritten from "sharding vs DDP decisions and the runbook" to "dispatch-mode runbook, the 5% subset workflow, and the legacy static-shard track".
- The v1.3-test-report index bullet was NOT added (18-04 owns it; the report does not exist yet) — verified by grep.

### Task 2 — ONBOARDING §6 extension (commit 257132f)

- Kept the existing single-GPU sentences; appended three blocks in the file's existing voice:
  1. Dispatch paragraph — `pipeline/run_sweep_shard.py --mode dispatch` (one shared root, live dispatcher table on stdout, `dispatch_state.json` terminal check `status == "done"`), TUI slot-4 composes the same argv natively, runbook link `[multi-gpu.md](multi-gpu.md)` (resolves to the landed 18-01 reality).
  2. 5% subset workflow summary in the generate → configure → run → consume shape, one sentence per leg, naming `script/make_subset_datasets.py` and the subset registry/root pair isolation (VAL-02).
  3. The mandatory Pitfall-4 disambiguation: §5's `--tasks <name1,name2>` filter selects WHICH full datasets enter the matrix; the 5% subset mechanism samples ROWS into a separate dataset/registry pair — different concepts, different tools, never interchangeable.

### Task 3 — GETTING-STARTED descriptor refresh + zero-stale audit (commit 81ff1ac)

- Line 154 bullet: "multi-GPU sweep orchestration" → "multi-GPU sweep orchestration: dispatch mode, the 5% subset workflow, and the legacy static track". File stays CPU-scoped, pointer-only (no GPU workflow inlined).
- Zero-stale audit executed across all three files, commands and findings:

```bash
# audit 1 — static-sharding-only framing (expect zero hits)
grep -niE '(only|sole) (mode|way).*shard|sharding is the' README.md docs/ONBOARDING.md docs/GETTING-STARTED.md
# → no output (exit 1): zero findings

# audit 2 — every multi-gpu.md cross-reference target exists post-18-01
grep -c '## Which mode when' docs/multi-gpu.md                                  # → 1
grep -c '## The 5% subset workflow' docs/multi-gpu.md                           # → 1
grep -c '## CLI runbook — dispatch mode' docs/multi-gpu.md                      # → 1
grep -c 'smoke procedure (executed on this machine)' docs/multi-gpu.md          # → 1

# audit 3 — premature report references (expect all :0)
grep -c 'v1.3-test-report' README.md docs/ONBOARDING.md docs/GETTING-STARTED.md
# → README.md:0, docs/ONBOARDING.md:0, docs/GETTING-STARTED.md:0

# scope check — only the three planned files changed
git diff --name-only cc26bb7..HEAD   # → README.md, docs/ONBOARDING.md, docs/GETTING-STARTED.md
```

Audit result: **zero findings** on every leg.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - prose accuracy] Run Pipeline closing prose "the next section" anchor**
- **Found during:** Task 1
- **Issue:** The paragraph ending the Run Pipeline subsection said the leaderboard files "are produced by the unified exporter in the next section" — inserting the new subsection between that prose and Export Runs would have made "next section" point at the wrong section.
- **Fix:** Rephrased to "produced by the unified exporter (see the *Export Runs to the Leaderboard* section below)" — position-independent and accurate.
- **Files modified:** README.md
- **Commit:** b1d7833

Other than that, the plan executed exactly as written.

## Verification Evidence

All three task verify blocks green (run verbatim):

- Task 1: `grep -c 'make_subset_datasets' README.md` ≥ 1 ✓; `grep -ci 'dispatch' README.md` ≥ 3 ✓; `--mode dispatch` present ✓; `5% subset…subset datasets` present ✓; retired framing string absent ✓; `v1.3-test-report` absent ✓.
- Task 2: generator/dispatch/`--tasks`/subset/stratified-5% tokens all present in ONBOARDING ✓.
- Task 3: GETTING-STARTED dispatch-first pointer present ✓; static-only regex zero hits across all three ✓; premature-report count zero across all three ✓ (full command outputs above).

Every command and number in the new content is sourced from: `script/make_subset_datasets.py:140-175` (flag surface), `/root/autodl-tmp/phase15-evidence/subset-generation.log` (subset expected output), `15-03-PLAN.md:127` + `15-03-SUMMARY.md` (r2 dispatch argv, 12-cell matrix), `15-VERIFICATION.md:163` (consumption line), and the 18-01-landed `docs/multi-gpu.md` runbook (mode vocabulary, subset-pair configure shape). No invented flags; the report link was provably not added by this plan.

## Auth Gates

None.

## Known Stubs

None — documentation-only plan; no stubs, no skipped tests, no unrun verify steps.

## Threat Flags

None — no new surface beyond the plan's threat model (T-18-02 disambiguation note landed as mandated; T-18-SC vacuous: zero installs).

## Self-Check: PASSED

All four artifacts exist on disk (README.md, docs/ONBOARDING.md, docs/GETTING-STARTED.md, this SUMMARY); all three task commits (b1d7833, 257132f, 81ff1ac) are ancestors of HEAD.
