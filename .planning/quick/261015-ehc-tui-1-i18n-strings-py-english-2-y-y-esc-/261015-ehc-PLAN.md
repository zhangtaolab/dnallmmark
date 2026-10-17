---
phase: quick-261015-ehc
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/strings.py
  - tests/tui/conftest.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_snapshots.py
  - tui/app.py
  - tui/__main__.py
  - tui/screens/env_check.py
  - tui/screens/selection.py
  - tui/screens/matrix.py
  - tui/screens/wizard.py
  - tui/screens/data_manager.py
  - tui/screens/run_config.py
  - tui/screens/monitor.py
  - tui/screens/about.py
  - tui/screens/nav.py
  - tui/services/sweep_launcher.py
  - tui/services/download_queue.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_sweep_launcher.py
  - docs/TUI-GUIDE.md
autonomous: true
requirements: [EHC-1, EHC-2, EHC-3, EHC-4]
user_setup: []

estimate:
  tokens: 120000
  raw_tokens: 60000
  tasks: 5
  confidence: low

must_haves:
  truths:
    - "EHC-1 (ruling 1): every operator-facing copy renders in the ACTIVE language with DEFAULT English — tui/strings.py is a bilingual registry (each constant carries zh + en, names byte-stable), the L app binding toggles zh<->en LIVE (all stacked screens re-render, footer/help binding labels follow, no app restart) and persists to the XDG state root via the settings.py system (DNALLMMARK_TUI_STATE_DIR redirectable; boot load happens ONLY in tui/__main__.main — test-constructed apps stay inert); the zh side applies the approved terminology table verbatim (sweep→训练任务, 输出根→结果目录, 附加/attach→监控, 发射/launch→启动, 短语门→二次确认, cell→训练项, 存储根→存储位置, 发现的 sweep→自动找到的训练任务); model names / dataset IDs / CUDA / filenames / kernel ids / CLI / flag names stay English in BOTH languages; every existing inventory tripwire (CFG_/LNC_/MON_/DL_/QUEUE_/SEL_) checks BOTH languages bidirectionally; glyph-first constants lead with their glyph in both languages; the code-files-zero-CJK lock keeps holding (both languages live only in tui/strings.py)"
    - "EHC-2 (ruling 2): in the three LAUNCH confirm surfaces — the slot-4 regular gate (_GateConfirmModal), the E2' typed-phrase modal (E2PhraseModal), and the monitor re-run confirm — `y` starts and `Esc` cancels; `enter` no longer passes any of them (a stray double-enter can never launch); the E2' full gate keeps the typed phrase as double insurance ON TOP (type phrase -> enter advances to the y-ready state -> y launches; the phrase-match predicate and the service-side structural gate are untouched); the shared ConfirmModal and its non-launch consumers (preset overwrite, queue cancels, wizard cancel) stay on enter, byte-identical"
    - "EHC-3 (ruling 3): with effective GPU count == 1 (WORLD_SIZE when parseable >=1, else lazy torch.cuda.device_count() honoring CUDA_VISIBLE_DEVICES, tolerant 0 when torch/CUDA unavailable), BOTH gated launch paths — the launcher gate (launch_spec via the slot-4 pipeline) and the monitor re-run path (launch_from_failures) — REFUSE to start when a live sweep is registered in the launcher registry, surfacing the running output root(s) in bilingual copy; the refusal is enforced in the service (spawner provably never called) and pre-checked in both screens before any confirm modal; multi-GPU (count >= 2) and count-0 machines are unrestricted; the raw launch_argv seam stays ungated (the pinned tier-1 contract)"
    - "EHC-4 (ruling 4 + the 2026-10-15 placement amendment): download SPEED (the parsed rate token, e.g. 892kB/s) renders ALONGSIDE the percent on slot 2 (the model-lane live download cell) and slot 3 (the dataset-lane queue progress cell) ONLY — when the CLI/child output carries no rate, the honest fallback is percent-only (never a fabricated speed); the speed rides the existing parse_progress/progress_cb/QueueProgressMessage plumbing as an additive field (every pre-existing injected fake keeps conforming); slot 4 (run config) gains NOTHING download-related and no global download banner exists anywhere"
    - "Invariants + gates: make lint + make typecheck green; the full suite at exactly the box baseline (7 documented failures + 9 strict-xfail goldens, zero new); tests/tui/__snapshots__/ byte-untouched with the xfail-strict state unchanged (this task's copy drift KEEPS the already-stale goldens failing; amend _GOLDEN_REFRESH_REASON in place per the 261014-mlc precedent and note the visual changes in the SUMMARY for D-03); @work never-exit pin, card-extraction allowlist, tee/registry/attach SEMANTICS all unchanged (attach behavior untouched — only its zh copy says 监控); zero new dependencies; textual 8.2.8; pipeline/ tree and DNALLM sibling untouched; commits plain (no attribution trailers)"
  artifacts:
    - tui/strings.py
    - tui/app.py
    - tui/services/sweep_launcher.py
    - tui/services/download_queue.py
    - tui/screens/selection.py
    - tui/screens/run_config.py
    - tui/screens/monitor.py
    - tui/screens/data_manager.py
  key_links:
    - "set_language() rebinds the strings module globals -> module-attribute access at every production call site (S.CONST) -> screen recompose on L -> footer/help binding descriptions remapped via translate_value"
    - "progress_cb(key, percent, speed) -> app on_progress/QueueProgressMessage(speed) -> apply_queue_progress -> the slot-2 _model_download_cell + the slot-3 queue progress cell"
    - "SweepLauncher.single_gpu_launch_blocked() -> the run_config gate pre-check + the monitor request_rerun pre-check -> the service-side first-stage refusal in launch_spec/launch_from_failures"
---

<objective>
The maintainer's 2026-10-15 three hardening rulings for the TUI, plus the same-day speed-display amendment — four shipped behaviors in one serial plan:

1. **EHC-1 — TUI bilingual i18n**: tui/strings.py becomes a bilingual registry (zh + en per constant, DEFAULT English), with a live global language toggle (`L`), persistence through the existing settings/state layer, the approved zh terminology table applied verbatim, and every existing inventory tripwire checking both languages.
2. **EHC-2 — launch-gate `y` confirm**: in the launch confirm gates, `y` starts / `Esc` cancels; `enter` no longer passes any launch gate (double-press protection); the E2' full gate keeps the typed phrase as double insurance on top.
3. **EHC-3 — single-GPU serialization guard**: on effective-GPU-count == 1 machines, both gated launch paths (slot-4 gate + monitor re-run) refuse while a live sweep is registered, naming the running output root; multi-GPU machines unrestricted.
4. **EHC-4 — download speed display**: the download progress surfaces on slot 2 (model lane) and slot 3 (dataset lane) show the parsed SPEED alongside the percent, with the honest percent-only fallback; slot 4 gains nothing download-related.

Purpose: operator-facing hardening of the console before public milestone close — bilingual reach with English-first defaults, misfire-proof launch confirms, no accidental single-GPU contention, and honest live transfer telemetry.
Output: five atomic commits on `autorun` (plain messages, `feat(261015-ehc)/test(261015-ehc)/...` scope tags), the full suite at the box baseline, goldens byte-untouched.

EXECUTOR NOTE (hard constraint): load the tui-design skill FIRST before touching any screen code; every textual 8.2.8 mechanism this plan marks "probe" must be probe-pinned before being relied on (the repo's established discipline — record the probe result in a code comment or test).
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/quick/261015-c4j-tui-ux-1-slot-2-kind-model-slot-3-downlo/261015-c4j-SUMMARY.md

@tui/strings.py
@tui/app.py
@tui/services/settings.py
@tui/services/sweep_launcher.py
@tui/services/download_queue.py
@tui/screens/selection.py
@tui/screens/run_config.py
@tui/screens/monitor.py
@tui/screens/data_manager.py
@tests/tui/test_strings_phase11.py
@tests/tui/conftest.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: EHC-1a — the bilingual strings registry (zh terminology + English authoring + both-language tripwires)</name>
  <files>tui/strings.py, tests/tui/conftest.py, tests/tui/test_strings_phase11.py, tests/tui/test_services_download_queue.py, tests/tui/test_snapshots.py</files>
  <behavior>
    - Test 1 (both-language inventory, phase11 + download_queue files): for lang in ("zh", "en"): strings.set_language(lang) -> every EXPECTED_* constant exists, is a non-empty str (dict/tuple for the six structured constants), name-prefix correct; restore zh afterward.
    - Test 2 (bidirectional completeness): dir(tui_strings)-derived defined sets for every registered prefix still equal the listed tuples (both directions) — unchanged mechanism, now language-independent (real module globals).
    - Test 3 (glyph-first, both languages): every MON_ stateful constant's first char is its glyph in zh AND in en.
    - Test 4 (registry consistency — the Task-2 precondition): for every distinct zh value carried by more than one constant, all such constants share ONE en value (same-zh implies same-en); every _REGISTRY entry has both values non-empty strings; the structured (dict/tuple) entries carry identical key sets / arities across languages.
    - Test 5 (terminology tripwire): the zh values contain zero occurrences of the retired terms 输出根 / 短语门 / 存储根, and no zh value contains the bare word "sweep" or "cell" except where the ruling keeps English-verbatim data (there are none in copy — sweep and cell are fully retired in zh copy).
    - Test 6 (default): a fresh import surface — strings.DEFAULT_LANGUAGE == "en" and language() == "en" after strings.set_language("en"); set_language persists module state until the next call.
  </behavior>
  <action>
    Restructure tui/strings.py in place as the bilingual registry while KEEPING the constant names and the real module-level globals (ty must keep seeing named typed attributes; the tripwire `dir()`/`hasattr`/`isinstance` mechanism must survive unchanged):
    - Add a private TypeVar-typed registration helper `def _t(name, zh, en)` — it records the (name -> (zh_value, en_value)) pair into a module-level `_REGISTRY` dict and RETURNS the ACTIVE-language value, so each constant stays an explicit typed module assignment of the exact shape `CONST = _t("CONST", "<zh>", "<en>")` (str constants infer str; the structured constants ENV_KERNEL_LABELS / ENV_STORAGE_LABELS / WIZM_FIELD_LABELS / WIZD_FIELD_LABELS / WIZM_STEPS / WIZD_STEPS pass their per-language whole dicts/tuples through the same helper — keys and arities identical across languages, only values translate). Constants whose value is language-neutral (glyphs like ENV_STATE_PASS "✓", data words like MON_COL_SEED "s{seed}", English-verbatim labels like SEL_COL_CATEGORY "Category", CFG_FIELD_SEEDS "seeds", ENV_KERNEL_DEGRADED "FAIL: kernel raised {error}") simply carry the same value twice.
    - Add `LANGUAGES = ("en", "zh")`, `DEFAULT_LANGUAGE = "en"`, an in-module `_ACTIVE_LANGUAGE = DEFAULT_LANGUAGE`, and `set_language(lang)` / `language()` — set_language validates lang against LANGUAGES and REBINDS every registry constant via globals() so module-attribute access (Task 2's `S.CONST`) resolves the new language live; `from tui.strings import X` copies remain frozen at import (accepted; production call sites convert in Task 2, tests stay intentionally frozen-see conftest pin below). Add the pure `translate_value(text, from_lang, to_lang)` — returns the registry's to_lang value for the entry whose from_lang value equals text (byte equality), else text unchanged (Task 2's binding-label remap; the same-zh-implies-same-en tripwire above is what makes it well-defined).
    - Apply the APPROVED zh terminology table VERBATIM while transcribing the zh values (grep every registry zh value for each retired term and rewrite per the table — do not paraphrase beyond the table; the retired zh terms 输出根 / 短语门 / 存储根 are rewritten EVERYWHERE in this file, comments included, so the whole-file grep gate below stays honest — English comments keep the established English terms sweep/cell/output root):
      sweep → 训练任务; 输出根 → 结果目录; 附加/attach → 监控; 发射/launch → 启动; 短语门 → 二次确认; cell → 训练项; 存储根 → 存储位置; 发现的 sweep → 自动找到的训练任务.
      Known hit sites (non-exhaustive — the grep sweep is authoritative): "sweep": LNC_E2_WARNING, LNC_LAUNCH_TOAST, LNC_EXIT_MESSAGE, LNC_EXIT_MESSAGE_MULTI, MON_DISCOVERED_TITLE, MON_DISCOVERED_EMPTY, MON_LOG_UNAVAILABLE; "输出根": CFG_FIELD_OUTPUT_ROOT, CFG_OUTPUT_ROOT_PROBLEM, MON_COL_ROOT, MON_ATTACH_TITLE, MON_ATTACH_PLACEHOLDER; "附加": MON_ATTACH_LABEL, MON_CELLS_EMPTY ("手动附加" → 手动监控); "cell": LNC_GATE_SUMMARY, LNC_LAUNCH_TOAST, CFG_PREVIEW_LINE, CFG_PREVIEW_LINE_CURVE, MON_CELLS_TITLE, MON_RESUME_NOTE, MON_RESUME_NOTE_SHORT, MON_RERUN_CONFIRM, MON_RERUN_TOAST, GAUNTLET_ROW_DRY_RUN_PASS ("cell(s) 计划成功" → "训练项 计划成功"); "短语门"+"cell": CFG_OUTPUT_ROOT_PROBLEM (→ "结果目录不可为文件系统根目录（二次确认与训练项布局均失效）: {value}"); "存储根": ENV_ROUTE_MISSING_MODELS. Attach SEMANTICS stay untouched — only the zh copy says 监控 (the 11-08 invariant).
    - Author the English half for every constant under these rules: (1) the leading glyph (✓ ✗ ◌ ⠋ ● ○ ⊘ ⚠) is preserved byte-exact; (2) the {placeholder} set is identical to the zh entry's; (3) English-verbatim DATA is never translated — registry keys, dataset keys, kernel ids, Category/seeds/PEFT/epochs/effective_batch_size, CLI commands, file paths, XDG/n_audit/trainer_state/tee, CUDA; (4) en uses ASCII punctuation, zh keeps its CJK punctuation; (5) concise operator register (footer/binding labels max 2 words). Seed exemplars to anchor the register (zh / en): APP_TITLE "DNALLM-Mark 控制台" / "DNALLM-Mark Console"; APP_QUIT_LABEL 退出 / "Quit"; APP_MIN_SIZE_MESSAGE "终端过小（需 ≥ 80x24，当前 {w}x{h}）— 请放大窗口" / "Terminal too small (need >= 80x24, current {w}x{h}) — please enlarge the window"; ENV_SCREEN_TITLE 环境检查 / "Environment Check"; SEL_COL_MODEL 模型 / "Model"; SEL_PRESENCE_MISSING "✗ 缺失" / "✗ missing"; NAV_LABEL_RUN_CONFIG 运行配置 / "Run Config"; QUEUE_STATE_DOWNLOADING "⠋ 下载中" / "⠋ downloading"; LNC_E2_WARNING (post-terminology zh) "⚠ 全量 E2' 训练任务 — 59 模型 × 50 数据集 × 3 种子 = 8850 训练项" / "⚠ Full E2' sweep — 59 models × 50 datasets × 3 seeds = 8850 cells" (the en side KEEPS the established English terms sweep/cell/output root — the terminology table governs the zh side only); MON_DISCOVERED_TITLE (post-terminology zh) "自动找到的训练任务 ({n}) — 默认结果目录 + 手动监控" / "Discovered sweeps ({n}) — default output root + manual attach".
    - Rewrite the module docstring contract: bilingual registry, DEFAULT English, set_language the live-switch seam, both languages single-homed here (zero CJK outside this module), D-02 kernel detail lines data-identical in both languages.
    - tests/tui/conftest.py: after the sys.path insert, add a module-level `from tui import strings; strings.set_language("zh")` with a comment: the committed zh surface stays fully covered by the existing zh assertions (conftest runs before test-module imports, so test-side `from tui.strings import X` copies freeze zh and match the zh-rendering apps); default-English coverage lands as dedicated Pilot tests in Task 2. tests/tui/test_snapshots.py: the same pin inside its inline script-mode bootstrap (the --regenerate path lacks conftest; the committed goldens are zh).
    - Extend the two inventory test files per the behavior block (both-language loops with zh restoration; the consistency tripwire; the terminology tripwire). Do NOT touch any production call site in this task — from-imports keep working off the real globals, so the whole suite stays green with only strings.py + the three test files + conftest changed.
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_strings_phase11.py tests/tui/test_services_download_queue.py tests/tui/test_snapshots.py -q && grep -c "输出根\|短语门\|存储根" tui/strings.py | grep -x "0" && make lint && make typecheck</automated>
  </verify>
  <done>strings.py is the bilingual registry (every constant via _t, names byte-stable, zh terminology applied, English authored per the rules); both-language tripwires + the consistency + terminology tripwires green; conftest + snapshot bootstrap pin zh; the FULL suite (`make test`) at exactly the box baseline (7 documented failures + 9 strict-xfail, zero new); lint/typecheck green; zero production call-site changes. Commit: feat(261015-ehc): bilingual strings registry + zh terminology + both-language tripwires</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: EHC-1b — L language toggle, persistence, live re-render, and the production module-attribute conversion</name>
  <files>tui/app.py, tui/__main__.py, tui/screens/env_check.py, tui/screens/selection.py, tui/screens/matrix.py, tui/screens/wizard.py, tui/screens/data_manager.py, tui/screens/run_config.py, tui/screens/monitor.py, tui/screens/about.py, tui/screens/nav.py, tui/strings.py, tests/tui/test_pilot_boot.py, docs/TUI-GUIDE.md</files>
  <behavior>
    - Test 1 (default English): with strings.set_language("en") set inside the test (conftest pinned zh at collection), a freshly constructed app's opening screen renders English copy (screen title, a state word, the storage title) — the committed default.
    - Test 2 (live toggle): boot under zh, press "L" -> the SAME mounted screen re-renders English copy (title + a row word), the app footer label for the toggle/quit switches language, a toast fires; press "L" again -> zh returns. No restart; no unhandled-key error.
    - Test 3 (persistence round-trip): with DNALLMMARK_TUI_STATE_DIR pointed at tmp_path, pressing L writes language.json carrying the new language; the boot-load helper (the __main__ path, called directly) reads it back and set_language matches; a corrupt/absent file resolves to DEFAULT_LANGUAGE, never raises.
    - Test 4 (test-app inertness): constructing DnallmMarkTui NEVER reads the language file (the boot_resume_queue precedent — the load lives only in tui/__main__.main).
  </behavior>
  <action>
    - Convert EVERY `from tui.strings import ...` in the production tree (tui/app.py + all ten tui/screens/*.py, including run_config.py's function-local from-imports inside `_problem_line`) to module-attribute access: import `from tui import strings as S` once per module and reference `S.CONST` at each use site. Constant names unchanged — the diff is purely mechanical (sed-able). After the sweep, `grep -rn "from tui.strings import" tui/` must return nothing. The one exception: tui/__main__.py may keep whatever import shape it needs for the boot load.
    - tui/strings.py: register two new constants through _t — APP_LANGUAGE_TOGGLE_LABEL (zh "语言" / en "Language") and APP_LANGUAGE_TOAST (zh "已切换到中文" / en "Switched to English"). They carry the APP_ prefix; grep the test tree for an APP_ inventory (none exists today — if one lands later it must register them; note this in the SUMMARY).
    - tui/app.py: add the app-level binding `Binding("L", "toggle_language", S.APP_LANGUAGE_TOGGLE_LABEL)` (verified free — no screen binds L/l; an Input's focused shift+L types into the input, which is correct k9s behavior). action_toggle_language: (a) new = the other language; (b) S.set_language(new); (c) persist via the settings.py system — settings.atomic_write(settings.state_dir() / "language.json", a tiny JSON {"language": new}); (d) remap binding descriptions — walk self.BINDINGS plus every screen instance in self.screen_stack's BINDINGS lists, and for each Binding whose description is a non-empty str, set it to S.translate_value(description, old, new) (PROBE on 8.2.8 whether Binding.description is assignable; if frozen, rebuild that list element in place with a new Binding carrying the translated description and the original key/action/show/key_display/priority); (e) re-render live — for each screen in the screen stack, call_after_refresh(screen.recompose) (PROBE: textual 8.2.8 recompose on mounted screens; if a screen class lacks it, fall back to remove_children + mount of its compose content — pick ONE mechanism and apply uniformly), then refresh the footers; (f) notify(S.APP_LANGUAGE_TOAST). Below the minimum grid (below_minimum_grid): still set + persist, skip the recompose/remap/toast chrome (the WR-06 posture).
    - tui/__main__.py main(): before app.run, tolerantly load the persisted language (json load of settings.state_dir()/"language.json"; missing/corrupt/wrong-value -> DEFAULT_LANGUAGE) and S.set_language(it) — the ONLY boot-load path (test apps stay inert). Do the read with a tiny module-local helper so Task-2's Test 3 can call it directly.
    - docs/TUI-GUIDE.md: document the L key (global toggle, persisted, default English) in the shared-keys section.
    - Pilot tests per the behavior block in tests/tui/test_pilot_boot.py (the toggle needs no fake services beyond the boot suite's existing ones; the persistence test pins the state-dir env itself).
  </action>
  <verify>
    <automated>grep -rn "from tui.strings import" tui/ | wc -l | grep -x "0" && uv run --group dev --group tui pytest tests/tui/test_pilot_boot.py tests/tui/test_pilot_run_config.py tests/tui/test_pilot_monitor.py tests/tui/test_pilot_selection.py -q && make lint && make typecheck</automated>
  </verify>
  <done>Every production strings reference is live module-attribute access; L toggles zh<->en live across all stacked screens with footer/help labels following, persists via DNALLMMARK_TUI_STATE_DIR-redirectable state, and boots only through __main__; default-English + toggle + persistence Pilot tests green; full `make test` at the box baseline. Commit: feat(261015-ehc): live L language toggle + persistence + module-attribute strings conversion</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: EHC-2 — launch-gate y-confirm (enter no longer passes any launch gate)</name>
  <files>tui/screens/selection.py, tui/screens/run_config.py, tui/screens/monitor.py, tui/strings.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_monitor.py, docs/TUI-GUIDE.md</files>
  <behavior>
    - Test 1 (regular gate): open the slot-4 gate on a valid non-E2' spec -> the confirm modal renders the y wording; pressing "enter" does NOT launch (launcher.launch_calls stays 0, modal still up); pressing "y" launches exactly once; "Esc" cancels cleanly.
    - Test 2 (E2' double insurance): on an E2'-class spec, typing the correct dirname -> enter ADVANCES to the y-ready state (indicator shows the y wording, input no longer focused) but does NOT launch; a further "enter" does nothing; "y" launches; a mismatched phrase leaves y inert.
    - Test 3 (re-run gate): the monitor's r-flow confirm refuses on enter and launches on y (fake launcher call-count asserted), Esc cancels.
    - Test 4 (scope boundary — regression pin): the NON-launch ConfirmModal consumers (preset overwrite on the selection screen, a queue cancel) still confirm on enter, byte-identical behavior.
  </behavior>
  <action>
    - tui/screens/selection.py: add `LaunchConfirmModal(ConfirmModal)` next to ConfirmModal — it adds `Binding("y", "confirm_launch", show=False)`, OVERRIDES `action_confirm` to a documented no-op (the inherited enter binding now lands on the no-op — plain-MRO method overriding, no binding-shadow semantics needed), and defines `action_confirm_launch` (dismiss + on_confirm). ConfirmModal itself and every existing consumer stay byte-identical (the 12-03 precedent).
    - tui/screens/run_config.py: `_GateConfirmModal` re-parents onto LaunchConfirmModal (it only adds the picker-return dismiss — unchanged job).
    - E2PhraseModal rework (the phrase stays double insurance ON TOP of y): `on_input_submitted` no longer confirms — on the matched verdict it ADVANCES: blur the input (PROBE 8.2.8: self.set_focus(None) or focusing the non-input Static — pick the proven blur) and keep the indicator on LNC_E2_MATCH_OK; mismatched enter stays the existing no-op pin. Add `Binding("y", "confirm_phrase_y", show=False)` — live ONLY on the matched verdict (while the input holds focus, y types into it — correct; the blur is what arms the key). The modal-level enter binding becomes the same advance/no-op (enter can NEVER launch from this modal). Esc unchanged.
    - tui/screens/monitor.py: request_rerun pushes LaunchConfirmModal directly (message MON_RERUN_CONFIRM) instead of bare ConfirmModal.
    - Registry value updates through _t (both languages): LNC_GATE_CONFIRM zh "启动以上训练任务？— [y] 启动 / Esc 取消" / en "Launch this sweep? — [y] launch / Esc cancel"; LNC_E2_MATCH_OK zh "✓ 目录名匹配 — [y] 确认启动" / en "✓ dirname matches — [y] to launch"; MON_RERUN_CONFIRM zh "重跑 {pairs} 个失败组合 × 种子 {seeds} = {n} 个训练项（--from-failures）？— [y] 重跑 / Esc 取消" / en "Re-run {pairs} failed pairs × seeds {seeds} = {n} cells (--from-failures)? — [y] re-run / Esc cancel" (keeps the 11-08 planned-cell estimate semantics; terminology 训练项 in zh).
    - Rewrite the touched Pilot assertions (the happy-path gate tests currently press enter twice; the E2' tests currently confirm on enter) to the y flow per the behavior block, and add the enter-refusal assertions. The service tier (launch_spec / launch_from_failures / the E2' phrase predicate) is UNTOUCHED — only the confirm key changed.
    - docs/TUI-GUIDE.md: the gate/confirm paragraphs name y/Esc (and the E2' two-step: phrase, enter, y).
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py tests/tui/test_pilot_monitor.py tests/tui/test_pilot_selection.py -q && make lint && make typecheck</automated>
  </verify>
  <done>enter provably cannot launch from any of the three gates (Pilot-pinned call counts); y starts, Esc cancels; the E2' phrase remains mandatory on top; other ConfirmModal consumers unchanged; tripwire inventories still green (names unchanged); full `make test` at the box baseline. Commit: feat(261015-ehc): y-confirm launch gates — enter no longer passes</done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: EHC-3 — single-GPU serialization guard on both launch paths</name>
  <files>tui/services/sweep_launcher.py, tui/screens/run_config.py, tui/screens/monitor.py, tui/strings.py, tests/tui/test_services_sweep_launcher.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_monitor.py, docs/TUI-GUIDE.md</files>
  <behavior>
    - Test 1 (effective_gpu_count): WORLD_SIZE=4 -> 4 (torch never imported); WORLD_SIZE unset + torch absent/unavailable -> 0, never raises; the lazy torch path is tolerant of every exception.
    - Test 2 (service refusal, call-count proof): SweepLauncher(gpu_count=1) with a live registry entry -> launch_spec AND launch_from_failures both return the single-GPU GateRefusal BEFORE any preview/official-keys/phrase stage, and the spawner is provably never called (call counts, the LNC-03 evidence style); gpu_count=2 -> launches normally; gpu_count=0 -> unrestricted; gpu_count=1 with NO live entry -> launches normally.
    - Test 3 (screen pre-checks): the slot-4 gate pipeline refuses with the problems modal naming the running root (fake launcher exposing the new seam); the monitor request_rerun refuses before pushing the confirm modal (fake launcher seam; y never reached).
    - Test 4 (fake tolerance): every pre-existing launcher fake WITHOUT the new method keeps the screens working (the tolerant getattr seam — the 11-03 precedent).
  </behavior>
  <action>
    - tui/services/sweep_launcher.py: module function `effective_gpu_count()` — WORLD_SIZE parsed as int when >= 1 wins; else a LAZY `import torch` inside a try/except (ImportError and every Exception -> 0) guarded by torch.cuda.is_available() then torch.cuda.device_count() (which honors CUDA_VISIBLE_DEVICES — a masked 4-GPU box reading 1 is correctly serialized); never raises, never imports torch at module top (the flops_counter lazy-seam precedent — CI lanes stay torch-free). SweepLauncher.__init__ gains `gpu_count=None` (None = probe live at each call; an int pins it for tests). Add `PROBLEM_SINGLE_GPU = "single_gpu_busy"`, `REFUSAL_STAGE_SINGLE_GPU = "single_gpu"`, and the public `single_gpu_launch_blocked()` returning the live-roots tuple when effective count == 1 AND live_sweeps() is non-empty, else None. Insert the guard as the FIRST stage of BOTH `launch_spec` and `launch_from_failures` (a busy single-GPU machine refuses before the operator is asked for any E2' phrase); the refusal carries the roots. `launch_argv` stays ungated (the pinned raw-seam contract) and `_spawn` untouched.
    - tui/screens/run_config.py: in the gate pipeline's registry-check stage (beside the CR-02 live_root check, after enumeration problems): `blocked = getattr(self._launcher, "single_gpu_launch_blocked", None)` and `blocked()` tolerant seam -> push ProblemsModal with the ("single_gpu_busy", ", ".join(roots)) tuple; extend `_problem_line` to map that code to LNC_SINGLE_GPU_BLOCKED.format(roots=detail).
    - tui/screens/monitor.py: request_rerun pre-checks the same seam BEFORE pushing the rerun confirm; the service-refusal render path (the non-phrase GateRefusal branch) maps the single_gpu_busy code to LNC_SINGLE_GPU_BLOCKED instead of the raw code: value join.
    - tui/strings.py: register LNC_SINGLE_GPU_BLOCKED through _t — zh "⚠ 单卡机器上已有训练任务在运行（{roots}）— 请等待完成、经退出门终止，或换一个结果目录" / en "⚠ a sweep is already running on this single-GPU machine ({roots}) — wait for it, kill it via the exit modal, or use a different output root" — AND add the name to EXPECTED_LNC_CONSTANTS in tests/tui/test_strings_phase11.py (the bidirectional completeness test fails any unregistered LNC_ constant).
    - Tier-1 + Pilot tests per the behavior block; the 12-x multi-GPU machinery is untouched (shard launches do not route through this launcher).
    - docs/TUI-GUIDE.md: one paragraph on the single-GPU serialization rule under the launch/monitor sections.
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_services_sweep_launcher.py tests/tui/test_pilot_run_config.py tests/tui/test_pilot_monitor.py tests/tui/test_strings_phase11.py -q && grep -c "^import torch\|^from torch" tui/services/sweep_launcher.py | grep -x "0" && make lint && make typecheck</automated>
  </verify>
  <done>On count==1 with a live sweep, both gated paths refuse before any confirm/phrase stage with bilingual copy naming the running root(s), spawner never called (call-count proof); count>=2 and count==0 unrestricted; torch stays lazily imported; fakes without the seam keep working; LNC inventory updated; full `make test` at the box baseline. Commit: feat(261015-ehc): single-GPU serialization guard on both launch paths</done>
</task>

<task type="auto" tdd="true">
  <name>Task 5: EHC-4 — download speed alongside the percent on slots 2 and 3 only</name>
  <files>tui/services/download_queue.py, tui/app.py, tui/screens/data_manager.py, tui/screens/selection.py, tests/tui/test_services_download_queue.py, tests/tui/test_pilot_data_manager.py, tests/tui/test_pilot_selection.py, docs/TUI-GUIDE.md</files>
  <behavior>
    - Test 1 (parse_speed): tqdm-style rates parse ("892kB/s", "1.23MB/s", "5.0 MiB/s", spaced and unspaced); the LAST rate in a multi-line chunk wins; chunks without a rate -> None; adversarial garbage ( ANSI-laden, CR-carried, huge digits ) -> None or the honest token, never an exception.
    - Test 2 (callback plumbing): a child whose stderr carries percent WITHOUT rate fires cb with speed=None; a stalled-percent stream with changing rates still fires (the dedupe is on the (percent, speed) pair); the model lane's -I child pump behaves identically to the dataset CLI lane.
    - Test 3 (slot 3 render): a downloading queue row with (percent, speed) renders the speed data word beside the percent in the progress cell; with speed=None the cell renders exactly today's percent/bar composition (byte-stable fallback).
    - Test 4 (slot 2 render): the model download column composes state word + percent + speed within the WIDENED column (nothing clipped — the c4j deviation lesson); speed=None keeps the exact c4j composition; the column header set is otherwise unchanged.
  </behavior>
  <action>
    - tui/services/download_queue.py: add `SPEED_RE` + `parse_speed(chunk) -> str | None` over the cleaned chunk (the clean_chunk discipline) capturing the last rate token shaped digits + optional decimal + optional space + optional binary i-prefix + B/s (covers tqdm's "892kB/s" / "1.23MB/s" and modelscope's spaced variants); return the token VERBATIM (parsed data, never translated, bilingual-neutral — no new strings constants). Extend BOTH stderr pumps (the dataset CLI lane's run_task on_stderr and the model lane's _run_model_download on_stderr) to parse both signals and fire `progress_cb(key, percent, speed)` when the integer percent OR the speed string changed (a big file's percent can stall while the rate streams — speed-only changes are real ticks); the callback signature grows the additive `speed=None` parameter so every pre-existing injected fake keeps conforming (the additive-fake pin from c4j).
    - tui/app.py: QueueProgressMessage gains the speed field (default None; the claim tick posts None); the driver's on_progress and its post-throttle compare (percent, speed) pairs instead of percent alone; the apply_queue_progress forward passes speed through the existing tolerant getattr seam (`apply_queue_progress(key, percent, speed)` — screens' methods gain the additive default).
    - tui/screens/data_manager.py (slot 3, dataset lane): the queue table's progress cell appends the speed as a dim data word beside the percent/bar composition; None renders exactly today's cell (honest percent-only fallback — never a fabricated speed).
    - tui/screens/selection.py (slot 2, model lane): `_model_download_cell` gains live_speed and composes state word + percent + speed for downloading rows; widen `_MODEL_DOWNLOAD_W` to fit the widest honest composition (measure with Rich — roughly 22 cells for word + " 100%" + " 123.4MB/s") following the UAT-width precedent (widen + h-scroll on narrow terminals; NEVER clip live data). The live-speed cache rides the existing `_live_percents` pattern.
    - PLACEMENT RULING (2026-10-15): download status AND speed render on slots 2 and 3 ONLY — tui/screens/run_config.py gains nothing (verified: it has no download rendering today — keep it that way), and no global download banner anywhere.
    - docs/TUI-GUIDE.md: the slot-2/slot-3 progress paragraphs name the speed word and the honest fallback.
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_services_download_queue.py tests/tui/test_pilot_data_manager.py tests/tui/test_pilot_selection.py -q && git diff --stat tui/screens/run_config.py | wc -l | grep -x "0" && make lint && make typecheck</automated>
  </verify>
  <done>Speed renders beside the percent on both acquisition screens whenever the child/CLI output carries a rate, with the honest percent-only fallback otherwise; slot 4 byte-untouched (the git-diff gate proves it); the additive callback seam keeps every pre-existing fake conforming; full `make test` at the box baseline. Commit: feat(261015-ehc): download speed on the slot-2/slot-3 progress surfaces</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| child process stderr -> TUI | download CLI / -I model child output crosses into parse_speed/parse_progress and renders on screen |
| state file -> boot | language.json under the XDG state root is machine-local but user-editable; read at boot |
| operator input -> launch | keystrokes at the confirm gates decide whether GPU work starts |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-ehc-01 | Tampering | parse_speed / parse_progress over child stderr | low | mitigate | regex-only extraction, no interpolation/shell; worst case a wrong token on one UI cell (the c4j T-c4j-02 posture); adversarial-garbage tests pin never-raises |
| T-ehc-02 | Tampering | language.json boot load | low | mitigate | tolerant json load; missing/corrupt/wrong-value resolves to DEFAULT_LANGUAGE, never raises, never blocks boot |
| T-ehc-03 | Elevation of privilege | the y-confirm rework weakening the E2' maintainer gate | high | mitigate | the phrase predicate and the service-side structural gate (launch_spec stage order, spawner-never-called) are untouched; Pilot tests pin enter-cannot-launch and phrase-then-y; the single-GPU guard adds a stage, removes none |
| T-ehc-04 | Denial of service | single-GPU guard reading a hung torch import | low | accept | lazy import inside try/except; worst case count 0 (unrestricted, the letter of the ruling); no timeout machinery warranted |
| T-ehc-SC | Tampering | package installs | high | mitigate | zero new packages in this plan (no pyproject/uv.lock change); the package-legitimacy gate has nothing to approve — any executor urge to add a dependency is out of scope and must be refused |
</threat_model>

<verification>
- `make lint` and `make typecheck` green after every task commit.
- `make test` after EVERY task at exactly the box baseline: 7 documented failures + 9 strict-xfail goldens, zero new failures (the pre-existing set is documented in `.planning/quick/261014-c2l-*/deferred-items.md` and `.planning/quick/261014-dcl-*/deferred-items.md`; never "fix" baseline failures here).
- `git status tests/tui/__snapshots__/` clean after every task — goldens byte-untouched, xfail-strict state unchanged; amend `_GOLDEN_REFRESH_REASON` in tests/tui/test_snapshots.py in place (the 261014-mlc precedent) naming this task's copy drift; enumerate the visual changes in the SUMMARY for the maintainer's D-03 `make snapshot-update` review.
- `grep -rn "from tui.strings import" tui/` empty after Task 2; `git grep -nP "[\x{4e00}-\x{9fff}]" -- tui/ ':!tui/strings.py'` still empty after every task (the CJK lock, both languages single-homed).
- `git diff --stat tui/screens/run_config.py` empty across Task 5 (the placement ruling's slot-4 purity proof).
- The @work never-exit AST pin (tests/tui/test_work_site_hardening.py) and the card-extraction allowlist (tests/tui/test_card_site_hardening.py) green unmodified.
</verification>

<success_criteria>
- All four maintainer rulings (EHC-1..4) demonstrably true per the must_haves truths — Pilot/tier-1 evidence, not prose.
- Five plain commits on `autorun` (no attribution trailers), each independently green at the baseline.
- Zero new dependencies; pipeline/ tree, DNALLM sibling, and slot-4 download purity untouched; textual probe results recorded.
</success_criteria>

<output>
Create `.planning/quick/261015-ehc-tui-1-i18n-strings-py-english-2-y-y-esc-/261015-ehc-SUMMARY.md` when done — including the D-03 visual-change enumeration for the golden refresh.
</output>
