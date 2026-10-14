---
phase: 10-data-manager-downloads-verification
verified: 2026-10-14T17:42:32Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/10-data-manager-downloads-verification/10-01-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-01-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-02-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-02-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-03-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-03-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-04-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-04-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-05-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-05-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-06-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-06-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-07-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-07-SUMMARY.md
  - pipeline/directories_config.py
  - tests/tui/fixtures/modelscope_stderr_interrupted.txt
  - tests/tui/fixtures/modelscope_stderr_success.txt
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_services_gauntlet.py
  - tests/tui/test_services_zenodo_bundle.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/data_manager.py
  - tui/screens/nav.py
  - tui/screens/selection.py
  - tui/services/download_queue.py
  - tui/services/env_check.py
  - tui/services/gauntlet.py
  - tui/services/registries.py
  - tui/services/run_config.py
  - tui/services/selection.py
  - tui/services/zenodo_bundle.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:5a877ff9c748c51c87e6a72fcb82584efe7750a6694fdaba72c3cb19acdcabe2"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-01 — a failed KIND_MODEL download flips the selection 下载 column to 已下载: model_presence gates on is_dir only (tui/services/selection.py) while the model-lane done gate requires config.json (MODEL_DONE_MARKER)"
    category: other
    reason: "Carried forward unchanged (selection.py untouched since the 4baaa2b pass — git-confirmed). Operator-facing correctness defect in the model presence column; model lane and its presence column are dcl/mlc scope layered after phase 10; no phase-10 SC covers it. Disposition-open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "reproduced at the 4baaa2b pass; untouched by 11-08 (file outside its diff)"
  - finding: "WR-02 — the slot-3 drill-down renders channel: unknown (unknown_key) for healthy KIND_MODEL queue rows (channel_detail consults only the DATASET registry)"
    category: other
    reason: "Carried forward unchanged (data_manager.py untouched since 4baaa2b). Degrades the D-03 drill-down surface only for KIND_MODEL rows that did not exist at phase 10; no phase-10 SC covers model-row drill-down content. Disposition-open"
    evidence_status: "code-traced at the 4baaa2b pass; untouched by 11-08"
  - finding: "IN-01 — z pressed during the mount probe-in-flight window fires DL_ZENODO_DISABLED_TOAST as fact while _zenodo_state is still None (tui/screens/data_manager.py)"
    category: other
    reason: "Carried forward unchanged. Transient copy issue; SC4 reachability and never-silent behavior unaffected. Disposition-open"
    evidence_status: "code-read at the 4baaa2b pass; untouched by 11-08"
  - finding: "IN-02 — ABOUT_MILESTONE_STAGE stale (names phase 9) in tui/strings.py (:605)"
    category: other
    reason: "Carried forward unchanged (strings.py WAS touched by 11-08, but only in the LNC_EXIT/MON_ blocks — this line is byte-identical). Cosmetic milestone metadata; no SC relevance. Disposition-open"
    evidence_status: "code-read at this pass: still '本相位: 9 自定义接入'"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report — Convergence Re-Verification (Staleness Refresh, Round 3)

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-14T17:42:32Z at HEAD dd16ad6 (branch autorun)
**Status:** passed — 5/5 SCs hold at the refreshed HEAD; zero regressions from the 11-08 delta
**Re-verification:** Yes — staleness refresh. Prior pass 5/5 at HEAD 4baaa2b (2026-10-14T16:01:25Z, digest `v3:sha256:b1282997…`). Since then, phase 11's gap plan 11-08 (verified passed in phase 11's own pass at fcdc4b6) touched THREE of this phase's covered files: `tui/app.py` (WR-05 multi-root ExitModal), `tui/services/sweep_launcher.py` (WR-04 O_EXCL tee + WR-01 root-basis `rc.resolve_dirs(spec).output_root_abs` in `_spawn`), `tui/strings.py` (WR-02/03/05 string constants). The SC1 chain files — `tui/services/download_queue.py`, `tui/services/run_config.py`, `tui/services/env_check.py` — are byte-identical since 4baaa2b (git-confirmed: `git diff --name-only 4baaa2b..dd16ad6` lists neither).

**Method:** every covered test lane re-run green at HEAD (388 test executions by this verifier, zero failures), plus this verifier's OWN agreement probe (bare production construction, both divergence modes + control) and a NON-VACUOUS env-kernel flip probe with a contrast control; structural gates, scoped ruff+ty, decision coverage, and a fresh covered-input fingerprint.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | SC1 one-click download via registry `download_url`; on landing, presence flips to ✓ in the selection table AND the environment check | ✓ VERIFIED | **Agreement property undisturbed by 11-08 — re-proven at HEAD.** The 11-08 `resolve_dirs` threading is on the OUTPUT-root axis only: `sweep_launcher.launch_spec` keys `_spawn` on `rc.resolve_dirs(spec).output_root_abs` (:612, the WR-01 launcher-registry basis — kill/detach/tee/attach keys, D-14); it never touches `dataset_root`. The dataset lane is byte-identical: `_datasets_base()` (download_queue.py:1187-1212) reads `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs`; consumption env_check.py:182/:212 binds the same chain; `compose_argv` threads `--dataset_root` via `_abs_against_repo_root` (run_config.py:1158-1160). Committed lane: queue module 195 passed in 0.65s (three `_cr01` agreement tests + four L6H-03 pins included). Verifier's own probe at HEAD (`.venv/bin/python -I /tmp/cr01-repro3/repro.py`, exit-verified): mode1 spec-without-file landing==consumption==configured root; mode2 relative-file CWD≠repo both == REPO_ROOT-anchored; control both == repo `pipeline/`. **Non-vacuous flip probe** (`/tmp/cr01-repro3/flip.py`, real `default_kernels()["dataset_dirs"]` under a configured root): control 50-of-50 missing with `GUE__emp_H3` exactly listed → after landing at the queue's resolved base 49-of-50, key ABSENT from the missing lines. Six landing legs funnel through the one helper at :2125/:2154/:2330/:2401/:2469/:2919 (line refs byte-identical to the 4baaa2b pass). |
| 2 | SC2 queue persists across TUI exit/crash and resumes where it stopped after restart | ✓ VERIFIED | Queue module fully green at HEAD (restart-resume end-to-end service tier, 20-row exhaustive transition table, credential-free 12-field persisted set — all in the 195); `test_boot_resume_rehydrates_and_kicks_once` green in the 32-pass named set; boot kick solely via `tui/__main__.py` (untouched — not in the 11-08 diff). The app.py 11-08 delta is confined to ExitModal/action_quit (WR-05) — the app's shared bare `DownloadQueueService()` construction (:400-403) and the queue worker/kick paths are byte-identical. All four covered Pilot modules (data_manager/nav_shell/selection/selection_custom — the app.py regression surface) green: 129 passed. |
| 3 | SC3 every landed download reconciles rows vs n_audit; mismatches prominent, never silently accepted | ✓ VERIFIED | Queue module green at HEAD: real-subprocess reconcile pass pair, mismatch-no-deletion, `test_committed_artifacts_byte_unchanged_across_real_reconcile_run`, `test_reaudit_argv_exactly_interpreter_and_script_no_flags`; `test_mismatch_banner_block_and_sort_to_top` green in the named set. The reconcile staged `Dataset_path` absolutization joins against the rerouted base (:2469) — unchanged since the passed round. |
| 4 | SC4 Zenodo bulk bundle (record 19135551, once public) reachable as alternate whole-package entry | ✓ VERIFIED | Full zenodo module green (23 tests, in the 32-pass run); `test_z_enqueues_only_when_public_never_silent_otherwise` green; extract target :2330 rides the rerouted base. strings.py's 11-08 additions touch only LNC_/MON_ blocks — the DL_/QUEUE_ string contract is untouched. |
| 5 | SC5 subprocess/thread-worker discipline (console never freezes); zero credentials stored or echoed | ✓ VERIFIED | Queue module green at HEAD: LIST argv / `start_new_session` / PIPEs / `env = dict(os.environ)` pins, credential-free persisted set, and the AST-based `test_service_module_never_imports_modelscope` ban — all in the 195. The 11-08 sweep_launcher tee change (O_EXCL + suffix retry) is launcher scope (phase 11 SCs) and introduces no in-process import; the ExitModal kill loop reuses the same launcher kill seam. |

**Score:** 5/5 truths verified (0 present-but-behavior-unverified).

### The key interaction — 11-08 `resolve_dirs` threading vs SC1 (checked, disjoint)

The caller-flagged risk: 11-08 threaded `rc.resolve_dirs(spec).output_root_abs` through `launch_spec` (`sweep_launcher.py:612`) and the CR-02 live-root pre-check (`tui/screens/run_config.py:1900` — phase 11's covered set, not phase 10's). Verification:

1. **Axis separation** — the threading concerns `output_root_abs` (where the sweep WRITES; launcher registry keys for kill/detach/tee/auto-attach). Phase 10's SC1 property concerns `dataset_root_abs` (where downloads LAND vs where the run/env-check READS). No code path from `launch_spec`/`_spawn` touches the dataset base.
2. **Chain byte-identity** — `download_queue.py`, `run_config.py`, `env_check.py` all unchanged in `4baaa2b..dd16ad6` (last touches: `00f3e19` / `1f16b3d` / `aa6161d` respectively, all at-or-before the passed 4baaa2b state).
3. **Behavioral re-proof** — the three `_cr01` agreement tests green in the 195-pass lane, plus this verifier's own fresh probe (agreement ×3 configurations + kernel flip 50→49 with exact-token contrast) at HEAD.
4. **Same discipline, not a conflict** — WR-01's root-basis rule aligns the launcher with the SAME `resolve_dirs`/REPO_ROOT anchoring the 10-07 reroute established for the dataset lane; the two changes compose rather than compete.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/download_queue.py` | The rerouted `_datasets_base` (run-config chain, the `_models_base` twin); six landing legs funnel through it | ✓ VERIFIED | Byte-identical to the passed 4baaa2b state (outside the 11-08 diff); reroute live at :1187-1212; legs at :2125/:2154/:2330/:2401/:2469/:2919; module lane 195 green |
| `tests/tui/test_services_download_queue.py` | Three `_cr01` agreement tests + dual-root autouse pin + four L6H-03 pins | ✓ VERIFIED | Unchanged since 00f3e19/cfbd9aa; 195 passed in 0.65s at HEAD |
| `tui/app.py` (11-08-delta covered file) | Phase-10 surfaces (queue construction, worker, boot resume, data-manager wiring) intact under the WR-05 exit-modal change | ✓ VERIFIED | Bare `DownloadQueueService()` at :400-403 unchanged; queue/worker paths untouched; all four covered Pilot modules green (129 passed) |
| `tui/services/sweep_launcher.py` (11-08-delta covered file) | WR-04 tee + WR-01 root-basis; no dataset-lane contact | ✓ VERIFIED | `resolve_dirs` appears only at :573/:612 for `output_root_abs`; `grep dataset` → no hits; covered test surface green |
| `tui/strings.py` (11-08-delta covered file) | Phase-10 DL_/QUEUE_ string contract untouched | ✓ VERIFIED | 11-08 diff touches only `LNC_EXIT_MESSAGE_MULTI`, `MON_RERUN_CONFIRM`, `MON_RERUN_NO_SEEDS` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `DownloadQueueService._datasets_base()` | `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` | the same chain the env-check `dataset_dirs` kernel (env_check.py:182/:212) and `compose_argv`'s `--dataset_root` (run_config.py:1158-1160) consume | ✓ WIRED | Code-read at HEAD + verifier probe agreement ×3 configurations + kernel-flip contrast + three green `_cr01` tests |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_datasets_base()` | `dirs.dataset_root_abs` | `run_config.load_state()` (run_config.json spec, seeded from directories.json via `seed_directory_defaults`) → `resolve_dirs` (REPO_ROOT-anchored) | ✓ | FLOWING — read per call, never memoized; the flip probe lands at the derived base and the real kernel re-read flips |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|--------|---------|--------|--------|
| CR-01 agreement: mode1 + mode2 + control (verifier's own repro, bare production construction) | `.venv/bin/python -I /tmp/cr01-repro3/repro.py` | AGREE=True ×3, exit 0 | ✓ PASS |
| CR-01 behavioral flip: real `dataset_dirs` kernel, configured root, exact-token contrast control | `.venv/bin/python -I /tmp/cr01-repro3/flip.py` | 50/50 missing `GUE__emp_H3` listed → 49/50, key absent | ✓ PASS |
| Queue module lane (3 `_cr01` + 4 L6H-03 pins + 188 others) | `.venv/bin/python -m pytest tests/tui/test_services_download_queue.py -q` | 195 passed in 0.65s | ✓ PASS |
| Named SC-evidence set (d-enqueue, overlay flip, mismatch-never-flips, live flip, z-toast, env-route, boot-resume, seeded snapshot CR-01, mismatch banner) + full zenodo module | `.venv/bin/python -m pytest <9 node IDs> tests/tui/test_services_zenodo_bundle.py -q` | 32 passed in 1.85s | ✓ PASS |
| All four covered Pilot modules (app.py regression surface) | `.venv/bin/python -m pytest tests/tui/test_pilot_data_manager.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_selection.py tests/tui/test_pilot_selection_custom.py -q` | 129 passed in 52.37s | ✓ PASS |
| Gauntlet module (covered set) | `.venv/bin/python -m pytest tests/tui/test_services_gauntlet.py -q` | 32 passed in 0.11s | ✓ PASS |
| Structural gates on the production file | `grep "^import directories_config"` / `grep "load_directories_tolerant"` over download_queue.py | both absent | ✓ PASS |
| ruff + ty (scoped to covered files incl. the three 11-08-delta files) | `.venv/bin/python -m ruff check …` / `.venv/bin/python -m ty check …` | All checks passed (both) | ✓ PASS |

Full-suite note (caller-provided box baseline, not re-run here — single-named-test discipline): 7 failed / 1743 passed / 9 xfailed. The delta vs the 4baaa2b baseline (7/1734/9) is exactly +9 passed = 11-08's new tests; the 7 failures are the recorded pre-existing set (test_determinism ×1, test_schemas ×5, test_services_run_config::test_storage_overview_defaults_mirror_real_consumers ×1), none in any phase-10 covered lane — this verifier's own covered-lane runs (388 executions) are fully green. The 2×2 GPU smoke writes only under `pipeline/finetuned/smoke-2x2-261014` + `pipeline/logs` (background noise, outside the covered surface).

### Probe Execution

No probe scripts are declared for this phase (plans' verify blocks are pytest/make lanes) — N/A. The two ad-hoc verifier probes above ran under `/tmp/cr01-repro3/` and leave no repo pollution (working tree: only the pre-existing `.planning/` state files).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 10-01..10-07 | One-click ModelScope download, registry `download_url` sole authority; presence flips in selection table AND env check | ✓ SATISFIED | SC1 row: chain byte-identity + verifier agreement probe + non-vacuous kernel flip + 195-pass lane |
| DATA-02 | 10-01, 10-04, 10-06 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 row |
| DATA-03 | 10-02 | Row-count reconciliation vs n_audit, mismatches prominent | ✓ SATISFIED | SC3 row |
| DATA-04 | 10-03 | Zenodo whole-package alternate entry | ✓ SATISFIED | SC4 row |

No orphaned requirements (REQUIREMENTS.md maps exactly DATA-01..04 to Phase 10; all four marked Complete).

### Decision Coverage

`check.decision-coverage-verify` → 16/16 honored, none not honored (non-blocking gate).

### Anti-Patterns Found

None. Debt-marker greps (`TBD|FIXME|XXX`, `TODO|HACK|PLACEHOLDER`) clean over all covered production files and the three 11-08-delta covered files; the `*PLACEHOLDER*` grep hits are named UI input-hint string constants (`SEL_FILTER_PLACEHOLDER` = "输入过滤词…" etc.) — intentional input-field placeholder text, not stubs. No stub patterns, no empty implementations.

### Advisory (New Scope / Out-of-SC, carried forward)

All four remain `open` in 10-REVIEW-DISPOSITION.md. None is a phase-10 SC; the model lane, model presence column, and model drill-down rows are dcl/mlc scope layered after phase 10. Three of the four host files are untouched since the 4baaa2b pass (selection.py, data_manager.py, and strings.py's IN-02 line — 11-08 edited strings.py but not that line). None gained or lost evidence this round; none breaches an SC; none blocks.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 failed KIND_MODEL download → 下载 column 已下载 (is_dir presence vs config.json done gate) | other | Reproduced at the 4baaa2b pass; model-presence column is dcl/mlc scope, no phase-10 SC covers it |
| 2 | WR-02 channel_detail renders unknown (unknown_key) for healthy KIND_MODEL rows | other | Degrades the D-03 drill-down only for post-phase-10 row kinds |
| 3 | IN-01 z probe-in-flight window asserts 未公开 as fact | other | Transient copy issue; SC4 reachability and never-silent behavior unaffected |
| 4 | IN-02 ABOUT_MILESTONE_STAGE names phase 9 (strings.py:605) | other | Cosmetic milestone metadata; no SC relevance; re-read at this pass, still stale |

Housekeeping notes for the maintainer: (a) 10-REVIEW-DISPOSITION.md's table row for CR-01 reads `fixed` but the frontmatter still carries `disposition: open` / `open: 5` — flip the frontmatter at triage so the counts agree; (b) the four advisories above remain the maintainer's separate fix queue.

### Human Verification Required

None — both prior live items remain discharged (10-UAT.md, 2026-10-13: the GB10 live smoke incl. the presence flip, and the `g` four-artifact check, baseline `2f7211d`). This refresh's delta (11-08) changed no phase-10 user-facing surface: the exit-modal/tee/strings changes are phase-11 SC surfaces, and the SC1 flip is re-proven mechanically (agreement ×3) and behaviorally (the non-vacuous kernel-flip contrast above). An optional live smoke under a configured slot-4 root remains available via the 10-06 procedure but gates nothing here.

### Gaps Summary

None. The staleness trigger (11-08 touching three covered files) is fully cleared: the touched changes sit on the output-root/exit-modal/string axes, disjoint from every phase-10 SC chain; the SC1 dataset chain is byte-identical to the passed state and behaviorally re-proven at HEAD; SC2-SC5 lanes all green; zero regressions.

### Fingerprint Refresh

`covered_files`/`covered_digest` in the frontmatter are the verbatim `verification.fingerprint` output at HEAD dd16ad6 (supersedes `v3:sha256:b1282997…` of the 4baaa2b pass; identical file scope, new digest reflecting the 11-08 edits to app.py/sweep_launcher.py/strings.py).

---

_Verified: 2026-10-14T17:42:32Z (HEAD dd16ad6)_
_Verifier: Claude (gsd-verifier, convergence staleness refresh round 3)_
