---
phase: quick-261016-hhx
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/strings.py
  - tui/screens/data_manager.py
  - tui/screens/selection.py
  - tui/screens/monitor.py
  - tui/screens/wizard.py
  - tui/screens/run_config.py
  - tui/screens/env_check.py
  - tui/app.py
  - tui/__main__.py
  - tui/services/settings.py
  - tui/services/download_queue.py
  - tests/tui/test_language_rederivation.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_data_manager.py
  - docs/demo/casts/*.zh.cast
  - docs/demo/casts/language-toggle-en.cast
  - docs/demo/gifs/*.zh.gif
  - docs/demo/gifs/language-toggle-en.gif
  - docs/demo/RECORDED.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-REVIEW-DISPOSITION.md
  - .planning/STATE.md
  - .planning/quick/261016-hhx-fix-08-delta-review-findings-cr-01-rende/261016-hhx-SUMMARY.md
autonomous: true
requirements: [CR-01, WR-01, WR-02, WR-03, IN-01, IN-02, IN-03]

estimate:
  tokens: 110000
  raw_tokens: 58000
  tasks: 4
  confidence: low

must_haves:
  truths:
    - "CR-01: an en-boot console (or the mirror: a zh-pinned import switched to en) renders ONE language everywhere after an L toggle or a persisted-zh boot — every DataTable column header, queue/sweep/cell state word, monitor [f]/[t] keycap, wizard step/field/quirk label, and run-config dir-picker field label re-derives at render time; structurally pinned by an AST test that forbids module/class-level captures of tui.strings registry constants outside the documented allowlist (nav NAV_SLOTS mount-time re-translation, class BINDINGS remap coverage, app TITLE), and behaviorally pinned by a Pilot test that toggles L on the mounted data-manager screen and asserts headers/state cells equal the fresh module-attribute reads"
    - "zh rendering is BYTE-IDENTICAL pre/post fix under the zh pin: the 9 golden SVG tests stay green UNMODIFIED (the new MON keycap constants carry exactly the old split() projections: zh 失败清单/日志尾随, en Failures/Log tail)"
    - "WR-01: the string registry is injective in BOTH directions (zh->en tripwire exists; a new en->zh tripwire passes) — WIZ_BACK_LABEL en becomes 'Back a step' and QUEUE_STATE_PENDING en becomes '◌ waiting' (NOT '◌ queued' — MON_STATE_QUEUED already owns that en value; the reviewer's example word would create a fresh collision); the wizard b binding description translates to 上一步 on en->zh; no committed en demo cast contains either changed token (verified: every '◌ pending' occurrence in *-en.cast is an env-screen row, and the b binding is show=False)"
    - "WR-02: enqueue_zenodo on an unwritable state rail rolls the append back and returns persist_failed (no ghost row survives a reload); the z action toasts QUEUE_PERSIST_FAILED_TOAST with the bundle label at error severity"
    - "WR-03: pressing L (the _rerender_screen remount path) while an env check is in flight restarts ZERO kernels — the gated-fake Pilot test proves the kernel call count is unchanged, rows are not reset to pending, and the run completes and renders its verdict"
    - "IN-01: KIND_MODEL ticks store nothing in _live_percents/_live_speeds and a KIND_MODEL completion pops any pre-seeded residue; IN-02: the 'language.json' literal exists exactly once in tui/ (tui/services/settings.py), consumed by app.py and __main__.py; IN-03: slot-3's present-row toast consumes DL_ENQUEUE_PRESENT_TOAST and SEL_ENQUEUE_PRESENT_TOAST is retired (zero consumers, inventory lists updated)"
    - "Gates: make lint + make typecheck green; full make test lands at EXACTLY the 7F baseline (test_determinism 1, test_schemas 5, test_services_run_config 1) with zero new failures and every new test passing; node --test 26/26"
    - "Demo honesty: all 10 zh GIFs re-recorded (2026-10-16) with NO English-only header strings in their casts (grep 'Row reconcile' / 'n_audit baseline rows' over *-zh.cast == 0) plus language-toggle-en re-recorded (its zh segment carried 3 frozen 'State' headers — planning-time grep evidence); RECORDED.md rows auto-refreshed with real targets and sizes; docs/TUI-DEMO.md prose untouched unless it quotes a changed header word"
    - "Bookkeeping: the SEVEN disposition rows CR-01, WR-01, WR-02, WR-03, IN-01, IN-02, IN-03 read fixed with their fix commits' short hashes (IN-04 STAYS open — it is not part of this review); STATE.md gains the 261016-hhx quick row; commits are plain (zero trailers); the branch is pushed"
  artifacts:
    - tui/strings.py
    - tui/screens/data_manager.py
    - tui/screens/selection.py
    - tui/screens/monitor.py
    - tui/screens/wizard.py
    - tui/screens/run_config.py
    - tui/screens/env_check.py
    - tui/services/download_queue.py
    - tests/tui/test_language_rederivation.py
    - docs/demo/RECORDED.md
    - .planning/phases/08-tui-foundation-env-check-selection/08-REVIEW-DISPOSITION.md
  key_links:
    - "render-time re-derivation functions (_queue_columns/_state_cells/_model_columns/_queue_state_cells/_sweep_state_cells/_cell_state_cells/_quirk_fields/_kind_spec/_dir_input_fields) -> every on_mount/compose/render call site -> _rerender_screen's recompose + on_mount re-invocation -> the L toggle and the persisted-zh boot render one language"
    - "MON_FAILURES_KEYCAP/MON_LOG_KEYCAP registry constants -> monitor BINDINGS descriptions -> remap_binding_descriptions byte-equality translation (previously impossible: split() substrings never matched a registry value)"
    - "strings._REGISTRY injectivity (both directions) -> translate_value -> remap_binding_descriptions + nav TopMenuBar mount-time re-translation"
    - "enqueue_zenodo _persist_locked check -> ACTION_PERSIST_FAILED rollback -> action_zenodo_bundle error toast (the _toast_enqueue_outcome persist_failed arm mirrored)"
    - "env_check on_mount population-only guard (_results/_check_in_flight/_last_outcome) -> _rerender_screen mid-run remount -> the in-flight worker's run-id-tagged messages keep landing on the rebuilt rows"
    - "scripts/demo/record.sh -> pexpect driver -> casts/gifs + --recorded-row RECORDED.md refresh"
---

<objective>
Fix the 08 delta review's 1 Critical + 3 Warnings + 3 Infos (CR-01 the ehc
import-frozen i18n bug and its WR/IN satellites), then re-record the zh demo
GIFs that captured the mixed-language chrome. Maintainer 2026-10-16 chose
fix-first (same route as 261016-a4f); after this lands, the 08→12 verification
chain resumes.

Purpose: the L toggle and a persisted-zh boot must render ONE language
everywhere — today every module-frozen copy value (column headers, state
vocabularies, keycaps, wizard labels, dir-field map) stays in the boot
language while the chrome flips, and the zh-pinned test conftest structurally
cannot see it. The public demo GIFs currently ship that mixed UI.
Output: two fix commits (CR-01; WR/IN cluster) with regression tests, one
demo-asset commit, one bookkeeping commit; all gates at the exact box
baseline; pushed.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/08-tui-foundation-env-check-selection/08-REVIEW.md
@.planning/phases/08-tui-foundation-env-check-selection/08-REVIEW-DISPOSITION.md
@tui/strings.py
@tui/app.py
@tui/screens/data_manager.py
@tui/screens/selection.py
@tui/screens/monitor.py
@tui/screens/wizard.py
@tui/screens/run_config.py
@tui/screens/env_check.py
@tui/screens/nav.py
@tui/services/download_queue.py
@tests/tui/conftest.py
@tests/tui/test_strings_phase11.py
@tests/tui/test_services_download_queue.py
@tests/tui/test_pilot_data_manager.py
@tests/tui/test_pilot_env_check.py
</context>

<preconditions>
- READ FIRST: the committed 08-REVIEW.md (context list above) — every finding
  carries exact line numbers and empirical reproductions. Its line numbers are
  planning-time evidence (verified on-disk 2026-10-16 at d800613); re-verify
  each site against the live file before editing.
- Scope ruling (MUTABLE-SCOPE authority): tui/ edit freeze is LIFTED for this
  task — fixing tui/ IS the task. Edit scope: the tui/ files listed above,
  their test files, docs/demo/ assets, and the two bookkeeping files. The
  pipeline/ tree, the DNALLM sibling repo (read-only), and CI config stay
  untouched.
- Test baseline (pinned): exactly 7 failed / 1798 passed, membership
  test_determinism 1 + test_schemas 5 + test_services_run_config 1; node
  26/26; make lint + make typecheck green. ANY different failure set at gate
  time = stop and report.
- The 9 golden SVG tests (tests/tui/test_snapshots.py) are regular tests and
  the zh renders must stay BYTE-IDENTICAL under the zh pin (the conftest pins
  zh before imports, so render-time reads and the old frozen reads both
  resolve zh). If a golden goes red: judge whether the change is a
  legitimate behavior change of the fix — if YES, STOP and report for the
  maintainer's D-03 ruling (never regenerate goldens yourself); if NO (a
  conversion bug), fix the code. make snapshot-update is maintainer-only.
- The zh demo re-record runs REAL ModelScope downloads + the bounded
  plant-dnabert-6mer training (~10-15 min total) — pre-authorized (bounded
  GPU runs OK; the E2' full sweep remains dual-gated and untouched). Real
  run artifacts stay gitignored under finetuned/{demo,demo-fail}. The EHC-3
  single-GPU guard refuses the recording if a live sweep runs — if it does,
  STOP and report; never kill a maintainer sweep.
- Conventions: bilingual copy lives ONLY in tui/strings.py via
  _t(name, zh, en) with identical placeholder sets; production modules read
  module-attribute S.CONST (never from-import copies); kernel detail lines
  are DATA rendered verbatim; commits are plain with ZERO trailers; say
  push/merge/commit in English.
- Disposition note: the task brief says "八行" (8 rows) but enumerates 7 IDs —
  the review carries exactly 7 findings (1C/3W/3I). IN-04 in the ledger is
  marked "(not in the current review)" and STAYS open. Fix exactly CR-01,
  WR-01, WR-02, WR-03, IN-01, IN-02, IN-03.
</preconditions>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: CR-01 — render-time re-derivation of every module-frozen copy site + the structural regression tests</name>
  <files>tui/strings.py, tui/screens/data_manager.py, tui/screens/selection.py, tui/screens/monitor.py, tui/screens/wizard.py, tui/screens/run_config.py, tests/tui/test_language_rederivation.py, tests/tui/test_strings_phase11.py</files>
  <behavior>
    - AST pin: parsing every tui/**/*.py except strings.py, NO module-top-level or class-body assignment references a tui.strings registry constant (attribute read via the module's strings alias, or a from-imported constant name) — except the allowlist: nav.py NAV_SLOTS (the documented mount-time re-translation site) and _NAV_SLOTS_LANGUAGE, any class-body assignment whose target is BINDINGS (remap_binding_descriptions owns them), and app.py TITLE (re-set by the toggle). The checker carries a positive control (a synthetic snippet that MUST be flagged).
    - Behavioral pin: with the zh-pinned conftest import (the production en-boot mirror), a Pilot test on the mounted data-manager screen presses L and the #dl-queue column labels plus a queue state cell equal the FRESH module-attribute reads under en (S.QUEUE_COL_TASK etc. read after set_language) — pre-fix this fails with the frozen zh values, post-fix it passes.
    - Wizard: a freshly built kind spec under en carries en step names and field labels (unit-level, via the new builder); under zh (restored) it carries zh.
    - Keycap byte-continuity: MON_FAILURES_KEYCAP == MON_FAILURES_TITLE.split(" (")[0] and MON_LOG_KEYCAP == MON_LOG_TITLE.split(" — {")[0] in BOTH languages.
    - zh goldens: the 9 SVG tests stay green unmodified.
  </behavior>
  <action>
    Write the tests first (RED), then convert. Cite CR-01 in every code
    comment you touch (the 16e21b5 docstring idiom). Line numbers below are
    planning-time; re-verify on disk.

    1. tui/strings.py — register the two monitor keycap constants in the MON_
       block (near MON_FAILURES_TITLE/MON_LOG_TITLE, planning-time 1616/1650):
       MON_FAILURES_KEYCAP = _t("MON_FAILURES_KEYCAP", "失败清单", "Failures")
       and MON_LOG_KEYCAP = _t("MON_LOG_KEYCAP", "日志尾随", "Log tail") —
       the values are EXACTLY the current split() projections in both
       languages (zh render stays byte-identical for the goldens; en render
       unchanged), and being byte-equal registry values is what finally makes
       remap_binding_descriptions able to translate them. Add them to
       EXPECTED_MON_CONSTANTS in tests/tui/test_strings_phase11.py (the
       bidirectional MON_ inventory lock).

    2. tui/screens/data_manager.py — convert the four frozen structures to
       functions that read S.* at CALL time (the env_check.py:427-431 /
       matrix.py render-time pattern; call-site shapes unchanged):
       _QUEUE_COLUMNS (151) -> _queue_columns(); _MISSING_COLUMNS (158) ->
       _missing_columns(); _FULL_COLUMNS (166) -> _full_columns();
       _STATE_CELLS (188) -> _state_cells() returning the dict. Update the
       five call sites: on_mount 674, _render_missing 855,
       _render_presence_view 889 + 918, _state_cell 1020. Column keys and
       widths stay language-neutral literals inside the functions.

    3. tui/screens/selection.py — same conversion: _MODEL_COLUMNS (863) ->
       _model_columns() (call site _rebuild_rows 1574); _QUEUE_STATE_CELLS
       (893) -> _queue_state_cells() (call site _model_download_cell 955).
       The test-side literal _MODEL_COLUMNS_KEYS (tests/tui/
       test_pilot_selection.py:168) is independent — leave it.

    4. tui/screens/monitor.py — delete _FAILURES_KEYCAP/_LOG_KEYCAP (108-109,
       the split() substrings) and inline S.MON_FAILURES_KEYCAP /
       S.MON_LOG_KEYCAP directly in the two BINDINGS entries (754-755);
       remap now translates them. Convert _SWEEP_STATE_CELLS (113) ->
       _sweep_state_cells() and _CELL_STATE_CELLS (120) -> _cell_state_cells()
       (call sites 629, 633, 1413, 1485).

    5. tui/screens/wizard.py — convert the four frozen structures:
       QUIRK_FIELDS (186) -> _quirk_fields() (call sites 595, 647, 737, 853,
       1329); MODEL_STEPS (193) / DATASET_STEPS (224) -> _model_steps() /
       _dataset_steps() builders; KINDS (254) -> a module-level
       _KIND_NAMES: tuple = ("models", "datasets") (language-neutral, for the
       ctor validation at 558-561) plus def _kind_spec(kind) -> KindSpec
       building steps/labels/kind_name from fresh S.* reads. WizardModal
       stores self._kind_spec = _kind_spec(kind) in __init__ (581-582 already
       store steps/labels; kind_name consumers at 763, 769, 1290 switch from
       KINDS[self._kind] to self._kind_spec.kind_name). Ctor-frozen copy is
       the accepted modal semantics (constructed at push time in the active
       language) — the freeze being removed is the MODULE-level one.

    6. tui/screens/run_config.py — convert the ClassVar _DIR_INPUT_FIELDS
       (1749-1755) to def _dir_input_fields() -> dict (call site
       action_open_dir_picker 1798): the ctrl+o picker title re-derives.

    7. tests/tui/test_language_rederivation.py (NEW) — the CR-01 regression
       surface, two pins plus the wizard unit pin:
       (a) test_no_import_frozen_registry_captures — AST walk of tui/**/*.py
       (skip strings.py); resolve each module's tui.strings alias (both
       "from tui import strings [as X]" and "from tui.strings import A, B"
       forms); flag any Assign/AnnAssign at module top level or directly in
       a class body whose value references a name in
       set(tui.strings._REGISTRY) via that alias or as a from-imported
       binding; allowlist exactly: the target NAV_SLOTS or
       _NAV_SLOTS_LANGUAGE in tui/screens/nav.py, class-body assignments
       whose target name is BINDINGS, and TITLE in tui/app.py. Positive
       control: run the same checker over ast.parse of a synthetic offender
       module snippet and assert it IS flagged (the test_card_site_hardening
       positive-control idiom). Style the file header after
       tests/tui/test_work_site_hardening.py.
       (b) test_toggle_rerderives_data_manager_columns_and_state_cells —
       Pilot test in the test_pilot_data_manager.py harness idiom: build the
       app via the file's _app(queue=...) shape with a fake queue serving
       ONE pending dataset entry, monkeypatch STATE_DIR_ENV to tmp_path (the
       L press persists language.json — keep it out of the real XDG root),
       run_test(size=(120, 40)), _open_data_manager (press "3" + await
       workers), assert the #dl-queue "task" column label equals
       tui_strings.QUEUE_COL_TASK (zh under the pin), then press "L", await
       pilot.pause() + workers + pause, and assert the SAME fresh attribute
       read now labels the column (en) AND the pending row's state cell text
       equals tui_strings.QUEUE_STATE_PENDING read fresh. Assert against
       module-attribute reads, NEVER literals (value-change-proof for Task
       2's WR-01 edit). CRITICAL finally-block: tui_strings.set_language("zh")
       PLUS remap_binding_descriptions("en", "zh") — the toggle rebuilds
       class BINDINGS descriptions in place and later zh Pilot/golden tests
       depend on the restore.
       (c) test_kind_spec_reads_active_language — set_language("en") in a
       try/finally(zh): wizard._kind_spec("models").steps[0].name equals
       S.WIZM_STEPS[0] read fresh, and one WIZM_FIELD_LABELS label matches;
       restored to zh the same call returns zh.
    Then run the full tui/ suite slice to catch conversion fallout (several
    Pilot files assert zh headers/state words — they read module attributes
    so they follow the pin, but call-site mistakes will surface here).
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_language_rederivation.py tests/tui/test_snapshots.py tests/tui/test_strings_phase11.py -q && uv run --group dev --group tui pytest tests/tui -q -x -m "not slow"</automated>
  </verify>
  <done>Both new pins green (the AST allowlist is exactly the four sanctioned sites; the Pilot toggle test proves re-derivation); the 9 zh goldens green unmodified; the tui/ suite slice green (7F baseline untouched — none of the baseline files are in this slice); commit as fix(261016-hhx): CR-01 render-time i18n — plain, no trailers.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: WR-01/02/03 + IN-01/02/03 — registry injectivity, zenodo persist lane, env-remount guard, live-dict hygiene, shared filename constant, DL_ toast twin</name>
  <files>tui/strings.py, tui/services/download_queue.py, tui/screens/data_manager.py, tui/screens/env_check.py, tui/app.py, tui/__main__.py, tui/services/settings.py, tests/tui/test_strings_phase11.py, tests/tui/test_services_download_queue.py, tests/tui/test_pilot_env_check.py, tests/tui/test_pilot_data_manager.py</files>
  <behavior>
    - WR-01: a new en->zh injectivity tripwire (mirror of test_registry_consistency_same_zh_implies_same_en) passes — for every distinct en value carried by more than one constant, all such constants share ONE zh value; after the two value edits it holds. The wizard b binding description translates "Back a step" -> 上一步 under translate_value.
    - WR-02: with the state dir chmod 0o500, enqueue_zenodo() returns action persist_failed and a fresh queue load sees zero entries (append rolled back); the z action on the screen toasts QUEUE_PERSIST_FAILED_TOAST with the bundle label at error severity and kicks nothing.
    - WR-03: with a gated fake env service counting kernel invocations, triggering the _rerender_screen remount mid-run leaves the call count unchanged, keeps the completed rows' final glyphs (not reset to pending), and after the gate releases the run completes and renders the verdict + last-check line.
    - IN-01: a KIND_MODEL progress tick stores nothing in _live_percents/_live_speeds; a KIND_MODEL completion event pops pre-seeded residue for its key.
    - IN-02: grep -rn "language.json" over tui/ hits exactly one line (the settings.py constant definition).
    - IN-03: the slot-3 present-row enqueue toast assertion passes against DL_ENQUEUE_PRESENT_TOAST; SEL_ENQUEUE_PRESENT_TOAST no longer exists in tui/ or the inventory tuples.
  </behavior>
  <action>
    Write/extend the tests first, then fix. Cite the finding IDs in comments.

    1. WR-01 (tui/strings.py + tests/tui/test_strings_phase11.py): change
       WIZ_BACK_LABEL (845) en "Back" -> "Back a step" (show=False binding
       description — renders nowhere; verified zero cast/test pins) and
       QUEUE_STATE_PENDING (1114) en "◌ pending" -> "◌ waiting". DO NOT use
       the reviewer's example "◌ queued": MON_STATE_QUEUED (1565) already
       owns en "◌ queued" with a different zh — that word would recreate the
       collision. Planning-time verified: every "◌ pending" occurrence in
       the committed *-en.cast files is an env-screen row (ENV_STATE_PENDING
       — unchanged), so no en demo asset drifts. Add
       test_registry_consistency_same_en_implies_same_zh directly after the
       existing zh->en tripwire (same defaultdict shape, en-owners keyed on
       zh values, structured entries excluded).

    2. WR-02 (tui/services/download_queue.py + tui/screens/data_manager.py +
    tests/tui/test_services_download_queue.py): in enqueue_zenodo, replace
       the discarded self._persist_locked() (planning-time 1579) with the
       sibling-lane discipline (enqueue 1520-1523 / enqueue_model 1650-1653):
       on a non-None persist error, self._entries.pop() and return
       EnqueueOutcome(action=ACTION_PERSIST_FAILED, key=ZENODO_BUNDLE_KEY).
       In data_manager.action_zenodo_bundle (1280-1289), add an explicit
       persist_failed branch before the already_queued else:
       notify QUEUE_PERSIST_FAILED_TOAST.format(key=S.DL_BUNDLE_TASK_NAME)
       severity "error" (the _toast_enqueue_outcome persist_failed arm,
       1144-1147, mirrored — do not restructure the action into
       _toast_enqueue_outcome: the bundle label is not the raw outcome.key).
       Service test: mirror the state.chmod(0o500) pattern at
       test_services_download_queue.py:3665-3693 for the bundle lane
       (persist_failed + rollback + fresh-load-empty), plus a screen-side
       toast assertion if the existing zenodo Pilot test shape makes it
       cheap.

    3. WR-03 (tui/screens/env_check.py + tests/tui/test_pilot_env_check.py):
       make the on_mount tail (441-450) population-only on re-mount. Add
       instance state in __init__ (~394-398): self._check_in_flight = False
       and self._last_outcome: tuple[str, tuple, str | None] | None = None.
       run_full_check sets _check_in_flight = True at entry; the ACCEPTED
       CheckRunComplete handler (run_id matches) stores
       self._last_outcome = (checked_at, results, persist_error) and clears
       the flag (clear only on accepted — a stale-dropped completion belongs
       to a superseding run that set the flag itself). The on_mount cache-hit
       branch also stores _last_outcome. Restructure the tail: if
       self._results — re-apply every stored result via
       _apply_result_to_table and re-render _render_check_outcome(*
       self._last_outcome) when stored (partial results re-apply fine; the
       in-flight worker's run-id-tagged messages keep landing on the rebuilt
       rows); elif self._check_in_flight — leave the freshly built pending
       rows and return through _render_storage (NO cache consult, NO
       run_full_check); else — the existing cached_results()/run_full_check
       logic unchanged (first mount). Update the _rerender_screen docstring
       claim in app.py (989-1010) to state the now-true contract: env_check
       became population-only by guard (WR-03). Pilot test: extend
       FakeEnvCheckService with a per-kernel call counter if it lacks one;
       boot, wait for the gated first kernel's checking state, await
       app._rerender_screen(app.screen) (the toggle's exact mechanism), then
       release the gate, await completion, and assert the call count is
       unchanged by the remount, the completed rows kept final glyphs, and
       the verdict rendered.

    4. IN-01 (tui/screens/data_manager.py): in apply_queue_progress (799-800)
       move the two _live_percents/_live_speeds stores BELOW the guard
       (803-805) so only passing (dataset, downloading) ticks store; in
       apply_queue_event move the two pops (775-776) ABOVE the KIND_MODEL
       early return (771-772) so a model completion cleans residue. Unit
       tests in test_pilot_data_manager.py near the existing
       apply_queue_progress coverage: a KIND_MODEL tick leaves both dicts
       without the key; a KIND_MODEL done event pops a pre-seeded key.

    5. IN-02 (tui/services/settings.py + tui/__main__.py + tui/app.py):
       define LANGUAGE_FILE_NAME = "language.json" in settings.py next to
       state_dir (doc comment: the one persisted-language filename, EHC-1);
       __main__.py imports it (from tui.services.settings import
       LANGUAGE_FILE_NAME) keeping the module attribute available for its
       boot read and the existing tui_main.LANGUAGE_FILE_NAME test reference
       (test_pilot_boot.py:288 — unchanged); app.py action_toggle_language
       (1032) writes settings.state_dir() / settings.LANGUAGE_FILE_NAME.
       No test edit needed — the existing boot tests pin the behavior; the
       grep pin lands in this task's verify.

    6. IN-03 (tui/strings.py + tui/screens/data_manager.py + the two test
       files): register DL_ENQUEUE_PRESENT_TOAST = _t(
       "DL_ENQUEUE_PRESENT_TOAST", "该数据集已在场", "Dataset already
       present") in the DL_ block (same values as the SEL_ twin — the
       wording is dataset-specific and slot 3 is the only consumer); consume
       it at data_manager.py:1171; RETIRE SEL_ENQUEUE_PRESENT_TOAST
       (strings.py:1220 — zero consumers after the swap, grep-proven at
       planning time); update EXPECTED_SEL_CONSTANTS (drop the name, amend
       the 3331-3333 comment note) and EXPECTED_DL_CONSTANTS (add the name)
       in tests/tui/test_services_download_queue.py — both inventory locks
       are bidirectional over their prefixes; swap the import (469) and
       assertion (1280) in tests/tui/test_pilot_data_manager.py to the DL_
       constant.
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_strings_phase11.py tests/tui/test_services_download_queue.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_data_manager.py tests/tui/test_pilot_boot.py tests/tui/test_language_rederivation.py -q && LIT=$(grep -rn --include="*.py" "language.json" tui/ | wc -l) && [ "$LIT" -eq 1 ] && ! grep -rq "SEL_ENQUEUE_PRESENT_TOAST" tui/ tests/</automated>
  </verify>
  <done>All six findings fixed with their tests green; the en->zh injectivity tripwire passes; exactly one language.json literal in tui/; SEL_ENQUEUE_PRESENT_TOAST fully retired; the touched Pilot files green; commit as fix(261016-hhx): WR-01..03 + IN-01..03 — plain, no trailers.</done>
</task>

<task type="auto">
  <name>Task 3: re-record the zh demo GIFs (+ language-toggle-en) and refresh RECORDED.md</name>
  <files>docs/demo/casts/*-zh.cast, docs/demo/gifs/*-zh.gif, docs/demo/casts/language-toggle-en.cast, docs/demo/gifs/language-toggle-en.gif, docs/demo/RECORDED.md</files>
  <action>
    All 10 zh scenes re-recorded AFTER Tasks 1-2 are committed — the current
    zh GIFs captured the mixed-language chrome (planning-time evidence:
    dataset-download-zh.cast contains 17 frozen "Task" header renders;
    every zh cast carries en column-header words). Plus ONE en re-record:
    language-toggle-en (its mid-scene zh segment carries 3 frozen "State"
    headers — the bug itself on film; all other en casts verified free of
    frozen-copy artifacts AND of the Task-2-changed tokens, so they stay).

    1. For each of the ten scenes — env-check, selection-presets,
       language-toggle, run-config-preview, wizard, custom-entries,
       dataset-download, model-download, launch-monitor-kill,
       rerun-from-failures — run:
       bash scripts/demo/record.sh SCENE zh
       using speed 2.5 instead of the default 1.5 for launch-monitor-kill
       and rerun-from-failures (the script header's own recommendation for
       the long training scenes). Then:
       bash scripts/demo/record.sh language-toggle en
       The chain (asciinema rec -> pexpect driver -> meta exit-code gate ->
       100x30 header normalize -> agg -> --recorded-row) refreshes the
       RECORDED.md honesty row per scene automatically. Real downloads +
       the bounded training re-run (~10-15 min total, pre-authorized;
       finetuned/{demo,demo-fail} stay gitignored). If the EHC-3 guard
       refuses (a live sweep holds the GPU), STOP and report.
    2. Eyeball every refreshed RECORDED.md row: date 2026-10-16, real
       targets present, honest degradation notes wherever the recording
       degraded — the ledger must state what each GIF truly shows.
    3. Verify the casts: the frozen-header tokens are GONE from the zh
       renders and the zh headers are present (the verify block's greps).
       If docs/TUI-DEMO.md quotes any changed header/state word (grep it
       for the old en tokens "Row reconcile", "n_audit baseline rows",
       "◌ pending" in a queue-table context, and the zh headers), update
       ONLY those factual references — otherwise the prose stays
       byte-untouched.
    4. Spot-open one re-recorded zh GIF (e.g. dataset-download-zh.gif) and
       confirm the queue table headers are 任务/状态/进度/行数对账 with zh
       chrome — the visual twin of the grep evidence.
  <verify>
    <automated>bash -c 'for s in env-check selection-presets language-toggle run-config-preview wizard custom-entries dataset-download model-download launch-monitor-kill rerun-from-failures; do bash scripts/demo/record.sh "$s" zh || exit 1; done' && bash scripts/demo/record.sh language-toggle en && ! grep -rq -e "Row reconcile" -e "n_audit baseline rows" --include="*-zh.cast" docs/demo/casts/ && grep -q "行数对账" docs/demo/casts/dataset-download-zh.cast && grep -q "行数对账" docs/demo/casts/rerun-from-failures-zh.cast && grep -c "2026-10-16" docs/demo/RECORDED.md</automated>
  </verify>
  <done>Eleven GIFs re-recorded (10 zh + language-toggle-en) with refreshed honest RECORDED.md rows dated 2026-10-16; zero en-only header strings in any zh cast; the zh queue headers present in the queue-bearing casts; TUI-DEMO.md untouched or factually corrected only; commit as docs(261016-hhx): re-record zh demo GIFs post-CR-01 — plain, no trailers. The recordings run ~10-15 min; run the greps after.</done>
</task>

<task type="auto">
  <name>Task 4: full gates, disposition ledger, STATE row, push</name>
  <files>.planning/phases/08-tui-foundation-env-check-selection/08-REVIEW-DISPOSITION.md, .planning/STATE.md, .planning/quick/261016-hhx-fix-08-delta-review-findings-cr-01-rende/261016-hhx-SUMMARY.md</files>
  <action>
    1. Run the full gate suite: make lint && make typecheck && make test.
       Expected: lint/typecheck green; pytest at EXACTLY 7 failed with the
       pinned membership (test_determinism 1, test_schemas 5,
       test_services_run_config 1) and every other test passing (baseline
       1798P + the new tests); node --test 26/26. Any different failure
       set: stop and report — do not commit.
    2. Update .planning/phases/08-tui-foundation-env-check-selection/
       08-REVIEW-DISPOSITION.md: the SEVEN rows CR-01, WR-01, WR-02, WR-03,
       IN-01, IN-02, IN-03 -> disposition fixed with the short hash of the
       commit that fixed each (Task 1's commit for CR-01; Task 2's commit
       for the six WR/IN rows) in the Source column; IN-04 STAYS open (not
       part of this review). Update the frontmatter to match (the seven
       findings' disposition: fixed; open: 1).
    3. Append the 261016-hhx quick row to .planning/STATE.md's Quick Tasks
       Completed table (id, description: fix 08 delta review CR-01 + WR/IN
       + zh GIF re-record, date 2026-10-16, the Task-3-or-latest commit
       hash, directory link) and refresh last_activity.
    4. Write the 261016-hhx-SUMMARY.md (per the summary template): what
       changed per finding with file:line evidence, the WR-01 value-choice
       note (why "◌ waiting" not the reviewer's "◌ queued" — the
       MON_STATE_QUEUED collision), the language-toggle-en inclusion
       rationale, gate outputs, and the 7F/1-node gate evidence.
    5. Commit the bookkeeping as docs(261016-hhx): disposition + STATE row
       — plain, no trailers — then git push the branch.
  <verify>
    <automated>bash -c 'set -o pipefail; make lint && make typecheck && make test 2>&1 | tail -15' && test -z "$(git status --porcelain)" && git log --oneline -4</automated>
  </verify>
  <done>Gates at the exact baseline; the seven disposition rows fixed with hashes and IN-04 open; STATE row landed; SUMMARY written; working tree clean; branch pushed with plain commits.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| demo re-record -> network/GPU | the committed pexpect driver performs real ModelScope downloads and one bounded GPU training (pre-authorized; same surface as the 2026-10-15 recordings) |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-hhx-01 | Tampering | downloaded model/dataset payloads consumed by demo runs | low | accept | unchanged surface from the sanctioned original recordings; outputs land under gitignored finetuned/{demo,demo-fail} and never feed committed data |
| T-hhx-02 | Denial of Service | zh re-record colliding with a live production sweep on the single GPU | low | mitigate | the EHC-3 single-GPU serialization guard refuses at stage 0; executor stops and reports instead of killing the maintainer sweep |
| T-hhx-SC | Tampering | package installs (record.sh uses uv --with pexpect==4.9.0) | low | accept | no NEW packages this task; pexpect 4.9.0 already sanctioned in quick-261015-pex and pinned in the committed script |
</threat_model>

<verification>
- make lint + make typecheck green; make test at EXACTLY 7F (pinned membership) / all-new-tests-pass / node 26/26.
- The CR-01 AST pin and the L-toggle Pilot pin both green; the 9 zh goldens green UNMODIFIED.
- Both registry-injectivity tripwires (zh->en, en->zh) green.
- WR-02/WR-03/IN-01 behavior tests green; one language.json literal in tui/; SEL_ENQUEUE_PRESENT_TOAST gone.
- Eleven re-recorded GIFs; zero en-only header strings in zh casts; RECORDED.md rows dated 2026-10-16.
- Seven disposition rows fixed with commit hashes; IN-04 open; STATE row present; plain commits; pushed.
</verification>

<success_criteria>
The L toggle and a persisted-zh boot render one language everywhere, the
seven review findings are closed with regression coverage that would have
caught each, the public demo GIFs show the fixed zh UI with an honest
ledger, and the repo sits at its exact pre-task gate baseline plus the new
tests — pushed, with the 08→12 verification chain unblocked.
</success_criteria>

<output>
Create .planning/quick/261016-hhx-fix-08-delta-review-findings-cr-01-rende/261016-hhx-SUMMARY.md when done
</output>
