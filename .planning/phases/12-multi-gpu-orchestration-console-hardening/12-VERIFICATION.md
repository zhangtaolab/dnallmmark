---
phase: 12-multi-gpu-orchestration-console-hardening
verified: 2026-10-13T15:10:52Z
status: human_needed
score: 4/5 must-haves verified
covered_files: [".planning/WINDOWS.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-01-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-01-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-02-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-02-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-03-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-03-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-04-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-04-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-SUMMARY.md", "Makefile", "README.md", "dnallm-mark/css/progress.css", "dnallm-mark/css/styles.css", "dnallm-mark/data/progress/.gitkeep", "dnallm-mark/js/config.js", "dnallm-mark/js/data.js", "dnallm-mark/js/progress.js", "dnallm-mark/progress.html", "docs/multi-gpu.md", "pipeline/run_sweep_shard.py", "script/gen_progress.py", "tests/js/progress-page.test.js", "tests/test_sweep_shard.py", "tests/tui/__snapshots__/data_manager.svg", "tests/tui/__snapshots__/env_check.svg", "tests/tui/__snapshots__/monitor_empty.svg", "tests/tui/__snapshots__/monitor_running.svg", "tests/tui/__snapshots__/run_config.svg", "tests/tui/__snapshots__/selection_datasets.svg", "tests/tui/__snapshots__/selection_models.svg", "tests/tui/__snapshots__/wizard.svg", "tests/tui/test_gen_progress.py", "tests/tui/test_pilot_monitor.py", "tests/tui/test_pilot_run_config.py", "tests/tui/test_snapshots.py", "tui/screens/run_config.py", "tui/strings.py"]
covered_digest: "v3:sha256:9dfee6d8fcb15d5bcdedce42f097127840fa9f8b60d1e6333e7eab208a7d1a9a"
behavior_unverified: 1 # SC5's maintainer-review clause — present + wired + automation-green, but visual review is human-only by the phase's own D-03 gate
overrides_applied: 0
behavior_unverified_items:
  - truth: "SC5 — canonical screens pinned by SVG goldens reviewed and committed by the maintainer"
    test: "Open each of the 8 committed SVGs (tests/tui/__snapshots__/{env_check,selection_models,selection_datasets,data_manager,run_config,monitor_running,monitor_empty,wizard}.svg) in a browser/editor and compare against the 12-UI-SPEC corpus table (per-screen fixture state, 120x40)"
    expected: "Every golden shows the intended canonical screen state (marks, params values, five glyphs, stats/ETA, advisories) — visual rightness, not byte-stability; automation proves byte-stability only (the 12-03-SUMMARY human_judgment gate says exactly this)"
    why_human: "Byte-identical string comparison cannot see whether the frozen SVG content is the RIGHT picture; the phase's D-03 decision defines maintainer eyeball review as the trust gate before the corpus is relied on"
human_verification:
  - test: "D-03 maintainer review of the 8 committed SVG goldens in tests/tui/__snapshots__/ against the 12-UI-SPEC corpus table"
    expected: "All 8 goldens visually correct for their canonical screen states; any wrong-looking golden regenerated via make snapshot-update and re-reviewed before the corpus is trusted"
    why_human: "The golden tests prove byte-stability and drift-redness (determinism + sensitivity both green), not visual rightness — the phase's own D-03 gate makes maintainer review the deciding evidence"
  - test: "WINDOWS #21 (open): execute the 9-step N=2 multi-GPU smoke on the OTHER machine per docs/multi-gpu.md §'The 9-step N=2 multi-GPU smoke procedure' (bounded: 2 models x 1 task x 1 seed x 1 epoch, iDNA_ABF_datasets__5mC) and record outcomes"
    expected: "Steps 0-9 as documented: disjoint dry-run manifests, 2 workers with CUDA_VISIBLE_DEVICES=0/1, independent TUI views, isolation on failure, --from-failures re-run touching only the failed worker's root, --merge with SHA256-verified output, web mirror over worker roots then merged root, export equivalence, cleanup"
    why_human: "This GB10 host is single-GPU and dev/test only (D-05 machine-roles constraint); the N=2 validation is by design a maintainer-executed procedure on other hardware — not executor-executable, not CI-able. The tracking entry (WINDOWS #21, kind unrun-verify, status open, counters 15/21) was verified to exist and be open"
---

# Phase 12: Multi-GPU Orchestration & Console Hardening Verification Report

**Phase Goal:** With single-GPU validated, throughput scales out — CLI-invocable static model sharding × CUDA_VISIBLE_DEVICES with per-worker monitoring, artifact merge, and isolated failure re-run, plus the documented DDP-vs-sharding applicability decision — and the console ships its release extras: a static read-only web progress mirror and maintainer-verified snapshot goldens pinning the canonical screens
**Verified:** 2026-10-13T15:10:52Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Must-haves merged from ROADMAP Success Criteria (the contract) and the 5 PLAN frontmatters (12-01..12-05 add plan-level detail; the plan truths restate and detail the SCs — no scope reduction found; plan prohibitions checked separately below).

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | SC1: Multi-worker orchestration invokable from the CLI (not TUI-only): N workers over disjoint static model shards with CUDA_VISIBLE_DEVICES isolation, marker-skip as the only concurrency guard | ✓ VERIFIED | `pipeline/run_sweep_shard.py` (1252 lines, substantive): `lpt_shard` pure fn (L263-294, both tie-breaks + 0.0 weight coercion), `worker_root()` single naming authority (L200-216), spawn kwargs verbatim launcher discipline + exactly one added env key `CUDA_VISIBLE_DEVICES` (L1201-1212, `start_new_session=True`, `cwd=run_sweep.PIPELINE_DIR`, LIST argv, tee sibling log), collect-all validation (L1070-1154: workers/gpus-arity/models/registry-join/empty-shard/frozen-root-collision), aggregated exit 0-iff-all-0 with verdict table (L1224-1248). Behavioral: `tests/test_sweep_shard.py` 49/49 passed this verification incl. `test_n1_degenerate_real_subprocess_smoke` (real subprocess, 0.39s), `test_dry_run_disjointness_in_process`, `test_real_two_worker_dry_run_subprocess_chain`, `test_worker_argv_and_spawn_kwargs_under_default_gpus`. D-07 held: `git log` shows `run_sweep.py` last touched at 4f4367a (11-01), `run_finetune.py` untouched in Phase 12. No lock/claim/port machinery, no nvidia-smi, no device-count assumption (grep clean; module docs state the D-05/D-06 contracts) |
| 2 | SC2: The operator sees per-worker monitoring views, artifacts merge across workers, and a failed worker's shard re-runs in isolation without touching healthy workers | ✓ VERIFIED | Delta A (zero monitor code): `tests/tui/test_pilot_monitor.py::test_delta_a_discovered_pane_renders_worker_roots_independently` (L1718) PASSED this verification; `tui/screens/monitor.py` last touched at 3fa3fea (fix(11)) — untouched in Phase 12. Merge: `--merge` mode (run_merge L715-1039) with MERGE_ALLOWLIST constant, `_copy_verified` hash-copy-rehash-compare, `_rewrite_output_dir` boundary-guarded prefix swap, lane-equality refusal (Pitfall 6), stale-cell guard (WR-03); `test_merge_happy_path_copies_allowlist_and_rewrites` + `test_merged_root_is_consumer_equivalent` (export_runs.load_run_records union equivalence) + `test_merge_leaves_worker_roots_immutable` PASSED. Isolation re-run: `test_d08_from_failures_rerun_is_isolated_to_w0` PASSED (exactly-once re-attempt, w1 mtimes unchanged) |
| 3 | SC3: The DDP (torch-run data splitting) vs model-sharding applicability decision is documented and landed — single-large-model acceleration vs multi-model throughput | ✓ VERIFIED | `docs/multi-gpu.md` (249 lines) §"The decision: model sharding vs DDP" carries the decision matrix (what accelerates / code coupling incl. the `run_finetune.py:1357`/`:1542` WORLD_SIZE/LOCAL_RANK seam citation / coverage / honest limits / concurrency guarantee) + §适用场景 guidance (62-model sweeps → sharding; single-model frontier → DDP future) + explicit "the matrix above closes the DDP question by deciding it". README one-line link verified at README.md:122 |
| 4 | SC4: A read-only web progress mirror generated from sweep artifacts lets the team follow progress in a browser — static files only, no backend | ✓ VERIFIED | `script/gen_progress.py` (250 lines) imports `tui.services.sweep_monitor` (L92) and serializes its dataclasses (never re-walks/re-derives; D-05 same-source), frozen contract (version/generated_at/sweeps/cells; newest_mtime absent), byte-stable JSON (sort_keys/indent4/ensure_ascii=False), `main(argv=None, now=None)` injected clock; `tests/tui/test_gen_progress.py` 8/8 PASSED. Page: `dnallm-mark/progress.html` (38 lines, zero CDN scripts — grep verified), `js/progress.js` ProgressPage house controller (generated_at rendered VERBATIM from JSON L372-377), `css/progress.css` (71 lines); site integration one-liners verified: NAV_LINKS Progress entry (config.js:70), DataAPI.loadProgress (data.js:113), styles.css @import (L25). `node --test tests/js/progress-page.test.js` PASSED (fail 0). Data dir intentionally sample-free (.gitkeep only — the no-fabricated-data prohibition held) |
| 5 | SC5: Canonical screens are pinned by Textual snapshot SVG goldens reviewed and committed by the maintainer, failing CI CPU-side on visual regression | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Automation half VERIFIED: `tests/tui/test_snapshots.py` (912 lines) — 8 golden tests + determinism + sensitivity, 10/10 PASSED this verification (5.87s); 8 SVGs committed in `tests/tui/__snapshots__/`; `make snapshot-update` is the sole regeneration path (Makefile:130-132) and CI compares-only. The "maintainer-reviewed" clause is human-only by the phase's own D-03 gate (12-03-SUMMARY marks it `human_judgment: true` — "automation proves byte-stability, not visual rightness") — routed to Human Verification below, NOT marked verified by code |

**Score:** 4/5 truths verified (1 present, behavior-unverified: the SC5 maintainer-review clause)

### Plan-Prohibition Checks (negative must-haves)

| Prohibition | Status | Evidence |
| --- | --- | --- |
| 12-01: no edit to run_sweep.py / run_finetune.py; pipeline/ gains exactly one new file | ✓ HELD | git log: both files' last commits predate Phase 12; new pipeline file is run_sweep_shard.py only |
| 12-01: no lock/claim-file/port machinery; marker-skip only guard | ✓ HELD | grep for fcntl/flock/lockfile/socket/.bind in run_sweep_shard.py — no hits (docstring text only) |
| 12-01: no nvidia-smi probing / GPU enumeration / N>1 assumption | ✓ HELD | grep clean; gpus are operator-owned strings, arity-validated only (WR-01 fix confirmed in code at `_parse_gpus`) |
| 12-02: zero backend, zero CDN on new page, zero new deps | ✓ HELD | progress.html has no CDN script tags (grep); node lane pins zero-CDN; no dependency changes |
| 12-03: no fix at wrong layer; selection.py / styles.tcss byte-identical; no new bindings | ✓ HELD | `git log` on selection.py shows no Phase-12 commits; working-tree diff empty; the fix is the one sanctioned `dismiss()` override (L599-615) |
| 12-03: no new snapshot-plugin/syrupy/cairosvg install, string equality is the compare | ✓ HELD | test_snapshots.py docstring documents the resolver-blocked fallback lane; no pyproject/uv.lock change in Phase-12 commits |
| 12-04: no symlink/move merge; copy + SHA256 only | ✓ HELD | `_copy_verified` uses shutil.copyfile + sha256 compare (L544-573); no symlink/os.rename/shutil.move in merge path |
| 12-04: no orchestrator convenience flags beyond --merge/--include-checkpoints; no run_sweep edits | ✓ HELD | parse_args owns exactly the 7 flags; D-08 re-run is the documented one-liner run_sweep command (docs/multi-gpu.md §4) |
| 12-05: zero production-code changes in plan 05; never execute N=2 GPU procedure | ✓ HELD | 12-05 commits (a9a7d77, c53b92d, 44db88d) touch tests + .planning only; no real training run |

### Required Artifacts

All plan-declared artifacts manually verified at three levels (the `verify.artifacts` CLI verb parsed 0/0 — the plans use prose-style artifact strings rather than the structured `{path:}` shape — so Levels 1-3 were performed directly; results below are the authoritative check).

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `pipeline/run_sweep_shard.py` | NEW — launch + merge orchestrator | ✓ VERIFIED | 1252 lines; exists, substantive, wired (imported by its 49-test suite; Makefile PHASE12_MODULES lint guard L174) |
| `tests/test_sweep_shard.py` | NEW — tier-1 + merge + isolation + N=1 suites | ✓ VERIFIED | 1662 lines; 49/49 pass (run this verification) |
| `script/gen_progress.py` | NEW — scanner-serializing generator | ✓ VERIFIED | 250 lines; imports sweep_monitor L92; 8/8 golden tests pass |
| `tests/tui/test_gen_progress.py` | NEW — golden-JSON tests | ✓ VERIFIED | 382 lines; 8/8 pass |
| `dnallm-mark/progress.html` / `js/progress.js` / `css/progress.css` | NEW — frozen UI-SPEC page | ✓ VERIFIED | 38/427/71 lines; no CDN; house controller pattern |
| `js/config.js`, `js/data.js`, `css/styles.css` | one-line site edits | ✓ VERIFIED | NAV_LINKS L70, loadProgress L113, @import L25 |
| `tests/js/progress-page.test.js` | NEW — DOM-less JS lane | ✓ VERIFIED | 150 lines; node --test fail 0 |
| `tui/screens/run_config.py` | EDIT — delta B only | ✓ VERIFIED | `_PickerReturnModal` L580 + 5 re-parents + `_GateConfirmModal` L804; B1/B2 tests pass |
| `tests/tui/test_pilot_run_config.py` | EDIT — B1-B5 Pilot tests | ✓ VERIFIED | test_b1_* / test_b2_* family present (L1628+); spot-run passed |
| `tests/tui/test_snapshots.py` | NEW — harness + 8 goldens + determinism/sensitivity | ✓ VERIFIED | 912 lines; 10/10 pass |
| `tests/tui/__snapshots__/*.svg` (8) | NEW — committed corpus | ✓ VERIFIED | all 8 present (29-68KB each); compared by the passing golden tests |
| `Makefile` | lint guard + snapshot-update | ✓ VERIFIED | PHASE12_MODULES L174 (run_sweep_shard + gen_progress via wildcard guard); snapshot-update L132 |
| `docs/multi-gpu.md` | NEW — D-04 decision doc | ✓ VERIFIED | 249 lines; decision matrix, runbook, killpg, E2' boundary, machine roles, 9-step procedure |
| `README.md` | one-line link | ✓ VERIFIED | L122 |
| `tests/tui/test_pilot_monitor.py` | EDIT — delta A proof | ✓ VERIFIED | delta A test L1718 passes |
| `.planning/WINDOWS.md` | entry 21 unrun-verify | ✓ VERIFIED | row 38: kind unrun-verify, status open; frontmatter open_count 15 / total 21 |

### Key Link Verification

Manual wiring verification (the `verify.key-links` CLI verb parsed 0/0 for the same prose-shape reason; each link below was traced in code).

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| run_sweep_shard | run_sweep + registry_loader | sibling imports | ✓ WIRED | L181-182; WORKER_SCRIPT = run_sweep.PIPELINE_DIR / "run_sweep.py" |
| worker argv | run_sweep.py --models/--output-root | LIST argv + verbatim passthrough | ✓ WIRED | L1179-1187; kwargs proofs test passed |
| worker env CUDA_VISIBLE_DEVICES | torch | verbatim inheritance chain | ✓ WIRED | L1205-1209; spawn-kwargs test passed (incl. --gpus "2,5" per-index) |
| gen_progress | tui.services.sweep_monitor | import + dataclass serialization | ✓ WIRED | L92, L218-221; import-lock keeps scanner textual-free |
| gen_progress --output | dnallm-mark/data/progress/sweep.json → DataAPI.loadProgress → ProgressPage.loadData | fetch chain | ✓ WIRED | data.js:113 loads './data/progress/sweep.json'; progress.js:100 loadData; golden tests + JS lane green |
| NAV_LINKS | site-wide navbar | js/navbar renders CONFIG.NAV_LINKS | ✓ WIRED | config.js:70 entry appended; navbar module unchanged |
| _PickerReturnModal.dismiss | #cfg-picker refocus | call_after_refresh(picker.focus) | ✓ WIRED | run_config.py:599-615; B1/B2 tests passed |
| test_snapshots | export_screenshot → SVGs | UTF-8 string equality | ✓ WIRED | L782-816; 10/10 passed |
| make snapshot-update | regeneration entry | module --regenerate block | ✓ WIRED | Makefile:132 → test_snapshots.py main block L895+ |
| --merge | worker_root() (12-01 shared fn) | one naming authority | ✓ WIRED | run_merge L790 reuses worker_root |
| merged root | export_runs / sweep_monitor / gen_progress | consumer equivalence | ✓ WIRED | test_merged_root_is_consumer_equivalent PASSED |
| docs step 7 | script/gen_progress.py | mirror command in runbook | ✓ WIRED | docs/multi-gpu.md §6 |
| WINDOWS #21 | docs procedure → 12-05-SUMMARY | one thread | ✓ WIRED | all three verified present; entry open |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | ---|
| progress.html page | sweep.json payload | gen_progress → sweep_monitor.full_scan/stats/cells_view over real artifact roots | Yes — scanner reads real run_record/manifest trees; golden tests pin the serialized shape over fixture trees; the committed site data dir is deliberately sample-free (.gitkeep, no fabricated values — prohibition held) | ✓ FLOWING |
| gen_progress.py | generated_at | injected/real clock, ISO-8601 UTC | Yes — rendered verbatim by the page (progress.js L372-377), never a client clock | ✓ FLOWING |
| run_sweep_shard verdict table | failed-cell count | worker root sweep_failures.json | Yes — `_failed_cell_count` reads the real file (L454-473); verdict-table test passed over fixture failures | ✓ FLOWING |
| merged manifest | cells/failures unions | per-worker manifests + verified copies | Yes — consumer-equivalence test proves load_run_records(merged) == union of workers | ✓ FLOWING |

### Behavioral Spot-Checks

Run this verification as single named tests (never the full workspace suite; module suites run at most once each).

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| N=1 real-subprocess orchestrator smoke (real run_sweep child, frozen root, exit 0) | `pytest tests/test_sweep_shard.py::test_n1_degenerate_real_subprocess_smoke -q` | 1 passed in 0.39s | ✓ PASS |
| Dry-run disjointness invariant (pairwise-disjoint output_dirs, union == unsharded) | `pytest tests/test_sweep_shard.py::test_dry_run_disjointness_in_process -q` | passed | ✓ PASS |
| D-08 isolated failure re-run (only w0 written; w1 mtimes unchanged) | `pytest tests/test_sweep_shard.py::test_d08_from_failures_rerun_is_isolated_to_w0 -q` | passed | ✓ PASS |
| Spawn kwargs proofs (sessions, cwd, env CUDA_VISIBLE_DEVICES per index, LIST argv) | `pytest tests/test_sweep_shard.py::test_worker_argv_and_spawn_kwargs_under_default_gpus -q` | passed | ✓ PASS |
| Merge happy path + consumer equivalence + worker-root immutability | `pytest ...::test_merge_happy_path_copies_allowlist_and_rewrites ::test_merged_root_is_consumer_equivalent -q` | 3 passed | ✓ PASS |
| Full orchestrator module (LPT, validation, aggregation, merge, edge probes) | `pytest tests/test_sweep_shard.py -q` (once) | 49 passed in 0.42s | ✓ PASS |
| Snapshot goldens: determinism + sensitivity + monitor_running compare | `pytest tests/tui/test_snapshots.py -q` (once, full module) | 10 passed in 5.87s | ✓ PASS |
| Delta A: N-root discovered table renders worker roots independently | `pytest tests/tui/test_pilot_monitor.py::test_delta_a_discovered_pane_renders_worker_roots_independently -q` | passed in 0.70s | ✓ PASS |
| Delta B: modal dismiss refocuses picker; digits navigate immediately | `pytest tests/tui/test_pilot_run_config.py::test_b1_preview_modal_esc_refocuses_picker ::test_b2_digit_navigates_immediately_after_preview_dismiss -q` | 2 passed | ✓ PASS |
| gen_progress golden contract over fixture trees | `pytest tests/tui/test_gen_progress.py -q` (once) | 8 passed | ✓ PASS |
| Progress page JS lane (zero-CDN, no timers, .gitkeep-only) | `node --test tests/js/progress-page.test.js` | fail 0 | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes are declared by this phase's plans or summaries; the phase's verification contract is pytest + node lanes (executed above). SKIPPED (no probes declared).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| MGPU-01 | 12-01, 12-05 | CLI-invocable model sharding × CUDA_VISIBLE_DEVICES multi-worker static orchestration | ✓ SATISFIED | Truth 1 (SC1) evidence |
| MGPU-02 | 12-04, 12-05 | Per-worker monitoring views + artifact merge + isolated failure re-run | ✓ SATISFIED | Truth 2 (SC2) evidence |
| MGPU-03 | 12-04 | DDP vs model-sharding applicability decision landed | ✓ SATISFIED | Truth 3 (SC3) evidence: docs/multi-gpu.md decision matrix |
| WEB-01 | 12-02 | Read-only web progress mirror, static artifacts, no backend | ✓ SATISFIED | Truth 4 (SC4) evidence |
| TEST-01 | 12-03 | Textual snapshot SVG goldens for canonical screens, maintainer-reviewed commit | ✓ SATISFIED (automation) / review clause → human | Truth 5 (SC5) evidence |

Orphaned-requirement check (Step 6c): REQUIREMENTS.md maps exactly MGPU-01/02/03, WEB-01, TEST-01 to Phase 12 — all five are claimed by plan frontmatter (12-01: MGPU-01; 12-02: WEB-01; 12-03: TEST-01; 12-04: MGPU-02+MGPU-03; 12-05: all five). No orphans. REQUIREMENTS.md marks all five `[x]` Complete under milestone v1.2 — consistent with the codebase evidence found.

### Decision Coverage

`check.decision-coverage-verify`: skipped=false, blocking=false, **12/12 decisions honored** (D-01..D-12 all trace to shipped artifacts), not_honored=[].

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| (none) | — | — | — | Debt-marker scan (TBD/FIXME/XXX) clean across all 14 phase-modified source/test/doc files; TODO/HACK/PLACEHOLDER scan clean (the one `SEL_FILTER_PLACEHOLDER` hit is a legit strings.py constant import, not a stub) |

Notes: `tui/strings.py` was modified during the phase — by the sanctioned WR-08 review fix (ae303de, recorded in 12-REVIEW-FIX.md, delta re-reviewed clean), moving operator-facing copy INTO strings.py (conformance to the strings convention, the direction the 12-03 prohibition wants). Not a violation. The review loop's records are complete: 8 warnings fixed with atomic commits d8c54a8..b010e65, 4 info-level findings open by design (IN-01..04 in 12-REVIEW-DISPOSITION.md).

### Coincidental-Reliance Check

None flagged. The real-subprocess tests use fixture registries — a fixture supplying input the real caller also supplies (explicitly not-flagged). Ordering in spawn/wait/aggregation is enforced by code (`proc.wait()` over all, verdict printed after); no undeclared preconditions found behind any VERIFIED truth.

### Human Verification Required

### 1. D-03 maintainer review of the 8 committed SVG goldens

**Test:** Open each of `tests/tui/__snapshots__/{env_check,selection_models,selection_datasets,data_manager,run_config,monitor_running,monitor_empty,wizard}.svg` and compare against the 12-UI-SPEC corpus table (per-screen fixture state at 120x40).
**Expected:** Every golden visually shows the intended canonical screen state (marks, rendered param values, the five cell glyphs, stats/ETA, advisories). Any wrong-looking golden is regenerated via `make snapshot-update` and re-reviewed before the corpus is trusted.
**Why human:** The golden tests prove byte-stability, determinism, and red-on-drift — not visual rightness. The phase's own D-03 decision and the 12-03-SUMMARY `human_judgment: true` gate define maintainer eyeball review as the deciding evidence; this is the SC5 "maintainer-verified" clause.

### 2. WINDOWS #21 — other-machine N=2 multi-GPU smoke

**Test:** Execute the 9-step procedure in `docs/multi-gpu.md` §"The 9-step N=2 multi-GPU smoke procedure" on the other machine (bounded: 2 models × iDNA_ABF_datasets__5mC × 1 seed × 1 epoch), then record outcomes against the WINDOWS #21 entry.
**Expected:** Disjoint dry-run manifests; 2 workers pinned CUDA_VISIBLE_DEVICES=0/1; independent per-worker TUI views; failure isolation; `--from-failures` re-run touching only the failed worker's root; `--merge` with SHA256-verified union; web mirror generated over worker roots then the merged root separately; export equivalence; cleanup. Close WINDOWS #21 afterward.
**Why human:** This GB10 host is single-GPU and dev/test only (D-05 machine-roles constraint — absence of a local N=2 run is by design, not a gap); the validation is maintainer-executed on other hardware. The tracking entry was verified: WINDOWS.md row 21, kind `unrun-verify`, status **open**, counters open_count 15 / total 21 — `/gsd-ship` keeps it visible.

### Gaps Summary

No gaps. All five roadmap success criteria are implemented, substantive, wired, and behaviorally spot-checked green (49/49 orchestrator module, 10/10 goldens, 8/8 generator, delta A/B Pilot tests, node lane). All plan prohibitions held. Requirements MGPU-01/02/03, WEB-01, TEST-01 all accounted for; decision coverage 12/12. The phase routes exactly two items to humans by its own design: the D-03 golden review (the SC5 clause that code cannot verify) and the WINDOWS #21 other-machine N=2 smoke — hence `human_needed`, not `passed`.

---

_Verified: 2026-10-13T15:10:52Z_
_Verifier: Claude (gsd-verifier)_
