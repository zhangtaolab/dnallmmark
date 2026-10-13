---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: "05"
subsystem: ui
tags: [strings, i18n, copywriting-contract, tripwire, cjk-lock, tui, phase-11]

requires:
  - phase: 10-03
    provides: the DL_/QUEUE_ bidirectional inventory-tripwire pattern (EXPECTED_* tuples + both directional tests) this plan extends to the three new prefixes
  - phase: 11-01
    provides: the variant×PEFT collect-all refusal CFG_COMPOSITION_PROBLEM mirrors (driver as single authority; TUI mirrors as preview problem)
  - phase: 08-02
    provides: tui/strings.py as the D-12 single home and the gap-filler provenance precedent (SEL_PRESENCE_UNKNOWN)
provides:
  - 99 Phase-11 copy constants in tui/strings.py — CFG_ 38 / LNC_ 13 / MON_ 48, verbatim from the 11-UI-SPEC Copywriting Contract (grouped rows expanded to individual constants) plus the 3 documented plan-owned gap-fillers (CFG_FIELD_EBS, CFG_COMPOSITION_PROBLEM, MON_STATE_ARTIFACTS_SWEEP) and the 80-col MON_RESUME_NOTE_SHORT
  - tests/tui/test_strings_phase11.py — the bidirectional inventory lock over the three prefixes (defined + complete) + glyph-distinctness tests (5 cell states ◌ ⠋ ✓ ✗ ⊘; 3 sweep states ● ○ ◌; every state constant opens with its glyph)
  - ENV_VERDICT_CRITICAL_FAIL present-tense amendment (same name, same {kernel_names} field) with the consumer assertion pinning the new blocking-state wording and the retired future tense gone
  - the sanctioned one-line 11-UI-SPEC correction: PROBE_INELIGIBLE "data, 7 names" → "data, 9 names" (UI-checker fix 1 closed; the hint copy needed no change — {models} stays dynamic)
  - the 11-06 contract note (UI-checker fix 2): the slot-4 enter-key pin is a Pilot assertion in test_pilot_run_config.py, recorded in the tripwire docstring and below
affects: [11-06 run-config screen (consumes every CFG_/LNC_ constant by name), 11-07 monitor screen (consumes every MON_ constant by name), CFG-01/LNC-01/MON-01]

actuals:
  tokens: 5393   # chars/4 over the realized diff (21572 chars, 4 files)
  tasks: 2
  commits: 4
plan_head_before: 840f0d383f702714beacf43d224be6dbfd41f5f2
plan_head_after: 7e9fba7d0a907378570668aa34e7dd7689ffd7e1

tech-stack:
  added: []   # zero new dependencies (constants + tests only)
  patterns:
    - "strings-block + sibling-tripwire pattern (the 10-03 W1-mirror precedent, third application): copy lands first with a drift tripwire, screens consume by name"
    - "gap-filler provenance idiom: plan-owned constants carry a comment naming the gap (SEL_PRESENCE_UNKNOWN precedent) so reviewers can separate contract wording from plan wording"

key-files:
  created:
    - tests/tui/test_strings_phase11.py
  modified:
    - tui/strings.py
    - tests/tui/test_pilot_env_check.py
    - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-UI-SPEC.md

key-decisions:
  - "CFG_VARIANT_HEAD_NOTE carries the head-alias frozen pair (evo2_1b_base / megaDNA_updated) as static copy — the Copywriting Contract words that row verbatim; the PROBE_INELIGIBLE prohibition was read as covering the 9-name probe list only (rendered dynamically via {models}), which the comment boundary in strings.py documents explicitly"
  - "The consumer assertion at test_pilot_env_check.py:351 was constant-derived (no test pinned the retired future-tense literal), so the Task-2 update ADDS the present-tense/absent-retired-tense pins while keeping the kernel-names formatting, glyph membership, and the constant-derived render assertion — exactly the plan's conditional ('if a test asserts the retired future-tense substring')"
  - "MON_RESUME_NOTE_SHORT: the 80-col parenthetical wording from the MON_RESUME_NOTE row became its own constant (derived name, table-sourced copy) alongside the CFG_DIRS_TITLE_SHORT precedent — the tripwire lists it like any other name"

patterns-established:
  - "Third application of the bidirectional inventory lock: EXPECTED_CFG/LNC/MON tuples + test_cfg_lnc_mon_string_inventory_defined + test_cfg_lnc_mon_inventory_complete_no_unlisted_constants — a new toast that skips registration fails the tripwire (IN-09)"
  - "Glyph tests mirror the queue-state shape: ordered glyph assertions per state family + a first-char-is-the-glyph sweep over every stateful constant (NO_COLOR redundancy)"

requirements-completed: [CFG-01, LNC-01, MON-01]

coverage:
  - id: D1
    description: "The CFG_ copy block (38 constants) — slot-4 chrome, picker/params/dirs labels, value states, derived hints, preview line/modal, incl. the 2 plan-owned gap-fillers"
    requirement: CFG-01
    verification:
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_cfg_lnc_mon_string_inventory_defined
        status: pass
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_cfg_lnc_mon_inventory_complete_no_unlisted_constants
        status: pass
    human_judgment: false
  - id: D2
    description: "The LNC_ copy block (13 constants) — gate modal + E2' typed-phrase escalation, launch toasts, exit-modal kill/detach/cancel row"
    requirement: LNC-01
    verification:
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_cfg_lnc_mon_string_inventory_defined
        status: pass
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_cfg_lnc_mon_inventory_complete_no_unlisted_constants
        status: pass
    human_judgment: false
  - id: D3
    description: "The MON_ copy block (48 constants) — monitor chrome + cadence note, 3 discovered-sweep states incl. the artifacts-sweep gap-filler, cell table + 5 cell states + resume notes, stats/ETA variants, failures + gated re-run, log tail, attach flow, rescan"
    requirement: MON-01
    verification:
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_mon_cell_state_strings_glyph_first_and_distinct
        status: pass
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_mon_sweep_state_strings_glyph_first_and_distinct
        status: pass
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_mon_state_copy_first_char_is_the_glyph
        status: pass
    human_judgment: false
  - id: D4
    description: "The bidirectional inventory tripwire over CFG_/LNC_/MON_ — every listed name defined and non-empty AND every defined constant listed (sorted diffs on both failure directions)"
    verification:
      - kind: unit
        ref: tests/tui/test_strings_phase11.py#test_cfg_lnc_mon_inventory_complete_no_unlisted_constants
        status: pass
    human_judgment: false
  - id: D5
    description: "ENV_VERDICT_CRITICAL_FAIL present-tense amendment (✗ …启动已被运行配置启动门阻断) rendered through its existing consumer with the {kernel_names} field preserved and the retired future tense gone"
    verification:
      - kind: integration
        ref: tests/tui/test_pilot_env_check.py#test_critical_fail_verdict_names_kernels_and_routes_missing_data
        status: pass
    human_judgment: false
  - id: D6
    description: "The sanctioned one-line 11-UI-SPEC prose correction — PROBE_INELIGIBLE '(data, 7 names, …)' → '(data, 9 names, …)' matching the verified frozen list"
    verification:
      - kind: other
        ref: "pipeline/run_finetune.py:527-537 PROBE_INELIGIBLE carries 9 names; 11-UI-SPEC.md lines 212-213 now read '(data, 9 names, never duplicated…)' (commit 7e9fba7, one changed line)"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-10-13
status: complete
---

# Phase 11 Plan 05: Phase-11 Copy Contract + Inventory Tripwire Summary

**All 99 CFG_/LNC_/MON_ constants landed verbatim in `tui/strings.py` with a bidirectional drift tripwire, the ENV_VERDICT present-tense amendment pinned through its consumer, and the stale 7→9 PROBE_INELIGIBLE spec count corrected**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-13T01:49:08Z
- **Completed:** 2026-10-13T02:01:12Z
- **Tasks:** 2 (both TDD: RED → GREEN)
- **Files modified:** 4

## Accomplishments

- The D-12 single-home contract now covers the phase's three prefixes: CFG_ 38 / LNC_ 13 / MON_ 48 = 99 constants, every Copywriting-Contract row verbatim (grouped MON_COL_* rows expanded to individual constants), plus the 3 documented plan-owned gap-fillers (CFG_FIELD_EBS = "effective_batch_size", CFG_COMPOSITION_PROBLEM, MON_STATE_ARTIFACTS_SWEEP = "◌ 历史产物") and the 80-col MON_RESUME_NOTE_SHORT — the constant-count cross-check holds (landed == tripwire tuple lengths == 99).
- The bidirectional inventory lock extends to the new prefixes: `test_cfg_lnc_mon_string_inventory_defined` (every name exists, str, non-empty, prefix-correct) + `test_cfg_lnc_mon_inventory_complete_no_unlisted_constants` (set equality over `dir(tui.strings)` with sorted diffs — unregistered AND stale both fail).
- Glyph-distinctness tests mirror the queue-state one: the five cell states lead ◌ ⠋ ✓ ✗ ⊘ in order, the three sweep states lead ● ○ ◌ pairwise distinct, and every stateful constant (10: 5 cell + 3 sweep + 2 resume notes) opens with its glyph — the NO_COLOR redundancy rule.
- `ENV_VERDICT_CRITICAL_FAIL` retires its future tense: `✗ 关键项未通过: {kernel_names} — 启动已被运行配置启动门阻断` — same constant name, same field, the ✗ glyph kept; the screen consumer (`tui/screens/env_check.py:490`) renders from the constant unchanged in shape, and the consumer test now pins the new blocking-state substring plus the absence of the retired wording.
- UI-checker fix 1 closed: the 11-UI-SPEC prose now says "data, 9 names" — matching the verified frozen list (`run_finetune.py:527-537`); the probe-hint copy needed no change (the `{models}` field is dynamic by design).

## Task Commits

Each task executed as a TDD RED → GREEN pair:

1. **Task 1: The CFG_/LNC_/MON_ blocks + the bidirectional tripwire** — RED `9413297` (test) / GREEN `b113627` (feat)
2. **Task 2: ENV_VERDICT amendment + consumer update + spec correction + full gates** — RED `631a40d` (test) / GREEN `7e9fba7` (feat; includes the sanctioned .planning one-liner)

**Plan metadata:** (see final docs commit below)

## Files Created/Modified

- `tui/strings.py` — the three group-banner blocks (运行配置 CFG_ / 启动门 LNC_ / 任务监控 MON_) + the ENV_VERDICT amendment; provenance comments throughout, gap-fillers named plan-owned
- `tests/tui/test_strings_phase11.py` — NEW: the sibling tripwire (both directions) + 3 glyph tests; docstring records the CJK-lock extension note and the enter-key pin pointer for 11-06/07
- `tests/tui/test_pilot_env_check.py` — the critical-fail consumer assertion extended with the present-tense pins
- `.planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-UI-SPEC.md` — one line: "7 names" → "9 names"

## Verification

- `uv run --group dev --group tui pytest tests/tui/test_strings_phase11.py tests/tui/test_pilot_env_check.py tests/tui/test_services_download_queue.py -q` — 5 + 28 + 161 all green (the existing DL_/QUEUE_ tripwire stays green alongside the new prefixes)
- `make test` — **1222 passed** (pytest; the 11-01 baseline 1217 + this plan's 5 new tests) + node lane 18 passed
- `make lint` — all checks passed
- `make typecheck` — all checks passed
- TDD RED evidence in transcript: Task 1 all 5 target tests failed on the planned missing-constant assertions; Task 2 the target consumer test failed on `assert '启动已被运行配置启动门阻断' in '✗ … 启动流程将被阻断（阻断接线于 Phase 11）'`

## Decisions Made

- **CFG_VARIANT_HEAD_NOTE boundary** — the row names the head-alias frozen pair statically (contract wording, copied verbatim); the PROBE_INELIGIBLE prohibition is about the 9-name probe list, which stays data via `{models}`. The strings.py comment documents this boundary so future readers don't "fix" one into the other.
- **Consumer-test update shape** — the existing ~351 assertion was constant-derived (nothing pinned the old literal anywhere in the suite, grep-verified), so the update adds the two pins (new substring present, retired substring absent) rather than replacing a literal — keeping every other aspect of the assertion per the plan.
- **MON_RESUME_NOTE_SHORT naming** — the table words the 80-col copy in a parenthetical without a constant name; derived the name after the CFG_DIRS_TITLE_SHORT precedent and listed it in the tripwire like any table constant.

## Deviations from Plan

None — plan executed exactly as written (the three Decisions above are faithful applications of plan-conditional wording, recorded for review visibility).

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Contract Note for 11-06 (UI-checker fix 2 — recorded per the plan)

The slot-4 **enter-key pin** is a Pilot assertion in `tests/tui/test_pilot_run_config.py`, not a copy change: `enter` on the picker / with no field focused opens the 启动门; an Input's own Enter never launches (typing never launches). The pointer lives in the tripwire docstring next to the constants it protects. The CJK-lock extension is likewise recorded there: each new Pilot suite adds its screen module to its `_GREP_LOCK_MODULES` tuple (test_pilot_env_check.py precedent); the services glob lock already covers new services modules automatically.

## Next Phase Readiness

- **11-06 (run-config screen)** can assume every CFG_/LNC_ constant exists by name with the documented format fields ({n}/{models_total}/{path}/{model}/{mode}/{variant}/{models}/{value}/{models}/{tasks}/{seeds}/{fractions}/{cells}/{i}/{problem}/{output_root}/{dirname}/{error}/{done}/{total}/{root}) — render sites import by name; a rename now fails the tripwire, not the screen. The enter-key pin lands there per the contract note above.
- **11-07 (monitor screen)** likewise for every MON_ constant — including the three-state discovered vocabulary (● ○ ◌) and the ETA degradation ladder (估算中… / {lo}–{hi} / —).
- No stubs, no threat-flag surface (constants + tests only; zero new dependencies, zero packages installed).

## Self-Check: PASSED

All 5 claimed files exist on disk; all 4 task commits (9413297, b113627, 631a40d, 7e9fba7) are ancestors of HEAD; the spec edit verified at lines 212-213 ("(data, 9" / "names, never duplicated…"), committed in 7e9fba7.

---
*Phase: 11-run-config-launch-gates-single-gpu-monitoring*
*Completed: 2026-10-13*
