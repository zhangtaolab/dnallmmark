---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-14T14:20:48Z
status: passed
score: 6/6 must-haves verified
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
  - .planning/phases/08-tui-foundation-env-check-selection/08-08-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-08-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-09-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-09-SUMMARY.md
  - dnallm-mark/data/n_audit.json
  - pipeline/env_smoke.py
  - tests/test_env_smoke_bytes.py
  - tests/tui/test_card_site_hardening.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_work_site_hardening.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/about.py
  - tui/screens/data_manager.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/monitor.py
  - tui/screens/selection.py
  - tui/screens/wizard.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:98c5096d9dd9a5ab25584befb2565d42481f22d51ea4948cb34fc10f903a41eb"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "w never exits: ANY w press on the models screen with a loader-accepted non-dict card merged opens WizardModal over the officials' vocabularies — re-executed by this verifier through the REAL app + REAL SelectionBackend (non-dict overlay via DNALLMMARK_CUSTOM_REGISTRY_DIR, 60 entries merged, degraded card verbatim [1,2,3]) at BOTH the default and a moved cursor position; A/B control against the pre-fix tree 1ad474f reproduces the exact crash (AttributeError 'list' object has no attribute 'get', build_wizard) — the flip is machine-proven, not assumed"
    - "enter never exits on the degraded row: t → filter-narrow → tab → enter opens the card-less RowDetailModal (entry_key the key, _card == {}, border title the key, 0 log lines); pre-fix A/B control reproduces AttributeError 'list' object has no attribute 'items' at RowDetailModal.on_mount"
    - "d never exits + the hardening: the Pilot press stays silent-and-alive (no modal, no toast) AND the direct unit call on a non-dict card entry returns None without raising (pre-fix it raised AttributeError at the or-{} chain — A/B proven); the UNKNOWN-presence shield is no longer load-bearing"
    - "The family cannot regrow: the AST pin verified non-vacuous by this verifier's OWN mutation tests — scanner over the real tree finds exactly 5 extraction nodes in exactly the 4 allowlisted functions with 0 violations; a clean tree copy flags nothing; stripping _open_detail's guard yields 'allowlisted but its isinstance(card, dict) guard is gone' with file:line; this verifier's independent raw sweep of every \"card\" string across tui/ finds ZERO extraction sites outside the allowlist (all construction/comparison sites accounted: run_config.py:298 dict-narrowed by its isinstance loop, _custom_*_entry sole feed guarded at selection.py:433, _matches_substring explicitly skips card)"
    - "Zero new failures against the locked box baseline: full suite run ONCE by this verifier → 7 failed / 1731 passed / 9 xfailed (same 7 as the baseline: 6 documented data/schema + 1 machine-state storage-overview; 1731 = 1725 + 6 new tests); ruff + ty green; snapshots untouched; loader byte-unmodified (0 diff lines 22ca261..HEAD); strings.py + tui/services/ + pyproject.toml + uv.lock unchanged over the whole 08-09 range (0 diff lines 1ad474f..HEAD); textual 8.2.8"
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "CLOSED by its successor: Phase 11 landed the env preflight + E2' typed gate (d8e63ed) and the launch gate screen — Phase 11 verification passed at c50abe4, UAT 64ad9e3. Kept as the historical deferral record."
advisory:
  - finding: "Pin guard-granularity: the card-site pin's guard-presence check is per-FUNCTION — stripping ONE of build_wizard's two comprehension guards leaves the sibling's isinstance in the function and the pin stays green (verified by this verifier's mutation test)"
    category: other
    reason: "Implements the plan's own per-function wording ('each of which must still contain an isinstance guard') exactly; the residual is covered behaviorally — the w Pilot regression test exercises BOTH comprehensions (this verifier re-executed it). A per-node guard check would close it; not a must-have breach."
    evidence_status: "none provided — evidenced in this report's mutation table; tracked here for the audit trail only"
  - finding: "WR-02: degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "Introduced by quick-261014-mlc (post-phase scope); tracked open in 08-REVIEW-DISPOSITION.md. Unchanged this pass. Resolved by carrying a degraded signal on SelectionData and rendering a state row."
    evidence_status: "none provided"
  - finding: "WR-03: new synchronous event-loop file reads (_render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "Added by quick tasks 261014-f4w/mlc (post-phase scope); bounded local-file stalls, not a Phase 8 must-have breach; tracked open in the disposition. Unchanged this pass."
    evidence_status: "none provided"
  - finding: "IN-01..IN-04: dead strings constants after the slot split; matrix Header() chrome inconsistency; missing is_valid_coordinate guard in EnvCheckScreen.action_show_detail (present in SelectionScreen.action_show_detail); degenerate filter tokens (=x, type=)"
    category: other
    reason: "Info-level, post-phase scope, tracked open in 08-REVIEW-DISPOSITION.md; none breaches a Phase 8 must-have. Unchanged this pass."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-14T14:20:48Z
**Status:** passed
**Re-verification:** Yes — fourth pass (round-3 flip check), after gap plans 08-08 and 08-09 (commits d04ed04..783f43a). This pass re-executed the two round-2 crash chains with this verifier's OWN real-app Pilot reproductions (independent of the executor's tests) through the REAL selection backend — including an A/B control against the pre-fix tree that reproduces both crashes exactly — mutation-tested the family pin, ran this verifier's own card-extraction sweep across tui/, cheaply re-confirmed Truths 1-5 at HEAD 783f43a, and ran the full suite once (7 failed / 1731 passed / 9 xfailed == the locked box baseline exactly, zero new failures).

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | Quick regression at HEAD: recipe unchanged (`make tui`, Makefile:206; `--group tui --group gpu python -m tui`); `get_default_screen() → EnvCheckScreen` (app.py:424-426); 8 kernel labels live-confirmed (`len(ENV_KERNEL_LABELS) == 8`); boot + env-check Pilot suites green inside the full-suite baseline run |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | Quick regression: `ENV_LAST_CHECK_LINE = "上次检查: {checked_at}"` (strings.py:94) rendered env_check.py:544; `Binding("r", "refresh")` (:324); cache/persistence tests green in the suite |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates launch-required subset | ✓ VERIFIED | Quick regression (live, `python -I` over the real services): `CRITICAL ∩ ROUTING = ∅` (disjoint=True); `QUICK_CHECK_KERNEL_IDS` 7 ids ⊂ the 8 kernel labels; Phase-11 deferral stays CLOSED (launch-flow wiring landed d8e63ed, Phase 11 verified passed at c50abe4) |
| 4 | SC4: Model/dataset lists first-class selectable; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Quick regression (live, real backend): `load_selection_data()` → 59 models / 50 datasets, `models_load_error` None; bindings intact; selection + matrix lanes green in the suite (41 passed incl. the four 08-09 tests) |
| 5 | SC5: Presence columns; templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n via constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Quick regression (live + grep): `model_presence` computes real local state over the merged registry (present 4 / missing 55 on this box — flowing from real filesystem+n_audit, not static); presence map 50 entries; presets tier-1 (2) / tier-2 (3) / all (59) + saved customs, `load_error` None, zero unknown keys; 0 textual imports across tui/services/; 0 CJK outside strings.py; `[tui]` group = exactly textual>=8.2,<9 + platformdirs + jsonschema (installed 8.2.8); ruff + ty green; full suite at the exact box baseline |
| 6 | Goal-derived foundation invariant: tolerant artifact loading landed such that loader-accepted registry inputs degrade — the console never exits on them | ✓ VERIFIED | **FLIPPED — machine-proven by this verifier's own executions.** The three guards land in the 08-08 idiom at the exact sites (build_wizard :718-727 walrus dict-narrowing in BOTH comprehensions; _open_detail :2167-2169 bind + `card if isinstance(card, dict) else {}`; _manual_landing_path :1772-1774 the model_presence idiom verbatim; RowDetailModal untouched per plan). This verifier wrote an INDEPENDENT reproduction script (not the executor's tests) over the REAL app + REAL SelectionBackend with a non-dict overlay (`{"hand-edited-nondict": [1,2,3]}` via DNALLMMARK_CUSTOM_REGISTRY_DIR): **20/20 checks PASS at HEAD** — w at default AND moved cursor opens WizardModal with officials' vocabularies (14 species, 5 tokenizers) and no exception; enter on the degraded row opens the card-less RowDetailModal (key title, `_card == {}`, 0 log lines); d stays silent-and-alive; the unit call returns None. **A/B control against the pre-fix tree (1ad474f via temp worktree): the SAME script reproduces both round-2 crashes exactly** (w → `AttributeError('list' object has no attribute 'get')` at build_wizard, both cursors; enter → `AttributeError('list' object has no attribute 'items')` at RowDetailModal; unit → AttributeError at the or-{} chain; d alive pre-fix exactly as the plan documents — the incidental shield). The reproduction is non-vacuous by construction. Family pin non-vacuous: mutation-tested below; independent sweep below; executor's four named tests green (4 passed) |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (d8e63ed), Phase 11 verification passed at c50abe4. Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

Carried forward from the prior pass (tracked open in 08-REVIEW-DISPOSITION.md), plus one new evidenced granularity note recorded for the audit trail.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Pin guard-granularity: guard-presence is checked per-FUNCTION, so one-of-two guard deletion inside build_wizard escapes the pin alone | other | Plan implements its own per-function wording; the w Pilot regression test (re-executed by this verifier) exercises both comprehensions, so the behavioral layer covers the residual; a per-node check would close it |
| 2 | WR-02: degraded compat map renders a silent blank models table on slot 2 | architectural | mlc-scope; review-tracked open; no execution evidence this pass |
| 3 | WR-03: synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | f4w/mlc-scope; bounded stall; review-tracked open |
| 4 | IN-01..IN-04: dead constants, matrix Header chrome, missing coordinate guard in env detail action, degenerate filter tokens | other | info-level, later scope |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tui/screens/selection.py` | slot-2 models screen + the three extraction-site guards | ✓ VERIFIED | Guards at :718-727 / :2167-2169 / :1772-1774 in the 08-08 idiom; RowDetailModal untouched (prohibition held); behavior proven by this verifier's own A/B reproductions |
| `tests/tui/test_pilot_selection.py` | w/enter/d real-app Pilot trio + the unit pin | ✓ VERIFIED | 4 named tests green this pass; full lane 41 passed incl. the 08-08 chain tests |
| `tests/tui/test_card_site_hardening.py` | the card-extraction family pin | ✓ VERIFIED | Green; 5 nodes / 4 allowlisted functions / 0 violations on the real tree (this verifier's own scanner run); mutation-tested below; module docstring carries the 8-row sweep ledger |
| `pipeline/env_smoke.py` | structured kernels; fail-closed registry reads | ✓ VERIFIED | Unchanged since 08-08; goldens green in the suite |
| `tui/services/registries.py` | entries + presence + compat; isinstance-guarded projections | ✓ VERIFIED | Byte-unchanged over 08-09 (0 diff lines); live 59/50 through the real seam |
| `tui/services/selection.py` | filter/presets/presence; model_presence guard | ✓ VERIFIED | Byte-unchanged over 08-09; live presets derivation correct |
| `tests/tui/test_work_site_hardening.py` | the 08-08 @work never-exit AST pin | ✓ VERIFIED | Green in the same lane (3 passed with the card pin); composes with the new pin |
| `tui/app.py` / `tui/strings.py` / `pyproject.toml [tui]` | composition root / i18n single home / textual isolation | ✓ VERIFIED | strings.py + pyproject + uv.lock unchanged over 08-09; group contents exact; textual 8.2.8 |
| `pipeline/registry_loader.py` | fail-loud contract BYTE-UNMODIFIED (prohibition) | ✓ VERIFIED | `git diff 22ca261..HEAD` over the file: 0 lines |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `w` keypress | WizardModal | build_wizard guarded vocabularies | ✓ WIRED | This verifier's own Pilot run: wizard pushed at both cursors, officials' vocabularies populate, no exception |
| `enter` on degraded row | card-less RowDetailModal | _open_detail isinstance narrowing | ✓ WIRED | This verifier's own Pilot run: modal pushed, `_card == {}`, key title, empty log |
| `d` on degraded row | silent no-op | UNKNOWN-presence branch + hardened _manual_landing_path | ✓ WIRED | Pilot: alive, no modal, no toast; unit: returns None (pre-fix it raised — A/B proven) |
| AST family pin | every card extraction site in tui/ | scanner + allowlist + guard-presence | ✓ WIRED | Mutation-tested: guard strip → named violation with file:line; clean copy → 0 violations |
| `make tui` | `tui.app` | recipe → `python -m tui` | ✓ WIRED | Recipe unchanged; boot Pilot green in the suite |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | 0 imports across all service modules |
| Presence column | committed n_audit | load → presence map | ✓ WIRED | Live: 50-entry presence map, real present/missing distribution |
| i18n copy | constants module | strings.py only | ✓ WIRED (negative) | 0 CJK outside strings.py in tui/ |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| model list | `load_model_entries()` | overlay-merged registry | Yes — live 59 + degraded custom (60 merged in the repro; card verbatim) | ✓ FLOWING |
| dataset list | `load_dataset_entries()` | committed registry | Yes — live 50 | ✓ FLOWING |
| presence | `model_presence` / presence map | filesystem + n_audit + queue reconcile | Yes — real present/missing split on this box | ✓ FLOWING |
| presets | `derive_presets` | pipeline/sweep_priorities.json | Yes — tier-1/tier-2/all, zero unknown keys | ✓ FLOWING |
| wizard vocabularies | observed_species/tokenizers | merged entries' guarded card reads | Yes — 14 species / 5 tokenizers over the officials | ✓ FLOWING |

### Behavioral Spot-Checks

All run by this verifier at HEAD 783f43a (independent script at /tmp, not the executor's tests; A/B controls against pre-fix 1ad474f via a temp worktree, removed after).

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| **Chain A re-execution: `w` at HEAD** | Own Pilot script over REAL app + REAL backend, non-dict overlay | 60 entries merged, card verbatim [1,2,3]; no exception at default AND moved cursor; WizardModal pushed; 14 species / 5 tokenizers | ✓ PASS |
| **Chain A control: `w` PRE-FIX (1ad474f)** | Same script, pre-fix worktree | `app._exception = AttributeError('list' object has no attribute 'get')` at build_wizard, both cursors — script exit 1 | ✓ CRASH REPRODUCED (the flip is real) |
| **Chain B re-execution: `enter` at HEAD** | t → slash → filter "nondict" → tab → enter | Filter narrows to exactly the degraded row; RowDetailModal pushed, entry_key correct, `_card == {}`, border title the key, 0 log lines, no exception | ✓ PASS |
| **Chain B control: `enter` PRE-FIX** | Same nav, pre-fix worktree | `AttributeError('list' object has no attribute 'items')` — script exit 1 | ✓ CRASH REPRODUCED |
| **Chain C: `d` at HEAD** | Same nav, press d | Alive, no modal, no toast, table keeps focus | ✓ PASS |
| Chain C control: `d` PRE-FIX | Same, pre-fix worktree | Alive (the documented incidental UNKNOWN shield — passes pre-fix exactly as the plan states) | ✓ MATCHES PLAN |
| Unit: `_manual_landing_path` at HEAD | Direct call, non-dict card entry | Returns None, no raise | ✓ PASS |
| Unit control: PRE-FIX | Same, pre-fix worktree | `AttributeError('list' object has no attribute 'get')` at the or-{} chain | ✓ RAISES PRE-FIX (hardening real) |
| Executor's 4 named tests | `pytest -k "survives_non_dict_card or degraded_row or manual_landing_path_returns_none"` | 4 passed | ✓ PASS |
| Pins + full selection lane | `pytest tests/tui/test_card_site_hardening.py tests/tui/test_work_site_hardening.py tests/tui/test_pilot_selection.py -q` | 41 passed | ✓ PASS |
| **Pin mutation test (guard strip)** | This verifier imports the pin scanner; strips _open_detail's guard in a temp copy | Clean copy: 0 violations; mutant: `tui/screens/selection.py:2154 _open_detail — allowlisted but its isinstance(card, dict) guard is gone` | ✓ PASS (non-vacuous) |
| Pin mutation test (partial guard) | Strips ONE of build_wizard's two comprehension guards | 0 violations (per-function check sees the sibling's guard) — covered instead by the w Pilot test, which exercises both comprehensions | ℹ️ NOTE (advisory row 1) |
| **Independent card sweep** | Raw grep of every `"card"` string across tui/ (both quote styles) | 5 extraction nodes, ALL in the 4 allowlisted functions; every other hit accounted (run_config.py:298 construction behind its isinstance loop; registries/_custom_* projections behind their guards; `_matches_substring` explicitly skips card) | ✓ PASS (no unaccounted site) |
| Full suite (once) | `uv run --group dev --group tui pytest -q` | **7 failed / 1731 passed / 9 xfailed** — exactly the locked box baseline (same 7: 6 documented data/schema + 1 machine-state storage-overview); 1731 = 1725 + 6 new; zero new failures | ✓ PASS |
| Lint + typecheck | `make lint` / `make typecheck` | All checks passed (both) | ✓ PASS |
| Loader prohibition | `git diff 22ca261..HEAD -- pipeline/registry_loader.py` | 0 lines (byte-unmodified) | ✓ PASS |
| Snapshots prohibition | `git status --short -- tests/tui/__snapshots__/` | clean | ✓ PASS |
| 08-09 side prohibitions | `git diff 1ad474f..HEAD --stat -- tui/strings.py tui/services/ pyproject.toml uv.lock` | 0 lines — zero new constants, services byte-unchanged, zero new deps | ✓ PASS |
| Live T3 gates | `python -I` over real services | CRITICAL∩ROUTING=∅; quick-check 7 ids ⊂ 8 kernels | ✓ PASS |
| Architecture greps | services textual imports / CJK outside strings / [tui] group | 0 / 0 / exact (textual 8.2.8) | ✓ PASS |
| Debt markers | TBD/FIXME/XXX/TODO/HACK over tui/ | 0 real markers (PLACEHOLDER hits are all named strings constants for Textual Input placeholders) | ✓ PASS |

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06, 08-08 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (7-id subset) |
| SEL-01 | 08-07, 08-08, 08-09 | Browsable model/dataset lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4; the w/enter/d auxiliary action paths now degrade on the non-dict card class (Truth 6 closed this pass) |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4 (live: 3+customs, load_error None, zero unknowns) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (verified live in prior passes; templates lane green in the suite) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (presence map flowing) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | grep gate 0; zero new constants over 08-09 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No stubs, no unreferenced debt markers, no unwired seams found this pass | — | — |

### Human Verification Required

None. Every closure and regression is machine-evidenced by this verifier's own command executions above, including A/B pre-fix controls for both crash chains.

### Gaps Summary

No gaps. The round-2 residual is closed and the flip is machine-proven, not assumed: this verifier wrote an independent reproduction of both crash chains over the real app and the real selection backend, confirmed 20/20 checks at HEAD (wizard opens over the officials' vocabularies at any cursor; card-less detail modal on the degraded row; silent d; unit None), and ran the identical script against the pre-fix tree (1ad474f) where it reproduces both console exits exactly — so the reproductions demonstrably exercise the crash paths. The family pin was verified non-vacuous by direct mutation testing (guard strip → named file:line violation; clean copy → silent), and this verifier's own raw sweep of every `"card"` access across tui/ found zero extraction sites outside the four allowlisted functions — every construction and comparison site carries its own account (run_config.py:298 is dict-narrowed by its own loop; `_matches_substring` explicitly never reads card contents; the projections' sole feeds are guarded). Truths 1-5 were cheaply re-confirmed live at HEAD (gate disjointness, quick-check subset, 59/50 counts, presence flowing, presets, architecture greps), ruff + ty are green, all three prohibitions hold (loader byte-unmodified, snapshots clean, zero new constants/deps with textual still 8.2.8), and the full suite sits exactly at the locked box baseline: 7 failed / 1731 passed / 9 xfailed, zero new failures. One advisory granularity note is recorded (per-function guard-presence in the pin; behaviorally covered by the w test) — no must-have breach.

Phase 8 is 6/6. The console is trustworthy at rest: every consumer of the tolerant loader's output — load-path seams (08-08) and screen-side action paths (08-09) — degrades on the loader-accepted non-dict card, and the AST pin makes the closure structural for every future extraction site.

---

_Verified: 2026-10-14T14:20:48Z (fourth pass, round-3 flip check, post 08-09 gap closure, at HEAD 783f43a)_
_Verifier: Claude (gsd-verifier)_
