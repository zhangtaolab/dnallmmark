---
phase: 13-dynamic-dispatch-core
verified: 2026-10-20T08:05:00Z
status: human_needed
score: 22/23 must-haves verified
covered_files:
  - .planning/phases/13-dynamic-dispatch-core/13-01-PLAN.md
  - .planning/phases/13-dynamic-dispatch-core/13-01-SUMMARY.md
  - .planning/phases/13-dynamic-dispatch-core/13-02-PLAN.md
  - .planning/phases/13-dynamic-dispatch-core/13-02-SUMMARY.md
  - Makefile
  - pipeline/dispatch_core.py
  - pipeline/run_sweep_shard.py
  - tests/test_dispatch_core.py
covered_digest: "v3:sha256:96315fc2348732a98fd51f97667d217c86250a44a4002b9e42a4eb13cd41bfab"
behavior_unverified: 1 # Count of PRESENT_BEHAVIOR_UNVERIFIED truths (present + wired, behavior not exercised); detailed below
overrides_applied: 0
behavior_unverified_items:
  - truth: "A cell whose child exits 0 without final_metrics.json in its cell dir is recorded failed, never completed (CR-02) — the exit-0-swallowed-failure branch"
    test: "Run a dispatch launch whose fake child returns exit code 0 but writes no final_metrics.json into its cell dir (e.g. a spawner returning FakeProc(0) with no artifact writes), then inspect the claim JSON and dispatch_state.json"
    expected: "The cell's claim state is 'failed' with error naming the missing final_metrics.json, counts.failed == 1, run_dispatch exits 1 — never state 'completed'"
    why_human: "The branch exists and is wired (dispatch_core.py:756-763) but no test in tests/test_dispatch_core.py drives it: every fake-child helper writes the metrics artifact on code==0 (make_child_spawner), every failure-path test uses a non-zero exit (SC2 uses -9) or a dispatcher-side exception (CR-04/WR-03 pins). Deleting the elif branch would leave the entire 101-test targeted suite green. The no-requeue (A2) half of this truth IS test-proven by the SC2 kill test; only the exit-0-no-metrics sub-branch is unexercised."
unverified_prohibition_flags: 8 # ADR-550 D3 autonomous mode: non-authoritative LLM-judge verdicts recorded below; human review recommended
human_verification:
  - test: "Manually drive the CR-02 exit-0-no-metrics path (single-command check: one dispatch launch over a tiny fake registry whose spawner returns code 0 and writes no artifacts)"
    expected: "Claim state 'failed' with the 'final_metrics.json is missing' error, counts.failed == 1, exit code 1 — a swallowed training failure never reads as completed"
    why_human: "Runtime state transition with no asserting test in the suite (mutation-survivable branch); presence checks cannot see it"
  - test: "Review the 8 prohibition verdicts in the Prohibition Review section (all judged HELD by the automated LLM pass — non-authoritative)"
    expected: "Confirm each MUST-NOT held: no GPU probing, no silent empty-matrix fallback, no lease/timeout claim protocol, no in-run requeue, no exit-0-without-artifact completion (see CR-02 item above), no directory-shape mode inference, frozen surfaces untouched, dry-run side-effect-free"
    why_human: "Judgment-tier prohibitions are flagged unverified by design in the plans (status: unverified, flagged: true); autonomous verify records non-authoritative verdicts only"
---

# Phase 13: 动态调度核心 (Dynamic Dispatch Core) Verification Report

**Phase Goal:** The orchestrator dispatches (model×dataset×seed) cells as a work queue over per-GPU workers with worker-independent cell outputs, an exactly-once claim ledger, and resume semantics proven under mid-cell kill — legacy static sharding coexists behind explicit mode declaration
**Verified:** 2026-10-20T08:05:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

All evidence below was gathered directly from the codebase and by running the suites in this
verification pass (not from SUMMARY claims). Note: the code-review fix loop landed 7 additional
commits after the plan SUMMARYs (CR-01..CR-04, WR-01..WR-03) — the current tree has 52 dispatch
tests (not the 41 the SUMMARYs describe); all statements below reflect the current HEAD.

### Observable Truths

ROADMAP Success Criteria are the contract; PLAN must-haves are merged under them (deduplicated).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Dispatch dry-run writes ONLY {root}/sweep_manifest.json — static projection (status "planned", cell_dir_for output_dirs) + orchestrator_mode "dispatch" marker; no lock/state/claims/cell dirs/children | ✓ VERIFIED | Dry-run branch `dispatch_core.py:1098-1168` returns before lock acquisition; `test_dispatch_dry_run_writes_only_plan_manifest` passed (asserts the full no-side-effect set incl. empty spawner calls) |
| 2 | SC1: Two consecutive dispatch dry-runs produce byte-identical manifests | ✓ VERIFIED | `test_dispatch_dry_run_is_byte_identical_across_runs` passed (copy-aside + sha256); `_write_json`/`_dump_json_handle` indent=4/sort_keys/ensure_ascii=False discipline at `dispatch_core.py:273-285` |
| 3 | SC1: Dispatch planned identity set equals static per-worker dry-run union (identity projection only) | ✓ VERIFIED | `test_dispatch_dry_run_identity_set_equals_static_union` passed; projection composes `run_sweep.enumerate_matrix` verbatim (`dispatch_core.py:1041-1048`) |
| 4 | SC2 (P1 acceptance): worker killed mid-cell + relaunch re-dispatches exactly that cell; every cell completes exactly once, no duplicates, no orphans | ✓ VERIFIED | `test_sc2_kill_test_resume_exactly_once` passed — run 2 spawn set == {killed cell}, rglob metrics count == 12, 12 claims all completed, per-cell spawn counts 1/2, no tmp residue, new run_id on the requeued claim. Behavioral test with on-disk evidence assertions |
| 5 | SC3: Cell artifacts land at worker-independent cell_dir_for paths under ONE shared root; no {root}-mgpu-w{i} siblings; no worker identity in claims/state | ✓ VERIFIED | Happy-path test asserts artifacts at `run_sweep.cell_dir_for` under the shared root with zero mgpu siblings; `build_argv(model, task, seed, str(context["root"]), ...)` at `dispatch_core.py:706-718` |
| 6 | SC3: A second claim on a live-claimed cell is structurally refused by O_EXCL (EEXIST) | ✓ VERIFIED | `claim_cell` uses `os.open(O_CREAT\|O_EXCL\|O_WRONLY, 0o644)` at `dispatch_core.py:309`, FileExistsError → None; `test_claim_cell_double_claim_structurally_refused` passed; worker loop skips on None (`dispatch_core.py:693-704`) |
| 7 | SC4/lock: a second dispatcher on a live-pid lock is refused loudly naming pid + run_id; a provably dead pid is reclaimed | ✓ VERIFIED | `acquire_dispatcher_lock` `dispatch_core.py:456-553`: os.kill(pid, 0) liveness, live/PermissionError → named refusal, ProcessLookupError/OverflowError/malformed → atomic-overwrite reclaim. Tests `test_lock_live_pid_refuses_naming_holder`, `test_lock_dead_pid_is_reclaimed`, `test_lock_malformed_content_is_reclaimed`, `test_lock_out_of_range_pid_reclaimed_not_crashed`, `test_lock_empty_fresh_window_refuses_inflight_writer`, `test_lock_empty_stale_window_is_reclaimed` all passed |
| 8 | CR-02/A2: a cell exiting 0 without final_metrics.json is recorded failed, never completed; failed cells NOT requeued within a live run | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Code present + wired (`dispatch_core.py:754-763`). The A2 no-requeue half IS test-proven (SC2: run 1 spawns 12, never re-spawns the failed cell, exits 1) and the code!=0 half is test-proven (-9). But the exit-0-without-metrics sub-branch has NO asserting test: every fake-child helper writes metrics on code==0; deleting the elif leaves all 101 tests green. See behavior_unverified_items + Human Verification |
| 9 | Empty ENUMERATED matrix refuses by name before any worker spawns; empty PENDING on relaunch prints nothing-to-do and exits 0 | ✓ VERIFIED | Zero-cell refusal before lock (`dispatch_core.py:1086-1096`); drained-root verdict (`dispatch_core.py:1246-1259`); `test_dispatch_zero_enumeration_refuses_before_lock` and `test_drained_root_relaunch_is_nothing_to_do` passed |
| 10 | Queue order deterministic (enumerate_matrix sorted() + apply_priority_order stable reorder); duplicate identities never appear | ✓ VERIFIED | `dispatch_core.py:1033-1048` composes run_sweep verbatim; `test_dispatch_queue_order_is_deterministic` + `test_claim_filename_deterministic_and_injective` passed |
| 11 | EDGE: --workers 1 drains the whole queue; empty registry/filter intersection refuses by name (never full-registry fallback) | ✓ VERIFIED | `test_dispatch_single_worker_drains_whole_queue`, `test_dispatch_zero_enumeration_refuses_before_lock`, strips-to-empty refusals at `dispatch_core.py:890-931` |
| 12 | EDGE: fresh root queues every cell; relaunch over drained root queues zero and exits 0 | ✓ VERIFIED | `test_drained_root_relaunch_is_nothing_to_do` passed; skip filter at `dispatch_core.py:1199-1208` |
| 13 | EDGE: relaunch skip set is a pure per-cell function — order-independent | ✓ VERIFIED | `relaunch_decision` (`dispatch_core.py:592-626`) reads only per-cell marker/claim; `test_skip_set_is_order_independent` passed |
| 14 | EDGE: --mode dispatch + --merge refused with a named problem before either mode runs | ✓ VERIFIED | `run_sweep_shard.py:1166-1173` ahead of the merge branch; `test_dispatch_merge_combination_refused` + `test_dispatch_merge_combo_refusal_reasserted` passed |
| 15 | The entire pre-existing tests/test_sweep_shard.py suite passes UNMODIFIED (static tripwire) | ✓ VERIFIED | `git diff 13b1b4c..HEAD -- tests/test_sweep_shard.py` EMPTY; 49 shard tests passed in this verification's run (101 total with dispatch) |
| 16 | Happy path: every enumerated cell runs as ONE child pinned to exactly one worker's CUDA_VISIBLE_DEVICES (MGPU-01) | ✓ VERIFIED | Worker loop `dispatch_core.py:644-835`: queue pop under lock → claim → spawn with env CUDA_VISIBLE_DEVICES=gpus[i], start_new_session, cwd=PIPELINE_DIR, stderr=STDOUT; `test_dispatch_happy_path_end_to_end` + `test_dispatch_spawn_kwargs_verbatim_discipline` + `test_dispatch_workers_are_not_model_bound` + `test_dispatch_gpus_override_tokens_forward_verbatim` passed |
| 17 | dispatch_state.json mode evidence written BEFORE any claim/spawn, atomically | ✓ VERIFIED | Write order at `dispatch_core.py:1193` and `:1208`; `test_dispatch_state_file_exists_before_any_spawn` (every spawn observes the file) passed; `_atomic_write_json` tmp+os.replace |
| 18 | SC4: absent --mode == static; explicit --mode static byte-identical (argv, roots, tee logs); static launches acquire no dispatch lock | ✓ VERIFIED | `--mode` flag `run_sweep_shard.py:373` (default "static"); `test_mode_static_explicit_matches_default`, `test_static_mode_explicit_pins_argv_roots_and_logs`, `test_static_launch_never_acquires_dispatch_lock`, `test_mode_flag_visible_in_help` passed; --help output confirmed live in this pass |
| 19 | SC4/MGPU-06: --merge refuses ANY dispatch-evidence root (base or worker; state file / ledger dir / manifest orchestrator_mode marker) with the named "needs no merge" error BEFORE any copy; static no-evidence merge unchanged | ✓ VERIFIED | `_root_has_dispatch_evidence` (`run_sweep_shard.py:728-775`, run-recorded markers only) wired into run_merge collect-all (`:879-884`) before the copy pass; `_dispatch_merge_refusal` wording at `:778-785`; marker-matrix + 3 refusal tests + happy-path control passed |
| 20 | Dry-run priority/peft/variant shapes: priority permutes without changing the set; peft rides alias identities; config_variant joins every cell | ✓ VERIFIED | `test_dispatch_dry_run_priority_reorders_planned_cells`, `test_dispatch_dry_run_peft_alias_and_variant_flag_shapes`, `test_dispatch_peft_lane_enumerates_and_spawns_under_alias` passed; sweep_flags present-keys-only mirror at `dispatch_core.py:1119-1137` |
| 21 | Validation refusals: variant×peft named refusal; missing --seeds argparse code 2; empty --models named refusal; subset map pre-validated (WR-01); --from-failures honored loudly (CR-01) | ✓ VERIFIED | Mirror block `dispatch_core.py:933-969`, WR-01 at `:1019-1031`, CR-01 at `:1049-1085`; corresponding 6 tests passed |
| 22 | SC5: Full CPU gates green; zero CI changes; zero N>1 assumptions | ✓ VERIFIED | This pass ran: targeted pytest 101/101, `make lint` "All checks passed!" (file list includes pipeline/dispatch_core.py), `make typecheck` clean, node lane 26 pass / 0 fail; `git hash-object .github/workflows/ci.yml` == 33d2252eb594e0faecece9e8015a332d8d6479ef (plan-time baseline); no torch/GPU-count refs in the dispatch tests (CUDA_VISIBLE_DEVICES asserted as operator strings). Full `make test` carries 7 documented pre-existing failures (6 root-user chmod artifacts + 1 stale v1.2.0 version pin, commit 9a39bde verified ancestor of the 13-02 plan base fea5d8d; none of the 3 failing test files import any phase module) — recorded in deferred-items.md, outside the phase's blast radius per the 13-02 verification contract |
| 23 | pipeline/dispatch_core.py joins the ruff lint list via a Makefile-only PHASE13_MODULES existence guard; ci.yml untouched | ✓ VERIFIED | `Makefile:177-181` (PHASE13_MODULES foreach/wildcard) appended to the lint file list at `:191`; live `make lint` invocation shows pipeline/dispatch_core.py in the ruff command and exits 0 |

**Score:** 22/23 truths verified (1 present, behavior-unverified)

### Prohibition Review (ADR-550 D3 — autonomous mode: NON-AUTHORITATIVE LLM-judge verdicts)

All 8 plan-declared prohibitions judged HELD by the automated pass; flagged for human review per
the plans' `status: unverified, flagged: true`. Verdict evidence class noted per item.

| # | Prohibition (condensed) | Judge verdict | Evidence |
|---|------------------------|---------------|----------|
| 1 | No GPU device-count probing (no nvidia-smi/torch; operator-owned GPU strings) | HELD | dispatch_core imports are stdlib + siblings only (`:85-100`); only nvidia-smi mentions are help/docstring text saying "never probes"; default gpus from --workers count, not devices |
| 2 | No silent empty-matrix → full-registry degradation | HELD | Zero-cell named refusal `:1086-1096`; strips-to-empty refusals `:890-931`; CR-01 filter never silently no-ops (tests passed) |
| 3 | No lease/timeout claim protocol — reclaim rests solely on the singleton O_EXCL lock | HELD | `relaunch_decision` has no time component; claims reclaim via stale-tag overwrite only. Note: `_LOCK_WRITE_GRACE_SECONDS` (`:133`) applies ONLY to empty/unreadable locks inside the create-to-write window (CR-02 review fix) — a parseable lock with a live pid refuses regardless of age, so it is not a lease |
| 4 | No in-run requeue of failed cells (A2) | HELD | No requeue path in `_spawn_worker`; exit-1 message names Phase 14 MGPU-04; SC2 proves run 1 never re-spawns the failed cell |
| 5 | No exit-0-without-artifact completion (CR-02) | HELD (code) / branch UNTESTED | Code enforced at `:756-763`; no asserting test drives the branch — see truth #8 and the human-verification item |
| 6 | No directory-shape mode inference (merge refusal reads run-recorded evidence only) | HELD | `_root_has_dispatch_evidence` reads exactly the three markers (`run_sweep_shard.py:756-775`) |
| 7 | ci.yml and tests/test_sweep_shard.py untouched | HELD (deterministic) | `git diff 13b1b4c..HEAD` empty on both; ci.yml blob hash equals the plan-time baseline — test-tier-grade evidence |
| 8 | Dry-run writes no state/lock/claims/cell dirs | HELD | Branch returns before lock (`dispatch_core.py:1098-1168`); `test_dispatch_dry_run_writes_only_plan_manifest` asserts the full absence set (passed) |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|-----------|--------|---------|
| `pipeline/dispatch_core.py` | The dispatch engine (re-parse, validation mirror, enumeration+priority, O_EXCL lock/ledger, per-GPU workers, state writer, run_dispatch) | ✓ VERIFIED | 1,346 lines; `def run_dispatch` present (`:838`); all plan-named symbols present; gsd-tools verify.artifacts: passed, no issues |
| `tests/test_dispatch_core.py` | SC2/SC3 + happy-path + naming-freeze + validation-refusal + resume suites over the injectable seams | ✓ VERIFIED | 2,145 lines, 52 tests, all passing; verify.artifacts passed |
| `pipeline/run_sweep_shard.py` | --mode flag, mode routing, dispatch×merge refusal, merge-evidence check | ✓ VERIFIED | verify.artifacts passed; routing `:1166-1184`, evidence helper `:728-785`, collect-all wiring `:879-884` |
| `Makefile` | PHASE13_MODULES existence-guard lint slot | ✓ VERIFIED | verify.artifacts passed; `:177-181` + lint list `:191` |

### Key Link Verification

The gsd-tools `verify.key-links` verb resolved 2/4 (13-01) and 0/3 (13-02) — the unresolved
entries carry "from: must be a relative file path" (descriptive labels like "dispatcher claim
step" cannot be resolved to files by the tool). All 7 links were therefore verified manually:

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| pipeline/dispatch_core.py | pipeline/run_sweep.py | sibling imports (enumerate_matrix, apply_priority_order, build_argv, cell_dir_for, _manifest_payload, _write_json, RESUME_MARKER, METRICS_NAME, ...) | ✓ WIRED | `import run_sweep` (`:99`); all named symbols used at `:617, 680, 706, 980-982, 1041-1048, 1150-1161` |
| pipeline/run_sweep_shard.py | pipeline/dispatch_core.py | main() routes mode=="dispatch" to run_dispatch after the merge branch | ✓ WIRED | Lazy import + `dispatch_core.run_dispatch(args, passthrough, spawner=spawner, clock=clock)` (`:1181-1184`) |
| dispatch_core worker loop | run_sweep.build_argv | per-cell argv with SHARED root + verbatim static kwargs | ✓ WIRED | `:706-738` — build_argv(str(context["root"])), start_new_session=True, cwd=PIPELINE_DIR, env CUDA_VISIBLE_DEVICES, stdout=tee, stderr=STDOUT |
| dispatcher claim step | filesystem ledger | O_EXCL claim BEFORE spawn; finalize after wait() + artifact check | ✓ WIRED | claim at `:690-704` precedes spawner at `:727`; finalize at `:770` after the CR-02 check |
| dispatch dry-run branch | run_sweep projection | _manifest_payload/_write_json/cell_dir_for — one manifest shape across modes | ✓ WIRED | `:1150-1161` |
| run_sweep_shard run_merge | dispatch evidence on disk | markers-only helper, collect-all refusal before copy | ✓ WIRED | `:879-884` before the manifest/copy stages |
| Makefile lint target | pipeline/dispatch_core.py | PHASE13_MODULES existence guard | ✓ WIRED | Live `make lint` ruff command includes pipeline/dispatch_core.py; exit 0 |

### Data-Flow Trace (Level 4)

No UI rendering in this infra phase; the "data" is the on-disk protocol files. Every rendered/written
value traces to a real source (registry enumeration, real subprocess outcomes, real pid/run ids):

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| dispatch dry-run manifest | planned_records | run_sweep.enumerate_matrix over the real registry | ✓ | ✓ FLOWING |
| claim JSONs | cell key, lane flags, child_pid, state | enumerated cells + real proc.pid + real exit codes | ✓ | ✓ FLOWING |
| dispatch_state.json | counts (total/completed/failed/skipped), run_id | len(cells) + real per-cell outcomes | ✓ | ✓ FLOWING |
| worker tee logs | child stdout | real spawn seam (injected fakes in tests, Popen in prod) | ✓ | ✓ FLOWING |

No static returns, hardcoded payloads, or mock-fed values found on any write path.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Targeted suites (dispatch + static tripwire) | `.venv/bin/python -m pytest ../tests/test_dispatch_core.py ../tests/test_sweep_shard.py -q` (from pipeline/) | 101 passed in 1.41s | ✓ PASS |
| SC2 kill/resume exactly-once (named behavioral test) | included above — `test_sc2_kill_test_resume_exactly_once` | passed with on-disk exactly-once assertions | ✓ PASS |
| --mode flag surface | `run_sweep_shard.py --help` | shows `--mode {static,dispatch}` with bilingual-mode English help | ✓ PASS |
| Lint gate incl. dispatch_core | `make lint` | "All checks passed!" | ✓ PASS |
| Type gate | `make typecheck` | "All checks passed!" | ✓ PASS |
| Node lane | `node --test tests/js/*.test.js` | pass 26 / fail 0 | ✓ PASS |
| ci.yml zero-change pin | `git hash-object .github/workflows/ci.yml` | 33d2252eb594e0faecece9e8015a332d8d6479ef (== baseline) | ✓ PASS |
| Frozen surfaces | `git diff 13b1b4c..HEAD -- pipeline/run_sweep.py pipeline/run_finetune.py tests/test_sweep_shard.py .github/workflows/ci.yml` | empty | ✓ PASS |
| Full make test | not re-run in this pass (~30 min lane) | 7 documented pre-existing failures (deferred-items.md); provenance spot-verified: 9a39bde IS ancestor of plan base fea5d8d; failing TUI files import no phase module | ✓ PASS (per the 13-02 gate contract: only recorded baseline members fail) |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` declared by the plans or present in the repo for
this phase; the phase's runnable checks are the pytest/lint/typecheck/node lanes above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MGPU-01 | 13-01, 13-02 | Work-queue dispatch, one GPU per cell, deterministic dry-run-provable enumeration | ✓ SATISFIED | Truths 1-3, 9-11, 16, 17, 20, 21; happy-path/dry-run/queue-order suites passed |
| MGPU-02 | 13-01 | Worker-independent outputs, exactly-once O_EXCL ledger, kill-proven resume | ✓ SATISFIED | Truths 4-8, 12, 13; SC2/SC3/lock/skip suites passed (CR-02 sub-branch untested — flagged, does not undermine the requirement's test-pinned core) |
| MGPU-06 | 13-02 | Static coexistence behind explicit mode, loud mixed-mode merge refusal, dispatch roots need no merge | ✓ SATISFIED | Truths 14, 18, 19, 23 + unmodified 49-test tripwire |

Orphaned requirements: none — REQUIREMENTS.md maps exactly MGPU-01/02/06 to Phase 13
(MGPU-03/04/05 → Phase 14, VAL-* → 15, TUI-* → 16).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| pipeline/dispatch_core.py | 340, 342 | `return {}` in `read_claim` | ℹ️ Info (not a stub) | Documented tolerant-read contract: unreadable/malformed claim → {} which never equals "completed", so corrupt claims requeue (the honest direction) |
| pipeline/dispatch_core.py | 133 | `_LOCK_WRITE_GRACE_SECONDS = 5.0` time-based guard | ℹ️ Info (not a lease) | Applies only to empty/unreadable locks in the create-to-write window (review CR-02 fix); a parseable lock with a live pid refuses regardless of age — prohibition 3 intent held |

Debt markers (TBD/FIXME/XXX): none in any phase-modified file. TODO/HACK/PLACEHOLDER: none.
Disabled/skipped tests: none in either test file. No console-log-only implementations.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_dispatch_core.py | MGPU-01/02/06 | 52 | 0 | 0 | Behavioral/value (SC2 asserts per-cell spawn counts, on-disk artifact/claim counts, state dicts; byte-identity via sha256) | OK |
| tests/test_sweep_shard.py | static tripwire | 49 | 0 | 0 | Behavioral/value | OK — file byte-identical to pre-phase HEAD |

Expected-value provenance: assertions compare against `run_sweep.enumerate_matrix` outputs over a
locally-built fake registry — an independent oracle (the composed dependency), not the system under
test's own recorded output. Not circular. One coverage gap found (CR-02 branch, truth #8) —
WARNING-class, routed to human verification rather than a blocker: the code is present, wired, and
mirror-reviewed; only the test is missing.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts (gsd-tools
check.decision-coverage-verify): 16/16 honored, 0 not honored.

### Human Verification Required

Infrastructure/foundation phase — auto-pass UAT applies except for the behavior-unverified truth
and the flagged prohibitions below (1 + 1 items):

### 1. CR-02 exit-0-swallowed-failure branch

**Test:** Run one dispatch launch over a tiny fake registry whose injected spawner returns exit
code 0 but writes no final_metrics.json into the cell dir (a ~10-line pytest after the
`make_child_spawner` idiom, or a manual `run_cli` probe).
**Expected:** The cell's claim finalizes to state "failed" with the "final_metrics.json is missing"
error, dispatch_state.json counts failed == 1, and run_dispatch exits 1 — a swallowed training
failure never reads as completed (the false-leaderboard-number hazard).
**Why human:** The branch is present and wired (`dispatch_core.py:756-763`) but no existing test
drives it — every fake-child helper writes metrics on code==0, and every failure-path test uses a
non-zero exit or a dispatcher-side exception. Deleting the branch leaves the full targeted suite
green (mutation-survivable), so presence checks cannot certify the transition.

### 2. Prohibition verdicts (8 flagged, all auto-judged HELD — non-authoritative)

**Test:** Review the Prohibition Review table above.
**Expected:** Confirm each MUST-NOT held in the code (evidence cited per row; item 5 overlaps
with check #1 above).
**Why human:** Plans declare the prohibitions `status: unverified, flagged: true`; under
autonomous verification these carry non-authoritative LLM-judge verdicts only.

### Gaps Summary

No gaps_found: no truth FAILED, all artifacts exist/substantive/wired with real data flow, all
key links verified, no blockers or unreferenced debt markers, all three requirements satisfied
with strong behavioral evidence (SC2 kill test included). The single open item is evidentiary,
not functional: the CR-02 exit-0-without-metrics branch — present, wired, and enforced in code,
with the no-requeue sibling semantics test-proven — lacks a directly-asserting test, so it is
classified PRESENT_BEHAVIOR_UNVERIFIED and routed to human verification. An optional one-test
addition (fake child returning 0 with no artifact writes) would close it mechanically.

The full-suite environmental failures (6 root-user chmod artifacts, 1 stale v1.2.0 version pin)
are pre-existing, provenance-verified, and tracked in
`.planning/phases/13-dynamic-dispatch-core/deferred-items.md` — maintainer-owned, out of this
phase's blast radius.

---

_Verified: 2026-10-20T08:05:00Z_
_Verifier: Claude (gsd-verifier)_
