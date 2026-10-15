---
phase: 12-multi-gpu-orchestration-console-hardening
verified: 2026-10-14T17:33:12Z
status: human_needed
score: 4/5 must-haves verified
covered_files: [".planning/WINDOWS.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-01-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-01-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-02-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-02-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-03-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-03-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-04-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-04-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-SUMMARY.md", "Makefile", "README.md", "dnallm-mark/css/progress.css", "dnallm-mark/css/styles.css", "dnallm-mark/data/progress/.gitkeep", "dnallm-mark/js/config.js", "dnallm-mark/js/data.js", "dnallm-mark/js/progress.js", "dnallm-mark/progress.html", "docs/multi-gpu.md", "pipeline/run_sweep_shard.py", "script/gen_progress.py", "tests/js/progress-page.test.js", "tests/test_sweep_shard.py", "tests/tui/__snapshots__/data_manager.svg", "tests/tui/__snapshots__/data_manager_presence.svg", "tests/tui/__snapshots__/env_check.svg", "tests/tui/__snapshots__/monitor_empty.svg", "tests/tui/__snapshots__/monitor_running.svg", "tests/tui/__snapshots__/run_config.svg", "tests/tui/__snapshots__/selection_datasets.svg", "tests/tui/__snapshots__/selection_models.svg", "tests/tui/__snapshots__/wizard.svg", "tests/tui/test_gen_progress.py", "tests/tui/test_pilot_monitor.py", "tests/tui/test_pilot_run_config.py", "tests/tui/test_snapshots.py", "tui/screens/run_config.py", "tui/strings.py"]
covered_digest: "v3:sha256:b866930b52bb5fb9251b8fd6f2ae23718885e0f74a8f1df652794c50209921c5"
behavior_unverified: 1 # SC5's maintainer-review clause — automation green in its designed strict-xfail window, but golden refresh + visual review are human-only by the phase's own D-03 gate
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 4/5
  gaps_closed: [] # prior pass had NO gaps (human_needed from the two by-design human items only)
  gaps_remaining: []
  regressions: [] # stale-refresh pass: all 4 previously-verified truths re-verified green over the post-change tree; no regression found
advisory:
  - finding: "WR-01 — blanket strict-xfail absorbs SVG-render failures until the maintainer snapshot-update lands (golden-drift detection window)"
    category: other
    reason: "Designed interim state, not a defect: goldens staled by sanctioned post-phase quick tasks (261014-mlc slot rework + locked nav rename); the window IS bounded three ways — _GOLDEN_REFRESH_REASON names the causing task/date/closure action (test_snapshots.py:903-910, the review's own alternative fix), WINDOWS ledger entry #25 tracks it open, and strict=True still detects the flip direction. Closure action is the standing D-03 human item (make snapshot-update + marker removal + review). Sensitivity test proves red-on-drift capability today."
    evidence_status: "none provided (no failing test — the 9 xfailed are by design; determinism + sensitivity pass)"
  - finding: "WR-02 — pipeline/directories_config.py (quick-task 261014-f4w module, not a phase-12 artifact) missing from the make lint lane"
    category: architectural
    reason: "New-scope finding with no deterministic evidence: the module is ty-covered (whole pipeline/ tree) and ruff-clean today (review-verified). Phase 12's own Makefile contract (PHASE12_MODULES guard for run_sweep_shard + gen_progress, Makefile:174) is intact and verified this pass. The lint-gap is f4w follow-through, durably recorded as open in 12-REVIEW-DISPOSITION.md."
    evidence_status: "none provided (gap is future-drift risk only; no failing test)"
behavior_unverified_items:
  - truth: "SC5 — canonical screens pinned by SVG goldens reviewed and committed by the maintainer"
    test: "Maintainer runs make snapshot-update (regenerates all 9 goldens incl. the new data_manager_presence), removes the 9 strict-xfail markers, then eyeballs each committed SVG against the 12-UI-SPEC corpus table"
    expected: "All 9 goldens visually correct for their canonical screen states AND the strict-xfail markers removed so CI compares goldens red-on-drift again; closes WINDOWS #25 and the WR-01 window"
    why_human: "Byte-identical comparison cannot see visual rightness, and the current committed SVGs are knowingly stale since quick-261014-mlc — regeneration + review are the maintainer's D-03 gate by the phase's own decision; automation proves byte-stability, determinism, and sensitivity only"
human_verification:
  - test: "D-03 maintainer review of the now-9 committed SVG goldens in tests/tui/__snapshots__/ (env_check, selection_models, selection_datasets, data_manager, data_manager_presence, run_config, monitor_running, monitor_empty, wizard)"
    expected: "Run make snapshot-update first (all 9 are strict-xfail-stale since quick-261014-mlc reworked slot 2/3 and the locked nav label rename changed every top bar), remove the 9 xfail markers, then review each regenerated golden against the 12-UI-SPEC corpus table; close WINDOWS #25"
    why_human: "Machine-context note: the golden corpus grew 8→9 (data_manager_presence via quick-261014-dcl) and every golden is in the designed stale window pending this very snapshot-update — the refresh + eyeball review are the maintainer's D-03 trust gate; automation (determinism + sensitivity, 2 passed / 9 xfailed this pass) cannot close it"
  - test: "WINDOWS #21 (open): execute the 9-step N=2 multi-GPU smoke per docs/multi-gpu.md §'The 9-step N=2 multi-GPU smoke procedure' (bounded: 2 models × iDNA_ABF_datasets__5mC × 1 seed × 1 epoch) on the multi-GPU machine and record outcomes"
    expected: "Steps 0-9 as documented: disjoint dry-run manifests, 2 workers with CUDA_VISIBLE_DEVICES=0/1, independent TUI views, isolation on failure, --from-failures re-run touching only the failed worker's root, --merge with SHA256-verified output, web mirror over worker roots then merged root, export equivalence, cleanup; close WINDOWS #21 (ledger row 21, open; counters 19/25)"
    why_human: "Machine-context note: GB10 is single-GPU dev/test only (D-05 machine-roles) and the 4×5090 box was REPLACED — the target machine is now unspecified per maintainer 2026-10-14, so this is maintainer-executed on other hardware by design, not executor-executable and not CI-able. Live supporting evidence this pass: the dnabert smoke cells completed with full FLOPs artifacts (6.77e15 FLOs) through this milestone's chain, and a bounded dnamamba subset is running — single-GPU chain health is demonstrated; only the N=2 cross-worker procedure remains unexecuted"
---

# Phase 12: Multi-GPU Orchestration & Console Hardening Verification Report

**Phase Goal:** With single-GPU validated, throughput scales out — CLI-invocable static model sharding × CUDA_VISIBLE_DEVICES with per-worker monitoring, artifact merge, and isolated failure re-run, plus the documented DDP-vs-sharding applicability decision — and the console ships its release extras: a static read-only web progress mirror and maintainer-verified snapshot goldens pinning the canonical screens
**Verified:** 2026-10-14T17:33:12Z
**Status:** human_needed
**Re-verification:** Yes — STALE-REFRESH pass (covered source changed post-pass via quick tasks 261014-ir9/l6h/f4w/dcl/c2l/mlc + the 11-08 gap round); prior pass had no gaps

## Goal Achievement

### Observable Truths

Must-haves carried verbatim from the prior pass (ROADMAP Success Criteria × 5 PLAN frontmatters; no scope change). Stale-refresh scope established first: `git diff 9429ddf279 HEAD` (the commit at the prior verified timestamp) is EMPTY for `pipeline/run_sweep_shard.py`, `script/gen_progress.py`, all six web-mirror files, `tests/tui/test_gen_progress.py`, and `tests/js/progress-page.test.js` — their prior three-level + data-flow verdicts carry forward with only behavioral re-proof needed. Changed covered files: Makefile, README.md, docs/multi-gpu.md, tests/test_sweep_shard.py (docstring-only 62→59 count fix from ir9), tests/tui/test_pilot_monitor.py, tests/tui/test_pilot_run_config.py, tests/tui/test_snapshots.py, tui/screens/run_config.py, tui/strings.py, the snapshots corpus (8→9 SVGs), WINDOWS.md.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | SC1: Multi-worker orchestration invokable from the CLI: N workers over disjoint static model shards with CUDA_VISIBLE_DEVICES isolation, marker-skip as the only concurrency guard | ✓ VERIFIED | `pipeline/run_sweep_shard.py` byte-stable since the prior pass (1252 lines; 0 commits, empty diff vs 9429ddf279) — prior L1-L4 verdict holds verbatim. Behavioral re-proof over the POST-change tree: `pytest tests/test_sweep_shard.py -q` → **49 passed in 0.58s** this pass, including `test_n1_degenerate_real_subprocess_smoke`, `test_real_two_worker_dry_run_subprocess_chain`, `test_dry_run_disjointness_in_process`, `test_worker_argv_and_spawn_kwargs_under_default_gpus` — i.e. the real-subprocess chains re-proved against the CURRENT `run_sweep.py`, which post-phase gained `--model_root/--dataset_root/--log_dir` + `directories.json` (interaction seam reviewed sound in 12-REVIEW; the suite is the proof). D-07 phase-scoped prohibition held during the phase; post-phase run_sweep.py edits are sanctioned quick-task work outside the phase contract. No lock/port/nvidia-smi machinery (carried; bytes unchanged) |
| 2 | SC2: The operator sees per-worker monitoring views, artifacts merge across workers, and a failed worker's shard re-runs in isolation without touching healthy workers | ✓ VERIFIED | Merge/isolation code byte-stable (same module). Behavioral re-proof this pass: the 49/49 suite run includes `test_merge_happy_path_copies_allowlist_and_rewrites`, `test_merged_root_is_consumer_equivalent` (export_runs union equivalence), `test_merge_leaves_worker_roots_immutable`, `test_d08_from_failures_rerun_is_isolated_to_w0` — all green. Delta A re-proof over the CURRENT monitor (hardened by the sanctioned 11-08 round: WR-01 REPO_ROOT basis, WR-02 failure-derived seeds, WR-04 O_EXCL tee, WR-05 multi-root exit modal): `test_delta_a_discovered_pane_renders_worker_roots_independently` → **1 passed in 0.71s** — N-root discovered-table rendering survives the hardening intact |
| 3 | SC3: The DDP vs model-sharding applicability decision is documented and landed | ✓ VERIFIED | `docs/multi-gpu.md` decision matrix present at L17 (§"The decision: model sharding vs DDP"); post-phase doc commit (28b545b) + ir9 kept counts accurate — registry is 59 entries and both count sites (L21, L29) + the test docstring say 59 (empirically verified in 12-REVIEW; docstring fix confirmed in the git diff this pass). README links live at :122 and :541. 249→current line count changed only by docs-generation additions; the decision/runbook/9-step-procedure sections verified present (gen_progress mirror command at :165/:170/:236) |
| 4 | SC4: A read-only web progress mirror generated from sweep artifacts lets the team follow progress in a browser — static files only, no backend | ✓ VERIFIED | All artifacts byte-stable since prior pass (38/427/71-line page trio, generator, one-liner integrations — NAV_LINKS `config.js:70`, `DataAPI.loadProgress` `data.js:106-108`, zero CDN in progress.html re-confirmed by grep this pass). Behavioral re-proof: `pytest tests/tui/test_gen_progress.py -q` → **8 passed**; `node --test tests/js/progress-page.test.js` → **8 pass / 0 fail**. Wiring links re-confirmed: gen_progress→sweep_monitor import (L92), fetch chain, navbar render |
| 5 | SC5: Canonical screens are pinned by Textual snapshot SVG goldens reviewed and committed by the maintainer, failing CI CPU-side on visual regression | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Corpus grew 8→9 (`data_manager_presence.svg` via quick-261014-dcl); harness + 9 committed SVGs + determinism + sensitivity all present and wired (`GOLDENS` at :832, `make snapshot-update` sole regeneration path Makefile:132, CI compares-only). Automation green in its DESIGNED state this pass: `pytest tests/tui/test_snapshots.py -q` → **2 passed, 9 xfailed in 16.70s** (the 9 strict-xfail pins = this phase's goldens, matching the full-suite baseline's 9 xfailed; determinism + sensitivity both pass). But the committed SVGs are knowingly stale since quick-261014-mlc (slot 2/3 rework + locked nav rename changed every top bar) — regeneration + marker removal + maintainer eyeball review are the D-03 human gate (12-03-SUMMARY `human_judgment: true`). Routed to Human Verification below, NOT marked verified by code |

**Score:** 4/5 truths verified (1 present, behavior-unverified: the SC5 maintainer-review clause, now inside the designed snapshot-update window)

### Plan-Prohibition Checks (negative must-haves)

| Prohibition | Status | Evidence |
| --- | --- | --- |
| 12-01: no edit to run_sweep.py / run_finetune.py during the phase; pipeline/ gains exactly one new file | ✓ HELD (phase-scoped) | Prior-pass git evidence carries (both files' Phase-12-window commits predate the phase). Post-phase: run_sweep.py gained storage flags via sanctioned quick tasks (f4w/l6h) — outside the phase contract; orchestrator compatibility re-proven by the 49/49 real-subprocess suite |
| 12-01: no lock/claim-file/port machinery; marker-skip only guard | ✓ HELD | run_sweep_shard.py bytes unchanged since prior verification (grep-clean verdict carries verbatim) |
| 12-01: no nvidia-smi probing / GPU enumeration / N>1 assumption | ✓ HELD | Same — bytes unchanged |
| 12-02: zero backend, zero CDN on new page, zero new deps | ✓ HELD | progress.html CDN grep = 0 hits this pass; page trio byte-stable; no dependency changes in post-phase commits touching them (none exist) |
| 12-02: no fabricated values (honesty rules, web-side) | ✓ HELD | progress.js byte-stable; JS lane 8/8 green (the lane pins these rules) |
| 12-03: no fix at wrong layer; no new bindings; strings.py/styles.tcss byte-stible DURING the plan | ✓ HELD (phase-scoped) | The one sanctioned `dismiss()` override verified present post-changes: `_PickerReturnModal` at run_config.py:603 with `call_after_refresh(picker.focus)` at :633, 5 re-parents (:641/:666/:692/:723/:791), `_GateConfirmModal` at :827, push site :1977 — survived the 3 post-phase commits (CR-02 pre-check + c2l model-root + f4w log-dir row). B1/B2 behavioral re-proof: 2 passed. Post-phase strings.py/monitor.py changes are sanctioned quick-task/11-08 work |
| 12-03: no snapshot-plugin/syrupy/cairosvg install; string equality is the compare | ✓ HELD | test_snapshots.py compares UTF-8 SVG strings (:912-970 shape verified); no pyproject/uv.lock change for such deps in any post-phase commit (review-verified; grep of lockfile clean) |
| 12-04: no symlink/move merge; copy + SHA256 only | ✓ HELD | Merge path bytes unchanged since prior pass (verified `_copy_verified` verdict carries) |
| 12-04: no orchestrator convenience flags beyond --merge/--include-checkpoints; no run_sweep edits during phase | ✓ HELD | Bytes unchanged; parse_args surface frozen |
| 12-05: zero production-code changes in plan 05; never execute N=2 GPU procedure | ✓ HELD (phase-scoped) | Prior-pass commit evidence carries; no N=2 run exists on this host (WINDOWS #21 still open, correctly) |

### Required Artifacts

Byte-stable artifacts carry their prior three-level VERIFIED verdicts (empty diff vs 9429ddf279 proven this pass); changed artifacts re-verified.

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `pipeline/run_sweep_shard.py` | launch + merge orchestrator | ✓ VERIFIED | 1252 lines, byte-stable; 49/49 suite green this pass |
| `tests/test_sweep_shard.py` | tier-1 + merge + isolation suites | ✓ VERIFIED | 49/49 green; only post-phase change is the docstring 62→59 count fix (ir9) — verified in git diff |
| `script/gen_progress.py` | scanner-serializing generator | ✓ VERIFIED | 250 lines, byte-stable; 8/8 green |
| `tests/tui/test_gen_progress.py` | golden-JSON tests | ✓ VERIFIED | Byte-stable; 8/8 green this pass |
| `dnallm-mark/progress.html` / `js/progress.js` / `css/progress.css` | frozen UI-SPEC page | ✓ VERIFIED | 38/427/71 lines, byte-stable; zero CDN re-confirmed |
| `js/config.js`, `js/data.js`, `css/styles.css` | one-line site edits | ✓ VERIFIED | Byte-stable; NAV_LINKS :70, loadProgress :106, @import verified present |
| `tests/js/progress-page.test.js` | DOM-less JS lane | ✓ VERIFIED | Byte-stable; 8 pass / 0 fail this pass |
| `tui/screens/run_config.py` | delta B only (phase scope) | ✓ VERIFIED | Fix intact post-changes (:603/:633/:827/:1977); B1/B2 green; post-phase additions (CR-02 pre-check at :1910, c2l/f4w rows) reviewed sound in 12-REVIEW |
| `tests/tui/test_pilot_run_config.py` | B1-B5 Pilot tests | ✓ VERIFIED | B1/B2 named tests 2 passed this pass (file gained 6 post-phase commits: CR-02/WR-01 seam pins — additive, review-verified) |
| `tests/tui/test_snapshots.py` | harness + goldens + determinism/sensitivity | ✓ VERIFIED (automation) | 9 GOLDENS entries (:832-844), 9 xfail(strict) markers, `_GOLDEN_REFRESH_REASON` window bound at :903-910; 2 passed + 9 xfailed this pass |
| `tests/tui/__snapshots__/*.svg` | committed corpus | ✓ VERIFIED (9; stale-by-design) | 9 SVGs on disk (29-68KB class); comparison state = designed strict-xfail window pending maintainer refresh (see SC5) |
| `Makefile` | lint guard + snapshot-update | ✓ VERIFIED | PHASE12_MODULES :174 intact (run_sweep_shard + gen_progress); snapshot-update :132 intact. WR-02 note: directories_config.py (a post-phase f4w module, NOT phase scope) is absent from lint lists — advisory, see below |
| `docs/multi-gpu.md` | D-04 decision doc | ✓ VERIFIED | Decision matrix :17; runbook incl. gen_progress mirror steps; 59-count accurate post-ir9 |
| `README.md` | one-line link | ✓ VERIFIED | :122 + :541 (docs-generation added the second) |
| `tests/tui/test_pilot_monitor.py` | delta A proof | ✓ VERIFIED | Named delta A test green this pass; post-phase commits are 11-08 hardening pins (additive) |
| `.planning/WINDOWS.md` | entry 21 unrun-verify | ✓ VERIFIED | Row 21 open (unrun-verify, 2026-10-13); counters now open 19 / total 25 (ledger grew via quick tasks); golden-refresh entries #23-25 tracked |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| run_sweep_shard | run_sweep + registry_loader | sibling imports | ✓ WIRED | :181-182 re-confirmed; real-subprocess tests green over current run_sweep.py |
| worker env CUDA_VISIBLE_DEVICES | torch | verbatim inheritance | ✓ WIRED | Spawn-kwargs test green in the 49/49 run |
| gen_progress | tui.services.sweep_monitor | import + serialization | ✓ WIRED | :92 re-confirmed; 8/8 goldens green |
| gen_progress --output | data/progress/sweep.json → loadProgress → ProgressPage | fetch chain | ✓ WIRED | data.js:106 + JS lane 8/8 green |
| NAV_LINKS | site-wide navbar | js/navbar renders CONFIG.NAV_LINKS | ✓ WIRED | config.js:70 (byte-stable; the mlc nav rename was TUI strings.py only — web nav untouched) |
| _PickerReturnModal.dismiss | #cfg-picker refocus | call_after_refresh | ✓ WIRED | :603/:633 present post-changes; B1/B2 green |
| make snapshot-update | regeneration entry | module --regenerate block | ✓ WIRED | Makefile:132 → test_snapshots.py GOLDENS writer (review-verified writes all 9 incl. data_manager_presence) |
| --merge | worker_root() | one naming authority | ✓ WIRED | Byte-stable module; merge tests green |
| merged root | export_runs / sweep_monitor / gen_progress | consumer equivalence | ✓ WIRED | test_merged_root_is_consumer_equivalent green in the 49/49 run |
| docs step 7 | script/gen_progress.py | mirror command in runbook | ✓ WIRED | :165/:170/:236 |
| WINDOWS #21 | docs procedure → 12-05-SUMMARY | one thread | ✓ WIRED | Row 21 open; procedure verified present in docs |

### Data-Flow Trace (Level 4)

Byte-stable artifacts carry their prior FLOWING verdicts (empty diff proven); no data-path changed.

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| progress.html page | sweep.json payload | gen_progress → sweep_monitor over real artifact roots | Yes — scanner-driven; JS lane pins the render rules | ✓ FLOWING |
| gen_progress.py | generated_at | injected/real clock | Yes — byte-stable; golden tests pin | ✓ FLOWING |
| run_sweep_shard verdict table | failed-cell count | worker sweep_failures.json | Yes — byte-stable; verdict-table test green | ✓ FLOWING |
| merged manifest | cells/failures unions | per-worker manifests + verified copies | Yes — consumer-equivalence test green this pass | ✓ FLOWING |

### Behavioral Spot-Checks

Run this pass as single module suites / named tests (never the full workspace suite). Live-run context recorded per the refresh chain: dnabert smoke cells completed with full FLOPs artifacts (6.77e15 FLOs) through this milestone's chain; a bounded dnamamba subset is running.

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Orchestrator full module (LPT, validation, spawn, aggregation, merge, isolation, N=1 real subprocess) | `uv run --group dev --group tui pytest tests/test_sweep_shard.py -q` (once) | 49 passed in 0.58s | ✓ PASS |
| Goldens module (8→9 corpus; determinism + sensitivity + strict-xfail pins) | `uv run --group dev --group tui pytest tests/tui/test_snapshots.py -q` (once) | 2 passed, 9 xfailed in 16.70s | ✓ PASS (the 9 xfailed ARE the designed stale-window state; matches the full-suite baseline's 9 xfailed) |
| Generator golden contract | `uv run --group dev --group tui pytest tests/tui/test_gen_progress.py -q` (once) | 8 passed in 0.04s | ✓ PASS |
| Delta A: N-root discovered table renders worker roots independently (post-11-08 monitor) | `pytest tests/tui/test_pilot_monitor.py::test_delta_a_discovered_pane_renders_worker_roots_independently -q` | 1 passed in 0.71s | ✓ PASS |
| Delta B: modal dismiss refocuses picker; digits navigate immediately (post-c2l/f4w run_config) | `pytest ...::test_b1_preview_modal_esc_refocuses_picker ::test_b2_digit_navigates_immediately_after_preview_dismiss -q` | 2 passed in 1.24s | ✓ PASS |
| Progress page JS lane (zero-CDN, no timers, honesty rules) | `node --test tests/js/progress-page.test.js` | 8 pass / 0 fail | ✓ PASS |

Full workspace suite NOT re-run this pass (at-most-once discipline): module lanes above are the phase's evidence. The stated box baseline — 7 failed / 1743 passed / 9 xfailed — is consistent with observations: the 9 xfailed are directly observed above and are this phase's designed pins; the 7 failures are the documented pre-existing set recorded in the 10-07 gap-closure plan (5 schema/determinism pins stale after data commit 9e803ca + root-user chmod sims; WINDOWS #22 lineage), none in any phase-12 lane (all six phase-12 lanes green here).

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes declared by this phase's plans or summaries; the verification contract is pytest + node lanes (executed above). SKIPPED (no probes declared).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| MGPU-01 | 12-01, 12-05 | CLI-invocable model sharding × CUDA_VISIBLE_DEVICES multi-worker static orchestration | ✓ SATISFIED | Truth 1 (SC1) evidence |
| MGPU-02 | 12-04, 12-05 | Per-worker monitoring views + artifact merge + isolated failure re-run | ✓ SATISFIED | Truth 2 (SC2) evidence |
| MGPU-03 | 12-04 | DDP vs model-sharding applicability decision landed | ✓ SATISFIED | Truth 3 (SC3) evidence |
| WEB-01 | 12-02 | Read-only web progress mirror, static artifacts, no backend | ✓ SATISFIED | Truth 4 (SC4) evidence |
| TEST-01 | 12-03 | Textual snapshot SVG goldens for canonical screens, maintainer-reviewed commit | ✓ SATISFIED (automation) / review clause → human | Truth 5 (SC5) evidence |

Orphaned-requirement check: REQUIREMENTS.md maps exactly MGPU-01/02/03, WEB-01, TEST-01 to Phase 12 (rows 125-130), all `[x]` Complete — all five claimed by plan frontmatter. No orphans.

### Decision Coverage

`check.decision-coverage-verify`: skipped=false, blocking=false, **12/12 decisions honored** (D-01..D-12), not_honored=[].

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | — | — | Debt-marker scan (TBD/FIXME/XXX) clean across all covered source/test/doc files including the post-change ones; TODO/HACK scan clean; the SEL_*/WIZ_/*PLACEHOLDER hits are i18n input-placeholder string constants in strings.py (legit values, not stubs — same adjudication as prior pass) |

### Incremental Review Adjudication (12-REVIEW.md, committed 22b7304: 0 Critical / 2 Warnings / 2 Info)

All four findings adjudicated **advisory — none is a gap** (no FAILED truth, no MISSING/STUB artifact, no NOT_WIRED link, no blocker anti-pattern; all four are durably recorded as open in 12-REVIEW-DISPOSITION.md):

| # | Finding | Severity | Adjudication | Rationale |
| --- | ------- | -------- | ------------ | --------- |
| WR-01 | Blanket strict-xfail golden-drift window | warning | 📋 Advisory → folds into the standing D-03 human item | Designed interim state; window bounded three ways (`_GOLDEN_REFRESH_REASON` names task 261014-mlc + date + closure action at test_snapshots.py:903-910 — the review's own alternative fix, already in place; WINDOWS #25 tracks it open; strict=True detects the flip direction). Closure = the maintainer snapshot-update + review, i.e. exactly the standing human item. Sensitivity test proves red-on-drift today |
| WR-02 | directories_config.py missing from make lint | warning | 📋 Advisory (#3304: new-scope, unevidenced) | The module is a post-phase quick-task (261014-f4w) artifact, not phase scope; phase 12's lint contract (PHASE12_MODULES) is intact. ty covers the whole pipeline/ tree; ruff-clean today (review-verified). No deterministic evidence — future-drift risk only. Follow-through belongs to the f4w task lineage / disposition ledger |
| IN-01 | Pre-ir9 "62" fixture strings in out-of-scope TUI fakes | info | ℹ️ Info — deliberate, not a defect | Fixture values in test_pilot_env_check.py / test_pilot_nav_shell.py (neither a phase-12 covered file); review itself rules "should NOT be touched opportunistically" per fix discipline |
| IN-02 | docs cleanup bullet joins two rm commands on one rendered line | info | ℹ️ Info — cosmetic | Each code span copies individually; no functional impact; recorded open in the disposition ledger |

### Coincidental-Reliance Check

None flagged this pass. The byte-stability proof (empty diff vs 9429ddf279) makes the carried verdicts non-incidental — they hold over identical bytes; the changed files were behaviorally re-proven against the current tree (real-subprocess chains, current run_sweep.py, post-hardening monitor). No undeclared preconditions, no incidental ordering, no fixture-only preconditions behind any VERIFIED truth.

### Human Verification Required

### 1. D-03 maintainer review of the 9 committed SVG goldens (now includes snapshot-update)

**Test:** Run `make snapshot-update` to regenerate all 9 goldens (`tests/tui/__snapshots__/{env_check,selection_models,selection_datasets,data_manager,data_manager_presence,run_config,monitor_running,monitor_empty,wizard}.svg`), remove the 9 `xfail(strict=True)` markers in `tests/tui/test_snapshots.py`, then compare each regenerated golden against the 12-UI-SPEC corpus table (per-screen fixture state at 120x40). Close WINDOWS #25.
**Expected:** All 9 goldens visually correct for their canonical screen states (marks, rendered param values, the five cell glyphs, stats/ETA, advisories — post the mlc slot-2/3 rework and locked nav labels); the markers removed so CI compares red-on-drift again.
**Why human:** Machine context — the corpus is knowingly stale since quick-261014-mlc (every top bar changed); the refresh and the eyeball review are the maintainer's D-03 trust gate by the phase's own decision. Automation proves byte-stability, determinism, and sensitivity (2 passed / 9 xfailed this pass); it cannot prove visual rightness, and the current comparisons are absorbed into the designed xfail window (WR-01).

### 2. WINDOWS #21 — other-machine N=2 multi-GPU smoke

**Test:** Execute the 9-step procedure in `docs/multi-gpu.md` §"The 9-step N=2 multi-GPU smoke procedure" on the multi-GPU machine (bounded: 2 models × iDNA_ABF_datasets__5mC × 1 seed × 1 epoch), then record outcomes against WINDOWS #21 (row 21, open).
**Expected:** Disjoint dry-run manifests; 2 workers pinned CUDA_VISIBLE_DEVICES=0/1; independent per-worker TUI views; failure isolation; `--from-failures` re-run touching only the failed worker's root; `--merge` with SHA256-verified union; web mirror over worker roots then the merged root separately; export equivalence; cleanup. Close WINDOWS #21 (ledger counters open 19 / total 25).
**Why human:** Machine context — GB10 is single-GPU dev/test only (D-05 machine-roles), and the 4×5090 box was REPLACED: the target machine is now unspecified per maintainer 2026-10-14. By design maintainer-executed on other hardware; not executor-executable, not CI-able. Live supporting evidence this pass: dnabert smoke cells completed with full FLOPs artifacts (6.77e15 FLOs) through this milestone's chain and a bounded dnamamba subset is running — single-GPU chain health demonstrated; only the cross-worker N=2 procedure remains unexecuted.

### Gaps Summary

No gaps. The stale-refresh pass found zero regressions: the orchestrator and the entire web mirror are byte-stable since the prior verified pass (empty diff vs 9429ddf279), and every behaviorally-proven claim was re-proven green over the post-change tree (49/49 orchestrator incl. merge/isolation/consumer-equivalence; delta A over the 11-08-hardened monitor; delta B over the c2l/f4w-extended run_config; 8/8 generator; 8/8 JS lane; 2 passed + 9 designed-xfailed goldens). All plan prohibitions held (phase-scoped ones by prior git evidence, bytes-unchanged ones verbatim). Requirements MGPU-01/02/03, WEB-01, TEST-01 all satisfied; decision coverage 12/12. The incremental review's 2 warnings + 2 info findings are all adjudicated advisory (WR-01 folds into the standing D-03 human item; WR-02 is unevidenced new-scope recorded in the disposition ledger). The phase routes exactly two items to humans by its own design — the D-03 golden refresh + review (corpus now 9) and the WINDOWS #21 other-machine N=2 smoke (machine now unspecified after the 4×5090 replacement) — hence `human_needed`, not `passed`.

---

_Verified: 2026-10-14T17:33:12Z_
_Verifier: Claude (gsd-verifier)_
