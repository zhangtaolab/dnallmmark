"""
strings.py — the single home for operator-facing copy (Phase 8, 08-02,
I18N-01; the bilingual registry rework is quick-261015-ehc, EHC-1).

Contract:

- BILINGUAL REGISTRY, DEFAULT ENGLISH (EHC-1, the maintainer's 2026-10-15
  ruling 1): every constant is registered through ``_t(name, zh, en)`` and
  the module starts in English. ``set_language(lang)`` is the ONE live
  switch seam — it validates against ``LANGUAGES`` and rebinds every
  registered constant through ``globals()`` so module-ATTRIBUTE access
  (``from tui import strings as S`` then ``S.CONST``) resolves the new
  language immediately. Plain from-import copies of a constant stay
  frozen at import (the committed test surface relies on the conftest zh
  pin; production call sites use module-attribute access). Both
  languages are single-homed HERE — zero CJK outside this module.
- Chinese copy with technical terms in English verbatim — registry
  keys, kernel ids, filter axes, metric names, file paths, CLI commands,
  schema field names are never translated, in EITHER language.
- The approved zh terminology table (2026-10-15, applied verbatim —
  governs the zh side ONLY; English copy keeps the established English
  terms sweep / cell / output root): the zh words for sweep, output
  root, attach, launch, the typed-phrase gate, cell, the storage
  root, and discovered sweeps are 训练任务 / 结果目录 / 监控 / 启动 /
  二次确认 / 训练项 / 存储位置 / 自动找到的训练任务 (retired zh
  phrasings never reappear in this file — the grep gate).
  Attach SEMANTICS are untouched — only the zh word is 监控 (11-08).
- Plain module-level UPPER_SNAKE constants grouped by screen prefix
  (``APP_`` / ``ENV_`` / ``SEL_`` / ...); format fields are
  ``{name}`` placeholders consumed via ``str.format()`` at render sites.
  The zh/en pair of one constant carries the IDENTICAL placeholder set;
  glyph-first constants lead with their glyph in BOTH languages (the
  NO_COLOR redundancy rule).
- NO other module defines operator-facing copy — screens reference these
  constants, never inline copy.
- Kernel detail lines are DATA, not copy: drill-downs render env_smoke's
  own English PASS/FAIL lines verbatim (the byte-stable CLI contract,
  D-02) — data-identical in both languages; the chrome alone translates.
- Language-neutral values (glyphs, data words, English-verbatim labels)
  register the same value twice through ``_t``.

The committed zh values are the UI-SPEC Copywriting Contract wording
(with the 2026-10-15 terminology table applied); the en values are
authored per the EHC-1 rules: leading glyph byte-exact, identical
placeholders, English-verbatim data never translated, ASCII punctuation,
concise operator register (footer/binding labels at most 2 words).
"""

from typing import Any

# ===== The bilingual registry machinery (EHC-1, quick-261015-ehc) =====

#: The supported languages, DEFAULT FIRST (EHC-1: English is the
#: committed default; zh is the toggle target).
LANGUAGES = ("en", "zh")

#: The boot language (EHC-1); ``tui/__main__`` may override it from the
#: persisted settings before the app runs.
DEFAULT_LANGUAGE = "en"

#: name -> (zh_value, en_value), populated by ``_t`` at import time.
_REGISTRY: "dict[str, tuple[Any, Any]]" = {}

#: The active language until ``set_language`` changes it.
_ACTIVE_LANGUAGE = DEFAULT_LANGUAGE


def _t[RegistryT](name: str, zh: RegistryT, en: RegistryT) -> RegistryT:
    """Register one constant's (zh, en) pair; return the ACTIVE value.

    Every copy constant is an explicit typed module assignment of the
    exact shape ``CONST = _t("CONST", "<zh>", "<en>")`` — the TypeVar
    keeps ty seeing the literal's type (str constants stay ``str``; the
    six structured constants keep their dict/tuple shapes with identical
    keys/arities across languages). Language-neutral values pass the
    same value twice.

    Args:
        name: the constant's module name (byte-stable — screens and the
            inventory tripwires reference it).
        zh: the Chinese value (terminology-table compliant).
        en: the English value.

    Returns:
        The ACTIVE-language value (the module-level binding).
    """
    _REGISTRY[name] = (zh, en)
    return en if _ACTIVE_LANGUAGE == "en" else zh


def set_language(lang: str) -> None:
    """Switch every registered constant to ``lang`` (the live seam).

    Rebinds each registry constant through ``globals()`` so
    module-ATTRIBUTE access (``S.CONST``) resolves the new language
    immediately; import copies taken earlier stay frozen at their import
    moment (the conftest zh pin relies on this for the test surface).

    Args:
        lang: one of ``LANGUAGES``.

    Raises:
        ValueError: for any language outside ``LANGUAGES``.
    """
    global _ACTIVE_LANGUAGE
    if lang not in LANGUAGES:
        raise ValueError(
            f"unsupported language {lang!r} (choose from {LANGUAGES})")
    _ACTIVE_LANGUAGE = lang
    for name, (zh, en) in _REGISTRY.items():
        globals()[name] = zh if lang == "zh" else en


def language() -> str:
    """The active language (``DEFAULT_LANGUAGE`` until switched)."""
    return _ACTIVE_LANGUAGE


def translate_value(text: Any, from_lang: str, to_lang: str) -> Any:
    """Translate one registry VALUE between languages (byte equality).

    Returns the ``to_lang`` value of the first registry entry whose
    ``from_lang`` value equals ``text`` byte-for-byte; an unmatched
    ``text`` (data, markup, non-copy) returns unchanged. Well-defined
    because the registry-consistency tripwire holds: every distinct zh
    value carried by more than one constant implies ONE en value.

    Args:
        text: the value to translate (usually a binding description).
        from_lang: the language ``text`` is in.
        to_lang: the target language.

    Returns:
        The translated value, or ``text`` unchanged when unmatched.
    """
    for zh, en in _REGISTRY.values():
        source = zh if from_lang == "zh" else en
        if source == text:
            return en if to_lang == "en" else zh
    return text


# ===== App (Header / app chrome) =====
APP_TITLE = _t("APP_TITLE", "DNALLM-Mark 控制台", "DNALLM-Mark Console")
# Footer label for the app-level q binding (08-UI-SPEC Screen 1 footer:
# "[q] 退出"). App-level copy, not screen copy, because the binding lives
# on the composition root (08-03). 261016-v0z: q never exits directly
# anymore — no live sweep opens the Y/N quit confirm (LNC_EXIT_CONFIRM),
# a live sweep the kill/detach ExitModal — but the label VALUE stays
# byte-identical by deviation: it renders in the bottom bar of every
# golden-pinned screen, and the task's golden discipline forbids
# regeneration (D-03, maintainer-only); the confirm step is surfaced by
# the modal copy + the ctrl+q/ctrl+c help rows instead.
APP_QUIT_LABEL = _t("APP_QUIT_LABEL", "退出", "Quit")
# 261016-v0z / 261017-cdr / 261017-mad: the help-modal rows for the
# app-level exit keys whose bindings stay hidden from the bars (declared
# manually in DnallmMarkTui._binding_rows, resolved live so the L toggle
# re-derives them). ctrl+q is the declared mirror of the inherited App
# framework default — the same guarded quit action as q. 261017-mad (the
# maintainer's 2026-10-17 16:02 exit-key final ruling): F10 is the
# ANY-FOCUS primary exit — the F-key family is the only one clean against
# the terminal copy passthrough (an unscoped ctrl+shift+c is an
# indistinguishable 0x03), zellij, and typing; the declared priority
# binding routes through the v0z confirm chain. APP_Q_LABEL was
# withdrawn with the 261016-vxr intercept: a capital Q is a plain typing
# letter again.
APP_F10_LABEL = _t(
    "APP_F10_LABEL", "退出（任意焦点）", "Quit (any focus)")
APP_CTRLQ_LABEL = _t(
    "APP_CTRLQ_LABEL", "退出（同 q）", "Quit (same as q)")
# 261017-mad (the withdrawal): ctrl+c is NOT an exit key in this console
# — the 261017-cdr intercept is withdrawn and the key keeps textual
# 8.2.8's terminal-native semantics (a selection-holding Input copies
# through the Input's own binding; every other press hits the inherited
# notify-only help_quit default; modals chain-cut it). The help row is
# KEPT — reworded, not removed — as the one-line anti-misreading note
# (the maintainer ruling's stated preference to keep one explanation
# line: an operator pressing ctrl+c out of terminal-copy habit sees the
# row say copy/interrupt, never quit). Constant name and the literal
# ctrl+c key string stay (the three help-row pins import the constant
# and auto-derive).
APP_CTRLC_LABEL = _t(
    "APP_CTRLC_LABEL", "终端复制/中断（非退出）",
    "Terminal copy/interrupt (not quit)")
# Footer label + title for the app-level ? help binding/modal (08-UI-SPEC
# Keyboard map: "? | app | help modal (all bindings)").
APP_HELP_LABEL = _t("APP_HELP_LABEL", "帮助", "Help")
APP_HELP_TITLE = _t("APP_HELP_TITLE", "按键帮助", "Keybindings")
# One help-modal row per binding, in the UI-SPEC footer keycap format
# ("[r] 重检" style — key in brackets, then the binding's label).
APP_HELP_ROW = _t("APP_HELP_ROW", "[{key}] {label}", "[{key}] {label}")
# Min-size message (08-UI-SPEC Terminal Contract): below 80x24 the app
# renders ONLY this line, with the current dimensions, re-checked on
# resize. Halfwidth x per the spec wording.
APP_MIN_SIZE_MESSAGE = _t(
    "APP_MIN_SIZE_MESSAGE",
    "终端过小（需 ≥ 80x24，当前 {w}x{h}）— 请放大窗口",
    "Terminal too small (need >= 80x24, current {w}x{h}) — please "
    "enlarge the window")
# Modal-back label (esc) — shared app chrome: the env drill-down, the help
# modal, and every confirm surface use the same esc wording (08-UI-SPEC
# Keyboard map: "esc | modals | pop modal — never quits"). Lives next to
# the APP_ chrome block it belongs to (the env block follows).
APP_MODAL_BACK_LABEL = _t("APP_MODAL_BACK_LABEL", "返回", "Back")
# The L language toggle (261015-ehc, EHC-1): the app-level binding's
# footer label and the post-toggle confirmation toast. The toast's value
# is read AFTER set_language, so it always names the language the console
# just switched TO. NOTE: no APP_ inventory tripwire exists today; if one
# lands, both names must register (recorded in the 261015-ehc SUMMARY).
APP_LANGUAGE_TOGGLE_LABEL = _t(
    "APP_LANGUAGE_TOGGLE_LABEL", "语言", "Language")
APP_LANGUAGE_TOAST = _t(
    "APP_LANGUAGE_TOAST", "已切换到中文", "Switched to English")

# ===== 环境检查 (ENV-01..04) =====
# Kernel-id → operator label for the eight env-check rows and drill-down
# titles, in main() kernel order (08-RESEARCH verified; 261014-dcl added
# model_dirs before dataset_dirs). Keys are the stable CheckResult.name
# vocabulary from pipeline/env_smoke (08-01) — data, never translated;
# the values are the copy.
ENV_KERNEL_LABELS = _t(
    "ENV_KERNEL_LABELS",
    {
        "version_pins": "版本 pin",
        "dnallm": "dnallm 导入",
        "peft": "peft",
        "cuda": "CUDA",
        "matmul": "matmul 冒烟",
        "numpy": "numpy≥2",
        "model_dirs": "模型目录",
        "dataset_dirs": "数据集目录",
    },
    {
        "version_pins": "version pins",
        "dnallm": "dnallm import",
        "peft": "peft",
        "cuda": "CUDA",
        "matmul": "matmul smoke",
        "numpy": "numpy≥2",
        "model_dirs": "model dirs",
        "dataset_dirs": "dataset dirs",
    },
)

# Env panel row states (08-UI-SPEC Copywriting Contract "Env row states"):
# ✓ / ✗ / ◌ 待检 / ⠋ 检查中… — the glyph is the meaning-carrier (the
# glyph+color redundancy rule: every state stays legible under NO_COLOR);
# the pending/checking states carry their dim label in the same cell.
ENV_STATE_PASS = _t("ENV_STATE_PASS", "✓", "✓")
ENV_STATE_FAIL = _t("ENV_STATE_FAIL", "✗", "✗")
ENV_STATE_PENDING = _t("ENV_STATE_PENDING", "◌ 待检", "◌ pending")
ENV_STATE_CHECKING = _t("ENV_STATE_CHECKING", "⠋ 检查中…", "⠋ checking...")

# Degraded kernel line (WR-01, 08-08): the env-screen worker's per-kernel
# and enumeration guards format this ONE line for a kernel that raised —
# {error} carries the exception type + message (English technical
# wording: the env_smoke detail-line vocabulary is data, D-02, never
# translated). The FAIL: prefix lets _summary_of's strip derive the
# summary cell exactly the way every kernel line already does.
ENV_KERNEL_DEGRADED = _t(
    "ENV_KERNEL_DEGRADED",
    "FAIL: kernel raised {error}",
    "FAIL: kernel raised {error}")

# Env panel column headers (08-UI-SPEC Screen 1 header row: 状态 检查项
# 摘要). The 摘要 (summary) column carries each kernel's own first detail
# line (prefix-stripped) once its result arrives (08-06).
ENV_COL_STATE = _t("ENV_COL_STATE", "状态", "State")
ENV_COL_ITEM = _t("ENV_COL_ITEM", "检查项", "Check")
ENV_COL_SUMMARY = _t("ENV_COL_SUMMARY", "摘要", "Summary")

# Screen title for the title bar (08-UI-SPEC Screen 1 name: 环境检查).
ENV_SCREEN_TITLE = _t(
    "ENV_SCREEN_TITLE", "环境检查", "Environment Check")

# Last-check line (ENV-02 verbatim format "上次检查: YYYY-MM-DD HH:MM").
# The colon is HALFWIDTH (08-UI-SPEC Auto-Selected Default #12: ROADMAP +
# 08-CONTEXT wording; narrower in a double-width-CJK line) — a single
# constant the maintainer may flip.
ENV_LAST_CHECK_LINE = _t(
    "ENV_LAST_CHECK_LINE", "上次检查: {checked_at}",
    "Last check: {checked_at}")

# Last-check line — degraded (WR-03, 261016-a4f): rendered when the run
# COMPLETED but the persist tail itself failed (e.g. a read-only state
# dir). WHY a dedicated constant: a bare timestamp would promise a
# persisted same-day cache that does not exist — the degraded wording
# states the results were not saved and the check re-runs on restart
# (the next boot re-runs it as an honest cache miss). {checked_at}
# marks the attempt moment; {error} is DATA (the exception type +
# message rides verbatim, never translated — the ENV_KERNEL_DEGRADED
# precedent).
ENV_LAST_CHECK_DEGRADED = _t(
    "ENV_LAST_CHECK_DEGRADED",
    "上次检查: {checked_at} — 检查结果未保存（{error}），重启后重新检查",
    "Last check: {checked_at} — results not saved ({error}); "
    "the check re-runs on restart")

# Gate verdict — pass (08-UI-SPEC Copywriting Contract; renders from the
# tui.services.env_gate judgment, advisory this phase per D-09).
ENV_VERDICT_PASS = _t(
    "ENV_VERDICT_PASS", "✓ 环境就绪（可启动）",
    "✓ environment ready (launch allowed)")

# Gate verdict — critical fail (ENV-03): names the failing CRITICAL kernel
# ids (English verbatim, main() order) with the blocking note. Amended
# 11-05: the blocking is real (the run-config launch confirmation
# consumes the verdict), so the value states it in the present tense —
# same constant name, same {kernel_names} field. 261016-poa (UX-3):
# the old gate title term retired — the copy reads 启动确认 /
# launch confirmation.
ENV_VERDICT_CRITICAL_FAIL = _t(
    "ENV_VERDICT_CRITICAL_FAIL",
    "✗ 关键项未通过: {kernel_names} — 启动已被运行配置启动确认阻断",
    "✗ critical checks failed: {kernel_names} — launch is blocked by "
    "the run-config launch confirmation")

# Missing-data routing (ENV-03/SEL-04; amended 10-03): the count, the [3]
# keycap hint routing to the data-manager screen (the nav digit 3 IS the
# one navigation path — the hint surfaces it, no alias key), and the CLI
# audit command — English verbatim (file paths and CLI commands are never
# translated, I18N-01). The Phase-10-panel note is retired: the panel
# exists now.
ENV_ROUTE_MISSING_DATASETS = _t(
    "ENV_ROUTE_MISSING_DATASETS",
    "⚠ {n} 个数据集目录缺失 — [3] 前往数据管理；"
    "CLI 重跑审计: python script/audit_n_frequencies.py",
    "⚠ {n} dataset dirs missing — [3] open the data manager; "
    "CLI re-audit: python script/audit_n_frequencies.py")

# Missing-model routing (261014-dcl): models have NO CLI download
# command, so the wording must never promise one — it names the count
# and points at the run-config screen where the storage location is
# visible (manual placement is the remedy; the [4] keycap names the nav
# digit, the one navigation path). Glyph-first ⚠ per the redundancy
# rule. 261015-ehc: the zh wording applies the terminology table's
# storage-root word 存储位置.
ENV_ROUTE_MISSING_MODELS = _t(
    "ENV_ROUTE_MISSING_MODELS",
    "⚠ {n} 个模型目录缺失 — 模型需手动放置（[4] 运行配置可查看存储位置）",
    "⚠ {n} model dirs missing — models are placed by hand (the storage "
    "location is visible in [4] Run Config)")

# Env screen binding labels (08-UI-SPEC Keyboard map: r 重检, enter 详情).
ENV_REFRESH_LABEL = _t("ENV_REFRESH_LABEL", "重检", "Recheck")
ENV_DETAIL_LABEL = _t("ENV_DETAIL_LABEL", "详情", "Detail")

# Drill-down modal chrome (08-UI-SPEC Modal — 详情下钻): the title pairs the
# kernel id (English, data) with its ENV_KERNEL_LABELS label.
ENV_DETAIL_TITLE = _t(
    "ENV_DETAIL_TITLE", "{kernel_id} — {label}", "{kernel_id} — {label}")

# Quick check (ENV-04/D-09): consumed by the Phase 11 launch screen.
ENV_QUICK_CHECK_PASS = _t(
    "ENV_QUICK_CHECK_PASS", "快检通过（launch-required 子集）",
    "Quick check passed (launch-required subset)")
ENV_QUICK_CHECK_FAIL = _t(
    "ENV_QUICK_CHECK_FAIL", "✗ 快检失败: {kernel_names}",
    "✗ quick check failed: {kernel_names}")

# Storage overview (261014-f4w, F4W-04): the slot-1 read-only section
# listing all five effective run-artifact directories with existence
# glyphs. ENV_STORAGE_LABELS is keyed on the DIRECTORY_KEYS vocabulary
# (pipeline/directories_config.py) and ordered by it — the dict IS the
# row-order contract (the ENV_KERNEL_LABELS dict-of-labels shape); the
# footer note routes edits to slot 4 (the digit is the one nav path).
# 261015-ehc terminology: the zh output-root label is 结果目录 (the en
# side keeps the established English "output root").
ENV_STORAGE_TITLE = _t("ENV_STORAGE_TITLE", "存储目录", "Storage Dirs")
ENV_STORAGE_LABELS = _t(
    "ENV_STORAGE_LABELS",
    {
        "model_root": "模型根",
        "dataset_root": "数据集根",
        "output_root": "结果目录",
        "log_dir": "日志目录",
        "cache_dir": "模型缓存",
    },
    {
        "model_root": "model root",
        "dataset_root": "dataset root",
        "output_root": "output root",
        "log_dir": "log dir",
        "cache_dir": "model cache",
    },
)
ENV_STORAGE_NOTE = _t(
    "ENV_STORAGE_NOTE", "修改目录请到 4 运行配置",
    "Edit dirs in 4 Run Config")
# 261019-v3g (WINDOWS #33): the cache row's honest ABSENT state. The
# glyph is language-neutral — ◌ registered twice (the established
# indeterminate glyph from the monitor strip vocabulary); the note is
# training-scoped zh copy within the approved terminology table: an
# absent HF cache is created on demand at training, never a missing-dir
# error, while a PRESENT-but-unwritable cache keeps the ✗.
ENV_STATE_ON_DEMAND = _t("ENV_STATE_ON_DEMAND", "◌", "◌")
ENV_STORAGE_CACHE_ON_DEMAND = _t(
    "ENV_STORAGE_CACHE_ON_DEMAND",
    "未创建 — 训练时自动生成",
    "not created — created on demand at training")

# ===== 选择 (SEL-01..04, 08-07) =====
# Screen titles (08-UI-SPEC Screen 2 title bar). Since the 2026-10-14
# slot split (261014-mlc) slot 2 is MODELS ONLY — the m table toggle is
# gone and the title is constant.
SEL_SCREEN_TITLE_MODELS = _t(
    "SEL_SCREEN_TITLE_MODELS", "选择: 模型", "Selection: Models")

# Status line (top-right, zero-one-many): the marked-counts readout in the
# same structure for 0, 1, and many marks; totals are the live registry
# counts (59/50 against the committed registries).
SEL_STATUS_LINE = _t(
    "SEL_STATUS_LINE",
    "已标记: 模型 {n}/{models_total} · 数据集 {m}/{tasks_total}",
    "Marked: {n}/{models_total} models · {m}/{tasks_total} datasets")

# Filter bar (08-UI-SPEC Screen 2): the label, the k9s type-to-filter
# placeholder (Keyboard & Interaction Contract), and the live (N/total)
# readout (the slot-4 picker's own readout — untouched by the slot
# split). The slot-2 POOLED variant below carries the active pool mode
# (已适配 default / 全部 under t) so the default-filter state is always
# legible (MLC-02).
SEL_FILTER_LABEL = _t("SEL_FILTER_LABEL", "过滤: ", "Filter: ")
SEL_FILTER_PLACEHOLDER = _t(
    "SEL_FILTER_PLACEHOLDER", "输入过滤词…", "Type to filter...")
SEL_FILTER_COUNT = _t(
    "SEL_FILTER_COUNT", "({n}/{total})", "({n}/{total})")
SEL_FILTER_COUNT_POOLED = _t(
    "SEL_FILTER_COUNT_POOLED", "({pool} {n}/{total})", "({pool} {n}/{total})")

# Unknown-axis warning line (dim, under the Input): rendered while valid
# terms still apply; {axes} is the sorted known-axis vocabulary (data).
SEL_FILTER_UNKNOWN_AXIS = _t(
    "SEL_FILTER_UNKNOWN_AXIS", "未知过滤轴: {axis}（可用: {axes}）",
    "Unknown filter axis: {axis} (known: {axes})")

# Empty edge — filter no match: the documented row with the Esc-clear hint.
SEL_FILTER_NO_MATCH = _t(
    "SEL_FILTER_NO_MATCH", "无匹配行（0/{total}）— 调整过滤词，或 Esc 清除过滤",
    "No matching rows (0/{total}) — adjust the filter or press Esc to clear")

# Loading state: the single row covering the registry/n_audit read seam
# before rows compose (08-UI-SPEC UI Considerations, selection loading).
SEL_LOADING_ROW = _t("SEL_LOADING_ROW", "加载中…", "Loading...")

# Empty edge — registry load failure: names the path (the tolerant-loader
# None result); the app stays alive.
SEL_REGISTRY_LOAD_FAILED = _t(
    "SEL_REGISTRY_LOAD_FAILED",
    "✗ 注册表加载失败 — {registry_path} 不可读（容错 loader 返回空）",
    "✗ registry load failed — {registry_path} unreadable (tolerant "
    "loader returned empty)")

# n_audit absent (SEL-04 column-level empty state): every presence cell
# renders this copy; the CLI audit command stays English verbatim.
SEL_N_AUDIT_MISSING = _t(
    "SEL_N_AUDIT_MISSING",
    "✗ n_audit.json 缺失 — 在场列不可用；"
    "CLI 重跑: python script/audit_n_frequencies.py",
    "✗ n_audit.json missing — the presence column is unavailable; "
    "CLI re-run: python script/audit_n_frequencies.py")

# Model-table column headers (08-UI-SPEC Screen 2: 标 模型 类型 物种
# 规模(M) 数据). The mark column header is the single-char 标 (2 cells).
SEL_COL_MARK = _t("SEL_COL_MARK", "标", "Mk")
SEL_COL_MODEL = _t("SEL_COL_MODEL", "模型", "Models")
SEL_COL_TYPE = _t("SEL_COL_TYPE", "类型", "Type")
SEL_COL_SPECIES = _t("SEL_COL_SPECIES", "物种", "Species")
SEL_COL_SIZE = _t("SEL_COL_SIZE", "规模(M)", "Size(M)")

# Dataset-table column headers (标 · 任务键 · Category · 类型 · 指标 ·
# 数据; Category is the registry's own English field name — data, I18N-01).
SEL_COL_TASK = _t("SEL_COL_TASK", "任务键", "Task Key")
SEL_COL_CATEGORY = _t("SEL_COL_CATEGORY", "Category", "Category")
SEL_COL_METRIC = _t("SEL_COL_METRIC", "指标", "Metric")

# Presence column header (shared by both tables).
SEL_COL_PRESENCE = _t("SEL_COL_PRESENCE", "数据", "Data")

# Presence cells (SEL-04): present = pass glyph + thousands-separated
# exact train/dev/test counts (formatting happens only in the screen);
# missing = the missing glyph + word. 缺失 is the requirement-verbatim
# wording (✓ 在场 / ✗ 缺失).
SEL_PRESENCE_PRESENT = _t(
    "SEL_PRESENCE_PRESENT", "✓ {train}/{dev}/{test}", "✓ {train}/{dev}/{test}")
SEL_PRESENCE_MISSING = _t("SEL_PRESENCE_MISSING", "✗ 缺失", "✗ missing")
# Presence unknown (datasets: registry/audit drift — a key absent from
# n_audit). Gap-filler per the glyph-first redundancy rule (◌ pending-glyph
# family, dim render). Since 261014-dcl the MODELS column no longer
# lands here wholesale: for models, unknown is the no-Model_path/drift
# state of the new live presence decision (SEL_MODEL_PRESENCE_* below);
# datasets keep the n_audit drift meaning.
SEL_PRESENCE_UNKNOWN = _t("SEL_PRESENCE_UNKNOWN", "◌ 未知", "◌ unknown")

# Models-column presence cells (DCL-02, 261014-dcl): the live per-model
# download state decided in tui/services/selection over the effective
# model root (the run-config root when configured, the committed
# pipeline dir otherwise). Glyph-first per the redundancy rule. Since
# MLC-02 these are the 下载 column's present/missing states.
SEL_MODEL_PRESENCE_PRESENT = _t(
    "SEL_MODEL_PRESENCE_PRESENT", "✓ 已下载", "✓ downloaded")
SEL_MODEL_PRESENCE_MISSING = _t(
    "SEL_MODEL_PRESENCE_MISSING", "✗ 未下载", "✗ not downloaded")

# ===== Slot-2 models-only rework (MLC-02, 261014-mlc; the maintainer's
# 2026-10-14 slot split: slot 2 = models ONLY) =====
# The 适配 column cells (the committed dnallm_compat verdict, rendered):
# adapted officials, unadapted officials (revealed only under the t ALL
# pool, dim), and customs (always visible per the private-models-visible
# ruling — customs are operator-added, outside the official registry the
# ruling constrains).
SEL_COL_COMPAT = _t("SEL_COL_COMPAT", "适配", "Adapt")
SEL_COMPAT_ADAPTED = _t("SEL_COMPAT_ADAPTED", "已适配", "adapted")
SEL_COMPAT_UNADAPTED = _t("SEL_COMPAT_UNADAPTED", "未适配", "unadapted")
SEL_COMPAT_CUSTOM = _t("SEL_COMPAT_CUSTOM", "自定义", "custom")
# The 下载 column header + the honest manual-placement cell (missing
# unadapted-or-custom: the private/no-source state per the ruling —
# manual weight placement, NEVER huggingface guidance; the ◌ 未知 cell
# reuses SEL_PRESENCE_UNKNOWN).
SEL_COL_DOWNLOAD = _t("SEL_COL_DOWNLOAD", "下载", "Download")
SEL_MODEL_DL_MANUAL = _t("SEL_MODEL_DL_MANUAL", "手动放置", "manual placement")
# The pool-mode segments (the filter-count {pool} values) + the t
# binding label that toggles the pool.
SEL_POOL_ADAPTED = _t("SEL_POOL_ADAPTED", "已适配", "adapted")
SEL_POOL_ALL = _t("SEL_POOL_ALL", "全部", "All")
SEL_POOL_TOGGLE_LABEL = _t("SEL_POOL_TOGGLE_LABEL", "显示全部", "Show All")
# The d binding label (model download — one d vocabulary with the
# dataset lane's 入队, its own noun) + the two honest toasts: the
# already-downloaded no-op, and the manual-placement toast naming the
# landing dir (the effective model root joined with the row's
# Model_path) instructing manual weight placement there.
SEL_MODEL_DOWNLOAD_LABEL = _t("SEL_MODEL_DOWNLOAD_LABEL", "下载", "Download")
SEL_MODEL_PRESENT_TOAST = _t(
    "SEL_MODEL_PRESENT_TOAST", "该模型已下载", "Model already downloaded")
SEL_MODEL_MANUAL_TOAST = _t(
    "SEL_MODEL_MANUAL_TOAST",
    "⚠ {key} 需手动放置 — 请将模型权重放入 {path}",
    "⚠ {key} needs manual placement — put the model weights in {path}")

# Selection-screen binding labels (08-UI-SPEC Screen 2 footer mockup).
# The m table toggle label below is SLOT-4-OWNED since the 2026-10-14
# slot split (the run-config picker's own m flip — run_config.py; slot
# 2 retired its m binding; the t pool toggle has its own label above).
SEL_MARK_LABEL = _t("SEL_MARK_LABEL", "标记", "Mark")
SEL_SWITCH_LABEL = _t("SEL_SWITCH_LABEL", "数据集", "Datasets")
SEL_PRESET_LABEL = _t("SEL_PRESET_LABEL", "预设", "Presets")
SEL_MATRIX_LABEL = _t("SEL_MATRIX_LABEL", "矩阵", "Matrix")
SEL_TEMPLATE_LABEL = _t("SEL_TEMPLATE_LABEL", "模板", "Templates")
SEL_SAVE_PRESET_LABEL = _t("SEL_SAVE_PRESET_LABEL", "保存预设", "Save Preset")
SEL_FILTER_KEY_LABEL = _t("SEL_FILTER_KEY_LABEL", "过滤", "Filter")

# The env-screen s binding (08-UI-SPEC Keyboard map) was RETIRED by the
# 09-03 nav-shell migration: menu slot 2 supersedes it (one navigation
# path per target) — the action and this label constant were removed
# with it.

# Preset modal (08-UI-SPEC Keyboard map: tier-1 E2E 对 / tier-2 arena
# 代表 / 全部 / 自定义保存…). Derived labels for the built-ins; customs
# render their own saved name.
SEL_PRESET_TITLE = _t("SEL_PRESET_TITLE", "预设", "Presets")
SEL_PRESET_TIER_1 = _t("SEL_PRESET_TIER_1", "tier-1 E2E 对", "tier-1 E2E pairs")
SEL_PRESET_TIER_2 = _t(
    "SEL_PRESET_TIER_2", "tier-2 arena 代表", "tier-2 arena picks")
SEL_PRESET_ALL = _t("SEL_PRESET_ALL", "全部", "All")
# Empty edge — no saved customs: the documented entry with the save-flow
# hint (the s key names the save binding).
SEL_PRESET_NO_CUSTOMS = _t(
    "SEL_PRESET_NO_CUSTOMS", "尚无自定义预设 — 空格标记后按 s 保存当前选择",
    "No saved presets — mark with space, then press s to save")
# Success toast (preset applied, replacing semantics).
SEL_PRESET_APPLIED = _t(
    "SEL_PRESET_APPLIED", "✓ 已应用预设 {preset}（模型 {n}·数据集 {m}）",
    "✓ preset applied: {preset} (models {n} · datasets {m})")
# Save-success toast — Copywriting Contract gap-filler (the contract pins
# only the applied/exported toasts; a destructive-adjacent save needs its
# own feedback), same shape as the applied toast.
SEL_PRESET_SAVED = _t(
    "SEL_PRESET_SAVED", "✓ 预设已保存: {name}（模型 {n}·数据集 {m}）",
    "✓ preset saved: {name} (models {n} · datasets {m})")
# Save-failure warning — OSError persisting under the config root (a
# read-only location, a full disk): the save flow degrades to a warning
# toast, never a crash (the OS error detail is data).
SEL_PRESET_SAVE_FAILED = _t(
    "SEL_PRESET_SAVE_FAILED", "✗ 预设保存失败: {error}",
    "✗ preset save failed: {error}")
# Warning — preset unknown keys (registry evolution tolerance): loud, lists
# every skipped key.
SEL_PRESET_UNKNOWN_KEYS = _t(
    "SEL_PRESET_UNKNOWN_KEYS",
    "⚠ 预设含 {n} 个未知键（注册表已演进？）: {keys} — 已跳过",
    "⚠ preset carries {n} unknown keys (registry evolved?): {keys} "
    "— skipped")
# Destructive — overwriting a saved custom preset (Enter/Esc confirm).
SEL_PRESET_OVERWRITE_CONFIRM = _t(
    "SEL_PRESET_OVERWRITE_CONFIRM", "同名预设已存在: {name} — Enter 覆盖 / Esc 取消",
    "Preset {name} already exists — Enter overwrite / Esc cancel")
# Save-preset name input placeholder.
SEL_PRESET_NAME_PLACEHOLDER = _t(
    "SEL_PRESET_NAME_PLACEHOLDER", "输入预设名…", "Preset name...")

# Template modal (08-UI-SPEC Keyboard map: 导入模板 / 导出模板 / 转
# sweep_priorities tier).
SEL_TEMPLATE_TITLE = _t("SEL_TEMPLATE_TITLE", "模板", "Templates")
SEL_TEMPLATE_MENU_IMPORT = _t(
    "SEL_TEMPLATE_MENU_IMPORT", "导入模板", "Import template")
SEL_TEMPLATE_MENU_EXPORT = _t(
    "SEL_TEMPLATE_MENU_EXPORT", "导出模板", "Export template")
SEL_TEMPLATE_MENU_TIERS = _t(
    "SEL_TEMPLATE_MENU_TIERS", "转 sweep_priorities tier",
    "Convert to sweep_priorities tier")
SEL_TEMPLATE_PATH_PLACEHOLDER = _t(
    "SEL_TEMPLATE_PATH_PLACEHOLDER", "输入路径…", "Path...")
# Collect-all problem list (SEL-03 fail-fast): the header with the count,
# then one numbered line per problem ({location} is the JSON pointer, or
# the path for load failures).
SEL_TEMPLATE_PROBLEMS = _t(
    "SEL_TEMPLATE_PROBLEMS", "✗ 模板校验失败 — 共 {n} 处问题：",
    "✗ template validation failed — {n} problems:")
SEL_TEMPLATE_PROBLEM_LINE = _t(
    "SEL_TEMPLATE_PROBLEM_LINE", "{n}. {location}: {message}",
    "{n}. {location}: {message}")
# Import-success toast — Copywriting Contract gap-filler, same shape as
# the applied toast.
SEL_TEMPLATE_IMPORTED = _t(
    "SEL_TEMPLATE_IMPORTED", "✓ 模板已导入（模型 {n}·数据集 {m}）",
    "✓ template imported (models {n} · datasets {m})")
# Export-success toast (verbatim from the Copywriting Contract); the tier
# conversion export reuses it (it IS an export of the current selection).
SEL_TEMPLATE_EXPORTED = _t(
    "SEL_TEMPLATE_EXPORTED", "✓ 模板已导出: {path}",
    "✓ template exported: {path}")
# Write-failure problem line (template export / tier conversion): OSError
# from an unwritable or invalid operator path — the OS error detail is
# data; the modal stays open and nothing was written.
SEL_TEMPLATE_WRITE_FAILED = _t(
    "SEL_TEMPLATE_WRITE_FAILED", "✗ 写入失败: {error}",
    "✗ write failed: {error}")

# Destructive — clearing all marks (Enter/Esc confirm). Landed for the
# record per the Copywriting Contract; NO trigger exists ("if surfaced"
# — the keyboard map defines no clear binding; presets replace, they do
# not need a destructive clear).
SEL_CLEAR_MARKS_CONFIRM = _t(
    "SEL_CLEAR_MARKS_CONFIRM",
    "清除全部标记？（模型 {n} · 数据集 {m}）— Enter 确认 / Esc 取消",
    "Clear all marks? (models {n} · datasets {m}) — Enter confirm / "
    "Esc cancel")

# ===== 自定义条目呈现 (SEL_ custom additions, CUST-06/D-09/D-10/D-14, 09-06) =====
# The w/e binding labels, the toggle/no-op toasts, the disabled-mark
# warning, and the badge/count copy — 09-UI-SPEC Copywriting Contract
# verbatim. The 停用 toast carries the loader-level note (D-09: the
# disable is real run-removal, not a cosmetic dim).
SEL_WIZARD_LABEL = _t("SEL_WIZARD_LABEL", "接入", "Onboard")
SEL_TOGGLE_LABEL = _t("SEL_TOGGLE_LABEL", "停用", "Disable")
SEL_TOGGLE_DISABLED_TOAST = _t(
    "SEL_TOGGLE_DISABLED_TOAST", "✓ 已停用 {key}（运行不再加载，loader 级）",
    "✓ disabled {key} (runs no longer load it, loader-level)")
SEL_TOGGLE_ENABLED_TOAST = _t(
    "SEL_TOGGLE_ENABLED_TOAST", "✓ 已启用 {key}", "✓ enabled {key}")
SEL_TOGGLE_OFFICIAL_NOOP = _t(
    "SEL_TOGGLE_OFFICIAL_NOOP", "官方条目不可停用",
    "Official entries cannot be disabled")
# Warning — spacebar on a disabled custom row (T-09-13: a mark the sweep
# can never see is blocked at entry, never discovered at launch).
SEL_DISABLED_MARK_WARNING = _t(
    "SEL_DISABLED_MARK_WARNING", "⚠ {key} 已停用 — 运行不会加载该条目，标记无效",
    "⚠ {key} is disabled — runs never load it; the mark has no effect")
# The D-10 custom badge — the ◇ prefix on the key cell (bold + accent for
# enabled; the dim variant pairs with the suffix for disabled; glyph +
# weight carry the meaning under NO_COLOR).
SEL_CUSTOM_BADGE = _t("SEL_CUSTOM_BADGE", "◇", "◇")
SEL_DISABLED_SUFFIX = _t("SEL_DISABLED_SUFFIX", "（已停用）", " (disabled)")
# Count-line segment (D-10) — appended (dim) iff at least one custom entry
# is LANDED; counts cover both states (visible = counted; the sweep-visible
# enabled count is derivable from the markers). Zero customs omits the
# segment entirely (the Phase 8 look, byte-identical).
SEL_COUNT_CUSTOM_SEGMENT = _t(
    "SEL_COUNT_CUSTOM_SEGMENT",
    "官方 {official_models}/{official_datasets} · 自定义 {custom_models}/{custom_datasets}",
    "official {official_models}/{official_datasets} · custom "
    "{custom_models}/{custom_datasets}")

# ===== 矩阵总览 (matrix, SEL-01 auxiliary, 08-07) =====
MATRIX_TITLE = _t(
    "MATRIX_TITLE", "矩阵总览（只读）— {models} 模型 × {datasets} 数据集",
    "Matrix overview (read-only) — {models} models × {datasets} datasets")
MATRIX_SCROLL_HINT = _t(
    "MATRIX_SCROLL_HINT", "←/→ 横向滚动 · esc 返回",
    "←/→ scroll horizontally · esc back")
# Cursor readout line (below the table): the FULL task key of the cursor
# column (long-text resolution for 62-char keys).
MATRIX_CURSOR_READOUT = _t(
    "MATRIX_CURSOR_READOUT", "光标: {task_key}", "Cursor: {task_key}")

# ===== 接入向导 (WIZ_, CUST-01..03, 09-01 service tier) =====
# The validation-report chrome + problem wordings the service composes;
# the 09-04/09-05 wizard screens render the numbered lines. Report rows
# verbatim from the 09-UI-SPEC Copywriting Contract; field labels follow
# the wizard step tables (registry field names stay English verbatim,
# I18N-01). The service returns machine (field_key, message) pairs — the
# labels below are the screens' field_key → label map.

# Validation report header + numbered problem line (09-UI-SPEC
# Copywriting Contract verbatim; field-definition order).
WIZ_PROBLEMS_HEADER = _t(
    "WIZ_PROBLEMS_HEADER", "✗ 校验失败 — 共 {n} 处问题：",
    "✗ validation failed — {n} problems:")
WIZ_PROBLEM_LINE = _t(
    "WIZ_PROBLEM_LINE", "{i}. {field_label}: {problem}",
    "{i}. {field_label}: {problem}")

# Model wizard field labels (WIZM_) — key → label over the model
# field-definition order. English-verbatim field names (architecture /
# Tokenizer / huggingface / ...) are data and stay untranslated.
WIZM_FIELD_LABELS = _t(
    "WIZM_FIELD_LABELS",
    {
        "key": "键名",
        "Model_path": "本地路径",
        "size (M)": "规模(M)",
        "species": "物种",
        "type": "类型",
        "architecture": "architecture",
        "Tokenizer": "tokenizer",
        "context_len (bp)": "context_len (bp)",
        "huggingface": "huggingface",
        "modelscope": "modelscope",
        "series": "series",
        "quirks": "quirk",
    },
    {
        "key": "Key",
        "Model_path": "Local path",
        "size (M)": "Size(M)",
        "species": "Species",
        "type": "Type",
        "architecture": "architecture",
        "Tokenizer": "tokenizer",
        "context_len (bp)": "context_len (bp)",
        "huggingface": "huggingface",
        "modelscope": "modelscope",
        "series": "series",
        "quirks": "quirk",
    },
)

# Dataset wizard field labels (WIZD_) — key → label over the dataset
# field-definition order (train/dev/test label the split FILE inputs of
# step 2; Task_type renders as its step-3 wording 任务类型).
WIZD_FIELD_LABELS = _t(
    "WIZD_FIELD_LABELS",
    {
        "key": "键名",
        "Dataset_path": "数据集路径",
        "Category": "Category",
        "label_column": "标签列",
        "Train": "train",
        "Dev": "dev",
        "Test": "test",
        "labels": "标签数",
        "length": "序列长度",
        "type": "任务类型",
        "metric": "主指标",
        "citation": "citation",
        "source": "source",
        "license": "license",
        "preprocessing": "preprocessing",
    },
    {
        "key": "Key",
        "Dataset_path": "Dataset path",
        "Category": "Category",
        "label_column": "Label column",
        "Train": "train",
        "Dev": "dev",
        "Test": "test",
        "labels": "Labels",
        "length": "Seq length",
        "type": "Task type",
        "metric": "Metric",
        "citation": "citation",
        "source": "source",
        "license": "license",
        "preprocessing": "preprocessing",
    },
)

# Problem wordings — the {problem} segment of WIZ_PROBLEM_LINE. The
# collision / path-missing / needs-numeric rows match the 09-UI-SPEC
# validation-report example verbatim (ASCII parens); interpolated values
# ({key}/{path}/{value}…) are data.
WIZ_PROBLEM_REQUIRED = _t(
    "WIZ_PROBLEM_REQUIRED", "必填项，不能为空", "Required, cannot be empty")
WIZ_PROBLEM_NOT_OBJECT = _t(
    "WIZ_PROBLEM_NOT_OBJECT", "录入内容必须是对象 (收到 {type})",
    "Entry must be an object (got {type})")
WIZ_PROBLEM_KEY_FORMAT = _t(
    "WIZ_PROBLEM_KEY_FORMAT", "键名不能包含路径分隔符 ({key})",
    "Key must not contain path separators ({key})")
WIZ_PROBLEM_COLLISION_OFFICIAL = _t(
    "WIZ_PROBLEM_COLLISION_OFFICIAL", "与官方条目冲突 ({key})",
    "Collides with an official entry ({key})")
WIZ_PROBLEM_COLLISION_CUSTOM = _t(
    "WIZ_PROBLEM_COLLISION_CUSTOM", "与既有自定义条目冲突 ({key})",
    "Collides with an existing custom entry ({key})")
WIZ_PROBLEM_PATH_MISSING = _t(
    "WIZ_PROBLEM_PATH_MISSING", "路径不存在 ({path})",
    "Path does not exist ({path})")
WIZ_PROBLEM_NEEDS_NUMERIC = _t(
    "WIZ_PROBLEM_NEEDS_NUMERIC", "需为数字 ({value})",
    "Must be a number ({value})")
WIZ_PROBLEM_NEEDS_INTEGER = _t(
    "WIZ_PROBLEM_NEEDS_INTEGER", "需为整数 ({value})",
    "Must be an integer ({value})")
WIZ_PROBLEM_ENUM = _t(
    "WIZ_PROBLEM_ENUM", "取值无效 ({value})，可选: {allowed}",
    "Invalid value ({value}), allowed: {allowed}")
# Split-file problems ({file} is the split file name, {column} the
# collected label column).
WIZ_PROBLEM_SPLIT_FILE_MISSING = _t(
    "WIZ_PROBLEM_SPLIT_FILE_MISSING", "文件不存在 ({file})",
    "File not found ({file})")
WIZ_PROBLEM_SPLIT_UNREADABLE = _t(
    "WIZ_PROBLEM_SPLIT_UNREADABLE", "无法解析 ({file}: {reason})",
    "Cannot parse ({file}: {reason})")
WIZ_PROBLEM_SPLIT_NO_HEADER = _t(
    "WIZ_PROBLEM_SPLIT_NO_HEADER", "文件为空，无表头 ({file})",
    "File is empty, no header ({file})")
WIZ_PROBLEM_SPLIT_NO_SEQUENCE = _t(
    "WIZ_PROBLEM_SPLIT_NO_SEQUENCE", "表头缺少 sequence 列 ({file})",
    "Header lacks a sequence column ({file})")
WIZ_PROBLEM_SPLIT_NO_LABEL_COLUMN = _t(
    "WIZ_PROBLEM_SPLIT_NO_LABEL_COLUMN", "表头缺少标签列 {column} ({file})",
    "Header lacks label column {column} ({file})")
WIZ_PROBLEM_SPLIT_ZERO_ROWS = _t(
    "WIZ_PROBLEM_SPLIT_ZERO_ROWS", "无数据行 (0 行)", "No data rows (0 rows)")
WIZ_PROBLEM_SPLIT_COUNT_MISMATCH = _t(
    "WIZ_PROBLEM_SPLIT_COUNT_MISMATCH", "声明 {declared} 行，与实际 {counted} 行不符",
    "Declared {declared} rows, counted {counted}")

# ===== 接入向导 chrome (WIZ_, CUST-01/02 UI, 09-04) =====
# The wizard modal's own chrome copy (09-UI-SPEC Copywriting Contract
# verbatim). Kind names slot into 新增{kind} (模型/数据集); {indicator}
# renders the "{n}/{total}" step number — Typography amendment #9 styles
# that segment accent+bold (the screen composes the markup; this module
# never carries markup).
WIZ_KIND_MODELS = _t("WIZ_KIND_MODELS", "模型", "Models")
WIZ_KIND_DATASETS = _t("WIZ_KIND_DATASETS", "数据集", "Datasets")
WIZ_BORDER_TITLE = _t(
    "WIZ_BORDER_TITLE", "新增{kind} — 步骤 {indicator} · {step}",
    "New {kind} — step {indicator} · {step}")
# Model wizard step names (the border-title {step} values, in order).
WIZM_STEPS = _t(
    "WIZM_STEPS",
    ("基本信息", "架构与分词", "来源链接", "quirk 勾选"),
    ("Basics", "Architecture & tokenizer", "Source links", "Quirks"),
)
# Dataset wizard step names (the same slot, the dataset instance).
WIZD_STEPS = _t(
    "WIZD_STEPS",
    ("基本信息", "数据文件", "任务与指标", "溯源信息"),
    ("Basics", "Data files", "Task & metric", "Provenance"),
)
# The step-2 split-file-name Inputs' shared placeholder (the UI-SPEC
# wording renders the trio as train / dev / test 文件名).
WIZ_SPLIT_FILE_PLACEHOLDER = _t(
    "WIZ_SPLIT_FILE_PLACEHOLDER", "文件名", "Filename")
# Quirk checklist labels (D-02: exactly the three named quirks,
# unchecked default; execution-side mapping is Phase 11's).
WIZ_QUIRK_NO_SAFETENSORS = _t(
    "WIZ_QUIRK_NO_SAFETENSORS", "不使用 safetensors", "No safetensors")
WIZ_QUIRK_FP32_ONLY = _t("WIZ_QUIRK_FP32_ONLY", "仅支持 fp32", "fp32 only")
WIZ_QUIRK_SPECIAL_HEAD = _t(
    "WIZ_QUIRK_SPECIAL_HEAD", "需要特殊头 (head)", "Needs a special head (head)")
# Type-aware control advisory lines (D-03 — ADVISORY only, the collect-all
# pass is authoritative; fool-proofing never blocks onboarding).
WIZ_PATH_EXISTS = _t("WIZ_PATH_EXISTS", "✓ 路径存在", "✓ path exists")
WIZ_PATH_MISSING_ADVISORY = _t(
    "WIZ_PATH_MISSING_ADVISORY", "✗ 路径不存在（仍可继续，提交时统一校验）",
    "✗ path does not exist (you may continue; validated at submit)")
WIZ_NUMERIC_HINT = _t("WIZ_NUMERIC_HINT", "✗ 需为数字", "✗ must be a number")
# Footer hint (the modal's own 1-row keycap hint, migration table). The
# last step substitutes the submit keycap for the next-step one.
WIZ_FOOTER_HINT = _t(
    "WIZ_FOOTER_HINT", "[enter] 下一步  [b] 上一步  [esc] 取消",
    "[enter] next  [b] back  [esc] cancel")
WIZ_FOOTER_HINT_LAST = _t(
    "WIZ_FOOTER_HINT_LAST", "[enter] 提交校验  [b] 上一步  [esc] 取消",
    "[enter] validate  [b] back  [esc] cancel")
# Binding labels (the hint's keycap segments; Binding descriptions use
# the same wording). WR-01 (quick-261016-hhx, the 08 review): the en
# value is "Back a step" (NOT "Back") — APP_MODAL_BACK_LABEL already
# owns en "Back" with a different zh, and translate_value's byte
# equality needs the registry injective in BOTH directions (the b
# binding's en->zh remap returned the esc-back wording 返回 before).
WIZ_NEXT_LABEL = _t("WIZ_NEXT_LABEL", "下一步", "Next")
WIZ_BACK_LABEL = _t("WIZ_BACK_LABEL", "上一步", "Back a step")
WIZ_SUBMIT_LABEL = _t("WIZ_SUBMIT_LABEL", "提交校验", "Validate")
WIZ_CANCEL_LABEL = _t("WIZ_CANCEL_LABEL", "取消", "Cancel")
# Destructive — wizard esc-cancel with entered values (ConfirmModal gate;
# {n} is the filled-step count). Blank forms cancel silently.
WIZ_CANCEL_CONFIRM = _t(
    "WIZ_CANCEL_CONFIRM", "放弃本次录入？已填 {n} 步 — Enter 放弃 / Esc 继续",
    "Discard this entry? {n} steps filled — Enter discard / Esc continue")
# Validation report chrome: the report view's border title and the
# return-to-form hint (the 09-UI-SPEC report mockup).
WIZ_REPORT_TITLE = _t(
    "WIZ_REPORT_TITLE", "新增{kind} — 校验", "New {kind} — validation")
WIZ_REPORT_BACK_HINT = _t(
    "WIZ_REPORT_BACK_HINT", "[esc] 返回修改", "[esc] back to the form")
# The gauntlet phase's pending view: its title is the Copywriting
# Contract's gauntlet title verbatim; the back hint is the gauntlet
# mockup's esc row.
WIZ_GAUNTLET_BACK_HINT = _t(
    "WIZ_GAUNTLET_BACK_HINT", "[esc] 返回", "[esc] back")
# Step-1-only affordances (D-11; auto-default #7 placement) — the binding
# labels; the views themselves are 09-05 against the on_import/on_export
# seams.
WIZ_IMPORT_LABEL = _t("WIZ_IMPORT_LABEL", "从文件导入", "Import File")
WIZ_EXPORT_LABEL = _t(
    "WIZ_EXPORT_LABEL", "导出自定义注册表", "Export Registry")

# ===== 接入 gauntlet 面板 (GAUNTLET_, 09-05, CUST-04 UI + D-08/D-11) =====
# The gauntlet panel's rows / banner / toasts (09-UI-SPEC Copywriting
# Contract verbatim). Format fields: {item} is the item label below,
# {cells} the planned-cell count parsed from the service's
# ``planned_cells=N`` detail token, {summary} the item's remaining detail
# tokens joined verbatim (data, never translated), {key} the candidate
# registry key, {path} a filesystem path, {n} a count, {kind} 模型/数据集.
# 261015-ehc terminology: the zh {cells} wording is 训练项 (the en side
# keeps "cells").
GAUNTLET_TITLE = _t(
    "GAUNTLET_TITLE", "接入 gauntlet — {key}", "Onboarding gauntlet — {key}")
GAUNTLET_ITEM_DRY_RUN = _t(
    "GAUNTLET_ITEM_DRY_RUN", "dry-run 预检", "dry-run precheck")
GAUNTLET_ITEM_AUDIT = _t(
    "GAUNTLET_ITEM_AUDIT", "audit 对账", "audit reconcile")
GAUNTLET_ROW_PENDING = _t(
    "GAUNTLET_ROW_PENDING", "◌ {item} 待检", "◌ {item} pending")
GAUNTLET_ROW_RUNNING = _t(
    "GAUNTLET_ROW_RUNNING", "⠋ {item} …运行中", "⠋ {item} running...")
GAUNTLET_ROW_DRY_RUN_PASS = _t(
    "GAUNTLET_ROW_DRY_RUN_PASS",
    "✓ dry-run 预检 — {cells} 训练项 计划成功",
    "✓ dry-run precheck — {cells} cells planned successfully")
GAUNTLET_ROW_PASS = _t(
    "GAUNTLET_ROW_PASS", "✓ {item} — {summary}", "✓ {item} — {summary}")
GAUNTLET_ROW_FAIL = _t(
    "GAUNTLET_ROW_FAIL", "✗ {item} — {summary}", "✗ {item} — {summary}")
# The prominent CUST-04 failure banner — the 官方注册表零触碰 guarantee is
# contract wording (binding constraint 11), never paraphrased.
GAUNTLET_BANNER_FAIL = _t(
    "GAUNTLET_BANNER_FAIL", "✗ gauntlet 未通过 — {key} 未落盘（官方注册表零触碰）",
    "✗ gauntlet failed — {key} not landed (the official registry is "
    "never touched)")
GAUNTLET_ROW_LANDED = _t(
    "GAUNTLET_ROW_LANDED", "✓ 已落盘: {key} → {path}",
    "✓ landed: {key} → {path}")
# The land success toast reuses GAUNTLET_ROW_LANDED verbatim (the copy
# table names no separate toast — the landed row IS the success copy).
# Session undo (D-08): the [u] affordance is session-scoped (gone once the
# panel closes), explicit, immediately-after, toast-confirmed.
GAUNTLET_UNDO_AFFORDANCE = _t(
    "GAUNTLET_UNDO_AFFORDANCE", "[u] 会话内撤销", "[u] session undo")
GAUNTLET_UNDO_LABEL = _t(
    "GAUNTLET_UNDO_LABEL", "会话内撤销", "Session Undo")   # binding description (affordance minus keycap)
GAUNTLET_UNDO_TOAST = _t(
    "GAUNTLET_UNDO_TOAST", "✓ 已撤销 {key}", "✓ undone {key}")
# Drill-down chrome (derived, the ENV detail-title idiom): the row's item
# label over the subprocess's own verbatim output lines (data, no copy).
GAUNTLET_DRILL_TITLE = _t(
    "GAUNTLET_DRILL_TITLE", "{item} — 详情", "{item} — details")
GAUNTLET_DRILL_HINT = _t(
    "GAUNTLET_DRILL_HINT", "[enter] 详情", "[enter] details")
# D-11 import/export copy. The conflicts header names the collect-all
# count; problem lines reuse the SEL_TEMPLATE_PROBLEM_LINE shape. The
# exported toast deliberately differs from SEL_TEMPLATE_EXPORTED (that row
# says 模板已导出 — the registry export is its own wording).
GAUNTLET_IMPORT_CONFLICTS = _t(
    "GAUNTLET_IMPORT_CONFLICTS", "✗ 导入冲突 — 共 {n} 处：",
    "✗ import conflicts — {n} total:")
GAUNTLET_IMPORTED_TOAST = _t(
    "GAUNTLET_IMPORTED_TOAST", "✓ 已导入 {n} 条（{kind}）",
    "✓ imported {n} entries ({kind})")
GAUNTLET_EXPORTED_TOAST = _t(
    "GAUNTLET_EXPORTED_TOAST", "✓ 已导出: {path}", "✓ exported: {path}")
GAUNTLET_EXPORT_EMPTY_TOAST = _t(
    "GAUNTLET_EXPORT_EMPTY_TOAST", "尚无自定义条目可导出",
    "No custom entries to export")
# Derived: the export path-prompt's problems header (write-failure lines
# through the same numbered report surface).
GAUNTLET_EXPORT_PROBLEMS = _t(
    "GAUNTLET_EXPORT_PROBLEMS", "✗ 导出失败 — 共 {n} 处：",
    "✗ export failed — {n} problems:")

# ===== 导航壳 (NAV_, 09-03, D-13/D-15) =====
# Top-menu slot names — the RATIFIED verbatim resource nouns (D-13,
# 09-UI-SPEC Navigation Shell): never renamed, never re-translated. The
# digit prefix and 未开放 suffix are composed by the bar from NAV_SLOTS.
# 2026-10-14 slot split (261014-mlc): slot 2 is MODELS only and slot 3
# DATASETS only — value-only renames (names, bindings, routing
# untouched; the ENV_ROUTE_MISSING_DATASETS hint stays byte-identical
# per the maintainer ruling).
NAV_LABEL_ENV = _t("NAV_LABEL_ENV", "环境检查", "Environment Check")
NAV_LABEL_SELECTION = _t("NAV_LABEL_SELECTION", "模型", "Models")
NAV_LABEL_DATA = _t("NAV_LABEL_DATA", "数据集", "Datasets")
NAV_LABEL_RUN_CONFIG = _t("NAV_LABEL_RUN_CONFIG", "运行配置", "Run Config")
NAV_LABEL_MONITOR = _t("NAV_LABEL_MONITOR", "任务监控", "Monitor")
NAV_LABEL_ABOUT = _t("NAV_LABEL_ABOUT", "关于", "About")
# Placeholder suffix (slots 3/4/5 — implemented by their delivering
# phases) and the never-silent activation toast (D-13).
NAV_PLACEHOLDER_SUFFIX = _t("NAV_PLACEHOLDER_SUFFIX", "未开放", "n/a yet")
NAV_PLACEHOLDER_TOAST = _t(
    "NAV_PLACEHOLDER_TOAST", "该功能区于 Phase {n} 提供",
    "This area arrives in Phase {n}")

# ===== 关于屏 (ABOUT_, D-13 slot 6, 09-03) =====
# The five fixed row labels (D-13: 软件版本/数据版本/里程碑阶段/依赖版本/
# 仓库地址) + the title. Values are service-derived (tui/services/about);
# absent dependencies render the 未安装 value (dim, per-package tolerant).
ABOUT_TITLE = _t("ABOUT_TITLE", "关于 DNALLM-Mark", "About DNALLM-Mark")
ABOUT_ROW_SOFTWARE = _t("ABOUT_ROW_SOFTWARE", "软件版本", "Software version")
ABOUT_ROW_DATA = _t("ABOUT_ROW_DATA", "数据版本", "Data version")
ABOUT_ROW_MILESTONE = _t("ABOUT_ROW_MILESTONE", "里程碑阶段", "Milestone stage")
ABOUT_ROW_DEPS = _t("ABOUT_ROW_DEPS", "依赖版本", "Dependency versions")
ABOUT_ROW_REPO = _t("ABOUT_ROW_REPO", "仓库地址", "Repository")
# 软件版本 value with a resolved git sha (sha omitted → bare version).
ABOUT_VALUE_SOFTWARE_WITH_SHA = _t(
    "ABOUT_VALUE_SOFTWARE_WITH_SHA", "{version} (git {sha})",
    "{version} (git {sha})")
# 数据版本 value: official-only counts + the 自定义 landed counts + the
# n_audit 在场 signal (the honest machine-derivable data-state wording).
ABOUT_VALUE_DATA = _t(
    "ABOUT_VALUE_DATA",
    "官方注册表 {om} 模型 / {od} 数据集 · 自定义 {cm}/{cd} · {audit}",
    "official registry {om} models / {od} datasets · custom {cm}/{cd} · "
    "{audit}")
ABOUT_N_AUDIT_PRESENT = _t(
    "ABOUT_N_AUDIT_PRESENT", "n_audit.json 在场", "n_audit.json present")
ABOUT_N_AUDIT_ABSENT = _t(
    "ABOUT_N_AUDIT_ABSENT", "n_audit.json 缺失", "n_audit.json missing")
ABOUT_DEP_ABSENT = _t("ABOUT_DEP_ABSENT", "未安装", "not installed")
# 里程碑阶段 value — the one static milestone constant (Auto-Default #13:
# milestone metadata, not a machine probe; updated per milestone).
ABOUT_MILESTONE_STAGE = _t(
    "ABOUT_MILESTONE_STAGE",
    "v1.3.0 已交付 — 多 GPU 编排与验证（Phase 13-18）：动态调度/运行视图/"
    "失败恢复/双卡验证/TUI 多卡界面/error bar/文档",
    "v1.3.0 delivered — multi-GPU orchestration & validation "
    "(Phases 13-18): dynamic dispatch / run view / failure recovery / "
    "dual-GPU validation / TUI multi-GPU surface / error bars / docs")

# ===== 数据管理屏 (DL_, Phase 10, 10-03; D-12/D-13 + I18N-01) =====
# The data-manager screen chrome + Zenodo 整包 entry copy (10-UI-SPEC
# Copywriting Contract verbatim). Format fields: {n}/{total}/
# {present}/{missing} counts, {HH:MM} the probe moment, {error} a
# diagnostic, {key} a dataset key. Record ids (19135551), dataset
# keys, n_audit, and XDG state stay English verbatim.

DL_SCREEN_TITLE = _t("DL_SCREEN_TITLE", "数据集", "Datasets")
DL_MISSING_TITLE = _t(
    "DL_MISSING_TITLE", "缺失数据集 ({n}) — 来自 n_audit",
    "Missing datasets ({n}) — from n_audit")
DL_MISSING_COL_KEY = _t("DL_MISSING_COL_KEY", "数据集", "Datasets")
DL_MISSING_COL_ROWS = _t(
    "DL_MISSING_COL_ROWS", "n_audit 基线行数", "n_audit baseline rows")
DL_MISSING_EMPTY = _t(
    "DL_MISSING_EMPTY", "✓ 无缺失数据集 — 全部 {total} 个数据集在场",
    "✓ no missing datasets — all {total} present")

# The full-list 下载 column header (MLC-03, 261014-mlc): the merged
# presence status cell (✓ 在场 / ✗ 缺失 / ◌ 未知) — a live queue entry
# overlays its queue state word in the same cell.
DL_COL_DOWNLOAD = _t("DL_COL_DOWNLOAD", "下载", "Download")
DL_FULL_PRESENT = _t("DL_FULL_PRESENT", "✓ 在场", "✓ present")
DL_FULL_MISSING = _t("DL_FULL_MISSING", "✗ 缺失", "✗ missing")
DL_FULL_UNKNOWN = _t("DL_FULL_UNKNOWN", "◌ 未知", "◌ unknown")
# The dataset custom-entry wizard keycap (the w binding — slot 3 since
# the slot split; the same 接入 wording slot 2's w carries).
DL_WIZARD_LABEL = _t("DL_WIZARD_LABEL", "接入", "Onboard")

# The Zenodo 整包 four probe states (D-12; glyph+color dual channel on
# every one — probing/not-public dim, public ✓ success, failed ⚠
# warning; `z` on a disabled state is never silent). Since the
# 2026-10-14 ruling every line carries the 备选 prefix — Zenodo is the
# NON-DEFAULT alternate channel (ModelScope is the default; the line
# moved from the missing-list title row to the QUEUE title row).
DL_ZENODO_PROBING = _t(
    "DL_ZENODO_PROBING", "⠋ 备选 Zenodo 公开探测中 …",
    "⠋ probing the alternate Zenodo record...")
DL_ZENODO_NOT_PUBLIC = _t(
    "DL_ZENODO_NOT_PUBLIC", "[z] 备选 Zenodo 整包 · 未公开（探测于 {HH:MM}）",
    "[z] alternate Zenodo bundle · not public (probed at {HH:MM})")
DL_ZENODO_PUBLIC = _t(
    "DL_ZENODO_PUBLIC", "✓ 备选 Zenodo 整包已公开 — [z] 整包下载",
    "✓ alternate Zenodo bundle is public — [z] download the bundle")
DL_ZENODO_FAILED = _t(
    "DL_ZENODO_FAILED", "⚠ 备选 Zenodo 探测失败: {error}（稍后重试）",
    "⚠ alternate Zenodo probe failed: {error} (retry later)")
DL_ZENODO_DISABLED_TOAST = _t(
    "DL_ZENODO_DISABLED_TOAST",
    "Zenodo 记录 19135551 尚未公开 — 公开后此入口自动激活",
    "Zenodo record 19135551 is not public yet — this entry activates "
    "automatically once it publishes")
# The bundle queue row's 任务 cell label + the z keycap's action noun
# (the 备选 framing per the 2026-10-14 ruling).
DL_BUNDLE_TASK_NAME = _t(
    "DL_BUNDLE_TASK_NAME", "zenodo-19135551（整包）",
    "zenodo-19135551 (bundle)")
DL_ZENODO_KEY_LABEL = _t(
    "DL_ZENODO_KEY_LABEL", "备选 Zenodo 整包", "alternate Zenodo bundle")

# Bottom-bar keycap labels (D-15, each ≤ 4 CJK chars; 详情 reuses the
# existing ENV_DETAIL_LABEL — the shared-label precedent, one
# vocabulary for the same verb across screens).
DL_ENQUEUE_LABEL = _t("DL_ENQUEUE_LABEL", "入队", "Enqueue")
DL_RETRY_LABEL = _t("DL_RETRY_LABEL", "重试", "Retry")
DL_CANCEL_LABEL = _t("DL_CANCEL_LABEL", "取消", "Cancel")
DL_ENQUEUE_ALL_LABEL = _t("DL_ENQUEUE_ALL_LABEL", "全部入队", "Enqueue All")
# IN-03 (quick-261016-hhx, the 08 review): slot 3's full-list d-on-
# present-row no-op toast — its OWN DL_ constant (the retired SEL_
# present-toast twin, same values), so the copy lives with its owning
# surface (a slot-2 rewording of the SEL_ block can never drift slot
# 3's dataset wording).
DL_ENQUEUE_PRESENT_TOAST = _t(
    "DL_ENQUEUE_PRESENT_TOAST", "该数据集已在场", "Dataset already present")

# Derived gap-fillers (the SEL_PRESENCE_UNKNOWN precedent — the
# contract names no wording for these rows): the title-line presence
# summary the UI-SPEC layout requires, and the R-02 shape-D
# disabled-with-explanation toast (the drill-down carries the
# download_url — always diagnosable).
DL_PRESENCE_SUMMARY = _t(
    "DL_PRESENCE_SUMMARY", "在场 {present}/{total} · 缺失 {missing}",
    "present {present}/{total} · missing {missing}")
# The full presence view (DCL-03, 261014-dcl): the v-toggle's two
# surfaces — the full-view title (one row per official registry key)
# and the bottom-bar toggle label (the clip policy governs at 80 cols).
DL_PRESENCE_TITLE = _t(
    "DL_PRESENCE_TITLE", "全部数据集 ({n})", "All datasets ({n})")
DL_PRESENCE_TOGGLE_LABEL = _t(
    "DL_PRESENCE_TOGGLE_LABEL", "切换缺失/全部", "Missing/All")
DL_DISABLED_TOAST = _t(
    "DL_DISABLED_TOAST",
    "⚠ {key} 上游为镜像布局，不支持一键下载 — download_url 见详情",
    "⚠ {key} upstream uses a mirror layout with no one-click download — "
    "see download_url in the drill-down")
# WR-06: the channel-unavailable reasons that are NOT the shape-D
# mirror layout (no mirror, malformed values, an unreadable registry)
# get their own neutral toast naming the machine reason — never the
# factually wrong mirror-layout copy.
DL_UNKNOWN_TOAST = _t(
    "DL_UNKNOWN_TOAST", "⚠ {key} 下载通道暂不可用: {reason} — 详情见下钻",
    "⚠ {key} download channel unavailable: {reason} — see the drill-down")

# ===== 下载队列 (QUEUE_, Phase 10, 10-03; D-02..D-09) =====
# The queue table chrome, the five-state cells, the reconcile cells,
# the restart note, the mismatch banner, the toasts, and the two
# destructive cancel confirms (10-UI-SPEC Copywriting Contract
# verbatim).

QUEUE_TITLE = _t(
    "QUEUE_TITLE", "下载队列 ({n}) — 串行 · 状态持久化于 XDG state",
    "Download queue ({n}) — serial · state persisted under XDG state")
QUEUE_COL_TASK = _t("QUEUE_COL_TASK", "任务", "Task")
QUEUE_COL_STATE = _t("QUEUE_COL_STATE", "状态", "State")
QUEUE_COL_PROGRESS = _t("QUEUE_COL_PROGRESS", "进度", "Progress")
QUEUE_COL_RECONCILE = _t("QUEUE_COL_RECONCILE", "行数对账", "Row reconcile")
QUEUE_EMPTY = _t(
    "QUEUE_EMPTY", "队列为空 — 按 [d] 入队缺失数据集",
    "Queue empty — press [d] to enqueue missing datasets")

# The five state cells (D-02 verbatim; glyph+color dual channel — the
# leading glyph is the NO_COLOR carrier). WR-01 (quick-261016-hhx):
# QUEUE_STATE_PENDING en is "◌ waiting" (NOT "◌ pending") —
# ENV_STATE_PENDING already owns en "◌ pending" with a different zh
# (待检 vs 待下载), and the registry must stay injective in BOTH
# directions (the reviewer's example "◌ queued" would collide with
# MON_STATE_QUEUED's ◌ 排队 instead).
QUEUE_STATE_PENDING = _t("QUEUE_STATE_PENDING", "◌ 待下载", "◌ waiting")
QUEUE_STATE_DOWNLOADING = _t(
    "QUEUE_STATE_DOWNLOADING", "⠋ 下载中", "⠋ downloading")
QUEUE_STATE_DONE = _t("QUEUE_STATE_DONE", "✓ 完成", "✓ done")
QUEUE_STATE_FAILED = _t("QUEUE_STATE_FAILED", "✗ 失败", "✗ failed")
QUEUE_STATE_MISMATCH = _t(
    "QUEUE_STATE_MISMATCH", "⚠ 对账不一致", "⚠ reconcile mismatch")

# Reconcile cells (D-09; the running cell covers the automatic
# post-landing transient — auto-default #14).
QUEUE_RECONCILE_PASS = _t(
    "QUEUE_RECONCILE_PASS", "✓ {n} 行一致", "✓ {n} rows match")
QUEUE_RECONCILE_RUNNING = _t(
    "QUEUE_RECONCILE_RUNNING", "⠋ 对账中 …", "⠋ reconciling...")
QUEUE_RECONCILE_MISMATCH = _t(
    "QUEUE_RECONCILE_MISMATCH", "⚠ {n}≠{m}", "⚠ {n}≠{m}")

# Restart recovery note (D-06; dim render on recovered rows).
QUEUE_RESTART_NOTE = _t(
    "QUEUE_RESTART_NOTE", "上次中断 — 通道将续传",
    "interrupted last session — the channel will resume")

# The prominent mismatch banner (D-07/D-09) — 不自动删除 is contract
# wording, never paraphrased.
QUEUE_BANNER_MISMATCH = _t(
    "QUEUE_BANNER_MISMATCH",
    "⚠ 对账不一致 — {key}: n_audit 基线 {n} 行, 实测 {m} 行（不自动删除）",
    "⚠ reconcile mismatch — {key}: n_audit baseline {n} rows, measured "
    "{m} (nothing auto-deleted)")

# Toasts: enqueue feedback, the reconcile-pass presence flip, the
# retry no-op, and the probed CLI-absent state (modelscope stays
# English — a CLI name, never translated).
QUEUE_TOAST_ENQUEUED = _t(
    "QUEUE_TOAST_ENQUEUED", "✓ 已入队: {key}", "✓ enqueued: {key}")
QUEUE_TOAST_ENQUEUED_ALL = _t(
    "QUEUE_TOAST_ENQUEUED_ALL", "✓ 已入队 {n} 个缺失数据集",
    "✓ enqueued {n} missing datasets")
QUEUE_TOAST_ALREADY_QUEUED = _t(
    "QUEUE_TOAST_ALREADY_QUEUED", "{key} 已在队列中",
    "{key} is already in the queue")
QUEUE_FLIP_TOAST = _t(
    "QUEUE_FLIP_TOAST", "✓ {key} 下载完成且对账一致 — 在场已更新",
    "✓ {key} downloaded and reconciled — presence updated")
# The model-lane flip twin (261014-mlc): a done KIND_MODEL entry has NO
# reconcile leg — the honest wording names the 下载 column flip, never
# the dataset lane's 对账一致 claim.
QUEUE_FLIP_TOAST_MODEL = _t(
    "QUEUE_FLIP_TOAST_MODEL", "✓ {key} 模型下载完成 — 下载列已更新",
    "✓ {key} model download complete — download column updated")
QUEUE_RETRY_NOOP = _t(
    "QUEUE_RETRY_NOOP", "仅 失败/对账不一致 项可重试",
    "Only failed / reconcile-mismatch entries can retry")
QUEUE_CLI_UNAVAILABLE = _t(
    "QUEUE_CLI_UNAVAILABLE",
    "✗ modelscope CLI 不可用 — 请先安装 (pip install modelscope)",
    "✗ modelscope CLI unavailable — install it first "
    "(pip install modelscope)")
# WR-04: the refused enqueue when the queue state file cannot be
# written (read-only state root, full disk, quota) — never silent,
# never a lie about the channel.
QUEUE_PERSIST_FAILED_TOAST = _t(
    "QUEUE_PERSIST_FAILED_TOAST",
    "✗ 队列状态写入失败: {key} 未入队 — 检查磁盘空间与权限",
    "✗ queue state write failed: {key} not enqueued — check disk space "
    "and permissions")
# CR-02: the driver-stall companion in the same vocabulary — a CLAIM
# that cannot persist exits the driver (never the claim->refuse->recheck
# livelock); the entry stays pending for the fixed-rail re-kick.
QUEUE_PERSIST_DRIVER_TOAST = _t(
    "QUEUE_PERSIST_DRIVER_TOAST",
    "✗ 队列状态写入失败，驱动已停止: {key} — 修复磁盘/权限后重新入队驱动",
    "✗ queue state write failed, driver stopped: {key} — fix the disk/"
    "permissions, then re-enqueue")

# Progress cell, indeterminate (auto-default #3: never a fabricated
# percent from unparsed output).
QUEUE_PROGRESS_INDETERMINATE = _t(
    "QUEUE_PROGRESS_INDETERMINATE", "⠋ …", "⠋ …")

# Destructive — the two x-cancel confirms (Enter/Esc; the downloading
# copy names the channel's own resume retention, D-06).
QUEUE_CONFIRM_CANCEL_PENDING = _t(
    "QUEUE_CONFIRM_CANCEL_PENDING", "移出队列 {key}？— Enter 移出 / Esc 继续",
    "Remove {key} from the queue? — Enter remove / Esc keep")
QUEUE_CONFIRM_CANCEL_DOWNLOADING = _t(
    "QUEUE_CONFIRM_CANCEL_DOWNLOADING",
    "取消下载 {key}？已下载部分将由通道续传保留 — Enter 取消 / Esc 继续",
    "Cancel the {key} download? Partial data is kept for channel resume "
    "— Enter cancel / Esc keep")

# Derived gap-filler: the x-on-non-cancellable no-op toast (mirrors
# the retry toast's shape; the contract pins the retry row only).
QUEUE_CANCEL_NOOP = _t(
    "QUEUE_CANCEL_NOOP", "仅 待下载/下载中 项可取消",
    "Only pending / downloading entries can be cancelled")

# The g re-audit binding's label (show=False binding, auto-default #7
# — D-15's bottom bar is verbatim without it).
QUEUE_REAUDIT_LABEL = _t("QUEUE_REAUDIT_LABEL", "重新审计", "Re-audit")

# ===== 选择屏 d-入队 amendments (SEL_, Phase 10, 10-03; D-14) =====
# The selection-screen d key is the MODEL download since the 2026-10-14
# slot split (its label + toasts live in the MLC-02 block above); the
# dataset present-row no-op toast moved to the DL_ block at
# 261016-hhx IN-03 (DL_ENQUEUE_PRESENT_TOAST — its owning surface is
# the slot-3 data manager's full-list d; the former SEL_-prefixed name
# is RETIRED).

# ===== 运行配置 (CFG_, Phase 11, D-12) =====
# The slot-4 run-config screen chrome + the params pane + the preview
# line/modal (11-UI-SPEC Copywriting Contract verbatim; 11-06 renders).
# Format fields: {n}/{m} marked counts, {models_total}/{tasks_total}/
# {total} registry totals, {path} a filesystem path, {model}/{mode}/
# {variant} a key or a PEFT/variant value, {models} the dynamic
# PROBE_INELIGIBLE name list (read-source data — the names themselves
# NEVER appear in this module, the spec's own rule), {value} raw
# operator input, {models}/{tasks}/{seeds}/{fractions}/{cells}
# enumeration dimensions, {i}/{n}/{problem} numbered-problem segments.
# 261015-ehc terminology: the zh side says 训练项 where the counts are
# cells (the en side keeps "cells").

CFG_SCREEN_TITLE = _t("CFG_SCREEN_TITLE", "运行配置", "Run Config")
CFG_STATUS_LINE = _t(
    "CFG_STATUS_LINE", "已选: 模型 {n}/{models_total} · 数据集 {m}/{tasks_total}",
    "Selected: {n}/{models_total} models · {m}/{tasks_total} datasets")
CFG_PICKER_MODELS = _t(
    "CFG_PICKER_MODELS", "模型 ({n}/{total})", "Models ({n}/{total})")
CFG_PICKER_DATASETS = _t(
    "CFG_PICKER_DATASETS", "数据集 ({n}/{total})", "Datasets ({n}/{total})")
CFG_PARAMS_TITLE = _t("CFG_PARAMS_TITLE", "参数", "Params")
# Dirs section divider — the full 120-col label and the 80-col short
# variant (params labels shorten at the minimum grid).
CFG_DIRS_TITLE = _t(
    "CFG_DIRS_TITLE", "目录（默认仓库相对; 覆盖即绝对）",
    "Dirs (repo-relative defaults; overrides are absolute)")
CFG_DIRS_TITLE_SHORT = _t("CFG_DIRS_TITLE_SHORT", "目录", "Dirs")

# Params label rows (CFG-01; driver flag vocabulary stays English
# verbatim — seeds / PEFT / epochs are the flags' own names).
CFG_FIELD_SEEDS = _t("CFG_FIELD_SEEDS", "seeds", "seeds")
CFG_FIELD_PEFT = _t("CFG_FIELD_PEFT", "PEFT", "PEFT")
CFG_FIELD_VARIANT = _t("CFG_FIELD_VARIANT", "变体", "Variant")
CFG_FIELD_CURVE = _t("CFG_FIELD_CURVE", "曲线档位", "Curve steps")
CFG_FIELD_SUBSET = _t("CFG_FIELD_SUBSET", "公平子集", "Fair subset")
CFG_FIELD_EPOCHS = _t("CFG_FIELD_EPOCHS", "epochs 覆盖", "epochs override")
# The effective-batch-size label pair: the full 120-col label and the
# 80-col short variant. CFG_FIELD_EBS is a gap-filler (plan-owned, the
# SEL_PRESENCE_UNKNOWN precedent) — the contract names only the SHORT
# row, its parenthetical naming the full label; both live here so
# neither grid paraphrases the field.
CFG_FIELD_EBS = _t(
    "CFG_FIELD_EBS", "effective_batch_size", "effective_batch_size")
CFG_FIELD_EBS_SHORT = _t(
    "CFG_FIELD_EBS_SHORT", "eff_batch_size", "eff_batch_size")
# 261023-abu: the per-device starting batch row — flag vocabulary
# verbatim both languages (the CFG_FIELD_EBS/CFG_FIELD_WORKERS
# precedent); NO short variant (10 chars already fits the narrow
# column that renders the 13-char eff_batch_size). The placeholder
# hint names the child's OWN scaling rule (the CFG_GPUS_DEFAULT
# "—（…）" prompt-hint grammar: fullwidth parens zh, ASCII parens en)
# — an empty field threads NO --batch_size and the child's
# determine_batch_size scales the YAML default by sequence length.
CFG_FIELD_BATCH_SIZE = _t(
    "CFG_FIELD_BATCH_SIZE", "batch_size", "batch_size")
CFG_BATCH_SIZE_DEFAULT = _t(
    "CFG_BATCH_SIZE_DEFAULT", "—（默认: 按序列长度动态缩放）",
    "— (default: scaled by seq length)")
# 261015-ehc terminology: the zh row label for output_root is 结果目录
# (the en side keeps the established "output root").
CFG_FIELD_OUTPUT_ROOT = _t(
    "CFG_FIELD_OUTPUT_ROOT", "结果目录", "output root")
CFG_FIELD_DATASET_ROOT = _t("CFG_FIELD_DATASET_ROOT", "数据集根", "dataset root")
CFG_FIELD_MODEL_ROOT = _t("CFG_FIELD_MODEL_ROOT", "模型根", "model root")
CFG_FIELD_CACHE = _t("CFG_FIELD_CACHE", "模型缓存", "model cache")
# 261014-f4w: the error-log directory row label (the F4W-02 lane).
CFG_FIELD_LOG_DIR = _t("CFG_FIELD_LOG_DIR", "日志目录", "log dir")

# Params value states: the absent dim dash, the cache default, and the
# fairness-subset toggle pair (off / on-with-path). The OFF-with-path
# shape lives here too (WR-08, phase-12 review): the fullwidth
# parentheses are CJK punctuation and must never compose inline in a
# screen module — the I18N-01 single-home contract (the grep lock scans
# the punctuation/fullwidth ranges).
CFG_VALUE_ABSENT = _t("CFG_VALUE_ABSENT", "—", "—")
CFG_CACHE_DEFAULT = _t("CFG_CACHE_DEFAULT", "—（HF 默认）", "— (HF default)")
# 261014-c2l: the storage-root prompt hints (the CFG_CACHE_DEFAULT
# "—（…）" shape) — each documents the flag's default resolution root:
# the pipeline directory, under which models/ and datasets/ live. The
# hint renders as the Input's placeholder while the value is empty
# (the D-19 "./datasets" display default retired with the live flag).
CFG_MODEL_ROOT_DEFAULT = _t(
    "CFG_MODEL_ROOT_DEFAULT", "—（默认 pipeline/）", "— (default pipeline/)")
CFG_DATASET_ROOT_DEFAULT = _t(
    "CFG_DATASET_ROOT_DEFAULT", "—（默认 pipeline/）",
    "— (default pipeline/)")
# 261014-f4w: the log-dir prompt hint — the flag's default resolution
# is the ./logs dir under the pipeline working directory, documented as
# pipeline/logs/ (the CFG_MODEL_ROOT_DEFAULT "—（…）" shape).
CFG_LOG_DIR_DEFAULT = _t(
    "CFG_LOG_DIR_DEFAULT", "—（默认 pipeline/logs/）",
    "— (default pipeline/logs/)")
CFG_SUBSET_OFF = _t("CFG_SUBSET_OFF", "关", "off")
CFG_SUBSET_OFF_WITH_PATH = _t(
    "CFG_SUBSET_OFF_WITH_PATH", "关（{path}）", "off ({path})")
CFG_SUBSET_ON = _t("CFG_SUBSET_ON", "开（{path}）", "on ({path})")

# Derived hint lines (dim, 1 row under their field — the wizard
# advisory pattern). The head note's two names are the head-alias
# frozen pair the contract words verbatim (static copy); the
# PROBE_INELIGIBLE 9-name list is DATA rendered through {models} only.
CFG_PEFT_ALIAS_PREVIEW = _t(
    "CFG_PEFT_ALIAS_PREVIEW", "别名预览: {model}+{mode}（独立输出目录与续跑标记）",
    "Alias preview: {model}+{mode} (separate output dir and resume "
    "markers)")
CFG_VARIANT_ALIAS_PREVIEW = _t(
    "CFG_VARIANT_ALIAS_PREVIEW", "保存名: {model}+{variant}",
    "Save name: {model}+{variant}")
CFG_VARIANT_HEAD_NOTE = _t(
    "CFG_VARIANT_HEAD_NOTE", "head: evo2_1b_base / megaDNA_updated 保留基名",
    "head: evo2_1b_base / megaDNA_updated keep the base name")
CFG_VARIANT_PROBE_HINT = _t(
    "CFG_VARIANT_PROBE_HINT", "⚠ probe 不可用: {models}（专用 loader, 冻结不生效）",
    "⚠ probe unavailable: {models} (dedicated loaders; freezing does "
    "not apply)")

# Numbered-problem segments — the preview line, the [p] modal, and the
# gate share the gauntlet collect-all shape.
CFG_PROBE_INELIGIBLE_PROBLEM = _t(
    "CFG_PROBE_INELIGIBLE_PROBLEM", "{model}: probe 不可用（专用 loader）",
    "{model}: probe unavailable (dedicated loader)")
# Gap-filler (plan-owned, the SEL_PRESENCE_UNKNOWN precedent): the
# variant×PEFT composition refusal the 11-01 driver enforces and 11-02
# validates — mirrored as a preview problem (cheap composition-time
# prevention; the child stays authoritative).
CFG_COMPOSITION_PROBLEM = _t(
    "CFG_COMPOSITION_PROBLEM", "变体与 PEFT 不可同时启用（别名轴互斥）",
    "Variant and PEFT cannot be enabled together (mutually exclusive "
    "alias axes)")
CFG_SEEDS_INVALID_PROBLEM = _t(
    "CFG_SEEDS_INVALID_PROBLEM", "seeds 需为逗号分隔整数: {value}",
    "seeds must be comma-separated integers: {value}")
CFG_CURVE_INVALID_PROBLEM = _t(
    "CFG_CURVE_INVALID_PROBLEM", "曲线档位需为 (0, 1] 内的小数列表: {value}",
    "Curve steps must be a list of decimals in (0, 1]: {value}")
CFG_EMPTY_SELECTION_PROBLEM = _t(
    "CFG_EMPTY_SELECTION_PROBLEM", "未选择模型或数据集",
    "No models or datasets selected")
# WR-07 (phase-11 review): an output root resolving to the filesystem
# root — the E2' expected phrase would be empty (fail-closed boundary)
# and cells would land directly under /. 261015-ehc terminology: the zh
# wording names 二次确认 (the typed-phrase gate's new zh word) and 训练项.
CFG_OUTPUT_ROOT_PROBLEM = _t(
    "CFG_OUTPUT_ROOT_PROBLEM",
    "结果目录不可为文件系统根目录（二次确认与训练项布局均失效）: {value}",
    "The output root must not be the filesystem root (both the "
    "typed-phrase gate and the cell layout break): {value}")

# The live preview line (both shapes — the curve lane adds × 档) and
# the problems header/line shape shared by the line and the [p] modal.
CFG_PREVIEW_LINE = _t(
    "CFG_PREVIEW_LINE",
    "干跑: {models} 模型 × {tasks} 任务 × {seeds} 种子 = {cells} 训练项",
    "Dry run: {models} models × {tasks} tasks × {seeds} seeds = "
    "{cells} cells")
CFG_PREVIEW_LINE_CURVE = _t(
    "CFG_PREVIEW_LINE_CURVE",
    "干跑: {models} 模型 × {tasks} 任务 × {seeds} 种子 × {fractions} 档 = {cells} 训练项",
    "Dry run: {models} models × {tasks} tasks × {seeds} seeds × "
    "{fractions} steps = {cells} cells")
CFG_PREVIEW_PROBLEMS = _t(
    "CFG_PREVIEW_PROBLEMS", "⚠ 预览校验失败 — 共 {n} 处问题：",
    "⚠ preview validation failed — {n} problems:")
CFG_PREVIEW_PROBLEM_LINE = _t(
    "CFG_PREVIEW_PROBLEM_LINE", "{i}. {problem}", "{i}. {problem}")
CFG_PREVIEW_MODAL_TITLE = _t(
    "CFG_PREVIEW_MODAL_TITLE", "干跑预览", "Dry-run preview")
CFG_PREVIEW_NOTE = _t(
    "CFG_PREVIEW_NOTE", "同源: pipeline.run_sweep.enumerate_matrix（零复制）",
    "Same source: pipeline.run_sweep.enumerate_matrix (zero copies)")
CFG_ARGV_LABEL = _t("CFG_ARGV_LABEL", "argv（LIST）:", "argv (LIST):")

# 261014-f4w (F4W-03): the [s] save-as-defaults action — atomically
# writes the five dir values to directories.json and toasts the written
# path; the dim hint line states the restore-defaults copy (static —
# the toast already carries the concrete path).
CFG_SAVE_DEFAULTS_LABEL = _t(
    "CFG_SAVE_DEFAULTS_LABEL", "保存默认", "Save Defaults")
CFG_SAVE_DEFAULTS_TOAST = _t(
    "CFG_SAVE_DEFAULTS_TOAST", "已保存默认目录: {path}",
    "Saved default dirs: {path}")
# Rule-2 gap-filler: the save-failure twin of the success toast,
# {error} data (the SEL_PRESENCE_UNKNOWN precedent).
CFG_SAVE_DEFAULTS_FAILED_TOAST = _t(
    "CFG_SAVE_DEFAULTS_FAILED_TOAST", "✗ 保存默认目录失败: {error}",
    "✗ failed to save default dirs: {error}")
CFG_SAVE_DEFAULTS_HINT = _t(
    "CFG_SAVE_DEFAULTS_HINT", "恢复默认：删除配置文件或清空各目录后保存",
    "Restore defaults: delete the config file, or clear every dir and "
    "save")
# 261014-f4w (F4W-05): the ctrl+o directory picker over textual core's
# DirectoryTree — the modal's border title names the field being picked
# ({field} the row's CFG_FIELD label) and the f footer label selects
# the cursor's directory.
CFG_DIR_PICKER_LABEL = _t("CFG_DIR_PICKER_LABEL", "选目录", "Pick Dir")
CFG_DIR_PICKER_TITLE = _t(
    "CFG_DIR_PICKER_TITLE", "选择目录 — {field}",
    "Pick a directory — {field}")
CFG_DIR_PICKER_SELECT_LABEL = _t(
    "CFG_DIR_PICKER_SELECT_LABEL", "选此目录", "Select Dir")
# The slot-4 persistent dim hint line below the preview (UX-4,
# 261016-poa): the enter/Y/N affordances are otherwise hidden bindings
# — this row makes the launch-confirmation entry discoverable.
CFG_GATE_HINT = _t(
    "CFG_GATE_HINT", "回车 打开启动确认 · Y 启动 / N 取消",
    "Enter opens launch confirmation · Y launch / N cancel")
# Phase 16 (16-04, TUI-02, D16-15): the multi-GPU dispatch params
# section (UI-SPEC C.1) — the section title pair (the CFG_DIRS_TITLE
# narrow-grid mechanism), the workers/GPUs field labels (flag
# vocabulary English verbatim in both languages, the seeds/PEFT rule),
# the GPUs all-detected placeholder (the CFG_CACHE_DEFAULT "—（…）"
# prompt-hint grammar), the dim hint row, and the three collect-all
# problem mirrors (C.3 — cheap pre-filters; the shard CLI stays the
# validation authority, Pattern 7). {value} is raw operator input;
# {workers}/{n} are the structured workers_exceeds_gpus pair (16-03's
# format-ready (workers, gpu_count) detail).
CFG_MGPU_TITLE = _t(
    "CFG_MGPU_TITLE", "多 GPU 调度", "Multi-GPU dispatch")
# The 80-col short variant. NOTE: the en side diverges from the
# UI-SPEC table's "GPUs" BY THE REGISTRY INJECTIVITY LAW —
# MON_GPU_TITLE already owns the en value "GPUs" (zh GPU 状态), and the
# same-en-implies-same-zh tripwire forbids a second zh for one en;
# "Multi-GPU" is the natural shortening of the 120-col title (exactly
# how CFG_DIRS_TITLE_SHORT "Dirs" shortens "Dirs (repo-relative…)").
CFG_MGPU_TITLE_SHORT = _t(
    "CFG_MGPU_TITLE_SHORT", "多卡", "Multi-GPU")
CFG_FIELD_WORKERS = _t("CFG_FIELD_WORKERS", "workers", "workers")
# NOTE: the en side spells the flag's OWN lowercase form "gpus" — the
# UI-SPEC table's en "GPUs" is impossible under the registry
# injectivity law (MON_GPU_TITLE owns en "GPUs" with zh GPU 状态, and
# same-en-implies-same-zh forbids a second zh); the lowercase spelling
# is exactly the --gpus flag vocabulary (the CFG_FIELD_SEEDS "seeds"
# precedent) and the zh side stays the table's verbatim "GPUs".
CFG_FIELD_GPUS = _t("CFG_FIELD_GPUS", "GPUs", "gpus")
# WR-03 (phase-16 review): the default copy names the child's OWN
# resolution rule — an empty field threads NO --gpus and dispatch_core
# binds the FIRST ``workers`` GPU indices (range(workers)), never all
# detected GPUs; "workers" is the sibling FIELD name (a static
# placeholder, not interpolated).
CFG_GPUS_DEFAULT = _t(
    "CFG_GPUS_DEFAULT", "—（默认: GPU 0..workers-1）",
    "— (default: GPUs 0..workers-1)")
CFG_MGPU_HINT = _t(
    "CFG_MGPU_HINT", "workers = 并发训练项数（一卡一项）",
    "workers = concurrent cells (one per GPU)")
CFG_WORKERS_INVALID_PROBLEM = _t(
    "CFG_WORKERS_INVALID_PROBLEM", "workers 需为 ≥1 的整数: {value}",
    "workers must be an integer >= 1: {value}")
CFG_GPUS_INVALID_PROBLEM = _t(
    "CFG_GPUS_INVALID_PROBLEM", "GPUs 需为逗号分隔的非负整数: {value}",
    "GPUs must be comma-separated non-negative integers: {value}")
CFG_WORKERS_EXCEED_GPUS_PROBLEM = _t(
    "CFG_WORKERS_EXCEED_GPUS_PROBLEM", "workers ({workers}) 超过 GPU 数量 ({n})",
    "workers ({workers}) exceeds the GPU count ({n})")

# ===== 启动确认/执行 (LNC_, Phase 11) =====
# The [enter] launch-confirmation pipeline, the E2' typed-phrase
# escalation (LNC-03 — the maintainer-authorization boundary, never
# bypassable from the UI), the launch toasts, and the app-level exit
# modal's kill/detach/cancel row (11-UI-SPEC Copywriting Contract
# verbatim; 11-06 renders). Format fields: {models}/{tasks}/{seeds}/
# {cells} enumeration dimensions, {output_root}/{root} the resolved
# output root, {dirname} the E2' typed phrase (this run's output
# directory name), {error} a spawn diagnostic, {done}/{total}
# live-sweep counts.
# 261015-ehc terminology: the zh side says 训练任务/训练项 (the en side
# keeps the established sweep/cells wording). 261016-poa (UX-3): the
# old gate title term retired everywhere living — the title now
# reads 启动确认 / Launch Confirmation; 261016-poa (UX-5/UX-6): the
# confirm modal lists the planned {model} × {task} pairs (12 + total
# line) and the copy names the [Y]/[N] pair.

LNC_GATE_TITLE = _t("LNC_GATE_TITLE", "启动确认", "Launch Confirmation")
LNC_GATE_SUMMARY = _t(
    "LNC_GATE_SUMMARY",
    "{models} 模型 × {tasks} 任务 × {seeds} 种子 = {cells} 训练项 → {output_root}",
    "{models} models × {tasks} tasks × {seeds} seeds = {cells} cells "
    "→ {output_root}")
LNC_GATE_CONFIRM = _t(
    "LNC_GATE_CONFIRM", "确认启动以上训练？— [Y] 启动 / [N] 取消",
    "Launch these training runs? — [Y] launch / [N] cancel")
# 261017-dnr (DNR-1): the launch-confirm Footer keycap for the y answer
# key — mirroring the message's [Y] word so the answer is visible at a
# glance (the 261017-cdr QuitConfirmModal precedent). Verified: NO
# identical 启动/Launch pair exists anywhere in the registry (a new
# pair, both injectivity tripwires stay green); the n side reuses
# LNC_EXIT_CONFIRM_NO (its 取消/Cancel pair is exact — the WIZ_BACK
# identical-pair precedent, zero new constant for n).
LNC_GATE_CONFIRM_YES = _t(
    "LNC_GATE_CONFIRM_YES", "启动", "Launch")
# The confirm modal's planned-pair list (UX-5): one 模型+数据集 pair per
# line, service-derived from the fresh preview cells (seeds stay in the
# counts formula above, never per-row); language-neutral copy. Large
# lists cap at the first 12 pairs + the {pairs} total line.
LNC_GATE_PAIR_LINE = _t(
    "LNC_GATE_PAIR_LINE", "{model} × {task}", "{model} × {task}")
LNC_GATE_PAIRS_MORE = _t(
    "LNC_GATE_PAIRS_MORE", "…共 {pairs} 组", "… {pairs} pairs total")
# Phase 16 (16-04, TUI-02, D16-11): the dispatch-plan preview line —
# the ONE confirm-face addition, rendered on BOTH faces (the Y/N
# confirm above the pair list, the E2' typed-phrase modal above the
# warning block; auto-default #12). {workers}/{gpus}/{cells} arrive
# service-side through GateSummary (the modal renders, never
# computes): {gpus} is the typed list or the all({n}) resolution rule
# with the detected count at preview time (auto-default #8 — the
# default resolves at LAUNCH, the preview names the rule + live
# count, never a guess in place of data); {cells} is the SAME fresh
# same-source preview enumeration the summary line already shows
# (auto-default #7 — no dry-run subprocess enters the gate path); the
# trailing （预览）/(preview) marks the honest preview (resume-marker
# skips can only shrink the real queue; once running,
# dispatch_state.json is the truth).
LNC_GATE_DISPATCH_LINE = _t(
    "LNC_GATE_DISPATCH_LINE",
    "调度计划: {workers} workers × GPUs {gpus} · 排队 {cells} 训练项（预览）",
    "Dispatch plan: {workers} workers × GPUs {gpus} · {cells} cells "
    "queued (preview)")
# The E2' escalation block (terraform-style typed phrase): the frozen
# full-matrix warning wording, the authorization note, the type prompt,
# and the live mismatch/match indicator pair.
LNC_E2_WARNING = _t(
    "LNC_E2_WARNING",
    "⚠ 全量 E2' 训练任务 — 59 模型 × 50 数据集 × 3 种子 = 8850 训练项",
    "⚠ Full E2' sweep — 59 models × 50 datasets × 3 seeds = 8850 cells")
LNC_E2_AUTH_NOTE = _t(
    "LNC_E2_AUTH_NOTE", "需维护者显式授权（LNC-03; 判定与短语校验不可绕过）",
    "Requires explicit maintainer authorization (LNC-03; the verdict "
    "and the phrase check cannot be bypassed)")
LNC_E2_TYPE_PROMPT = _t(
    "LNC_E2_TYPE_PROMPT", "输入本次输出目录名以确认: {dirname}",
    "Type this run's output directory name to confirm: {dirname}")
LNC_E2_MATCH_OK = _t(
    "LNC_E2_MATCH_OK", "✓ 目录名匹配 — [Y] 启动 / [N] 取消",
    "✓ dirname matches — [Y] launch / [N] cancel")
LNC_E2_MISMATCH = _t(
    "LNC_E2_MISMATCH", "✗ 目录名不一致 — 请完整输入 {dirname}",
    "✗ dirname mismatch — type {dirname} in full")
# The env-block modal's route hint (composes with ENV_QUICK_CHECK_FAIL —
# reused verbatim; no new copy for the verdict itself).
LNC_ENV_BLOCKED_HINT = _t(
    "LNC_ENV_BLOCKED_HINT", "[1] 前往环境检查", "[1] open Environment Check")
# EHC-3 (261015-ehc ruling 3), amended in place by 16-03 (D16-10, the
# MON_RERUN_CONFIRM amendment precedent — the constant NAME is
# unchanged; gate-order tests and every format site reference it): the
# single-GPU serialization refusal became MULTI-GPU capacity
# arithmetic — the wording adds the requested {workers} and the
# machine's {n} GPUs beside the live {roots}, all computed
# service-side in the GpuCapacityBlock. The zh wording applies the
# terminology table (训练任务 / workers / GPU stay verbatim).
LNC_SINGLE_GPU_BLOCKED = _t(
    "LNC_SINGLE_GPU_BLOCKED",
    "⚠ GPU 容量不足 — 运行中训练任务（{roots}）+ 本次 {workers} workers "
    "超过 {n} GPU：请等待完成、经退出门终止，或减少 workers",
    "⚠ GPU capacity exceeded — live sweeps ({roots}) + {workers} workers "
    "requested exceed the {n} GPUs: wait, kill via the exit modal, or "
    "lower workers")
# Launch feedback: success (toast + auto-nav to the monitor) and the
# spawn-failure toast ({error} is data).
LNC_LAUNCH_TOAST = _t(
    "LNC_LAUNCH_TOAST",
    "✓ 训练任务已启动（分离）— {cells} 训练项 → {output_root} · 跳转任务监控",
    "✓ sweep launched (detached) — {cells} cells → {output_root} · "
    "switching to the monitor")
LNC_LAUNCH_FAILED_TOAST = _t(
    "LNC_LAUNCH_FAILED_TOAST", "✗ 启动失败: {error}",
    "✗ launch failed: {error}")
# The app-level exit modal (D-06): one row, three keys, default detach.
LNC_EXIT_TITLE = _t("LNC_EXIT_TITLE", "退出", "Quit")
LNC_EXIT_MESSAGE = _t(
    "LNC_EXIT_MESSAGE",
    "运行中的训练任务: 完成 {done}/{total}（{root}）— "
    "[enter] 分离退出（默认） / [k] 终止后退出 / [esc] 返回",
    "Running sweep: {done}/{total} done ({root}) — "
    "[enter] detach & exit (default) / [k] kill & exit / [esc] back")
# WR-05 (11-08 gap closure): the MULTI-live-sweep form — names EVERY
# live root (full resolved paths joined; basenames collide — two
# "finetuned" roots are the triggering scenario) with the count, and
# deliberately DROPS the done/total fields (per-root counts from one
# attached root would mix sources). [k]/[enter] act on ALL live roots.
LNC_EXIT_MESSAGE_MULTI = _t(
    "LNC_EXIT_MESSAGE_MULTI",
    "运行中的训练任务: {n} 个（{roots}）— "
    "[enter] 分离退出（默认） / [k] 终止后退出 / [esc] 返回",
    "Running sweeps: {n} ({roots}) — "
    "[enter] detach & exit (default) / [k] kill & exit / [esc] back")
# 261016-v0z (the maintainer's always-confirm ruling: 退出的时候要确认，
# 不能一按q就直接退出了): the no-sweep quit-confirm row — the [Y]/[N]
# pair mirrors LNC_GATE_CONFIRM; y is the ONLY confirm key (enter is
# structurally inert, EHC-2), n/esc cancel. The live-sweep ExitModal
# above keeps its own kill/detach/cancel triple unchanged.
LNC_EXIT_CONFIRM = _t(
    "LNC_EXIT_CONFIRM", "确认退出控制台？— [Y] 退出 / [N] 取消",
    "Quit the console? — [Y] quit / [N] cancel")
# 261017-cdr (CDR-3): the QuitConfirmModal Footer keycaps for the y/n
# answer keys — mirroring the message's [Y]/[N] words so the answers
# are visible at a glance. Identical registry pairs already exist
# (退出/Quit as APP_QUIT_LABEL/LNC_EXIT_TITLE, 取消/Cancel as
# WIZ_CANCEL_LABEL/DL_CANCEL_LABEL — the WIZ_BACK identical-pair
# precedent), so both bidirectional injectivity tripwires stay green.
LNC_EXIT_CONFIRM_YES = _t(
    "LNC_EXIT_CONFIRM_YES", "退出", "Quit")
LNC_EXIT_CONFIRM_NO = _t(
    "LNC_EXIT_CONFIRM_NO", "取消", "Cancel")
# 261017-dnr (DNR-4): the ExitModal Footer keycaps for the enter/k
# action keys — the zh/en wording lifted VERBATIM from the
# LNC_EXIT_MESSAGE / LNC_EXIT_MESSAGE_MULTI copy so the keycaps say
# exactly what the message says (terminology already approved in the
# message constants; visibility only — enter remains the detach-and-exit
# default, the Phase-11 design). Verified: no identical pairs exist for
# either (both injectivity tripwires stay green).
LNC_EXIT_DETACH_KEYCAP = _t(
    "LNC_EXIT_DETACH_KEYCAP", "分离退出", "detach & exit")
LNC_EXIT_KILL_KEYCAP = _t(
    "LNC_EXIT_KILL_KEYCAP", "终止后退出", "kill & exit")

# ===== 任务监控 (MON_, Phase 11) =====
# The slot-5 monitor screen chrome, the discovered-sweep pane, the cell
# table + its five per-seed states, the stats/ETA variants, the failure
# list + gated re-run, the log tail, the attach flow, and the rescan
# toast (11-UI-SPEC Copywriting Contract verbatim; 11-07 renders).
# Format fields: {n} counts, {root} the attached output root, {seed} a
# configured seed, {done}/{total}/{model}/{task}/{elapsed}/{eta} the
# stats segments, {lo}/{hi} the ETA range, {model}/{task} full keys,
# {path} the tee file or attach path, {cells} a launch count,
# {fraction}/{state} the per-fraction detail pair. Reused verbatim from
# earlier phases (no new constants): the QUEUE_* progress-bar cell
# grammar, ENV_DETAIL_LABEL 详情, APP_MODAL_BACK_LABEL 返回, the WIZ_*
# path advisories, ENV_QUICK_CHECK_FAIL/PASS.
# 261015-ehc terminology: the zh side says 训练任务 (sweep), 训练项
# (cell), 结果目录 (output root), and 监控 (attach) per the approved
# table — attach SEMANTICS are untouched, only the zh word changed.

MON_SCREEN_TITLE = _t("MON_SCREEN_TITLE", "任务监控", "Monitor")
MON_SCAN_NOTE = _t(
    "MON_SCAN_NOTE", "扫描: 前沿 2s · 全扫 60s", "Scan: frontier 2s · full 60s")
# ===== 261018-kvj (the maintainer's 2026-10-18 15:01 tabbed contract) =====
# The two-tab vocabulary replaces the discovered/cells master-detail pair
# (WINDOWS #40 closed BY the redesign): the presentation unit is ONE RUN
# (一次运行) — a live handle on 正在运行/Running, a terminal or interrupted
# run on 历史/History. The old MON_DISCOVERED_*/MON_CELLS_* master-detail
# copy (and its 发现 machine vocabulary) is DELETED, not kept beside the
# tabs. sweep_failures.json stays verbatim where it appears (a filename —
# data, never machine vocabulary).
MON_TAB_RUNNING = _t("MON_TAB_RUNNING", "正在运行", "Running")
MON_TAB_HISTORY = _t("MON_TAB_HISTORY", "历史", "History")
# The tab-count badge both tab titles render — data composition.
MON_TAB_COUNT = _t("MON_TAB_COUNT", "({n})", "({n})")
# 261018-kvj #41 (optimistic first paint): the standing note that paints
# at mount BEFORE the first scan lands — skeleton + note only, never a
# fabricated row; the first scan message clears it.
MON_SCANNING = _t("MON_SCANNING", "扫描中…", "Scanning…")
# The Running tab's actionable empty state: enter routes to slot 4 (the
# ONLY launch gate — slot 5 never duplicates it).
MON_RUNNING_EMPTY = _t(
    "MON_RUNNING_EMPTY", "暂无运行中任务 — 回车打开启动确认",
    "No running tasks — press Enter to open the launch confirm")
MON_HISTORY_EMPTY = _t(
    "MON_HISTORY_EMPTY", "暂无历史运行", "No past runs yet")
# The tab-switch keys (left/right/tab) — one keycap for the footer row.
MON_TAB_SWITCH_KEYCAP = _t(
    "MON_TAB_SWITCH_KEYCAP", "切换页签", "switch tab")

# The running card's 261019-f0x surface: the summary strip's elapsed/
# ETA/rate segments + the History row's dual-presence badge (a live
# re-run over a root that carries prior history). The four retired
# card-line constants (MON_CARD_SCALE / MON_SCALE_UNKNOWN /
# MON_CARD_CURRENT / MON_CARD_CURRENT_NONE) left with the surface that
# worded them (the kvj retirement precedent — the strip + matrix
# redesign deleted their lines).
MON_HISTORY_RERUN_BADGE = _t(
    "MON_HISTORY_RERUN_BADGE", "重跑进行中", "re-run in progress")

# 261019-f0x (the maintainer's 2026-10-18 10:48 slot-5 redesign: 方案 B
# 为骨架 + 方案 D 的右栏): the B-skeleton summary strip's data segments —
# {t} the minute-granularity elapsed, {eta}+{clock} the point ETA with
# its wall-clock landing, {lo}/{hi} the multi-root min–max range, and
# {rate} the derived it/s (pure arithmetic over parsed service fields,
# never a new service read) — plus the [w] wide-toggle keycap (the k9s
# narrow/wide precedent). One block, one tripwire edit.
MON_STRIP_ELAPSED = _t("MON_STRIP_ELAPSED", "耗时 {t}", "elapsed {t}")
MON_STRIP_ETA = _t(
    "MON_STRIP_ETA", "预计 {eta}（{clock}）", "ETA {eta} ({clock})")
MON_STRIP_ETA_RANGE = _t(
    "MON_STRIP_ETA_RANGE", "预计 {lo}–{hi}", "ETA {lo}–{hi}")
MON_STRIP_RATE = _t("MON_STRIP_RATE", "{rate} it/s", "{rate} it/s")
# 261019-n0w: the D right pane's step/max line — zh IDENTICAL to en
# (the data-forward MON_COL_SEED / MON_STRIP_RATE precedent: step and
# max are checkpoint numbers, no new terminology enters the zh table).
MON_DETAIL_STEPS = _t(
    "MON_DETAIL_STEPS", "step {step}/{max}", "step {step}/{max}")
MON_WIDE_KEYCAP = _t("MON_WIDE_KEYCAP", "宽表", "wide")
# 261019-pe0: the [*] tree-state keycap (expand ALL / collapse ALL — the
# locked nav contract; Running-tab-effective, silent elsewhere — the d/e/w
# precedent). zh/en data-forward-terse: ± carries expand/collapse, 全部
# is "all" — no new terminology enters the zh table.
MON_TREE_TOGGLE_KEYCAP = _t(
    "MON_TREE_TOGGLE_KEYCAP", "± 全部", "± all")

# 261018-kvj Task 2: the graduation toasts — a run the screen OBSERVED
# running that reaches a terminal state between two on-screen scans
# graduates (card leaves Running, a History row appears, the toast names
# the run). Screen-local by design: a finish while another screen is up
# graduates silently on the next visit (honest, no stale toast).
MON_GRADUATED_DONE_TOAST = _t(
    "MON_GRADUATED_DONE_TOAST", "✓ 运行完成 — 已移入历史：{root}",
    "✓ run finished — moved to History: {root}")
MON_GRADUATED_INTERRUPTED_TOAST = _t(
    "MON_GRADUATED_INTERRUPTED_TOAST", "⏸ 运行中断 — 已移入历史：{root}",
    "⏸ run interrupted — moved to History: {root}")

# The cell table: title + the resume note riding the same title row
# (MON-05 standing chrome, never a scrolling toast), the empty state,
# the column headers, the five per-seed cell states, and both
# resume-note variants (the 80-col one drops the trainer_state reason).
# C4J-3 (261015-c4j): the table is the model×dataset ENTRIES list —
# the 状态 column carries the folded state word + the done/total seed
# counts, the 进度 column the training progress (steps + percent + bar
# on running rows, the honest indeterminate when nothing parses).
# The run drill modal (enter on a card or a History row): the snapshot
# title + the column headers the per-run cells table reuses (model,
# task, the five per-seed states, progress). 261018-kvj: the always-
# visible cells table is gone — the drill is a read-once snapshot
# (the LogTailModal read-once precedent).
MON_RUN_CELLS_TITLE = _t(
    "MON_RUN_CELLS_TITLE", "训练项 — {root}", "cells — {root}")
MON_COL_ROOT = _t("MON_COL_ROOT", "结果目录", "output root")
MON_COL_PROGRESS = _t("MON_COL_PROGRESS", "进度", "Progress")
MON_COL_ACTIVITY = _t("MON_COL_ACTIVITY", "最近活动", "latest activity")
MON_COL_MODEL = _t("MON_COL_MODEL", "模型", "Models")
MON_COL_TASK = _t("MON_COL_TASK", "任务", "Task")
MON_COL_SEED = _t("MON_COL_SEED", "s{seed}", "s{seed}")
MON_COL_STATE = _t("MON_COL_STATE", "状态", "State")
MON_STATE_QUEUED = _t("MON_STATE_QUEUED", "◌ 排队", "◌ queued")
# 261017-uwr (UWR-1/UWR-4): the running glyph joins the ruling's ⏵/✓/⏸
# triple so header and table carry the SAME glyph for the same state.
MON_STATE_RUNNING = _t("MON_STATE_RUNNING", "⏵ 运行", "⏵ running")
MON_STATE_DONE = _t("MON_STATE_DONE", "✓ 完成", "✓ done")
MON_STATE_FAILED = _t("MON_STATE_FAILED", "✗ 失败", "✗ failed")
MON_STATE_SKIPPED = _t("MON_STATE_SKIPPED", "⊘ 跳过", "⊘ skipped")
# 261017-uwr (UWR-1): the third state — no record, no marker, and no
# live sweep plans the pair (kill-left checkpoint residue / stale
# dirs). Honest history, never a phantom running glyph (WINDOWS #34).
MON_STATE_INTERRUPTED = _t(
    "MON_STATE_INTERRUPTED", "⏸ 中断", "⏸ interrupted")
MON_RESUME_NOTE = _t(
    "MON_RESUME_NOTE", "⊘ 续跑: {n} 训练项 因 trainer_state 标记跳过",
    "⊘ resume: {n} cells skipped via trainer_state markers")
# The 80-col resume-note variant (the contract's parenthetical wording;
# derived constant name — the table words the copy, not a second name).
MON_RESUME_NOTE_SHORT = _t(
    "MON_RESUME_NOTE_SHORT", "⊘ 续跑: {n} 训练项 跳过",
    "⊘ resume: {n} cells skipped")

# The entries list's progress cell (C4J-3): the steps+percent data-word
# composition (the 10-cell bar appends in code — the data_manager
# progress grammar), the honest indeterminate for running rows whose
# checkpoint trainer_state parses nothing (never a fabricated number),
# and the done/total seed-counts segment appended to the state word.
MON_PROGRESS_STEPS = _t(
    "MON_PROGRESS_STEPS", "{step}/{max} {percent}%", "{step}/{max} {percent}%")
# 261017-uwr: the running row's indeterminate cell rides the ⏵ glyph
# (the state cell's own glyph — one glyph per state across the row).
MON_PROGRESS_INDETERMINATE = _t(
    "MON_PROGRESS_INDETERMINATE", "⏵ …", "⏵ …")
MON_ENTRY_SEED_COUNTS = _t(
    "MON_ENTRY_SEED_COUNTS", "{done}/{total}", "{done}/{total}")

# 261018-kvj: the D-17 stats line + the ETA pending/range variants are
# RETIRED with the master-detail surface — the running card carries the
# current-cell line (per-cell progress/ETA via the checkpoint-pair
# grammar) and the done/total bar; MON_TOTAL_UNKNOWN/MON_ETA_UNKNOWN
# survive as the honest degradations the card/history cells render.
MON_TOTAL_UNKNOWN = _t("MON_TOTAL_UNKNOWN", "总数未知", "total unknown")
MON_ETA_UNKNOWN = _t("MON_ETA_UNKNOWN", "—", "—")

# The [f] failure list (MON-03/D-11): title, the happy zero, the row
# shape, the gated re-run keycap + confirm + toast. The zh count
# wording says 训练项 (the en side keeps "cells"); sweep_failures.json
# is a filename and stays verbatim in both languages.
MON_FAILURES_TITLE = _t(
    "MON_FAILURES_TITLE", "失败清单 ({n}) — sweep_failures.json",
    "Failures ({n}) — sweep_failures.json")
# CR-01 (quick-261016-hhx, 08 review): the [f] keycap's OWN registry
# constant — byte-equal to the old MON_FAILURES_TITLE.split(" (")[0]
# projection in BOTH languages, so the zh goldens stay byte-identical —
# replacing the consuming module's split() substring, which never
# byte-matched any registry value and therefore could not translate
# under remap_binding_descriptions.
MON_FAILURES_KEYCAP = _t("MON_FAILURES_KEYCAP", "失败清单", "Failures")
MON_FAILURES_EMPTY = _t(
    "MON_FAILURES_EMPTY", "✓ 无失败训练项", "✓ no failed cells")
MON_FAILURE_ROW = _t(
    "MON_FAILURE_ROW", "{model} × {task} × seed_{seed}",
    "{model} × {task} × seed_{seed}")
MON_RERUN_LABEL = _t("MON_RERUN_LABEL", "重跑失败", "Re-run Failed")
# AMENDED in place (11-08 gap closure, WR-03): the confirm names the
# PLANNED-CELL estimate — {pairs} distinct (model, task) failure pairs
# × the {seeds} fan-out = {n} cells, the exact enumeration
# launch_from_failures performs — replacing the entry-count {n} form
# that understated a multi-seed re-run's GPU spend ~3x. The constant
# NAME is unchanged (its registered inventory entry stands).
MON_RERUN_CONFIRM = _t(
    "MON_RERUN_CONFIRM",
    "重跑 {pairs} 个失败组合 × 种子 {seeds} = {n} 个训练项（--from-failures）"
    "？— [y] 重跑 / Esc 取消",
    "Re-run {pairs} failed pairs × seeds {seeds} = {n} cells "
    "(--from-failures)? — [y] re-run / Esc cancel")
MON_RERUN_TOAST = _t(
    "MON_RERUN_TOAST", "✓ 失败重跑已启动 — {cells} 训练项 → {root}",
    "✓ failure re-run launched — {cells} cells → {root}")
# WR-02 (11-08 gap closure): the refuse-loudly reason for an
# underivable re-run seed set (no leading glyph — it composes under
# LNC_LAUNCH_FAILED_TOAST's ✗ prefix).
MON_RERUN_NO_SEEDS = _t(
    "MON_RERUN_NO_SEEDS", "无法推导重跑种子（失败记录与训练项表均无种子）— 已拒绝重跑",
    "Cannot derive re-run seeds (no seeds in the failures or the cell "
    "rows) — re-run refused")

# The [t] log tail (MON-04/D-10): title, the dim tee line, the designed
# CLI-launched unavailable state (never a fabricated empty log).
MON_LOG_TITLE = _t("MON_LOG_TITLE", "日志尾随 — {root}", "Log tail — {root}")
# CR-01 (quick-261016-hhx, 08 review): the [t] keycap's OWN registry
# constant — byte-equal to the old MON_LOG_TITLE.split(" — {")[0]
# projection in BOTH languages (zh goldens stay byte-identical); also
# removes the width coupling to the title's separator wording.
MON_LOG_KEYCAP = _t("MON_LOG_KEYCAP", "日志尾随", "Log tail")
MON_LOG_TEE_LINE = _t(
    "MON_LOG_TEE_LINE", "tee 落盘: {path}", "tee file: {path}")
MON_LOG_UNAVAILABLE = _t(
    "MON_LOG_UNAVAILABLE", "无日志可尾随 — 该训练任务由 CLI 启动, 无 tee 落盘",
    "No log to tail — this sweep was launched from the CLI; no tee on "
    "disk")

# The attach flow ([a] + enter-on-row): keycap label, modal title, the
# path-input placeholder, the invalid-path toast (never silent), and
# the attached toast. 261015-ehc terminology: the zh word is 监控
# (attach semantics untouched — the 11-08 invariant); en keeps
# "attach".
MON_ATTACH_LABEL = _t("MON_ATTACH_LABEL", "监控", "Attach")
MON_ATTACH_TITLE = _t(
    "MON_ATTACH_TITLE", "监控训练任务结果目录", "Attach sweep output root")
MON_ATTACH_PLACEHOLDER = _t(
    "MON_ATTACH_PLACEHOLDER", "输入结果目录路径…", "Output root path...")
MON_ATTACH_INVALID_TOAST = _t(
    "MON_ATTACH_INVALID_TOAST",
    "✗ {path} 不是训练任务结果目录（无训练任务产物）",
    "✗ {path} is not a sweep output root (no sweep artifacts there)")
MON_ATTACHED_TOAST = _t(
    "MON_ATTACHED_TOAST", "✓ 已监控: {root}", "✓ attached: {root}")

# The [r] rescan keycap + its toast.
MON_RESCAN_LABEL = _t("MON_RESCAN_LABEL", "重扫", "Rescan")
MON_RESCAN_TOAST = _t(
    "MON_RESCAN_TOAST", "✓ 已完成全扫（{n} 训练任务）",
    "✓ full scan done ({n} sweeps)")

# 261016-vxr (VXR-2): the slot-5 [k] kill-confirm family — stop the
# ATTACHED training through the launcher's kill channel WITHOUT exiting
# the console (the maintainer's live-session batch). The keycap mirrors
# MON_FAILURES_KEYCAP/MON_LOG_KEYCAP style; the confirm's [Y]/[N] pair
# mirrors LNC_GATE_CONFIRM/LNC_EXIT_CONFIRM (y the ONLY confirm key —
# enter is structurally inert, EHC-2 extended to the kill). Consumers:
# tui/screens/monitor.py (KillConfirmModal + action_kill_running +
# the outcome toasts).
MON_KILL_KEYCAP = _t("MON_KILL_KEYCAP", "停止", "Kill")
MON_KILL_TITLE = _t(
    "MON_KILL_TITLE", "停止训练 — {root}", "Stop training — {root}")
MON_KILL_CONFIRM = _t(
    "MON_KILL_CONFIRM", "确认停止当前训练任务？— [Y] 停止 / [N] 取消",
    "Stop the current training task? — [Y] stop / [N] cancel")
MON_KILL_TOAST = _t(
    "MON_KILL_TOAST", "✓ 已发送停止信号：{root}",
    "✓ Stop signal sent: {root}")
MON_KILL_TOAST_DEAD = _t(
    "MON_KILL_TOAST_DEAD", "任务已先行结束：{root}",
    "Already finished before the stop: {root}")
MON_KILL_UNAVAILABLE = _t(
    "MON_KILL_UNAVAILABLE",
    "无法停止：{root} 上没有本控制台启动的运行中训练",
    "Cannot stop: no live TUI-launched sweep at {root}")
MON_KILL_FAILED = _t(
    "MON_KILL_FAILED", "✗ 停止失败: {error}", "✗ stop failed: {error}")

# 261018-toe (the maintainer's 2026-10-18 21:21 slot-5 ruling): the
# History-tab row actions — [d] 删除 (a strong y-only confirm over the
# rm -rf of a DEAD run's output root; a live root is structurally
# undeletable, the deletion runs off the event loop, a rescan follows)
# and [e] 续跑 (the one-click resume of a dead run's incomplete items
# through the existing failures pipeline). The zh side says 训练项
# (cell) per the approved table — never 细胞; the [e] label is
# 续跑 / en resume. Consumers: tui/screens/monitor.py (DeleteConfirmModal
# + action_delete_history + action_resume_history + the outcome toasts).
MON_DELETE_KEYCAP = _t("MON_DELETE_KEYCAP", "删除", "Delete")
MON_DELETE_TITLE = _t(
    "MON_DELETE_TITLE", "删除运行 — {root}", "Delete run — {root}")
MON_DELETE_CONFIRM = _t(
    "MON_DELETE_CONFIRM",
    "将永久删除结果目录：{root}（{n} 训练项，不可恢复）？— [Y] 删除 / [N] 取消",
    "Permanently delete the output root: {root} ({n} cells, "
    "unrecoverable)? — [Y] delete / [N] cancel")
MON_DELETE_TOAST = _t(
    "MON_DELETE_TOAST", "✓ 已删除：{root}", "✓ deleted: {root}")
MON_DELETE_FAILED = _t(
    "MON_DELETE_FAILED", "✗ 删除失败: {error}", "✗ delete failed: {error}")
MON_DELETE_REFUSED_LIVE = _t(
    "MON_DELETE_REFUSED_LIVE",
    "运行中的任务不可删除（先停止再删除）：{root}",
    "Cannot delete a running task (stop it first): {root}")
# The [e] keycap lands with the Task-2 binding (the footer paints both
# row actions); the remaining MON_RESUME_* family arrives with the flow.
MON_RESUME_KEYCAP = _t("MON_RESUME_KEYCAP", "续跑", "Resume")
MON_RESUME_CONFIRM = _t(
    "MON_RESUME_CONFIRM",
    "续跑 {pairs} 个未完成组合 × 种子 {seeds} = {n} 个训练项（已完成训练项将按标记自动跳过）"
    "？— [y] 续跑 / Esc 取消",
    "Resume {pairs} incomplete pairs × seeds {seeds} = {n} cells "
    "(completed cells skip via their markers)? — [y] resume / Esc cancel")
MON_RESUME_TOAST = _t(
    "MON_RESUME_TOAST", "✓ 续跑已启动 — {cells} 训练项 → {root}",
    "✓ resume launched — {cells} cells → {root}")
MON_RESUME_NOTHING = _t(
    "MON_RESUME_NOTHING", "无未完成训练项，无需续跑：{root}",
    "No incomplete cells to resume: {root}")
MON_RESUME_REFUSED_LIVE = _t(
    "MON_RESUME_REFUSED_LIVE",
    "运行中的任务不可续跑（同根二次启动会冲突）：{root}",
    "Cannot resume a running task (a second launch at the same root "
    "would conflict): {root}")

# Cell detail (enter): the title shape and the per-fraction line under
# --curve (record fields render verbatim — data, never translated).
MON_CELL_DETAIL_TITLE = _t(
    "MON_CELL_DETAIL_TITLE", "{model} × {task} × seed_{seed}",
    "{model} × {task} × seed_{seed}")
MON_FRACTION_LINE = _t(
    "MON_FRACTION_LINE", "frac_{fraction}: {state}", "frac_{fraction}: {state}")

# Phase 16 (16-01, TUI-01, D16-15): the G GPU-lanes panel — a standing
# section on the slot-5 monitor (both tabs, D16-05). The lane row is
# DATA-FORWARD: the identical value registers for both languages (the
# MON_CELL_DETAIL_TITLE precedent — GPU/%/MiB/°C stay verbatim) and the
# 10-cell utilization bar composes in CODE over it (UI-SPEC Surface A
# rule 3). MON_GPU_ABSENT is the ONE degradation shape every probe
# failure mode shares (D16-02, the ABOUT_DEP_ABSENT 未安装 word);
# MON_GPU_NONE is the explicit zero-GPU empty state (D16-04). Both
# carry the ◌ glyph first (NO_COLOR legibility).
MON_GPU_TITLE = _t("MON_GPU_TITLE", "GPU 状态", "GPUs")
MON_GPU_ROW = _t(
    "MON_GPU_ROW", "GPU {i}  {util}%  {used}/{total} MiB  {temp}°C",
    "GPU {i}  {util}%  {used}/{total} MiB  {temp}°C")
MON_GPU_ABSENT = _t(
    "MON_GPU_ABSENT", "◌ nvidia-smi 未安装", "◌ nvidia-smi not installed")
MON_GPU_NONE = _t("MON_GPU_NONE", "◌ 未检测到 GPU", "◌ no GPUs detected")
# Phase 16 (16-02, TUI-03, D16-15): the dispatch rows on the Running
# card (UI-SPEC Surface B) — consumed from tui/services/dispatch_state
# .py (the tolerant frozen-v2 reader). MON_DISPATCH_LINE maps 1:1 to
# the schema: status renders VERBATIM including unrecognized values
# (the passthrough rule), done = counts.completed, total =
# counts.total, queue = queue_depth. MON_DISPATCH_WORKER_BUSY is
# DATA-FORWARD: the identical value registers for both languages (the
# MON_GPU_ROW precedent — worker/GPU/⏵/seed_ stay verbatim); the
# ` × frac_{fraction}` segment appends in CODE when non-null.
# MON_DISPATCH_WORKER_IDLE reuses the ◌ queued glyph; the busy row
# reuses ⏵ — no new glyph. MON_DISPATCH_STALE is the D16-08 marker:
# the ⚠ glyph leads (NO_COLOR legibility) and the row renders ABOVE
# the dispatch line while the rows stay (last-known-good).
# MON_DISPATCH_MALFORMED (WR-04, phase-16 review) is the DISTINCT
# honesty marker for a malformed-only view — a parseable snapshot
# violating the schema's SNAPSHOT INVARIANT is an invariant violation,
# NOT outdated data, so it never borrows the staleness copy (the two
# rows render independently; both lead with the same ⚠ glyph).
MON_DISPATCH_LINE = _t(
    "MON_DISPATCH_LINE", "调度 {status} · 完成 {done}/{total} · 队列 {queue}",
    "dispatch {status} · {done}/{total} done · queue {queue}")
MON_DISPATCH_WORKER_BUSY = _t(
    "MON_DISPATCH_WORKER_BUSY",
    "worker {i} · GPU {gpu} · ⏵ {model} × {task} × seed_{seed}",
    "worker {i} · GPU {gpu} · ⏵ {model} × {task} × seed_{seed}")
MON_DISPATCH_WORKER_IDLE = _t(
    "MON_DISPATCH_WORKER_IDLE", "worker {i} · GPU {gpu} · ◌ 空闲",
    "worker {i} · GPU {gpu} · ◌ idle")
MON_DISPATCH_STALE = _t(
    "MON_DISPATCH_STALE",
    "⚠ 调度状态过期（{age}s ≥ {grace}s）— 数据可能不是最新",
    "⚠ dispatch state stale ({age}s >= {grace}s) — data may be outdated")
MON_DISPATCH_MALFORMED = _t(
    "MON_DISPATCH_MALFORMED",
    "⚠ 调度计数不一致（快照不变量被违反）— 数值按原样显示",
    "⚠ dispatch counts inconsistent (snapshot invariant violated) — "
    "values shown verbatim")
