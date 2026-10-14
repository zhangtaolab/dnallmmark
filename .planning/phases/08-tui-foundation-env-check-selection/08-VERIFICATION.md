---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-14T12:07:58Z
status: gaps_found
score: 5/6 must-haves verified
covered_files:
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-SUMMARY.md
  - dnallm-mark/data/n_audit.json
  - pipeline/env_smoke.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_registries.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/data_manager.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/selection.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:3d800c023d043285ba7fd29a70fef036b7a0694190a3f732dbca867390d404e9"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
gaps:
  - truth: "Goal-derived foundation invariant (the phase goal's own words: 'trustworthy at rest' + 'tolerant artifact loader' landed): registry inputs the loader contract accepts or that are merely unreadable degrade to the documented load-error state — the console never exits on them (08-07 truth: registry failure → 'the app stays alive'; _load_entries docstring: 'never an exception through the screen')"
    status: failed
    reason: >-
      Two crash chains, both reproduced by this verifier's own execution at
      HEAD 0852b53, both ending in a full console exit through textual 8.2.8's
      default exit_on_error=True (verified: App._handle_exception "Always
      results in the app exiting"; 0 of the 34 @work sites in tui/ pass
      exit_on_error=False). (1) A non-dict custom entry — input the loader
      contract deliberately accepts and merges (pinned by
      tests/test_registry_loader.py::test_non_dict_custom_entry_still_merges_after_skip_filter
      as formerly-accepted input) — raises AttributeError in
      registries.load_model_entries()'s card.get() projection: reproduced
      ("PROJECTION CRASHES: AttributeError - 'list' object has no attribute
      'get'"). (2) A corrupt official models_info.json raises
      json.JSONDecodeError (a ValueError) that escapes
      selection._load_entries' (OSError, SystemExit) tuple: reproduced
      (uncaught traceback through the seam). Dating per the #3304 evidence
      gate: git log -S shows BOTH crash sites on Phase 8 commits — the
      projection at c065f95 (08-04) and the except tuple at dafcf94 (08-07) —
      NOT the mlc/261014 delta; the later-seam adjudication is refuted. The
      defect was latent through the three prior passes (their suites never
      exercised non-dict entries or corrupt-official-JSON through the TUI
      seam) and is now execution-proven (also independently found by the
      committed incremental review, 08-REVIEW.md CR-01, disposition open).
    artifacts:
      - path: tui/services/registries.py
        issue: "load_model_entries()/load_dataset_entries() call card.get(...) on every overlay-merged entry without an isinstance(card, dict) guard (around L135-160)"
      - path: tui/screens/selection.py
        issue: "_load_entries catches only (OSError, SystemExit) — json.JSONDecodeError from a corrupt OFFICIAL registry escapes (around L794-807); the escaped exception exits the app via the default exit_on_error"
      - path: tui/screens/env_check.py
        issue: "same root-cause family (WR-01): the boot/refresh worker calls result = kernel() unguarded (around L445) and the env_smoke directory kernels read registries bare — a missing/corrupt registry crashes the opening screen in exactly the state it exists to diagnose"
    missing:
      - "isinstance(card, dict) guard in the registries projections (project non-dict cards as the empty card), mirroring the management-read loop's existing guard at selection.py:433-434"
      - "widen _load_entries' tuple to include json.JSONDecodeError (or ValueError) so a corrupt OFFICIAL registry degrades to the load-error state"
      - "make every @work site that owns a tolerant read pass exit_on_error=False (or wrap the reads/kernel loop per-call) so no escape exits the console — including the env screen's per-kernel loop"
      - "regression tests: a non-dict custom entry through SelectionBackend.load_selection_data() (must degrade, never raise) and a corrupt official registry through _load_entries (must return the ([], path) degrade)"
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "CLOSED by its successor: Phase 11 landed the env preflight + E2' typed gate (d8e63ed) and the launch gate screen — Phase 11 verification passed at c50abe4, UAT 64ad9e3. Kept as the historical deferral record."
advisory:
  - finding: "WR-02: degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "Introduced by quick-261014-mlc (post-phase scope: the compat map did not exist in Phase 8); no execution evidence produced this pass; tracked open in 08-REVIEW-DISPOSITION.md. Resolved by carrying a degraded signal on SelectionData and rendering a state row."
    evidence_status: "none provided"
  - finding: "WR-03: new synchronous event-loop file reads (_manual_landing_path, _render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "Added by quick tasks 261014-f4w/mlc (post-phase scope); bounded local-file stalls, not a Phase 8 must-have breach; tracked open in the disposition. Resolved by routing through the existing worker discipline or amending the module contract."
    evidence_status: "none provided"
  - finding: "IN-01..IN-04: dead strings constants after the slot split; matrix Header() chrome inconsistency; missing is_valid_coordinate guard in EnvCheckScreen.action_show_detail; degenerate filter tokens (=x, type=)"
    category: other
    reason: "Info-level, post-phase scope, tracked open in 08-REVIEW-DISPOSITION.md; none breaches a Phase 8 must-have. IN-03 (the missing coordinate guard) becomes load-bearing to fix alongside the CR-01 gap if the kernel-row table ever becomes dynamic."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-14T12:07:58Z
**Status:** gaps_found
**Re-verification:** Yes — stale-fingerprint refresh. The 2026-10-13 pass (5/5 at 8b92766) went stale because phases 09-12 and quick tasks 261014-l6h/mlc/f4w/dcl/ir9 reshaped the covered surface (selection.py models-only slot 2, registries.py compat loader, 8th env kernel, storage rows, 62→59 confidential removal). This pass re-verified all five roadmap SCs at HEAD 0852b53, ran the full tui lane, re-proved the architecture invariants, adjudicated the committed review's CR-01 against the #3304 evidence gate with independent git dating and fresh crash reproductions, and recomputed the fingerprint.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | `get_default_screen() → EnvCheckScreen` (app.py:424-426); `make tui` recipe unchanged (`uv run --group tui --group gpu python -m tui`); env screen now renders EIGHT kernels (dcl's `model_dirs` added additively before `dataset_dirs`, never blocking `can_launch`); boot + env-check Pilot suites green (28 + 1 tests in the 1022-passed lane) |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE = "上次检查: {checked_at}"` (strings.py:86) rendered at env_check.py:503; `Binding("r", "refresh")` at :303; same-day cache service + persistence tests green in the lane; dcl's delta threaded run-config roots into the directory kernels without touching the cache discipline |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates launch-required subset | ✓ VERIFIED | env_gate CRITICAL/ROUTING disjointness intact with ROUTING now `{model_dirs, dataset_dirs}` (additive, aa6161d); quick_check subset 7 ids (matmul still excluded, D-09 held); the Phase-11 deferral is CLOSED — the launch-flow blocking landed in Phase 11 (env preflight + E2' typed gate d8e63ed, verified passed at c50abe4) |
| 4 | SC4: Model/dataset lists are first-class selectable surfaces; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Slot 2 (models): space/m/t/p/x/s/slash/v + digit bindings all present at HEAD (selection.py:1256-1289); k9s filter over stable row_keys intact. Dataset side reshaped by the maintainer's locked 2026-10-14 slot-split ruling (.planning/.continue-here.md decisions_made: "slot 2 = models only; slot 3 = datasets only"): dataset marks remain settable through presets (p) and template import (x) and display in the matrix (v) + status line; the interactive dataset table lives on slot 3. Live-verified this pass: presets derive 3 entries in menu order with tier-1 pair semantics (`Preset(id='tier-1', models=('plant-dnamamba-6mer','PlantHelixSeek'), tasks=(...))`); matrix + selection Pilot suites green. Count is now 59 models / 50 datasets — the 62→59 delta is the maintainer-directed confidential Chaoba removal (ir9, 1f16b3d), a sanctioned data change, not a regression. The selection-building capability the SC promises holds through the reshaped surfaces |
| 5 | SC5: Presence columns (✓/✗ + n_audit rows); templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n through constants module; enumerated foundation invariants (services textual-free, `[tui]` isolation, Pilot tests green CPU-side) | ✓ VERIFIED | Presence live-run at HEAD: 50 datasets → 50 `present` with exact integer row tuples through unchanged `presence_for`; template↔tier round-trip live-verified (models True / tasks True through template_to_tiers→tiers_to_template); i18n grep over screens/app/__main__: 0 CJK hits; services textual-free: 0 imports across all 20 service modules; `[tui]` group = exactly `textual>=8.2,<9` + platformdirs + jsonschema, absent from data/dev/gpu; Pilot lane at HEAD: **1 failed / 1022 passed / 9 xfailed** — the single failure is `test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers` (quick-261014-f4w scope, machine-state: `pipeline/logs` exists on this dev box), NOT a Phase 8 test; the 9 xfailed are the documented strict-xfail SVG goldens pending the maintainer's snapshot-update after the nav rename |
| 6 | Goal-derived foundation invariant: the tolerant artifact loader is landed such that malformed registry inputs degrade — the console is "trustworthy at rest" and "the app stays alive" on registry failure (the goal's own parenthetical; 08-07's registry-failure truth; `_load_entries`' own docstring: "never an exception through the screen") | ✗ FAILED | **Reproduced by this verifier at HEAD** (fresh executions, not review claims): (1) non-dict custom entry → `load_model_entries()` raises `AttributeError: 'list' object has no attribute 'get'` — input the loader contract deliberately merges (pinned accepted input); (2) corrupt official models_info.json → `json.JSONDecodeError` escapes `_load_entries`' `(OSError, SystemExit)` tuple (uncaught traceback). Both escape a `@work` worker into textual 8.2.8's default handler — verified from the installed package: `App._handle_exception` "Always results in the app exiting"; `work()` default `exit_on_error=True`; **0 of 34 `@work` sites in tui/ override it** — so each chain EXITS the whole console instead of rendering `SEL_REGISTRY_LOAD_FAILED`. Dating (#3304): `git log -S` puts the projection at c065f95 (08-04) and the except tuple at dafcf94 (08-07) — **Phase 8 commits, not the mlc delta**; the flagged files are also git-modified since the prior verified timestamp, so the finding is in-contract as a regression-class blocker AND carries deterministic evidence either way. Matches committed review CR-01 (disposition: open) |

**Score:** 5/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (d8e63ed), Phase 11 verification passed at c50abe4. Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

New-scope findings from the committed incremental review with no deterministic evidence produced this pass — reported, not blocking. (Post-phase scope: all introduced by quick tasks 261014-f4w/mlc, after the phase passed; all tracked open in 08-REVIEW-DISPOSITION.md.)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-02: degraded compat map renders a silent blank models table on slot 2 | architectural | mlc-scope (compat map postdates Phase 8); review-tracked open; no execution evidence this pass |
| 2 | WR-03: synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | f4w/mlc-scope additions; bounded stall, no must-have breach; review-tracked open |
| 3 | IN-01..IN-04: dead constants, matrix Header chrome, missing coordinate guard in env detail action, degenerate filter tokens | other | info-level, later scope; IN-03 worth fixing alongside the CR-01 gap |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pipeline/env_smoke.py` | structured kernels + renderer main() | ✓ VERIFIED | 8 kernels at HEAD (dcl added `model_dirs` additively); golden byte suite green in the lane; the bare-read tolerance hole is recorded under Truth 6's gap, not as a stub |
| `tui/app.py` | composition root, default screen, shared mark sets | ✓ VERIFIED | `get_default_screen → EnvCheckScreen` (L424); `_marked_tasks`/`_marked_models` shared sets injected into selection + matrix (L419/445); substantive (~850 lines), wired |
| `tui/screens/env_check.py` | env panel screen | ✓ VERIFIED | 8 rows, refresh binding (:303), last-check line (:503), drill-down; Pilot suite green |
| `tui/screens/selection.py` | slot-2 models screen (post-mlc) | ✓ VERIFIED (with Truth 6 seam hole) | bindings/marks/presets/templates/matrix intact (L1256-1289); substantive (~2100 lines); the `_load_entries` tuple and the projection crash are the Truth 6 gap |
| `tui/screens/matrix.py` | read-only 59×50 matrix | ✓ VERIFIED | no mark/filter/preset bindings (read-only by absent bindings held); suite green |
| `tui/services/registries.py` | entries + presence + compat | ✓ VERIFIED (with Truth 6 projection hole) | presence_for live-verified; `load_dnallm_compat` is mlc-additive |
| `tui/services/env_gate.py` / `quick_check.py` | pure judgments | ✓ VERIFIED | CRITICAL/ROUTING disjoint; quick-check 7 ids; additive dcl delta only |
| `tui/services/selection.py` / `templates.py` | filter/presets/templates | ✓ VERIFIED | live preset derivation + round-trip this pass |
| `tui/strings.py` | i18n single home | ✓ VERIFIED | 0 CJK outside it; new copy (DL_/CFG_/LNC_/MON_) all landed here |
| `pyproject.toml` `[tui]` group | textual isolation | ✓ VERIFIED | exactly `textual>=8.2,<9` + platformdirs + jsonschema; absent from data/dev/gpu |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `make tui` | `tui.app` | recipe → `python -m tui` → bootstrap | ✓ WIRED | Recipe unchanged; boot Pilot test green |
| Nav digit 2 / 3 | Selection / Data screens | `app.nav` routing | ✓ WIRED | Post-mlc labels 2 模型 / 3 数据集 (value-only rename); routing tests green |
| env screen | env_smoke kernels | imported CheckResult (no subprocess) | ✓ WIRED | Zero subprocess greps; byte goldens green |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | 0 imports across 20 service modules |
| `tui/strings.py` | all screens | constants only | ✓ WIRED | CJK grep 0 over screens + app + __main__ |
| Presence column | committed n_audit | load → merge → presence_for | ✓ WIRED | Live-run: 50/50 present, exact row tuples — FLOWING |
| Tolerant registry seam | degraded state | `_load_entries` → `SEL_REGISTRY_LOAD_FAILED` | ✗ NOT_WIRED (2 input classes) | Non-dict custom entry and corrupt official JSON escape the seam and exit the app — Truth 6 gap |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection/matrix presence | `presence_for(key, audit)` | committed `n_audit.json` + queue reconcile overlay | Yes — 50/50 present with exact integer rows | ✓ FLOWING |
| model list | `load_model_entries()` | overlay-merged registry | Yes — 59 entries (62−3 sanctioned ir9 removal) | ✓ FLOWING (crash hole on non-dict customs = Truth 6) |
| presets menu | `derive_presets(path, …)` | `pipeline/sweep_priorities.json` | Yes — 3 presets, tier-1 pair live-verified | ✓ FLOWING |
| templates | `template_to_tiers`/`tiers_to_template` | schema-validated template docs | Yes — round-trip verified live | ✓ FLOWING |
| env panel | kernels → CheckResult list | real kernel execution + persisted state file | Yes — Pilot suites + cache tests green | ✓ FLOWING |

### Behavioral Spot-Checks

All run by this verifier at HEAD 0852b53.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full tui lane | `uv run --group dev --group tui pytest tests/tui -q` | 1 failed / 1022 passed / 9 xfailed in 241s | ✓ PASS for Phase 8 scope (the 1 failure is f4w's machine-state storage test, outside Phase 8; xfails are the documented pending goldens) |
| **CR-01 chain 1 reproduction** | non-dict custom entry via `DNALLMMARK_CUSTOM_REGISTRY_DIR` → `load_model_entries()` | `loader merged OK: [1, 2]` then `PROJECTION CRASHES: AttributeError - 'list' object has no attribute 'get'` | ✗ FAIL (evidence for Truth 6) |
| **CR-01 chain 2 reproduction** | corrupt official `models_info.json` → `_load_entries(...)` | uncaught `json.decoder.JSONDecodeError` traceback through the seam (loader raises; seam does not catch) | ✗ FAIL (evidence for Truth 6) |
| App-exit consequence | inspect installed textual 8.2.8 `App._handle_exception` + `work()` defaults; grep `exit_on_error` in tui/ | "Always results in the app exiting"; default `exit_on_error=True`; 0 overrides / 34 `@work` sites | ✗ CONFIRMED (both chains exit the console) |
| Crash-site dating (#3304) | `git log -S 'card.get("type") or ""' -- tui/services/registries.py`; `git log -S 'except (OSError, SystemExit)' -- tui/screens/selection.py` | c065f95 (08-04, 2026-10-11) / dafcf94 (08-07, 2026-10-11) | ✗ CONFIRMED Phase 8 origin — mlc adjudication refuted |
| 59/50 + presence + round-trip + presets | `python -I` driving the real services | 59 models, 50 datasets, 50 present, round-trip True/True, 3 presets with pair semantics | ✓ PASS |
| Services textual-free / i18n single-home | greps over `tui/services/` and screens+app+__main__ | 0 / 0 | ✓ PASS |
| Debt markers | `TBD\|FIXME\|XXX` over all 15 phase-covered source files | 0 hits | ✓ PASS |

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 (8 kernels at HEAD, additive) |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (7-id subset, matmul excluded) |
| SEL-01 | 08-07 | Browsable model/dataset lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4 — model surface fully intact; dataset surface reshaped by the maintainer's locked 2026-10-14 slot-split ruling (slot 3 datasets-primary; dataset marks via presets/templates; matrix unchanged). 62→59 is the sanctioned ir9 confidential removal. Capability holds |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4 (live-verified this pass) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (round-trip live-verified; schema frozen) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (50/50 live + refresh-stable pins green) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | grep gate 0 across the grown tree |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| tui/services/registries.py | ~135-160 | Unguarded `card.get()` projection over loader-accepted non-dict entries (CR-01 chain 1) | 🛑 Blocker | Console exit on a hand-edited user-owned custom registry — Truth 6 gap |
| tui/screens/selection.py | ~794-807 | Tolerant seam except tuple misses `json.JSONDecodeError` (CR-01 chain 2) | 🛑 Blocker | Console exit on corrupt official registry — Truth 6 gap |
| tui/screens/env_check.py | ~445 | Unguarded `result = kernel()` loop + bare-read kernels (WR-01 family) | ⚠️ Warning | Boot crash on missing/corrupt registry — same root cause; folded into the gap's fix scope |

### Human Verification Required

None. The single failing truth is machine-evidenced (fresh reproductions with exact commands above); the SC4 surface deviation is adjudicated by the maintainer's own locked ruling document, not by unverifiable judgment.

### Gaps Summary

One gap, one root cause. The tolerant artifact-loading foundation — a non-retrofittable decision named in the phase goal's own sentence — is incomplete: two input classes the seam's own docstring promises to survive ("never an exception through the screen") instead exit the entire console, because every `@work` site relies on textual 8.2.8's default `exit_on_error=True` (verified from the installed package; zero overrides across 34 sites). Chain 1 is the sharpest breach: a non-dict entry in the user-owned `custom_models.json` is input the loader contract *deliberately accepts and merges* (pinned by the loader's own test as formerly-accepted input), yet the Phase 8 projection raises AttributeError on it. Chain 2 (corrupt official registry JSON escaping the `(OSError, SystemExit)` tuple) plus the WR-01 kernel-loop site share the same root cause.

Adjudication trail (per the #3304 evidence gate, as instructed): `git log -S` dates both crash sites to Phase 8 commits (c065f95 / dafcf94, both 2026-10-11) — the "introduced by the mlc/261014 delta" escape is factually refuted; additionally both files are git-modified since the prior verified timestamp, making the finding regression-class in-contract; and it carries deterministic evidence (this verifier's own reproductions, independently matching committed review CR-01, disposition open). The prior 5/5 passes never red-flagged it because no suite exercised these inputs through the TUI seam — which is precisely why the gap asks for the two regression tests alongside the guards.

Everything else holds at HEAD: all five roadmap SCs verified with behavioral evidence, all nine requirements satisfied, every architecture invariant re-proven over the grown tree (20 textual-free services, i18n single-home with all new copy landed in strings.py, `[tui]` isolation, atomic-write settings), the sanctioned surface reshapes (slot split, 8th kernel, 62→59) documented with their maintainer provenance, and the tui lane green at 1022 passed with the sole failure outside Phase 8 scope. The fix is small and surgical (an isinstance guard, a widened except tuple, exit_on_error=False at the tolerant-read sites, two regression tests) — after which the phase returns to fully passed.

---

_Verified: 2026-10-14T12:07:58Z (stale refresh at HEAD 0852b53)_
_Verifier: Claude (gsd-verifier)_
