"""
The CFG_/LNC_/MON_ string block (Phase 11, 11-05, D-12) — the inventory
tripwire the 11-06/11-07 screens build against.

The fixed pattern is the phase-10 sibling
(``tests/tui/test_services_download_queue.py``: EXPECTED_DL_CONSTANTS /
EXPECTED_QUEUE_CONSTANTS + the two directional tests): every constant
name the run-config and monitor screens render must exist, be a
non-empty str, at module level in ``tui/strings.py`` — and the lock is
BIDIRECTIONAL (IN-09), so a new toast that skips registration fails
here instead of silently drifting out of the inventory's coverage.

Contract note for 11-06/11-07 — the CJK lock rides along with the
screens, nothing to edit in THIS file: the screen-module grep test (no
Chinese literals outside ``tui/strings.py`` in ``tui/screens/`` +
``tui/app.py``) extends to the new screen modules
(``tui/screens/run_config.py``, ``tui/screens/monitor.py``) when they
land — each new Pilot suite adds its own screen module to its
``_GREP_LOCK_MODULES`` tuple (the test_pilot_env_check.py precedent),
and the whole-services glob lock already covers any new services
modules. Every CFG_/LNC_/MON_ constant the screens render comes from
this module by name.

The slot-4 enter-key pin (UI-checker fix 2: enter on the picker / with
no field focused opens the 启动确认 launch confirmation; Inputs consume
their own Enter — typing never launches) is a Pilot assertion in
``tests/tui/test_pilot_run_config.py`` (11-06), NOT a copy change —
recorded here so the next plan finds it next to its copy constants.
"""

from tui import strings as tui_strings

#: The complete expected CFG_ inventory (slot-4 chrome, picker/params/
#: dirs labels, value states, derived hints, preview problems + modal,
#: the two plan-owned gap-fillers CFG_FIELD_EBS and
#: CFG_COMPOSITION_PROBLEM).
EXPECTED_CFG_CONSTANTS = (
    "CFG_SCREEN_TITLE", "CFG_STATUS_LINE", "CFG_PICKER_MODELS",
    "CFG_PICKER_DATASETS", "CFG_PARAMS_TITLE", "CFG_DIRS_TITLE",
    "CFG_DIRS_TITLE_SHORT", "CFG_FIELD_SEEDS", "CFG_FIELD_PEFT",
    "CFG_FIELD_VARIANT", "CFG_FIELD_CURVE", "CFG_FIELD_SUBSET",
    "CFG_FIELD_EPOCHS", "CFG_FIELD_EBS", "CFG_FIELD_EBS_SHORT",
    "CFG_FIELD_OUTPUT_ROOT", "CFG_FIELD_DATASET_ROOT",
    "CFG_FIELD_MODEL_ROOT", "CFG_FIELD_CACHE", "CFG_FIELD_LOG_DIR",
    "CFG_VALUE_ABSENT", "CFG_CACHE_DEFAULT", "CFG_MODEL_ROOT_DEFAULT",
    "CFG_DATASET_ROOT_DEFAULT", "CFG_LOG_DIR_DEFAULT", "CFG_SUBSET_OFF",
    "CFG_SUBSET_OFF_WITH_PATH", "CFG_SUBSET_ON",
    "CFG_PEFT_ALIAS_PREVIEW", "CFG_VARIANT_ALIAS_PREVIEW",
    "CFG_VARIANT_HEAD_NOTE", "CFG_VARIANT_PROBE_HINT",
    "CFG_PROBE_INELIGIBLE_PROBLEM", "CFG_COMPOSITION_PROBLEM",
    "CFG_SEEDS_INVALID_PROBLEM", "CFG_CURVE_INVALID_PROBLEM",
    "CFG_EMPTY_SELECTION_PROBLEM", "CFG_OUTPUT_ROOT_PROBLEM",
    "CFG_PREVIEW_LINE",
    "CFG_PREVIEW_LINE_CURVE", "CFG_PREVIEW_PROBLEMS",
    "CFG_PREVIEW_PROBLEM_LINE", "CFG_PREVIEW_MODAL_TITLE",
    "CFG_PREVIEW_NOTE", "CFG_ARGV_LABEL",
    # 261014-f4w (F4W-03/F4W-05): the save-as-defaults action + the
    # directory picker — eight new names joining the bidirectional
    # inventory in the same change as their screens, plus the Rule-2
    # save-failure toast the WR-03 surface demands.
    "CFG_SAVE_DEFAULTS_LABEL", "CFG_SAVE_DEFAULTS_TOAST",
    "CFG_SAVE_DEFAULTS_FAILED_TOAST", "CFG_SAVE_DEFAULTS_HINT",
    "CFG_DIR_PICKER_LABEL",
    "CFG_DIR_PICKER_TITLE", "CFG_DIR_PICKER_SELECT_LABEL",
    # 261016-poa (UX-4): the slot-4 launch-confirmation entry hint.
    "CFG_GATE_HINT",
)

#: The complete expected LNC_ inventory (launch-confirmation modal +
#: E2' typed-phrase escalation, launch toasts, the exit-modal
#: kill/detach/cancel row).
EXPECTED_LNC_CONSTANTS = (
    "LNC_GATE_TITLE", "LNC_GATE_SUMMARY", "LNC_GATE_CONFIRM",
    # 261017-dnr (DNR-1): the launch-confirm y Footer keycap beside the
    # confirm copy (a NEW registry pair — 启动/Launch had no twin; the n
    # side reuses LNC_EXIT_CONFIRM_NO below, the WIZ_BACK precedent).
    "LNC_GATE_CONFIRM_YES",
    "LNC_GATE_PAIR_LINE", "LNC_GATE_PAIRS_MORE",
    "LNC_E2_WARNING", "LNC_E2_AUTH_NOTE", "LNC_E2_TYPE_PROMPT",
    "LNC_E2_MATCH_OK", "LNC_E2_MISMATCH", "LNC_ENV_BLOCKED_HINT",
    "LNC_SINGLE_GPU_BLOCKED",
    "LNC_LAUNCH_TOAST", "LNC_LAUNCH_FAILED_TOAST", "LNC_EXIT_TITLE",
    "LNC_EXIT_MESSAGE", "LNC_EXIT_MESSAGE_MULTI",
    # 261016-v0z: the no-sweep quit-confirm row (the [Y]/[N] pair
    # mirrors LNC_GATE_CONFIRM — y the only confirm key, enter inert).
    # 261017-cdr (CDR-3): the YES/NO Footer-keycap pair beside it —
    # visible y/n answer keys on the modal (identical registry pairs
    # already exist, injectivity-safe).
    "LNC_EXIT_CONFIRM",
    "LNC_EXIT_CONFIRM_YES", "LNC_EXIT_CONFIRM_NO",
    # 261017-dnr (DNR-4): the ExitModal enter/k Footer keycaps — wording
    # lifted verbatim from the LNC_EXIT_MESSAGE copy (visibility only;
    # no identical pairs existed, injectivity-safe).
    "LNC_EXIT_DETACH_KEYCAP", "LNC_EXIT_KILL_KEYCAP",
)

#: The complete expected MON_ inventory — 261018-kvj restructured to
#: the two-tab surface: tab titles/badges/scanning/empty states, the
#: running-card lines, the History columns incl. the dual-presence
#: badge, the graduation toasts, the run-drill modal, the five cell
#: states + resume notes, failures + gated re-run, log tail, attach
#: flow, rescan, cell detail. The retired master-detail family
#: (MON_DISCOVERED_*, MON_CELLS_TITLE/EMPTY, MON_CONTEXT_HEADER, the
#: sweep-state trio, the scale/ETA columns, the stats-line/ETA
#: variants) is DELETED with the surface it worded.
EXPECTED_MON_CONSTANTS = (
    "MON_SCREEN_TITLE", "MON_SCAN_NOTE",
    # 261018-kvj: the two-tab vocabulary + the #41 optimistic-paint
    # note + both empty states + the tab-switch keycap.
    "MON_TAB_RUNNING", "MON_TAB_HISTORY", "MON_TAB_COUNT",
    "MON_SCANNING", "MON_RUNNING_EMPTY", "MON_HISTORY_EMPTY",
    "MON_TAB_SWITCH_KEYCAP",
    # the running card + the History row's dual-presence badge + the
    # graduation toasts (Task 2). 261019-f0x: the four card-line
    # constants (MON_CARD_SCALE / MON_SCALE_UNKNOWN / MON_CARD_CURRENT /
    # MON_CARD_CURRENT_NONE) retired with their surface (the strip +
    # matrix redesign — the kvj retirement precedent).
    "MON_HISTORY_RERUN_BADGE",
    "MON_GRADUATED_DONE_TOAST", "MON_GRADUATED_INTERRUPTED_TOAST",
    # 261019-f0x (the B-skeleton + D-right-pane redesign): the summary
    # strip's elapsed/ETA/rate segments + the [w] wide-toggle keycap —
    # one block, one tripwire edit (+5/-4 with the retirements above).
    # 261019-n0w: +MON_DETAIL_STEPS (the pane's step/max line, zh == en
    # — the data-forward precedent).
    # 261019-pe0: +MON_TREE_TOGGLE_KEYCAP (the [*] tree-state
    # expand/collapse-all keycap beside MON_WIDE_KEYCAP — the +1
    # precedent, same commit as the constant).
    "MON_STRIP_ELAPSED", "MON_STRIP_ETA", "MON_STRIP_ETA_RANGE",
    "MON_STRIP_RATE", "MON_WIDE_KEYCAP", "MON_DETAIL_STEPS",
    "MON_TREE_TOGGLE_KEYCAP",
    # the History/drill tables' columns (root/progress survive; the
    # activity column replaces the retired ETA column).
    "MON_RUN_CELLS_TITLE", "MON_COL_ROOT", "MON_COL_PROGRESS",
    "MON_COL_ACTIVITY", "MON_COL_MODEL", "MON_COL_TASK",
    "MON_COL_SEED", "MON_COL_STATE",
    "MON_STATE_QUEUED", "MON_STATE_RUNNING",
    "MON_STATE_DONE", "MON_STATE_FAILED", "MON_STATE_SKIPPED",
    "MON_RESUME_NOTE", "MON_RESUME_NOTE_SHORT",
    "MON_TOTAL_UNKNOWN", "MON_ETA_UNKNOWN", "MON_FAILURES_TITLE",
    "MON_FAILURES_EMPTY",
    "MON_FAILURE_ROW", "MON_RERUN_LABEL", "MON_RERUN_CONFIRM",
    "MON_RERUN_TOAST", "MON_RERUN_NO_SEEDS", "MON_LOG_TITLE",
    "MON_LOG_TEE_LINE", "MON_LOG_UNAVAILABLE", "MON_ATTACH_LABEL",
    "MON_ATTACH_TITLE", "MON_ATTACH_PLACEHOLDER", "MON_ATTACH_INVALID_TOAST",
    "MON_ATTACHED_TOAST", "MON_RESCAN_LABEL", "MON_RESCAN_TOAST",
    "MON_CELL_DETAIL_TITLE", "MON_FRACTION_LINE",
    # C4J-3 (261015-c4j): the entries-list columns/cells — the 状态
    # column header, the steps+percent progress format, the honest
    # indeterminate, and the done/total seed-counts segment.
    "MON_PROGRESS_STEPS",
    "MON_PROGRESS_INDETERMINATE", "MON_ENTRY_SEED_COUNTS",
    # CR-01 (quick-261016-hhx): the [f]/[t] keycap constants —
    # byte-equal registry twins of the old split() title projections so
    # remap_binding_descriptions can finally translate them.
    "MON_FAILURES_KEYCAP", "MON_LOG_KEYCAP",
    # 261016-vxr (VXR-2): the slot-5 [k] kill-confirm family — the
    # keycap, the modal title/confirm, the three outcome toasts, and
    # the channel-unavailable refusal.
    "MON_KILL_KEYCAP", "MON_KILL_TITLE", "MON_KILL_CONFIRM",
    "MON_KILL_TOAST", "MON_KILL_TOAST_DEAD", "MON_KILL_UNAVAILABLE",
    "MON_KILL_FAILED",
    # 261017-uwr (UWR-1): the third cell state (the History tab reuses
    # the ✓/⏸ cell vocabulary for its rows — 261018-kvj).
    "MON_STATE_INTERRUPTED",
    # 261018-toe (the slot-5 History row actions): the [d] delete
    # family — keycap, modal title/confirm, the success/failed toasts,
    # the live-root refusal — plus the [e] keycap (the remaining
    # MON_RESUME_* family lands with the flow itself).
    "MON_DELETE_KEYCAP", "MON_DELETE_TITLE", "MON_DELETE_CONFIRM",
    "MON_DELETE_TOAST", "MON_DELETE_FAILED", "MON_DELETE_REFUSED_LIVE",
    "MON_RESUME_KEYCAP",
    # 261018-toe Task 3: the [e] resume family — the honest confirm
    # (pairs × seeds with the completed-skip note), the launched toast,
    # the nothing-to-resume refusal, and the live-root refusal.
    "MON_RESUME_CONFIRM", "MON_RESUME_TOAST", "MON_RESUME_NOTHING",
    "MON_RESUME_REFUSED_LIVE",
    # Phase 16 (16-01, TUI-01): the G GPU-lanes panel — the title, the
    # data-forward lane row (identical in both languages, the bar
    # composed in code), the ONE absent shape every probe failure mode
    # shares (D16-02), and the explicit zero-GPU empty state (D16-04).
    "MON_GPU_TITLE", "MON_GPU_ROW", "MON_GPU_ABSENT", "MON_GPU_NONE",
)

#: The per-seed cell states in spec order, and their contract glyphs.
MON_CELL_STATE_CONSTANTS = (
    "MON_STATE_QUEUED", "MON_STATE_RUNNING", "MON_STATE_DONE",
    "MON_STATE_FAILED", "MON_STATE_SKIPPED", "MON_STATE_INTERRUPTED",
)

#: Every state-carrying constant (the six cell states + both
#: resume-note variants — 261018-kvj: the sweep-state trio retired with
#: the discovered table; the History rows render the cell vocabulary's
#: ✓/⏸ words) — each must OPEN with its glyph.
MON_STATEFUL_CONSTANTS = (
    *MON_CELL_STATE_CONSTANTS,
    "MON_RESUME_NOTE", "MON_RESUME_NOTE_SHORT",
)

#: The glyph vocabulary these states draw from (261018-kvj: ● ○ leave
#: with the sweep-state trio; ⏵ (261017-uwr) and ⏸ remain the
#: running/interrupted carriers the two tabs render).
MON_STATE_GLYPHS = {"◌", "⏵", "✓", "✗", "⊘", "⏸"}


def test_cfg_lnc_mon_string_inventory_defined():
    """The drift tripwire: every CFG_/LNC_/MON_ name the 11-06/11-07
    plans consume exists, non-empty, at module level in tui/strings.py
    (the D-12 single home) — a rename or gap fails HERE, before any
    screen lands.

    261015-ehc (EHC-1): the check runs over BOTH languages — the
    registry rebinds its constants per language, so each side must
    carry the full inventory (zh restored for the committed zh-rendering
    test surface)."""
    try:
        for lang in ("zh", "en"):
            tui_strings.set_language(lang)
            for prefix, names in (("CFG_", EXPECTED_CFG_CONSTANTS),
                                  ("LNC_", EXPECTED_LNC_CONSTANTS),
                                  ("MON_", EXPECTED_MON_CONSTANTS)):
                for name in names:
                    assert hasattr(tui_strings, name), (lang, name)
                    value = getattr(tui_strings, name)
                    assert isinstance(value, str) and value, (lang, name)
                    assert name.startswith(prefix), name
    finally:
        tui_strings.set_language("zh")


def test_cfg_lnc_mon_inventory_complete_no_unlisted_constants():
    """IN-09: the single-home lock is BIDIRECTIONAL over the three new
    prefixes — every CFG_/LNC_/MON_ constant tui/strings.py defines is
    listed in the expected tuples, so a new toast that skips
    registration fails here instead of silently drifting out of the
    inventory's coverage."""
    listed = (set(EXPECTED_CFG_CONSTANTS) | set(EXPECTED_LNC_CONSTANTS)
              | set(EXPECTED_MON_CONSTANTS))
    defined = {name for name in dir(tui_strings)
               if name.startswith(("CFG_", "LNC_", "MON_"))}
    assert defined == listed, (
        "the string inventory and the tripwire must match exactly — "
        f"unregistered: {sorted(defined - listed)}; "
        f"stale registrations: {sorted(listed - defined)}"
    )


def test_mon_cell_state_strings_glyph_first_and_distinct():
    """The NO_COLOR redundancy contract: each of the six per-seed cell
    states leads with its distinct glyph (◌ ⏵ ✓ ✗ ⊘ ⏸, spec order —
    261017-uwr: ⏵ replaces the ⠋ spinner glyph and ⏸ joins)."""
    state_glyphs = [
        getattr(tui_strings, name)[0] for name in MON_CELL_STATE_CONSTANTS
    ]
    assert state_glyphs == ["◌", "⏵", "✓", "✗", "⊘", "⏸"]
    assert len(set(state_glyphs)) == 6


def test_mon_sweep_state_strings_glyph_first_and_distinct():
    """261018-kvj REDIRECTED: the sweep-state trio (● ○ ◌) retired with
    the discovered table — the pin now holds the two-tab surface's
    glyph discipline over the states the two tabs actually render:
    the ✓/⏸ cell-vocabulary words the History rows reuse and the ⏵
    running word the cards' progress cells carry, pairwise distinct
    under NO_COLOR (the same glyphs, one vocabulary everywhere)."""
    assert tui_strings.MON_STATE_DONE[0] == "✓"
    assert tui_strings.MON_STATE_INTERRUPTED[0] == "⏸"
    assert tui_strings.MON_STATE_RUNNING[0] == "⏵"
    assert len({tui_strings.MON_STATE_DONE[0],
                tui_strings.MON_STATE_INTERRUPTED[0],
                tui_strings.MON_STATE_RUNNING[0]}) == 3


def test_mon_state_copy_first_char_is_the_glyph():
    """Every MON_ state constant — the five cell states, the three sweep
    states, and both resume-note variants — opens with its glyph, the
    NO_COLOR carrier (the glyph+color redundancy rule: color never
    carries the meaning alone). 261015-ehc: the glyph leads in BOTH
    languages."""
    try:
        for lang in ("zh", "en"):
            tui_strings.set_language(lang)
            for name in MON_STATEFUL_CONSTANTS:
                value = getattr(tui_strings, name)
                assert value[0] in MON_STATE_GLYPHS, (
                    f"{lang}:{name} must lead with its glyph "
                    "(NO_COLOR carrier)"
                )
    finally:
        tui_strings.set_language("zh")


def test_mon_context_header_placeholders_and_terminology():
    """261018-kvj REDIRECTED: MON_CONTEXT_HEADER retired with the
    master-detail context line — the pin now holds the redesign's
    placeholder discipline on the constants that replaced its role:
    the graduation toasts carry the IDENTICAL {root} placeholder set in
    both languages, and the zh side keeps the approved terminology
    (运行 for run) with the retired 输出根 term never returning."""
    import string

    def placeholders(value):
        return {field for _literal, field, _spec, _conv
                in string.Formatter().parse(value) if field}

    for name in ("MON_GRADUATED_DONE_TOAST",
                 "MON_GRADUATED_INTERRUPTED_TOAST"):
        zh, en = tui_strings._REGISTRY[name]
        assert placeholders(zh) == placeholders(en) == {"root"}, name
        assert "输出根" not in zh, name  # the retired term never returns
        assert "运行" in zh, name


def test_mon_running_and_interrupted_glyphs_match_header_triple():
    """The state constants and the header carry the SAME glyph for the
    same state: MON_STATE_RUNNING opens ⏵, MON_STATE_INTERRUPTED opens
    ⏸ (the header's three segments render those exact constants'
    glyphs — one glyph per state everywhere)."""
    try:
        for lang in ("zh", "en"):
            tui_strings.set_language(lang)
            assert tui_strings.MON_STATE_RUNNING[0] == "⏵"
            assert tui_strings.MON_STATE_INTERRUPTED[0] == "⏸"
            assert tui_strings.MON_PROGRESS_INDETERMINATE[0] == "⏵"
    finally:
        tui_strings.set_language("zh")


# =====================================================================
# The bilingual registry tripwires (261015-ehc, EHC-1 — Task 1)
# =====================================================================


def test_registry_consistency_same_zh_implies_same_en():
    """translate_value's well-definedness precondition: for every
    distinct zh value carried by more than one constant, all such
    constants share ONE en value — a zh phrase always translates to the
    same English words, wherever it renders (the Task-2 binding-label
    remap depends on it). Structured (dict/tuple) entries are excluded
    from the value-equality join — they compare as whole objects, and
    the shape test below covers them."""
    from collections import defaultdict

    zh_owners: defaultdict[str, set[str]] = defaultdict(set)
    for zh, en in tui_strings._REGISTRY.values():
        if isinstance(zh, str) and isinstance(en, str):
            zh_owners[zh].add(en)
    ambiguous = {zh: ens for zh, ens in zh_owners.items() if len(ens) > 1}
    assert not ambiguous, (
        "same-zh constants must share one en value (translate_value "
        f"would be ambiguous for: {sorted(ambiguous)})"
    )


def test_registry_consistency_same_en_implies_same_zh():
    """WR-01 (quick-261016-hhx, the 08 review): the MIRROR tripwire —
    for every distinct en value carried by more than one constant, all
    such constants share ONE zh value. translate_value matches by byte
    equality in BOTH directions (remap_binding_descriptions rebuilds
    class BINDINGS en->zh on every toggle), so an en phrase must also
    translate to the same zh words everywhere — the zh->en tripwire
    alone covered only one direction while WIZ_BACK_LABEL/APP_MODAL_
    BACK_LABEL ("Back") and QUEUE_STATE_PENDING/ENV_STATE_PENDING
    ("◌ pending") already collided. Structured entries excluded (the
    shape test covers them)."""
    from collections import defaultdict

    en_owners: defaultdict[str, set[str]] = defaultdict(set)
    for zh, en in tui_strings._REGISTRY.values():
        if isinstance(zh, str) and isinstance(en, str):
            en_owners[en].add(zh)
    ambiguous = {en: zhs for en, zhs in en_owners.items() if len(zhs) > 1}
    assert not ambiguous, (
        "same-en constants must share one zh value (the en->zh remap "
        "would be ambiguous for: "
        f"{sorted(ambiguous)})"
    )


def test_registry_entries_carry_both_languages_and_matching_shapes():
    """Every _REGISTRY entry has both values non-empty; the structured
    (dict/tuple) entries carry identical key sets / arities across
    languages with non-empty str leaves (keys and shape are data —
    only the leaf copy translates)."""
    for name, (zh, en) in tui_strings._REGISTRY.items():
        if isinstance(zh, str) and isinstance(en, str):
            assert isinstance(zh, str) and zh, name
            assert isinstance(en, str) and en, name
        elif isinstance(zh, dict) and isinstance(en, dict):
            assert zh and en, name
            assert set(zh) == set(en), (
                f"{name}: dict keys must be identical across languages")
            for key in zh:
                assert isinstance(zh[key], str) and zh[key], (name, key)
                assert isinstance(en[key], str) and en[key], (name, key)
        elif isinstance(zh, tuple) and isinstance(en, tuple):
            assert zh and en, name
            assert len(zh) == len(en), (
                f"{name}: tuple arity must be identical across languages")
            for zh_item, en_item in zip(zh, en):
                assert isinstance(zh_item, str) and zh_item, name
                assert isinstance(en_item, str) and en_item, name


def test_zh_terminology_table_applied():
    """The approved 2026-10-15 zh terminology table: the retired zh
    terms never appear in any zh value, and the bare words sweep / cell
    are fully retired from zh copy (word-boundary match — English-
    verbatim DATA such as the sweep_failures.json filename and the
    sweep_priorities tier name keeps its underscore-joined spelling in
    both languages)."""
    import re

    retired = ("输出根", "短语门", "存储根")
    word_re = re.compile(r"\b(sweep|cell)\b")
    for name, (zh, _en) in tui_strings._REGISTRY.items():
        text = zh if isinstance(zh, str) else "".join(
            str(item) for item in (
                zh.values() if isinstance(zh, dict) else zh))
        for term in retired:
            assert term not in text, (name, term)
        assert not word_re.search(text), (
            f"{name}: the bare word sweep/cell is retired in zh copy")


def test_default_language_is_english_and_set_language_persists():
    """EHC-1: the committed default is English — DEFAULT_LANGUAGE is
    'en', set_language('en') lands language() on 'en', and the module
    state persists until the next call (zh restored afterward for the
    committed zh-rendering test surface)."""
    assert tui_strings.DEFAULT_LANGUAGE == "en"
    assert "en" in tui_strings.LANGUAGES and "zh" in tui_strings.LANGUAGES
    try:
        tui_strings.set_language("en")
        assert tui_strings.language() == "en"
        assert tui_strings.APP_TITLE == "DNALLM-Mark Console"
        tui_strings.set_language("zh")
        assert tui_strings.language() == "zh"
        assert tui_strings.APP_TITLE == "DNALLM-Mark 控制台"
    finally:
        tui_strings.set_language("zh")
