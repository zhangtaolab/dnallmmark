---
phase: 18-docs-authoring
plan: 01
subsystem: docs
tags: [documentation, multi-gpu, dispatch-mode, runbook, subset-workflow]
requires:
  - "Phase 13/14 dispatch CLI surface (pipeline/run_sweep_shard.py:352-469)"
  - "Phase 15 executed evidence (docs/multi-gpu.md smoke record; 15-03-SUMMARY; phase15-evidence pack)"
  - "Phase 16 shipped TUI surfaces (16-UI-SPEC.md:77-82)"
provides:
  - "docs/multi-gpu.md dispatch-first: DOCS-01 delivered for the multi-GPU runbook"
  - "Generalized dispatch launch/watch/--rerun-failed runbook sections (copy-pasteable)"
  - "5% subset workflow documented end-to-end with executed row counts"
  - "First-class static-track --cleanup subsection"
affects:
  - "18-02 (README/docs-index descriptor refresh points at this dispatch-first file)"
tech-stack:
  added: []
  patterns:
    - "mode-table lead (three-way dispatch/static/DDP-deferred) replacing the sharding-vs-DDP decision section"
    - "executed-reality expected-output blocks (subset-generation.log quoted verbatim)"
key-files:
  created: []
  modified:
    - docs/multi-gpu.md
decisions:
  - "Static is the CLI parser default but is documented under an explicit legacy track with --mode static spelled into every launch command — the mode choice is always visible in a copied command"
  - "The sharding-vs-DDP decision record was CONDENSED into the three-way mode table (WORLD_SIZE/LOCAL_RANK seam citations preserved), not deleted — MGPU-06 coexistence"
  - "The dispatch track was inserted after machine-roles/E2' and directly before the subset workflow + smoke record, keeping the executed smoke section as the file's last section per the plan's letter"
metrics:
  duration: 5 min
  completed: 2026-10-22
  tasks: 3
  files: 1
status: complete
actuals:
  tokens: 5074   # chars/4 over git diff c008a6e..HEAD (docs/multi-gpu.md only)
  tasks: 3
  commits: 3     # MEASURED: git rev-list --count c008a6e..HEAD
plan_head_before: c008a6e72fc8a526c01ded9cc997fd24f7682dd7
plan_head_after: 4174eefd252fc2244fc47ad356a77f33df5641f9
---

# Phase 18 Plan 01: multi-gpu.md dispatch-first rewrite Summary

**One-liner:** docs/multi-gpu.md restructured dispatch-first — three-way mode table (dispatch primary / static legacy / DDP deferred), a generalized dispatch launch/watch/--rerun-failed runbook, the 5% subset workflow with executed row counts, and a first-class --cleanup subsection, with the executed Phase-15 smoke record byte-preserved (sha256 dcdbc798…).

## What Was Executed

### Task 1 — dispatch-first structural restructure (tracer) — commit 9caa5ff

- Intro rewritten: TWO coexisting modes since Phase 13 (dispatch primary:
  one dispatcher, one shared root, O_EXCL claim ledger; static legacy: LPT
  sharding under frozen sibling roots). The stale "TUI composes single
  sweeps (D-01)" claim DELETED — replaced with the Phase-16 reality (slot-4
  native dispatch launch, slot-5 dispatch state + GPU lanes). The
  run_sweep/run_finetune byte-untouched statement retained.
- "The decision: model sharding vs DDP" section replaced by a "Which mode
  when" three-way table (What accelerates / Roots / Failure recovery / Live
  view / Use when) + the condensed DDP-deferral paragraph with the
  `run_finetune.py:1450`/`:1635` WORLD_SIZE/LOCAL_RANK seam citations
  preserved (MGPU-06 coexistence, nothing deleted).
- Static runbook (§1-§6) relabeled under "CLI runbook — legacy static mode
  (`--mode static`)"; `--mode static` token added to both §1 launch
  commands (7 file occurrences post-edit vs baseline 1).
- Smoke section: exactly ONE sanctioned prose edit — the
  "(the full dispatch-first docs pass is Phase 18, DOCS-01)" parenthetical
  removed; heading + all fenced command/output blocks byte-identical.
- Tracer feedback gate: the task's verify is automated-only (grep/sha) and
  human spot-check is deferred to phase review per the plan — verify
  re-run end-to-end green, expanded without checkpoint.

### Task 2 — dispatch-mode runbook sections — commit 3da927d

- "CLI runbook — dispatch mode (`--mode dispatch`)" track inserted before
  the smoke section with four subsections:
  - Launch: generalized `--mode dispatch --dry-run` block copied from the
    executed smoke argv shape (offline env exports; explicit absolute
    `--output-root`/`--log_dir` rationale — child cwd pinned to
    `pipeline/`, prevents `directories.json` seeding; real launch = same
    minus `--dry-run`; ONE shared root, no merge ever, MGPU-06).
  - Watch: dispatcher stdout plain-line table (D15-10) + Phase-16 TUI
    surfaces, every claim traced to 16-UI-SPEC.md:77-82 (slot-5 dispatch
    rows from `dispatch_state.json` v2, ≥60 s stale marking, G GPU-lanes
    panel with utilization/memory/temperature on the 2 s cadence, 未安装/N=0
    empty states; slot-4 workers/GPUs fields compose the dispatch argv with
    a dispatch-plan preview on confirm).
  - `--rerun-failed` promoted to first-class: implies dispatch, needs
    neither `--models` nor `--seeds`, verbatim lane replay (D14-06), loud
    unequal-lane refusal (D14-08), `dispatch_ledger/archive/` rerun_of
    genealogy (D14-07); the executed empty-ledger refusal line quoted as
    expected output.
  - Failure-recovery-per-mode cross-link table (dispatch → --rerun-failed;
    static → §4 from-failures recipe).

### Task 3 — subset workflow + --cleanup promotion + zero-stale sweep — commit 4174eef

- "The 5% subset workflow (generate → configure → run → consume)" section:
  generate leg with the full required flag surface of
  `script/make_subset_datasets.py` + the executed output block quoted
  verbatim from `/root/autodl-tmp/phase15-evidence/subset-generation.log`
  (5mC train 105 / dev 11 / test 117 from 2110/234/2344; emp_H3 598/74/74
  from 11971/1497/1497) and the semantics stated once (per-split
  independent stratified sampling, `k = max(1, int(n × fraction))`
  floor-of-1, run-twice byte-identical); explicit disambiguation from the
  `--tasks` task filter; configure+run leg with the subset PAIR
  (`--registry-dir` + `--dataset_root`, both absolute) and the 15-03
  Pitfall-1 guard (--dataset_root steers children; --registry-dir alone
  never does) + D15-07/VAL-02 isolation rules; consume leg with the
  export_runs dry-run one-liner and the unmodified-chain r2 evidence
  pointer.
- `--cleanup` extracted from §5 Merge into its own "### 6. Cleanup"
  subsection (typed `--yes PHRASE` = resolved root, dual verification
  before removal, merged root never a target, dispatch roots refuse both);
  existing merge prose kept; Web mirror renumbered §7.
- Zero-stale final sweep green; smoke fence hash re-verified a third time;
  `make lint` + `make typecheck` pass (source untouched).

## Deviations from Plan

None — plan executed exactly as written. (The Task-1 commit message
contains a cosmetic typo "WORLd_SIZE"; content and code fences are
correct.)

## Verification Evidence

All three task gate sets green in sequence (each re-asserts the smoke
fence sha256 `dcdbc7980786b71b50458ef64869fb83d27ebc33b6c33d19f1f1a9f9e2d8017f`):

- Task 1: hash OK; smoke heading count == 1; `is Phase 18, DOCS-01` and
  `composes single sweeps` no longer grep; `--mode static` count 7 (≥3);
  `--mode dispatch` count 5 (≥2).
- Task 2: `rerun-failed` count 6 (≥2); `dispatch_state` count 6 (≥2);
  GPU-lanes mention present; `--mode dispatch --dry-run` block present;
  hash OK.
- Task 3: `make_subset_datasets` present; `datasets-smoke` +
  `registry-smoke` present; row counts 105/11/117 + 598/74/74 present;
  Cleanup heading matches; hash OK.
- `git status` confirms zero tracked changes outside docs/multi-gpu.md
  from this plan (pre-existing orchestrator-owned SVG noise untouched).

## Known Stubs

None — no placeholders; every command and number traces to
`pipeline/run_sweep_shard.py:352-469`, the executed smoke/sweep records,
or the named Phase-15 evidence artifacts.

## Self-Check: PASSED

- docs/multi-gpu.md exists and is the only modified file (496 lines).
- Commits 9caa5ff, 3da927d, 4174eef all present on `autorun`, ancestors
  of HEAD.
