---
phase: 10-data-manager-downloads-verification
verified: 2026-10-14T15:28:17Z
status: gaps_found
score: 4/5 must-haves verified
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
covered_digest: "v3:sha256:5aa541baedc0197b9768524ff745787b5cfe0282988515f704bd8d9874d37fcb"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining:
    - "SC1 env-check conjunct: presence flips to present in the environment check — broken under a configured dataset root (CR-01, delta-introduced by quick-261014-l6h after the 2026-10-13 pass)"
  regressions:
    - "SC1: the queue's dataset landing base (_datasets_base, download_queue.py:1207-1213) resolves through directories.json CWD-anchored and ignores the run-config spec, while every consumption side (env kernel env_check.py:182/212, sweep launcher compose_argv --dataset_root) resolves REPO_ROOT-anchored through run_config.load_state() — deterministically reproduced, both divergence modes"
gaps:
  - truth: "SC1 — on landing, presence flips to present in the selection table AND the environment check (the env-check conjunct fails under a configured dataset root)"
    status: failed
    reason: "The l6h delta gave the queue's dataset landing base a chain (constructor param > directories.json dataset_root CWD-resolved > repo pipeline/) that diverges from the chain every consumption side uses (run_config.resolve_dirs(load_state()).dataset_root_abs, REPO_ROOT-anchored — the env-check dataset_dirs kernel and compose_argv's --dataset_root). With a slot-4 dataset root configured but directories.json absent (the primary UI flow: set 数据集根, never press [s] 保存默认), downloads land under repo pipeline/datasets while the env kernel and the launched sweep read <configured-root>/datasets. The queue's reconcile reads its own landing base, so the TUI flips presence to present for data the configured run cannot read — the env fail → [3] download → env recheck loop never closes, breaching the phase goal's core promise (an env-check presence FAIL always fixable from the console). A relative directories.json dataset_root diverges the same way whenever TUI CWD != repo root (Path(v).resolve() vs _abs_against_repo_root). The same delta routed the model lane correctly (_models_base walks the run-config chain 'so download landing and presence checking can never disagree about the root'); the dataset lane did not get the twin treatment."
    artifacts:
      - path: "tui/services/download_queue.py"
        issue: "_datasets_base (:1207-1213) file tier reads directories.json via Path(file_root).resolve() (CWD-anchored) and never consults run_config.load_state(); production constructs DownloadQueueService() bare (tui/app.py:388) so the param tier is never threaded"
      - path: "tui/services/env_check.py"
        issue: "consumption side (:182, :212) — check_dataset_dirs(root=resolve_dirs(load_state()).dataset_root_abs), REPO_ROOT-anchored"
    missing:
      - "Route the _datasets_base file tier through run_config.resolve_dirs(run_config.load_state()).dataset_root_abs exactly as _models_base (:1237-1242) already does for model_root_abs — load_state() already seeds the spec from directories.json (seed_directory_defaults fills UNSET fields only), so the file-tier redirect, param-beats-file, corrupt-file degrade, and byte-identity-when-absent semantics survive; only the CWD anchoring and the spec-blindness disappear"
      - "A regression test pinning landing-base/consumption-base agreement across the three configurations (spec set + no file; relative file value + CWD != repo; default)"
advisory:
  - finding: "WR-01 — a failed KIND_MODEL download flips the selection 下载 column to 已下载: model_presence gates on is_dir only (tui/services/selection.py:543-546) while the model-lane done gate requires config.json (MODEL_DONE_MARKER, download_queue.py:217/:1999); every exit-0 failure path (nonzero exit, model_nesting_ambiguous, model_hoist_error, landing_incomplete) leaves the landing dir the -I child created early"
    category: other
    reason: "Real operator-facing correctness defect in the model presence column, deterministically reproduced (dir without config.json -> 'present'); NOT a phase-10 SC breach — the model lane and its presence column are dcl/mlc scope layered after phase 10, and phase-10 SCs are dataset-scoped except SC5 (discipline/credentials, which hold). Flagged for the mlc-surface follow-up; open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "reproduced: python -I over tui.services.selection.model_presence with a dir-but-no-config.json landing -> PRESENT"
  - finding: "WR-02 — the slot-3 drill-down renders channel: unknown (unknown_key) for healthy KIND_MODEL queue rows: DataManagerBackend.channel_detail (tui/screens/data_manager.py:465-485) consults only the DATASET registry (resolve_channel), so model keys fall to the unknown branch despite a healthy dnallm -I channel"
    category: other
    reason: "Degrades the phase-10 D-03 verbatim drill-down surface, but only for KIND_MODEL rows that did not exist at phase 10; no phase-10 SC covers model-row drill-down content. Open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "code-traced: channel_detail has no model-registry fallback"
  - finding: "IN-01 — z pressed during the mount probe-in-flight window fires DL_ZENODO_DISABLED_TOAST ('尚未公开') as fact while _zenodo_state is still None (tui/screens/data_manager.py:1279)"
    category: other
    reason: "Transient copy issue only; the entry stays reachable (SC4 unaffected — the run-time leg re-probes regardless); the press is never silent. Open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "code-read"
  - finding: "IN-02 — ABOUT_MILESTONE_STAGE stale ('本相位: 9 自定义接入', tui/strings.py:605) while the shell records slots 4/5 real since phases 11-06/11-07"
    category: other
    reason: "Cosmetic milestone metadata, documented 'updated per milestone'; no SC relevance. Open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "code-read"
human_verification:
  - test: "GB10 live smoke (10-06-SUMMARY procedure): enqueue a missing dataset via d on slot 3; observe download → landing → reconcile → the presence flip + env-check flip"
    expected: "Toast chain → done; the key leaves the missing list; env recheck flips"
    result: "discharged 2026-10-13 (10-UAT.md item 1, live pass recorded at the prior verification); NOTE the env-check flip half of this live check is only meaningful in the DEFAULT (unconfigured-root) configuration until the SC1 gap is closed — under a configured dataset root the live smoke would now exhibit the divergence"
    why_human: "Requires the real modelscope CLI + token + a multi-GB download on the GB10 host"
  - test: "The g re-audit four-artifact live check"
    expected: "git status shows exactly the four committed artifacts"
    result: "discharged 2026-10-13 (10-UAT.md item 2; baseline committed as 2f7211d)"
    why_human: "No CI test may execute a default-outputs audit by design"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report — Stale-Refresh Re-Verification

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-14T15:28:17Z at HEAD 92166f2 (branch autorun)
**Status:** gaps_found — 4/5 SCs hold; SC1's env-check conjunct is broken under a configured dataset root (CR-01, delta-introduced, deterministically reproduced)
**Re-verification:** Yes — stale refresh. Prior PASS at HEAD 8b92766 (2026-10-13T09:33:12Z, digest `v3:sha256:bd4a0243…`); 117 commits since, including quick tasks 261014-c2l/dcl/f4w/l6h/mlc and phases 07-09 verification docs. Covered files heavily modified: download_queue.py (+614), screens/selection.py (+639), screens/data_manager.py (+298), run_config.py (+360), plus services/env_check.py, services/selection.py, registries.py, strings.py, app.py.

**Method:** goal-backward against the CURRENT code. Every SC chain re-traced through the live source (not the prior report's line numbers), the CR-01 divergence modes executed as an isolated reproduction (`.venv/bin/python -I`, injected XDG state/config roots, production-style bare construction), and 16 named SC-evidence tests + 3 slot-3 Pilot tests run green individually. The five 10-REVIEW.md findings (1 Critical / 2 Warning / 2 Info, all delta-introduced, all disposition `open` in 10-REVIEW-DISPOSITION.md) adjudicated under #3304 and the phase's own SCs.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | SC1 one-click download via registry `download_url`; on landing presence flips in the selection table AND the environment check | ✗ FAILED | The positive chain holds and is test-pinned (registry-only authority `resolve_channel` :2872; slot-3 `d` enqueue_cursor → service.enqueue → kick, Pilot-pinned `test_d_enqueues_missing_cursor_with_all_outcome_toasts`; landing gate `_landing_details` :2108-2139; reconcile gate; overlay flip `test_overlay_flips_missing_presence_to_present_and_back`, `test_missing_datasets_flips_over_done_reconciled_entries_cr01`, `test_backend_missing_snapshot_flips_over_real_seeded_state_cr01`, `test_mismatch_and_failed_entries_never_flip_presence` — all green). But the ENV-CHECK conjunct fails under a configured dataset root: `_datasets_base()` (download_queue.py:1207-1213) resolves directories.json CWD-anchored and ignores the run-config spec, while the env kernel (env_check.py:182/212) and the sweep launcher (`compose_argv` --dataset_root) resolve REPO_ROOT-anchored through `run_config.load_state()` — downloads land where the configured run cannot read while the queue's own reconcile flips TUI presence present. Deterministic repro below. This is CR-01 from 10-REVIEW.md, confirmed as a truth-level breach, not merely a review opinion. |
| 2 | SC2 queue persists across exit/crash and resumes | ✓ VERIFIED | Persist/downgrade machinery intact: `_persist_locked` exact `_ENTRY_FIELDS` set (now 12 fields incl. the mlc `kind` — still credential-free, `test_persisted_entries_carry_no_credential_fields` green); `_load_locked` downgrade is state-based and kind-agnostic (covers KIND_MODEL), active-key guard and IN-11 ordering preserved; boot kick only via `tui/__main__.py`. Named tests green: `test_restart_resume_end_to_end_service_tier`, `test_boot_resume_rehydrates_and_kicks_once`, `test_state_machine_transition_table_exhaustive`. |
| 3 | SC3 every landed download reconciles rows vs n_audit; mismatches prominent, never silently accepted | ✓ VERIFIED | `reconcile_dataset` (:2449-2519 read at HEAD): candidate-only temp registry, `Dataset_path` ABSOLUTIZED against the queue's base, all four output flags at temp paths, env = os.environ + one CUSTOM_DIR_ENV override, verdict from the parsed temp n_audit. Reworked slot-3 keeps prominence: `_sorted_entries` mismatch/failed first (:530-536), `queue-banner-mismatch` (:997). Named tests green: real-subprocess pass pair + mismatch-no-deletion, `test_mismatch_banner_block_and_sort_to_top`, `test_reconcile_cells_four_vocabularies`, `test_reaudit_argv_exactly_interpreter_and_script_no_flags`, `test_committed_artifacts_byte_unchanged_across_real_reconcile_run`. |
| 4 | SC4 Zenodo 19135551 alternate whole-package entry reachable | ✓ VERIFIED | mlc demoted the line to the queue title row (`备选`), still reachable: `z` binding (:600), `action_zenodo_bundle` (:1276) enqueues only on PROBE_PUBLIC, never-silent otherwise; four-state line (:1004-1016: probing/public/not_public/failed); `probe_zenodo` delegates through the queue's seam (:455-463). `test_run_task_zenodo_bundle_offline_end_to_end_done` and `test_z_enqueues_only_when_public_never_silent_otherwise` green. |
| 5 | SC5 subprocess/thread-worker discipline; console never freezes; zero credentials | ✓ VERIFIED | Both lanes: LIST argv, `start_new_session=True`, PIPEs, env exactly `dict(os.environ)`; dataset lane `compose_download_argv`, model lane `[sys.executable, "-I", "-c", MODEL_DOWNLOAD_PROGRAM, landing, repo_id]` (:1944-1945, fixed program — no operator code); driver `@work(exclusive=True, thread=True)`; zero modelscope imports in `tui/` (re-grepped at HEAD); persisted set pinned credential-free. Note: under the SC1 divergence the model lane's `_models_base` (:1237-1242) is the CORRECT pattern — it walks the run-config chain so landing and presence agree. |

**Score:** 4/5 truths verified (0 present-but-behavior-unverified).

### The SC1 failure — CR-01 traced and reproduced (deterministic evidence)

Reproduction (this verifier, `.venv/bin/python -I /tmp/cr01-repro/repro.py`, injected `DNALLMMARK_TUI_STATE_DIR`/`DNALLMMARK_TUI_CONFIG_DIR`, `DownloadQueueService` constructed exactly as production app.py:388 does):

```text
[mode1: run_config.json carries dataset_root=/tmp/cr01-repro/sweep-data, directories.json absent]
landing(_datasets_base)   = /home/forrest/Github/dnallmmark/pipeline
consumption(load_state)   = /tmp/cr01-repro/sweep-data      AGREE=False
[mode2: directories.json carries relative "rel-ds", CWD=/tmp/cr01-repro, no state file]
landing(_datasets_base)   = /tmp/cr01-repro/rel-ds
consumption(load_state)   = /home/forrest/Github/dnallmmark/rel-ds   AGREE=False
[aligned control: nothing set]                              AGREE=True (both repo pipeline/)
```

Mode 1 is the primary UI flow: the operator sets 数据集根 on slot 4 (the spec persists/threads — `compose_argv` emits `--dataset_root`, the env kernel checks it) without pressing `[s]` 保存默认 (which is what writes directories.json). The download then lands under repo `pipeline/datasets`, the queue's reconcile passes over its own base, the TUI flips presence present — and the env recheck still FAILs. The `ENV_ROUTE_MISSING_DATASETS` loop (strings.py:118-119: "⚠ … [3] 前往数据管理") never closes, breaching the goal sentence "an env-check presence FAIL is always diagnosable and fixable from the console". Mode 2 breaks whenever the TUI runs from a CWD other than the repo root (`Path(v).resolve()` vs `_abs_against_repo_root`).

#3304 adjudication: this is a Step-3 TRUTH failure (SC1's env-check conjunct), not a Step-7 anti-pattern opinion — the evidence gate does not apply to truth failures. Even under the gate's own terms it is in-contract blocking: delta-introduced (l6h, `acb50a4`), on a file modified since the prior pass (download_queue.py, 3 commits since 2026-10-13T09:33:12Z), AND backed by deterministic evidence (the reproduction above). No override exists or is suggested — the fix is a real code change with a precedent twin in the same file.

### Advisory (New Scope / Out-of-SC, per #3304 and the phase's own SCs)

All five 10-REVIEW.md findings remain `open` in 10-REVIEW-DISPOSITION.md. CR-01 is promoted to the gap above; the remaining four are advisories — none breaches a phase-10 SC (the model lane, the model presence column, and the model drill-down rows are dcl/mlc scope that did not exist at phase 10; SC5's discipline/credential claims hold for the model lane).

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 failed KIND_MODEL download → 下载 column 已下载 (is_dir presence vs config.json done gate) | other | Reproduced (`dir-exists-no-config.json -> 'present'`); model-presence column is dcl/mlc scope, no phase-10 SC covers it |
| 2 | WR-02 channel_detail renders unknown (unknown_key) for healthy KIND_MODEL rows | other | Degrades the D-03 drill-down only for post-phase-10 row kinds; no SC covers model-row drill-down content |
| 3 | IN-01 z probe-in-flight window asserts 未公开 as fact | other | Transient copy issue; SC4 reachability and never-silent behavior unaffected |
| 4 | IN-02 ABOUT_MILESTONE_STAGE names phase 9 | other | Cosmetic milestone metadata; no SC relevance |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 13 SC-evidence tests (flip set, restart e2e, real-subprocess reconcile pair, reaudit argv, byte-unchanged, zenodo e2e, credential fields, transition table) | `.venv/bin/python -m pytest <13 named tests> -q` | 32 passed in 0.54s | ✓ PASS |
| Slot-3 one-click enqueue + z never-silent + boot resume | `pytest test_d_enqueues_missing_cursor_with_all_outcome_toasts test_z_enqueues_only_when_public_never_silent_otherwise test_boot_resume_rehydrates_and_kicks_once -q` | 3 passed in 1.97s | ✓ PASS |
| CR-01 divergence modes 1+2 (+ aligned control) | `.venv/bin/python -I /tmp/cr01-repro/repro.py` | AGREE=False / AGREE=False / control AGREE=True, exit 1 | ✗ FAIL (the gap) |
| WR-01 presence gate | `.venv/bin/python -I` over `selection.model_presence`, dir without config.json | `{'fake': 'present'}` | ✗ FAIL (advisory) |

Full-suite note (caller-provided baseline, not re-run here): 7 failed / 1731 passed / 9 xfailed on this box, with a 2×2 GPU smoke writing only under `pipeline/finetuned/smoke-2x2-261014` + `pipeline/logs` — treated as background noise; no phase-10 named test is among the failures run here.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 10-01..10-06 | One-click ModelScope download, registry `download_url` sole authority | ✗ PARTIAL — BLOCKED by SC1 gap | Chain present and test-pinned in default config; env-check fix-from-console promise broken under configured roots (CR-01) |
| DATA-02 | 10-01, 10-04, 10-06 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 evidence above |
| DATA-03 | 10-02 | Row-count reconciliation vs n_audit, mismatches prominent | ✓ SATISFIED | SC3 evidence above |
| DATA-04 | 10-03 | Zenodo whole-package alternate entry | ✓ SATISFIED | SC4 evidence above |

No orphaned requirements (REQUIREMENTS.md maps exactly DATA-01..04 to Phase 10; all marked Complete — DATA-01's Complete status predates the l6h regression and should be revisited after gap closure).

### Decision Coverage

`check.decision-coverage-verify` → 16/16 honored, none not honored (non-blocking gate).

### Anti-Patterns Found

Debt markers: none in any covered file (`TBD|FIXME|XXX` and `TODO|HACK` greps clean over the delta surface). The five review findings are adjudicated above (1 gap, 4 advisories); no stubs, no placeholder surfaces.

### Constraint Checklist (delta spot re-check)

- Official registries `pipeline/models_info.json` / `datasets_info.json`: `git diff 8b92766..HEAD --name-only` over them — unchanged by the covered delta except the ir9/l6h registry-maintenance commits outside phase-10 surfaces ( Chaoba removal, dnallm_compat.json addition) — registry authority for channel resolution intact (`SHAPE_A_REPOS` census still code-owned).
- Zero modelscope imports in `tui/` — re-grepped at HEAD: no matches.
- Strings single-home: new `DL_`/zenodo variants live in `tui/strings.py` (:637-646).

### Gaps Summary

One gap, truth-level, delta-introduced: SC1's environment-check conjunct. The dataset landing base must resolve through the same chain the env kernel and sweep launcher consume (`run_config.resolve_dirs(run_config.load_state()).dataset_root_abs`, REPO_ROOT-anchored) — the exact treatment the same delta already gave `_models_base()`. Until then, the phase's headline promise ("an env-check presence FAIL is always diagnosable and fixable from the console") is false for any operator who configures a dataset root on slot 4 without saving it as a default, and the console actively misleads (flips presence present for data the configured run cannot read). Four further review findings are advisories outside the phase-10 SCs, all recorded open in 10-REVIEW-DISPOSITION.md.

### Fingerprint Refresh

`covered_files`/`covered_digest` in the frontmatter are the verbatim `verification.fingerprint` output over HEAD 92166f2 (supersedes `v3:sha256:bd4a0243…` of 2026-10-13; the covered set now additionally names the delta surfaces this verification traced: `tui/services/run_config.py`, `tui/services/env_check.py`, `tui/services/selection.py`, `tui/services/registries.py`, `pipeline/directories_config.py`).

---

_Verified: 2026-10-14T15:28:17Z (HEAD 92166f2)_
_Verifier: Claude (gsd-verifier, stale-refresh re-verification)_
