---
phase: 10-data-manager-downloads-verification
verified: 2026-10-14T16:01:25Z
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
covered_digest: "v3:sha256:b1282997702424b993661593c24d6fc62700bd3be1d1c13b2e35366025d993f6"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "SC1 env-check conjunct (CR-01): _datasets_base rerouted through run_config.resolve_dirs(run_config.load_state()).dataset_root_abs (the _models_base twin, per-call never memoized); landing base == consumption base re-executed by THIS verifier across all three repro configurations (spec-without-file, relative-file CWD!=repo, aligned default) plus a behavioral env-kernel flip probe under a configured root"
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-01 — a failed KIND_MODEL download flips the selection 下载 column to 已下载: model_presence gates on is_dir only (tui/services/selection.py) while the model-lane done gate requires config.json (MODEL_DONE_MARKER)"
    category: other
    reason: "Carried forward unchanged (gap round touched neither file). Operator-facing correctness defect in the model presence column, deterministically reproduced at the prior pass; model lane and its presence column are dcl/mlc scope layered after phase 10; no phase-10 SC covers it. Disposition-open in 10-REVIEW-DISPOSITION.md for the maintainer's fix queue"
    evidence_status: "reproduced at prior pass (dir without config.json -> 'present'); untouched by the gap round"
  - finding: "WR-02 — the slot-3 drill-down renders channel: unknown (unknown_key) for healthy KIND_MODEL queue rows (channel_detail consults only the DATASET registry)"
    category: other
    reason: "Carried forward unchanged. Degrades the D-03 drill-down surface only for KIND_MODEL rows that did not exist at phase 10; no phase-10 SC covers model-row drill-down content. Disposition-open"
    evidence_status: "code-traced at prior pass; untouched by the gap round"
  - finding: "IN-01 — z pressed during the mount probe-in-flight window fires DL_ZENODO_DISABLED_TOAST as fact while _zenodo_state is still None (tui/screens/data_manager.py)"
    category: other
    reason: "Carried forward unchanged. Transient copy issue; SC4 reachability and never-silent behavior unaffected. Disposition-open"
    evidence_status: "code-read at prior pass; untouched by the gap round"
  - finding: "IN-02 — ABOUT_MILESTONE_STAGE stale (names phase 9) in tui/strings.py"
    category: other
    reason: "Carried forward unchanged. Cosmetic milestone metadata, documented 'updated per milestone'; no SC relevance. Disposition-open"
    evidence_status: "code-read at prior pass; untouched by the gap round"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report — Gap-Closure Re-Verification (Round 2)

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-14T16:01:25Z at HEAD 4baaa2b (branch autorun)
**Status:** passed — 5/5 SCs hold; the SC1 gap (CR-01) is closed and independently re-reproduced in the agreeing direction
**Re-verification:** Yes — gap-closure round 2. Prior gaps_found 4/5 (2026-10-14T15:28:17Z, HEAD 92166f2, digest `v3:sha256:5aa541ba…`); gap plan 10-07 executed (RED `cfbd9aa` / GREEN `00f3e19` / docs `4baaa2b`); the gap-round code delta is exactly two files (`tui/services/download_queue.py`, `tests/tui/test_services_download_queue.py`) — confirmed by `git diff --stat 92166f2..HEAD`.

**Method:** the prior gap re-executed by this verifier's OWN isolated reproduction (not the committed tests): injected `DNALLMMARK_TUI_STATE_DIR`/`DNALLMMARK_TUI_CONFIG_DIR` roots, the BARE production construction (`DownloadQueueService()`, exactly as `tui/app.py:388` constructs it), `.venv/bin/python -I`, both divergence modes plus the aligned control, AND a behavioral flip probe running the REAL env-check `dataset_dirs` kernel against a landing created at the queue's resolved base. Committed-lane re-runs: the full queue module (195 passed), a 9-node named SC-evidence set + the full zenodo module (31 passed), scoped ruff + ty, both structural gates, AST-level import scan, and the four L6H-03 pins proven byte-identical across the round.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | SC1 one-click download via registry `download_url`; on landing, presence flips to ✓ in the selection table AND the environment check | ✓ VERIFIED | **Gap closed — independently re-reproduced in the agreeing direction.** `_datasets_base()` (download_queue.py:1187-1212 at HEAD): param tier > `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` > repo `pipeline/` — the exact `_models_base` twin (:1216-1242), read per call (never memoized). Verifier repro (`.venv/bin/python -I /tmp/cr01-repro2/repro.py`, exit 0): mode 1 (spec-without-file, the primary slot-4 UI flow) landing == consumption == configured root; mode 2 (relative `directories.json` value, CWD=/tmp) both == `REPO_ROOT/rel-ds` (REPO_ROOT-anchored, NOT CWD-anchored); control both == repo `pipeline/`. **Behavioral flip probe**: with `dataset_root=/tmp/cr01-repro2/probe-data` configured, a landing created at the queue's base (`<root>/datasets/GUE/emp_H3/{train,dev,test}.csv`) makes the REAL `env_check.default_kernels()["dataset_dirs"]` kernel flip — 49/50 missing, `GUE__emp_H3` exactly the one no longer listed. Committed pins: the three `_cr01` agreement tests (state written via the service's own `save_state`, consumption twin imported from the same module the queue imports) green in the 195-pass module lane; the positive chain (registry-only authority, slot-3/slot-2 `d` enqueue, landing gate, reconcile gate, overlay flip, mismatch-never-flips, env route `[3]`) re-confirmed green (31-pass named set). All six dataset landing legs funnel through the one helper (:2125 landing gate, :2154 shape-C rename, :2330 zenodo extract, :2401 landed-keys scan, :2469 reconcile staged path, :2919 ChannelSpec local_dir) — one reroute covers every leg. |
| 2 | SC2 queue persists across TUI exit/crash and resumes where it stopped after restart | ✓ VERIFIED | Unchanged by the gap round (no engine/persistence edits — diff confirmed). Module lane at HEAD: `test_restart_resume_end_to_end_service_tier`, `test_state_machine_transition_table_exhaustive` (20 rows), `test_persisted_entries_carry_no_credential_fields` (12-field exact set, credential-free) all green in the 195; `test_boot_resume_rehydrates_and_kicks_once` green in the named set; boot kick solely via `tui/__main__.py` (file untouched this round). |
| 3 | SC3 every landed download reconciles rows vs n_audit; mismatches prominent, never silently accepted | ✓ VERIFIED | Unchanged by the gap round. Module lane at HEAD: real-subprocess pass pair + mismatch-no-deletion, `test_committed_artifacts_byte_unchanged_across_real_reconcile_run`, `test_reaudit_argv_exactly_interpreter_and_script_no_flags` all green in the 195. The reconcile staged `Dataset_path` absolutization now joins against the rerouted base (:2469) — same agreement chain as SC1. |
| 4 | SC4 Zenodo bulk bundle (record 19135551, once public) reachable as alternate whole-package entry | ✓ VERIFIED | Unchanged by the gap round. Full zenodo module green (22 tests) + `test_run_task_zenodo_bundle_offline_end_to_end_done` in the 195; slot-3 `test_z_enqueues_only_when_public_never_silent_otherwise` green in the named set; extract target :2330 rides the rerouted base. |
| 5 | SC5 subprocess/thread-worker discipline (console never freezes); zero credentials stored or echoed | ✓ VERIFIED | Re-checked at HEAD: LIST argv / `start_new_session` / PIPEs / `env = dict(os.environ)` pins green in the 195; model lane `[sys.executable, "-I", "-c", MODEL_DOWNLOAD_PROGRAM, landing, repo_id]` fixed program (:1947). **modelscope-import scan**: raw grep hits `from modelscope...` at :227 — that is STRING DATA inside the fixed `MODEL_DOWNLOAD_PROGRAM` constant (the `-I` child's own code, subprocess payload, never an in-process import); the AST-level scan answers ZERO real modelscope imports, and the AST-based `test_service_module_never_imports_modelscope` (:850, upgraded 261014-mlc precisely to keep this invariant strong against the string false-positive) is green. Credential-free persisted set re-pinned. |

**Score:** 5/5 truths verified (0 present-but-behavior-unverified).

### The closed gap — CR-01 flip-checked (verifier's own evidence)

The prior pass's two divergence modes, re-executed at HEAD 4baaa2b with fresh injected roots and the bare production construction:

```text
[mode1: run_config.json dataset_root=/tmp/cr01-repro2/m1-sweep-data/inner, directories.json absent]
  landing(_datasets_base)   = /tmp/cr01-repro2/m1-sweep-data/inner
  consumption(load_state)   = /tmp/cr01-repro2/m1-sweep-data/inner   AGREE=True
[flip probe: landing at <root>/datasets/GUE/emp_H3]
  env kernel missing list   = 49 of 50; GUE__emp_H3 NOT listed (flipped present)
[mode2: directories.json relative "rel-ds", CWD=/tmp/cr01-repro2, no state file]
  landing(_datasets_base)   = /home/forrest/Github/dnallmmark/rel-ds
  consumption(load_state)   = /home/forrest/Github/dnallmmark/rel-ds  AGREE=True (REPO_ROOT-anchored, not CWD)
[control: nothing set]      AGREE=True (landing == repo pipeline/, consumption None)
RESULT: PASS (exit 0)
```

Consumption side confirmed at HEAD by code read: the env kernel binds `dirs = run_config.resolve_dirs(run_config.load_state())` and `check_dataset_dirs(root=dirs.dataset_root_abs)` (env_check.py:182/:211-212); `compose_argv` threads `--dataset_root` as `_abs_against_repo_root(spec.dataset_root)` (run_config.py compose_argv tail) — the identical chain the landing base now reads. The ENV_ROUTE 前往数据管理 loop closes under a configured root: download lands where the configured run reads, so the env recheck flips.

**L6H-03 semantics survival:** the four pins — `test_file_dataset_root_redirects_spec_local_dir_and_gate_naming`, `test_constructor_dataset_root_beats_file_key`, `test_absent_param_and_file_keep_repo_pipeline_datasets_form`, `test_corrupt_directories_json_degrades_to_repo_default` — proven **byte-identical** across the round (function-body diff 92166f2 vs HEAD: IDENTICAL ×4; the test-file diff's removed lines are import-statement extensions and docstring/banner text only, zero executable pin-body lines) and green unmodified in the 195-pass lane. The module autouse fixture now pins BOTH roots (`DNALLMMARK_TUI_CONFIG_DIR` + `DNALLMMARK_TUI_STATE_DIR`) — the hermeticity requirement, since after the reroute every `_datasets_base()` call reads `settings.state_dir()/run_config.json`.

**Structural gates (production file):** `grep "^import directories_config"` → absent; `grep "load_directories_tolerant"` → absent (all file awareness flows through `load_state()`). Both PASS.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/download_queue.py` | The rerouted `_datasets_base` (run-config chain, the `_models_base` twin) | ✓ VERIFIED | Reroute live at HEAD (:1187-1212); retired import gone; docstring/banner/param-doc updated; six landing legs funnel through it |
| `tests/tui/test_services_download_queue.py` | Three `_cr01` agreement tests + the dual-root autouse pin; four L6H-03 pins untouched | ✓ VERIFIED | 195 passed in 0.68s (192 pre-gap + 3 new); pins byte-identical |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `DownloadQueueService._datasets_base()` | `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` | the same chain the env-check `dataset_dirs` kernel (env_check.py:182/:212) and `compose_argv`'s `--dataset_root` consume | ✓ WIRED | Code-read at HEAD + verifier repro agreement in all three configurations + three green `_cr01` tests through the real services |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_datasets_base()` | `dirs.dataset_root_abs` | `run_config.load_state()` (run_config.json spec, seeded from directories.json via `seed_directory_defaults`) → `resolve_dirs` (REPO_ROOT-anchored) | ✓ | FLOWING — no static return; the chain is read per call, so a live slot-4 edit steers the next landing |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| CR-01 divergence modes 1+2 + control + env-kernel flip probe (verifier's own repro, bare production construction) | `.venv/bin/python -I /tmp/cr01-repro2/repro.py` | AGREE=True ×3; flip probe: key not in kernel missing list; exit 0 | ✓ PASS |
| Queue module lane (3 `_cr01` + 4 L6H-03 pins + 188 others) | `.venv/bin/python -m pytest tests/tui/test_services_download_queue.py -q` | 195 passed in 0.68s | ✓ PASS |
| Named SC-evidence set (flip/mismatch-never-flips/live-flip/d-enqueue/z/boot-resume/env-route/seeded-snapshot + full zenodo module) | `.venv/bin/python -m pytest <9 node IDs> tests/tui/test_services_zenodo_bundle.py -q` | 31 passed in 2.56s | ✓ PASS |
| Structural gates on the production file | `grep "^import directories_config"` / `grep "load_directories_tolerant"` | both absent | ✓ PASS |
| ruff + ty (scoped to the two touched files) | `.venv/bin/python -m ruff check …` / `.venv/bin/python -m ty check …` | All checks passed (both) | ✓ PASS |
| modelscope in-process import ban (SC5) | AST walk over download_queue.py | ZERO real imports (the :227 hit is string data in the fixed child program; AST test green) | ✓ PASS |
| L6H-03 pin byte-integrity | function-body diff 92166f2 vs HEAD, ×4 pins | IDENTICAL ×4 | ✓ PASS |

Full-suite note (caller-provided box baseline, not re-run here — single-named-test discipline): 7 failed / 1734 passed / 9 xfailed = the recorded pre-existing set (6 documented + 1 machine-state, recorded in the 10-07 plan gate at `ac26570` BEFORE the round) + this plan's 3 new agreement tests; none of the 7 is a phase-10 named test — the queue module lane is fully green at HEAD per this verifier's own run. The 2×2 GPU smoke writes only under `pipeline/finetuned/smoke-2x2-261014` + `pipeline/logs` (background noise, outside the covered surface).

### Probe Execution

No probe scripts are declared for this phase (plans' verify blocks are pytest/make lanes) — N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 10-01..10-07 | One-click ModelScope download, registry `download_url` sole authority; presence flips in selection table AND env check | ✓ SATISFIED (unblocked — the CR-01 gap is closed) | SC1 row above: agreement matrix + verifier repro + flip probe + the full positive chain |
| DATA-02 | 10-01, 10-04, 10-06 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 row above |
| DATA-03 | 10-02 | Row-count reconciliation vs n_audit, mismatches prominent | ✓ SATISFIED | SC3 row above |
| DATA-04 | 10-03 | Zenodo whole-package alternate entry | ✓ SATISFIED | SC4 row above |

No orphaned requirements (REQUIREMENTS.md maps exactly DATA-01..04 to Phase 10).

### Decision Coverage

`check.decision-coverage-verify` → 16/16 honored, none not honored (non-blocking gate).

### Anti-Patterns Found

None. Debt-marker greps (`TBD|FIXME|XXX`, `TODO|HACK|PLACEHOLDER`) clean over both gap-round files; no stubs, no placeholder surfaces; no repo pollution from the verifier repro (working tree shows only the pre-existing untracked `.planning/` files; the mode-2 `rel-ds` path is resolved, never created).

### Advisory (New Scope / Out-of-SC, carried forward)

All four remain `open` in 10-REVIEW-DISPOSITION.md and untouched by the gap round (`git diff 92166f2..HEAD` touches neither `tui/screens/selection.py`, `tui/screens/data_manager.py`, nor `tui/strings.py`). None breaches a phase-10 SC — the model lane, the model presence column, and the model drill-down rows are dcl/mlc scope layered after phase 10.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 failed KIND_MODEL download → 下载 column 已下载 (is_dir presence vs config.json done gate) | other | Reproduced at prior pass; model-presence column is dcl/mlc scope, no phase-10 SC covers it |
| 2 | WR-02 channel_detail renders unknown (unknown_key) for healthy KIND_MODEL rows | other | Degrades the D-03 drill-down only for post-phase-10 row kinds |
| 3 | IN-01 z probe-in-flight window asserts 未公开 as fact | other | Transient copy issue; SC4 reachability and never-silent behavior unaffected |
| 4 | IN-02 ABOUT_MILESTONE_STAGE names phase 9 | other | Cosmetic milestone metadata; no SC relevance |

Housekeeping note for the maintainer: CR-01's disposition row in 10-REVIEW-DISPOSITION.md still reads `open`; the fix is verified by this pass — flip it to `fixed` at triage.

### Human Verification Required

None — both prior live items remain discharged (10-UAT.md, 2026-10-13: the GB10 live smoke incl. the presence flip, and the `g` four-artifact check, baseline `2f7211d`). The gap round changed only base resolution — no new visual/external surface: the configured-root env-check flip is proven mechanically (agreement matrix) and behaviorally (the real kernel flip probe above), and the real-CLI landing behavior was live-discharged in the default config with the `--local_dir` derivation base-agnostic. An optional extra-assurance live smoke under a configured slot-4 root (enqueue → land → env recheck flips) is available to the maintainer via the 10-06 procedure but gates nothing here.

### Gaps Summary

None. The single prior gap — SC1's env-check conjunct (CR-01) — is closed with the exact planned fix shape (the one-helper reroute, the `_models_base` twin), verified by this verifier's own reproduction of both divergence modes in the agreeing direction, the aligned default control, a real env-kernel flip probe under a configured root, three committed agreement tests through the real services, the six-landing-leg funnel, byte-identical L6H-03 pins, both structural gates, and clean scoped ruff/ty. SC2-SC5 re-confirmed green at HEAD. The phase goal sentence — "an env-check presence FAIL is always diagnosable and fixable from the console" — now holds under configured roots.

### Fingerprint Refresh

`covered_files`/`covered_digest` in the frontmatter are the verbatim `verification.fingerprint` output at HEAD 4baaa2b (supersedes `v3:sha256:5aa541ba…` of the gaps_found pass; the covered set is unchanged in scope and now includes 10-07-PLAN/SUMMARY automatically).

---

_Verified: 2026-10-14T16:01:25Z (HEAD 4baaa2b)_
_Verifier: Claude (gsd-verifier, gap-closure re-verification round 2)_
