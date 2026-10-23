---
phase: 19-tui-run-config-full-params
plan: "02"
subsystem: tui-run-config
tags: [advanced-params, run-config-screen, table-driven, choice-modal, restore-default, pd-19]

requires:
  - phase: 19-01
    provides: "run_sweep.ADVANCED_TRAIN_FLAGS — the frozen 18-row table (kinds/bounds/choices/default_display) + the PD-19-2 argv block position and PD-19-7 nested-key semantics this plan mirrors element-for-element"
  - phase: quick-261023-abu
    provides: "the batch_size 9-surface TUI precedent (row shape, parse block, persistence pair, composer pins) this plan generalizes table-driven"
provides:
  - "RunSpec.advanced + PARAM_ADVANCED/PROBLEM_ADVANCED_INVALID (detail <field>=<raw>) + _parse_bounded_float/_parse_json_object — the TUI service tier over the 18-param family"
  - "params['advanced'] persistence (only-when-non-empty, per-entry tolerant re-validation, SCHEMA_VERSION stays 1) and the _advanced_argv_elements block shared by BOTH composers (after --batch_size, before --cache_dir, table order)"
  - "The slot-4 two-layer params column: collapsed 高级参数 section ([a] toggle, [r] bulk restore), 13 table-generated Inputs + 5 ChoiceRows, YAML-default placeholders, the variance + EBS/GA hint lines"
  - "The generalized action_pick_choice (peft/variant byte-identical + the table-driven enum/bool branch) and ChoiceModal display labels decoupled from RadioButton ids"
  - "PD-19-3/8/9/10 realized — the UX decision set 19-03's driver channel builds on"
affects:
  - "19-03 (driver + goldens): the advanced rows/ids (#cfg-input-/#cfg-value-<dasherized>) and the [a]/[r] bindings are the driver's targets; run_config.svg/run_config_confirm.svg regeneration"
  - "the strings tripwire (every future CFG_ADV_* joins EXPECTED_CFG_CONSTANTS in the same change)"

actuals:
  tokens: 21261   # chars/4 over the realized 6-file diff (85045 chars)
  tasks: 3
  commits: 3      # measured: git rev-list --count fc1e75a..HEAD

plan_head_before: fc1e75a329174bcd9e897adbf5db4ebc945b0558
plan_head_after: b9df042fe0beccb2ad65b4e46f91167caa7c39f1

tech-stack:
  added: []
  patterns:
    - "one table driving the whole TUI family — parse dispatch, widget generation, placeholders, vocabularies, persistence re-validation, and BOTH composer blocks (PD-19-6, zero per-param hand copies)"
    - "family fresh-recompute semantics: the parse tail writes the advanced partial whenever the family raw dict is PRESENT (even all-empty), so a cleared field restores YAML-default immediately — deliberately distinct from the scalar fields' cleared-keeps-last-valid screen rule (P19-R5)"
    - "ChoiceModal labels decoupled from RadioButton ids: the head pseudo-option RENDERS the YAML default while its id/on_pick value stays the raw vocabulary (data, never copy)"

key-files:
  created: []
  modified:
    - tui/services/run_config.py
    - tui/screens/run_config.py
    - tui/strings.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_strings_phase11.py

key-decisions:
  - "The advanced family partial is written whenever the family raw dict is present (even empty) — each compose recomputes the WHOLE family from the pane, so empty/cleared/invalid entries drop out immediately (empty = YAML governs, P19-R5); the scalar fields' cleared-keeps-last-valid rule (the gpus pin) is deliberately NOT inherited, and the invalid path's SAVED spec loses the entry (still never a misread value)"
  - "json-kind prefill serializes via json.dumps(sort_keys=True), not str() — str() would emit Python repr (single quotes) that json.loads rejects on the next compose; the same serialization the composer threads"
  - "The problem detail names the UNDASHED field name (learning_rate=2.0) — the persistence/lane key vocabulary, rendering through the generic code+detail fallback exactly like epochs/ebs/batch_size (no per-field copy mapping)"
  - "The ChoiceRow pseudo-option value is the raw string 'default' (the peft 'none' grammar) on the collapsed row; only the modal's head DISPLAY label renders the YAML default (CFG_ADV_CHOICE_NONE + default_display)"
  - "SHORT twins: the plan-locked grad_accum_steps/lr_sched_kwargs plus measured save_total_lim, lr_sched_type, logging_strat (narrow budget = the 14-cell eff_batch_size precedent); labels are read FRESH via getattr so the width swap follows the live language (the CR-01 lesson)"
  - "The export placeholder-count pin stays at the COLLAPSED default (5) — an expanded export renders only the viewport-bounded subset of the 13 placeholders (VerticalScroll), so the expanded count is layout-dependent and not pinnable"

requirements-completed: ["TUI19-full-params", "P19-R1", "P19-R3", "P19-R4", "P19-R5", "P19-R6"]
# P19-R2's TUI leg (the 18-param surface) lands here; P19-R2's pipeline leg landed in 19-01; P19-R7/R8 (goldens + driver) are 19-03's lane.

coverage:
  - id: D1
    description: "Service tier: table-driven parse/validation/persistence/composition over the 18-row family — RunSpec.advanced, PROBLEM_ADVANCED_INVALID, _parse_bounded_float/_parse_json_object, params['advanced'] only-when-non-empty with per-entry tolerant re-validation, and the shared _advanced_argv_elements block in both composers at the PD-19-2 position"
    requirement: "P19-R5"
    verification:
      - kind: unit
        ref: "tests/tui/test_services_run_config.py#test_advanced_family_parity_with_run_sweep_table + test_parse_params_advanced_input_matrix_valid/invalid/empty_absent (13x3 parametrize) + test_compose_argv_full_advanced_block_element_for_element + test_compose_dispatch_argv_full_advanced_block_element_for_element + test_compose_argv_defaults_carry_zero_advanced_elements (18x) + test_persistence_advanced_round_trip_and_only_when_non_empty + test_pre_change_doc_advanced_absent_loads_empty + test_advanced_drifted_entry_loads_as_absent_never_misread"
        status: pass
      - kind: other
        ref: "python probe: RunSpec(advanced={'learning_rate': 1e-4}) threads ['--learning_rate','0.0001'] in both composers before --cache_dir; the int-row probe prints problems ()"
        status: pass
    human_judgment: false
  - id: D2
    description: "Screen tier: the two-layer params column — collapsed 高级参数 section ([a]/[r] bindings), 13 table-generated Inputs with YAML-default placeholders + variance/EBS-GA hints, prefill/reset/raw-collection loops, SHORT twins under the width mode"
    requirement: "P19-R1"
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_run_config.py#test_advanced_section_collapsed_by_default_and_a_toggles + test_advanced_input_rows_generated_from_table_in_order + test_advanced_typing_threads_and_invalid_problem + test_advanced_reset_clears_every_input_and_base_argv + test_advanced_prefill_seeds_inputs_from_spec + test_advanced_labels_shorten_at_narrow_grid + test_advanced_export_placeholder_count_collapsed_default"
        status: pass
    human_judgment: false
  - id: D3
    description: "The 5 enum/bool ChoiceRows — generalized action_pick_choice (peft/variant byte-identical), RadioSet modals with the leading 默认 pseudo-option rendering the YAML default, present-only threading with string serialization, r restores rows"
    requirement: "P19-R4"
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_run_config.py#test_advanced_scheduler_modal_lists_default_plus_twelve + test_advanced_scheduler_pick_threads_and_default_does_not + test_advanced_bf16_modal_and_string_serialization + test_advanced_strategies_share_three_option_vocabulary + test_advanced_reset_restores_choice_rows_to_default (peft/variant pilots byte-unmodified; Select( gate count 0)"
        status: pass
    human_judgment: false

duration: 54 min
completed: 2026-10-23
status: complete
---

# Phase 19 Plan 02: TUI run-config full-params (two-layer surface) Summary

**The slot-4 params column grew a collapsed 高级参数 layer over the frozen 18-row ADVANCED_TRAIN_FLAGS table — 13 table-generated Inputs + 5 RadioSet ChoiceRows, YAML-default placeholders with variance/EBS-GA hints, [a]/[r] affordances, one nested persistence key, and the PD-19-2 advanced argv block threaded by both composers element-for-element.**

## Performance

- **Duration:** 54 min (07:55–08:49 UTC)
- **Started:** 2026-10-23T07:55:19Z
- **Completed:** 2026-10-23T08:49:16Z
- **Tasks:** 3/3
- **Files modified:** 6 (exactly the plan's files_modified)

## Accomplishments

- **Task 1 (tracer, `a0f7a03`)**: learning_rate end-to-end — the table-driven `parse_params` tail (one loop, kinds/bounds/choices from `run_sweep.ADVANCED_TRAIN_FLAGS` via the existing import), `RunSpec.advanced`, the only-when-non-empty `params["advanced"]` persistence with per-entry tolerant re-validation, the shared `_advanced_argv_elements` block pinned after `--batch_size` / before `--cache_dir` in BOTH composers, the collapsed section + row + `a`/`r` bindings, and the CFG_ADV_* strings block + tripwire. Tracer verified end-to-end (suites + probe) before expansion.
- **Task 2 (`8c2a5ca`)**: the remaining 12 Input rows as compose-time generation over the table (13 total, table order, dasherized ids), the narrow-grid SHORT twins wired into `_apply_width_mode`, prefill (json via `json.dumps` so it re-parses) + reset loops, the 13x3 parser matrix parametrized over the table with invalids DERIVED from each row's own bounds, and the pilot battery (collapse/toggle/threading/invalid/reset/prefill/SHORT/export-count).
- **Task 3 (`b9df042`)**: the 5 enum/bool ChoiceRows in the unified 18-row table-order compose loop, `ChoiceRow` value memory, `ChoiceModal` display labels decoupled from ids (labels=None keeps peft/variant byte-identical), the table-driven `_open_advanced_choice_modal` (leading 默认 pseudo-option rendering the row's `default_display`; ids stay raw vocabulary), and the modal pilot battery (13-option scheduler proof, first-toggle cosine, default-absent re-pick, bf16 string serialization, 3-option strategy vocabulary, r over rows).

## Verification Evidence

- Final four-suite gate: `pytest tests/tui/test_pilot_run_config.py tests/tui/test_services_run_config.py tests/tui/test_strings_phase11.py tests/tui/test_import_lock.py` — **384 passed** (baseline 304; services 124→250, pilot 109→121, strings/import-lock extended; zero pre-existing tests modified except the two documented additions below).
- Probes: the Task-1 compose probe (`--learning_rate 0.0001` in both composers, before `--cache_dir`, 18 table rows) and the Task-2 int-row probe (problems `()` for valid `1`s) both green.
- Gates: `ruff check` + `ty check` clean over all three tui files + the touched tests; the `Select(` count over `tui/screens/run_config.py` is **0** (the RadioSet idiom mandate); the CJK screen lock green (two comment-word hits caught and fixed during execution); the strings tripwire bidirectional-green with every new constant listed.
- The D-12 10-element defaults lock and the peft/variant modal pilots pass **unmodified** (pilot git diff is insertions-only).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Correctness] The advanced family uses fresh-recompute semantics, not the scalar cleared-keeps-last-valid rule**
- **Found during:** Task 1 (service tail design)
- **Issue:** The screen's established rule (pinned by the gpus pilot: a CLEARED field keeps the last valid value in the spec) directly contradicts the plan's own truths — "an empty field threads nothing (empty = YAML governs = restore default, P19-R5)" and pilot item (e) "[r] … the preview returns to the base argv". Under last-valid-governs, clearing an input (or the reset action) could never remove a threaded flag.
- **Fix:** The parse tail writes `partials["advanced"]` whenever the family raw dict is PRESENT — even when every entry is empty — so each compose recomputes the whole family from the pane: cleared → absent, invalid → absent (+ the problem line). Documented in the parse_params docstring and the pilot assertions (the invalid path's SAVED spec loses the entry, unlike batch_size's).
- **Files modified:** tui/services/run_config.py
- **Verification:** `test_parse_params_advanced_empty_family_partial_restores_default`, `test_advanced_typing_threads_and_invalid_problem`, `test_advanced_reset_clears_every_input_and_base_argv`.
- **Committed in:** a0f7a03

**2. [Rule 1 - Correctness] json-kind prefill serializes via json.dumps, not str()**
- **Found during:** Task 1 (prefill pair)
- **Issue:** `str({'num_restarts': 2})` emits Python repr (single quotes) which `json.loads` rejects — a prefilled json row would turn into an `advanced_invalid` problem on the first compose.
- **Fix:** The prefill serializes dict values with `json.dumps(sort_keys=True)` (the same serialization the composer threads), so the round-trip re-parses.
- **Files modified:** tui/screens/run_config.py
- **Verification:** `test_advanced_prefill_seeds_inputs_from_spec`.
- **Committed in:** a0f7a03

---

**Total deviations:** 2 auto-fixed (2 correctness)
**Impact on plan:** Both keep the plan's pinned truths intact (P19-R5 restore-default; prefill round-trip fidelity). No scope creep.

## Issues Encountered

- The plan's inline probe commands need `PYTHONPATH=<repo>/pipeline:<repo>` under plain `uv run python -c` (the pytest conftest provides those roots; a bare `-c` does not) — environmental, zero code changes.
- textual 8.2.8 finding: a child's `.visible` flag does NOT reflect an ancestor's `display=False` — the collapse pilot reads the CONTAINER's display state (the actual mechanism), noted in the test.
- textual 8.2.8 finding: a ChoiceModal's RadioSet cursor starts at the HEAD option regardless of the current mark (the peft-modal navigation precedent) — test navigation adjusted; behavior untouched.
- The expanded-state export placeholder count is viewport-bounded (the params column is a VerticalScroll; rows below the fold never reach the SVG), so the deterministic pin is the collapsed default (5) — the plan anticipated pinning "whichever the existing export test drives"; documented in the test comment.
- Two CJK-lock hits from Chinese words (默认) inside my new screen COMMENTS — reworded to English; the lock scans the whole source, comments included.

## Known Stubs

None — every surface is wired end-to-end and test-pinned (parse → spec → persistence → both composers → screen rows/modals → strings tripwire).

## Auth Gates

None.

## Next Phase Readiness

- 19-03 (driver + goldens) can proceed: the advanced rows/ids follow `#cfg-input-`/`#cfg-value-<flag-dasherized>`, the `[a]`/`[r]` bindings exist, and the typed-param driver channel can assert typed-⇒-present / untouched-⇒-absent over the family exactly like `--batch-text`. Goldens (`run_config*.svg`) will change — regeneration stays 19-03's lane per the no-goldens constraint here.
- The 18-param family is fully settable from slot-4; empty/默认 means the YAML governs everywhere (P19-R5), with the base-config placeholder honesty + variance + EBS/GA hints (PD-19-3/PD-19-5 copy).

## Self-Check: PASSED

All six modified files exist on disk; commits a0f7a03, 8c2a5ca, b9df042 verified as ancestors of HEAD (b9df042); `git diff fc1e75a..HEAD --name-only` equals exactly the plan's files_modified; zero file deletions across the three commits; the pre-existing uncommitted dirt (monitor goldens, .planning phases 13-18, DATA.md, n_audit*, eval_subsets.json, milestone.lock) untouched.

---
*Phase: 19-tui-run-config-full-params*
*Completed: 2026-10-23*
