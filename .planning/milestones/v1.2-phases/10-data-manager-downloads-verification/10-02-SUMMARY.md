---
phase: 10-data-manager-downloads-verification
plan: 02
subsystem: tui-services
tags: [reconcile, audit-subprocess, row-count, presence-overlay, done-gate, mismatch, reaudit, n-audit-baseline]

requires:
  - phase: 10-data-manager-downloads-verification
    provides: "10-01's DownloadQueueService — the landed->done transition this plan gates, the persisted reconcile:null field, the stored-but-unused runner constructor seam, and the retry() failed+mismatch gating"
  - phase: 09-gauntlet
    provides: the audit-leg staging template (candidate-only temp registry, ABSOLUTE Dataset_path inertness, temp outputs, empty-overlay env) and the _audit_verdict pass criteria re-implemented verbatim
provides:
  - reconcile_dataset — the D-09 automatic post-landing audit subprocess (candidate-only temp registry, four temp output flags, empty-overlay env) with gauntlet verdict semantics and the official declared side from registry Train/Dev/Test
  - The done gate: done = landed AND reconcile pass; mismatch a first-class terminal state carrying declared+measured for the banner (deletes nothing, D-07)
  - merge_presence + reconciled_rows — the D-11 presence-flip substrate consumed by the UNCHANGED registries.presence_for (only reconcile-pass keys ever flip)
  - reaudit_baseline — the R-03 g action semantics (script DEFAULT outputs -> four worktree artifacts, maintainer review+commit; empty-overlay env; nothing automatic reaches it)
  - The four-artifact sha256 byte-unchanged regression pinning the anti-clobber guarantee
affects: [10-03 zenodo+strings, 10-04 data-manager screen (mismatch banner, g binding), 10-05 selection/env presence flip, 10-06 e2e]

actuals:
  tokens: 20210      # chars/4 over the realized diff (download_queue.py + tests)
  tasks: 3
  commits: 6         # MEASURED: git rev-list --count a186c43..HEAD (3 RED test + 3 GREEN feat, TDD)
plan_head_before: a186c43b60d5a09b92ab3728ceec74e97823dd1f
plan_head_after: 56a2e15ab229a47587f9944bbda177d6ae76f6fc

tech-stack:
  added: []            # zero new dependencies (the audit script + registry_loader are in-repo stdlib)
  patterns:
    - "Thin in-module re-implementation of the gauntlet audit leg for official keys (Q4 ruling) — staging + verdict semantics duplicated deliberately rather than imported, keeping both honest"
    - "done-gate insertion at the landed->done transition: reconcile pass/mismatch/failed map to done/mismatch/failed terminal states; the entry's reconcile field is the persisted verdict payload"
    - "Pure tasks-shaped overlay: merge_presence(audit_tasks, {key: rows}) feeds the UNCHANGED Phase 8 presence_for — presence flips by data composition, never by rewriting the committed baseline"

key-files:
  created: []
  modified:
    - tui/services/download_queue.py
    - tests/tui/test_services_download_queue.py

key-decisions:
  - "Parsed-record violations (missing=true, rows<=0, unified_eval_n<=0, declared!=measured) classify as mismatch; infrastructure failures (nonzero exit, timeout, unparseable n_audit, key absent, launch error, unreadable registry) classify as failed — the plan's 'every other shape is mismatch or failed' resolved on the artifact-disproof vs cannot-run line"
  - "outcome.measured carries the full parsed rows map including 0s (the gauntlet's internal map only kept >0 rows; the banner needs the complete data)"
  - "Real-subprocess tests stage a tmp repo carrying COPIES of script/audit_n_frequencies.py + pipeline/registry_loader.py (the script resolves REPO_ROOT from its own file and loads registry_loader by path) — controlled registry + fixture CSVs feed the REAL kernels with zero committed-artifact reach"
  - "_finish now always sets entry.reconcile (None on every non-verdict path): a new attempt's terminal transition replaces the stale payload; retry already re-queues failed/mismatch"
  - "The four-artifact sha256 regression was born-green (Task 1's implementation already satisfied it) — kept as the drift tripwire, not as RED evidence"
  - "ty flagged the frozen-dataclass mutation assertion on ReauditOutcome (read-only property) while the identical QueueEntry pattern passes — dropped the duplicate mutation assert rather than introducing the repo's first ty:ignore"

patterns-established:
  - "ReconcileOutcome/ReauditOutcome: frozen dataclasses carrying machine codes + data tokens + verbatim raw_output — the screens render, never parse"
  - "The log's [reconcile] section: subprocess legs append their verbatim output under a labeled section in the per-key drill-down log (D-03 completeness)"

requirements-completed: [DATA-03]

coverage:
  - id: D1
    description: "Automatic post-landing reconcile through the real audit subprocess with gauntlet verdict semantics; done gated on pass; mismatch a first-class state carrying declared+measured, deleting nothing"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (Lane 4: staging pins, verdict semantics, failure edges, done-gate paths)"
        status: pass
      - kind: integration
        ref: "tests/tui/test_services_download_queue.py::test_reconcile_real_subprocess_pass_over_fixture_csvs + ::test_reconcile_real_subprocess_mismatch_names_numbers_no_deletion (real audit script over fixture CSVs)"
        status: pass
  - id: D2
    description: "Presence-flip substrate: merge_presence overlay + reconciled_rows read-only derivation; only reconcile-pass (done) keys flip through the UNCHANGED presence_for"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (merge_presence/reconciled_rows suites incl. the end-to-end persisted-done -> presence_for flip)"
        status: pass
  - id: D3
    description: "The g re-audit semantics exactly per R-03: argv with NO output flags (script defaults write the four worktree artifacts for maintainer commit), empty-overlay env, timeout-bounded, failure-absorbing, unreachable from automatic paths"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (reaudit argv/env/absorption/knob suites + test_no_automatic_path_ever_constructs_a_no_flag_audit_argv)"
        status: pass
    human_judgment: true
    rationale: "No CI test may execute a default-outputs audit (it would rewrite the four committed artifacts by design). The real invocation is proven by the fake-runner argv pin; the maintainer's live g press is the documented check below."
  - id: D4
    description: "The committed-artifact anti-clobber guarantee: n_audit.json, n_audit.csv, eval_subsets.json, DATA.md byte-unchanged across every automatic path"
    requirement: DATA-03
    verification:
      - kind: integration
        ref: "tests/tui/test_services_download_queue.py::test_committed_artifacts_byte_unchanged_across_real_reconcile_run (sha256 before/after a full run_task with the real reconcile)"
        status: pass
  - id: D5
    description: "Full-suite + lint + typecheck gates green with the amended 10-01 engine tests (offline via the default passing fake reconcile runner)"
    requirement: DATA-03
    verification:
      - kind: integration
        ref: "make test (1057 pytest = 1010 baseline + 47 new, node 18/18, exit 0); make lint; make typecheck"
        status: pass

duration: 30min
completed: 2026-10-12
status: complete
---

# Phase 10 Plan 02: DATA-03 Row-Count Reconciliation Summary

**One-liner:** The DATA-03 correctness kernel — every landed download now reconciles against the declared n_audit baseline through the real audit subprocess (temp-staged, never clobbering), done is gated on the pass verdict, mismatch lands as a first-class state carrying declared/measured numbers, the presence overlay flips exactly on reconcile-pass through the unchanged Phase 8 mapping, and the explicit `g` re-audit writes the four worktree artifacts exactly as R-03 rules.

## What Was Built

### Task 1 — Reconcile subprocess leg + verdict + the done gate

`reconcile_dataset(key, run_id) -> ReconcileOutcome` re-implements the gauntlet audit-leg staging for the official-key variant (the Q4 ruling — thin re-implementation, no GauntletService import): a candidate-only temp registry holding exactly `{key: entry}` with the `Dataset_path` ABSOLUTIZED against the pipeline dir (the pathlib join replaces `--datasets-root` — that root is deliberately inert), an inert temp datasets-root, ALL FOUR output flags at temp paths under one staging temp root, and `env = os.environ + CUSTOM_DIR_ENV=<empty temp dir>` — invoked through the runner seam (`capture_output/text/timeout=300`, constructor-overridable). Verdict from the PARSED temp `n_audit.json` `tasks.{key}` record with the gauntlet `_audit_verdict` semantics verbatim: pass iff `missing` false, train/dev/test each rows > 0 (bool excluded), `unified_eval_n` > 0, and every declared registry `Train`/`Dev`/`Test` int equals the measured rows (absent declaration skips that split). Parsed-record violations are mismatch; nonzero exit / timeout / unparseable or absent n_audit / key absent / launch error / unreadable registry are failed — each a distinct problem code, verbatim raw output carried, never an exception. `run_task`'s landed->done transition now runs the gate: pass -> done (entry.reconcile populated with declared/measured/unified_eval_n/verdict), mismatch -> state mismatch (banner data; deletes nothing, D-07), failed reconcile -> failed. The verbatim per-key log gains a `[reconcile]` section. The 10-01 engine tests stay offline via `engine_service`'s default PASSING fake runner.

### Task 2 — Presence overlay merge + reconciled_rows (D-11 substrate)

Module-level pure `merge_presence(audit_tasks, reconcile_results)`: returns a NEW tasks-shaped dict where reconcile-pass keys read `missing: false` with their measured split rows — the UNCHANGED `registries.presence_for` maps it to PRESENCE_PRESENT with the exact measured ints (the Phase 8 four-status vocabulary stays the contract; git-diff clean on registries.py). `audit_tasks=None` + a non-empty overlay still serves the column (live truth alone); an overlay key the committed audit never carried simply appears (drift tolerance); zero I/O, inputs never mutated. `reconciled_rows(state_path=None)`: read-only tolerant derivation of `{key: (train, dev, test)}` from persisted done entries with a populated `reconcile.measured` (artifact_loader None sentinel; mismatch/failed/done-without-reconcile/non-int rows and corrupt or absent files all yield nothing). Only done keys ever enter the overlay — semantic 6's enforcement is upstream at the done gate.

### Task 3 — `g` re-audit (R-03) + the byte-unchanged regression

`reaudit_baseline(run_id) -> ReauditOutcome`: argv EXACTLY `[sys.executable, <absolute script path>]` with NO output flags — the script's own defaults write the four worktree artifacts (`dnallm-mark/data/n_audit.json`, `n_audit.csv`, `pipeline/eval_subsets.json`, `DATA.md`) for maintainer review and commit; no temp+replace, no narrow write. Env is `os.environ` plus exactly one override pinning `CUSTOM_DIR_ENV` at an empty temp dir (custom entries never leak into the refreshed baseline). `timeout_reaudit` knob (300 default); every failure absorbed into a not-ok outcome with verbatim output. Nothing automatic calls it — the shared-runner invariant test proves only `reaudit_baseline` constructs a no-flag audit argv while the run_task reconcile carries all four output flags. The four-artifact sha256 regression runs a full `run_task` with the REAL reconcile subprocess over fixture CSVs and asserts all four committed artifacts hash-identical before/after.

**The documented maintainer live check (no CI test may execute a default-outputs audit):** on the GB10 host, press `g` on a mismatch row in the data-manager screen (10-04's binding) — or run `python script/audit_n_frequencies.py` from the repo root — then `git status` must show EXACTLY the four artifacts modified (`dnallm-mark/data/n_audit.json`, `dnallm-mark/data/n_audit.csv`, `pipeline/eval_subsets.json`, `DATA.md`); the diff is the review surface and the maintainer commits it as the new baseline.

## Performance

- **Duration:** ~30 min (2026-10-12T14:22Z -> 14:52Z)
- **Tasks:** 3/3
- **Files modified:** 2 (both planned)

## Task Commits

Each task ran RED -> GREEN with separate commits:

1. **Task 1: Reconcile subprocess leg + verdict + the done gate** — `de685b6` (test, 25 RED) / `ee29add` (feat)
2. **Task 2: Presence overlay merge + reconciled_rows** — `f84376b` (test, 12 RED) / `c15bc3a` (feat)
3. **Task 3: reaudit_baseline + byte-unchanged regression** — `3993efe` (test, 9 RED + 1 born-green pin) / `56a2e15` (feat)

No REFACTOR commits needed (inline cleanup landed inside each GREEN).

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_services_download_queue.py -q` — **103 passed** (56 amended-offline 10-01 tests + 47 new).
- `uv run --group dev --group tui pytest tests/tui -q` — **487 passed** (registries presence_for behavior untouched; no existing test outside this plan's module modified).
- `make lint` — ruff **All checks passed**. `make typecheck` — ty **All checks passed**.
- `make test` — **exit 0**: pytest **1057 passed** (1010 baseline + 47 new), node lane 18/18.
- `grep -c "audit_n_frequencies" tui/services/download_queue.py` — nonzero (the reconcile/reaudit legs reference the real script).
- Scope: `git diff 71b05c4..HEAD -- tui/services/registries.py pipeline/ script/ dnallm-mark/` — EMPTY (zero out-of-plan tree changes; no uv/pyproject changes; the four committed artifacts untouched).

## Decisions Made

See key-decisions in the frontmatter; additionally:

- The staging-existence pins (overlay dir exists and is empty) assert INSIDE the fake-runner hook — the service's `TemporaryDirectory` is cleaned before `reconcile_dataset` returns, so post-return path assertions would be vacuously false (the gauntlet `capture_staging` idiom, applied).

## Deviations from Plan

**1. [Test-authoring slip, self-corrected] method name drift `reattach_baseline` -> `reaudit_baseline`**
- **Found during:** Task 3 RED authoring — the first test draft called `reattach_baseline`; the plan's contract is `reaudit_baseline`.
- **Resolution:** renamed across the tests and amended the RED commit (`3993efe`) before any implementation existed; the plan name is authoritative. No behavior impact.

**2. [Rule 1 - Bug] RED-fixture conflation in the real-mismatch test**
- **Found during:** Task 1 GREEN — `real_audit_repo(declared=(999,2,2))` also wrote 999 CSV rows, so declared==measured and the mismatch case passed vacuously.
- **Fix:** split the fixture into `declared` vs `rows` params; the mismatch test declares 999 against 4 actual rows. `tests/tui/test_services_download_queue.py`, inside the Task 1 GREEN commit `ee29add`.

**3. [Typecheck constraint] dropped the duplicate frozen-mutation assertion on ReauditOutcome**
- ty flags `outcome.ok = False` (frozen dataclass read-only property) while the identical QueueEntry pattern passes; the repo baseline is zero ty findings with no ignore comments, so the duplicate assertion was removed instead (the frozen decorator's runtime behavior is already pinned at the QueueEntry test). Committed in `56a2e15`.

**4. [Born-green test, documented] the four-artifact sha256 regression**
- The plan places it in Task 3, but Task 1's reconcile already guaranteed temp-only outputs, so the test passed on first run against the existing implementation. Kept as the anti-clobber drift tripwire (its stated purpose), not claimed as RED evidence.

---

**Total deviations:** 4 documented (1 self-corrected naming slip, 1 Rule 1 test bug, 1 typecheck-constraint adjustment, 1 born-green pin)
**Impact on plan:** No scope creep — every change is inside the two planned files; all gates green.

## Issues Encountered

None beyond the deviations above. `gsd_run` CLI was unavailable in this environment — state/roadmap/requirements updates below were applied manually following the documented handler behaviors.

## Known Stubs

None. The 10-01 `reconcile: null` field is now populated by the gate; the `runner` seam is now exercised (its intended consumer). No placeholder data flows anywhere.

## Threat Flags

None — no security-relevant surface beyond the plan's threat model. All five mitigations are test-pinned: T-10-02-01 (four-flag temp outputs + sha256 regression), T-10-02-02 (subprocess owns counting; unparseable -> failed, never a fabricated pass), T-10-02-03 (empty-overlay env pin on reaudit), T-10-02-04 (done-only overlay eligibility), T-10-02-05 (timeouts + absorption).

## Next Phase Readiness

- 10-03 (Zenodo + strings): composes on the same service/runner discipline; nothing in this plan blocks it.
- 10-04 (data-manager screen): the mismatch banner reads `entry.reconcile` (declared/measured) + `event.problems` (`Train_mismatch_declared=N_measured=M`); the `g` binding calls `reaudit_baseline`; drill-down shows the `[reconcile]` log section.
- 10-05 (selection/env integration): `merge_presence(registries.load_n_audit(), download_queue.reconciled_rows())` is the exact snapshot-builder seam; `presence_for` stays untouched.

## Self-Check: PASSED

All three touched files exist on disk; all six plan commits are ancestors of HEAD (`de685b6`, `ee29add`, `f84376b`, `c15bc3a`, `3993efe`, `56a2e15`); `commits: 6` measured from the persisted ledger (`a186c43..56a2e15`).

---
*Phase: 10-data-manager-downloads-verification*
*Completed: 2026-10-12*
