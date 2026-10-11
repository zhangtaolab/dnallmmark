"""
strings.py — the single home for operator-facing copy (Phase 8, 08-02,
I18N-01).

Contract (08-UI-SPEC I18N Contract, approved 2026-10-11):

- Chinese-primary copy with technical terms in English verbatim — registry
  keys, kernel ids, filter axes, metric names, file paths, CLI commands,
  schema field names are never translated.
- Plain module-level UPPER_SNAKE constants grouped by screen prefix
  (``APP_`` / ``ENV_`` / ``SEL_`` / ``MATRIX_``); format fields are
  ``{name}`` placeholders consumed via ``str.format()`` at render sites.
- NO other module defines operator-facing copy — screens reference these
  constants, never inline copy (greppable once screens land: no Chinese
  literals outside this module in tui/screens/ or tui/app.py).
- Kernel detail lines are DATA, not copy: drill-downs render env_smoke's own
  English PASS/FAIL lines verbatim (the byte-stable CLI contract, D-02);
  Chinese chrome only wraps them.
- No runtime locale switching in Phase 8 — this module is the seam that
  would make it possible later; no translation framework.

Values below are copied verbatim from the 08-UI-SPEC Copywriting Contract
(the authoritative wording). The full copy set grows here as 08-03..08-07
land their screens; 08-06 lands the complete APP_ shared block + ENV_ block
(the SEL_/MATRIX_ blocks are 08-07's).
"""

# ===== App (Header / app chrome) =====
APP_TITLE = "DNALLM-Mark 控制台"
# Footer label for the app-level q binding (08-UI-SPEC Screen 1 footer:
# "[q] 退出"). App-level copy, not screen copy, because the binding lives
# on the composition root (08-03).
APP_QUIT_LABEL = "退出"
# Footer label + title for the app-level ? help binding/modal (08-UI-SPEC
# Keyboard map: "? | app | help modal (all bindings, Chinese)").
APP_HELP_LABEL = "帮助"
APP_HELP_TITLE = "按键帮助"
# One help-modal row per binding, in the UI-SPEC footer keycap format
# ("[r] 重检" style — key in brackets, then the binding's Chinese label).
APP_HELP_ROW = "[{key}] {label}"
# Min-size message (08-UI-SPEC Terminal Contract): below 80x24 the app
# renders ONLY this line, with the current dimensions, re-checked on
# resize. Halfwidth x per the spec wording.
APP_MIN_SIZE_MESSAGE = "终端过小（需 ≥ 80x24，当前 {w}x{h}）— 请放大窗口"

# ===== 环境检查 (ENV-01..04) =====
# Kernel-id → operator label for the seven env-check rows and drill-down
# titles, in main() kernel order (08-RESEARCH verified). Keys are the stable
# CheckResult.name vocabulary from pipeline/env_smoke (08-01) — data, never
# translated; the values are the copy.
ENV_KERNEL_LABELS = {
    "version_pins": "版本 pin",
    "dnallm": "dnallm 导入",
    "peft": "peft",
    "cuda": "CUDA",
    "matmul": "matmul 冒烟",
    "numpy": "numpy≥2",
    "dataset_dirs": "数据集目录",
}

# Env panel row states (08-UI-SPEC Copywriting Contract "Env row states"):
# ✓ / ✗ / ◌ 待检 / ⠋ 检查中… — the glyph is the meaning-carrier (the
# glyph+color redundancy rule: every state stays legible under NO_COLOR);
# the pending/checking states carry their dim label in the same cell.
ENV_STATE_PASS = "✓"
ENV_STATE_FAIL = "✗"
ENV_STATE_PENDING = "◌ 待检"
ENV_STATE_CHECKING = "⠋ 检查中…"

# Env panel column headers (08-UI-SPEC Screen 1 header row: 状态 检查项
# 摘要). The 摘要 (summary) column carries each kernel's own first detail
# line (prefix-stripped) once its result arrives (08-06).
ENV_COL_STATE = "状态"
ENV_COL_ITEM = "检查项"
ENV_COL_SUMMARY = "摘要"

# Screen title for the title bar (08-UI-SPEC Screen 1 name: 环境检查).
ENV_SCREEN_TITLE = "环境检查"

# Last-check line (ENV-02 verbatim format "上次检查: YYYY-MM-DD HH:MM").
# The colon is HALFWIDTH (08-UI-SPEC Auto-Selected Default #12: ROADMAP +
# 08-CONTEXT wording; narrower in a double-width-CJK line) — a single
# constant the maintainer may flip.
ENV_LAST_CHECK_LINE = "上次检查: {checked_at}"

# Gate verdict — pass (08-UI-SPEC Copywriting Contract; renders from the
# tui.services.env_gate judgment, advisory this phase per D-09).
ENV_VERDICT_PASS = "✓ 环境就绪（可启动）"

# Gate verdict — critical fail (ENV-03): names the failing CRITICAL kernel
# ids (English verbatim, main() order) with the Phase-11 blocking note.
ENV_VERDICT_CRITICAL_FAIL = (
    "✗ 关键项未通过: {kernel_names} — 启动流程将被阻断（阻断接线于 Phase 11）"
)

# Missing-data routing (ENV-03/SEL-04): the count, the Phase-10 panel note,
# and the CLI audit command — English verbatim (file paths and CLI commands
# are never translated, I18N-01).
ENV_ROUTE_MISSING_DATASETS = (
    "⚠ {n} 个数据集目录缺失 — 数据下载面板于 Phase 10 提供；"
    "CLI 重跑审计: python script/audit_n_frequencies.py"
)

# Env screen binding labels (08-UI-SPEC Keyboard map: r 重检, enter 详情).
ENV_REFRESH_LABEL = "重检"
ENV_DETAIL_LABEL = "详情"

# Drill-down modal chrome (08-UI-SPEC Modal — 详情下钻): the title pairs the
# kernel id (English, data) with its ENV_KERNEL_LABELS label.
ENV_DETAIL_TITLE = "{kernel_id} — {label}"

# Modal-back label (esc) — shared app chrome: the env drill-down, the help
# modal, and every later Phase 8 confirm surface use the same esc wording
# (08-UI-SPEC Keyboard map: "esc | modals | pop modal — never quits").
APP_MODAL_BACK_LABEL = "返回"

# Quick check (ENV-04/D-09): the strings land NOW for Phase 11's launch
# screen to consume — no UI surface or call site exists in Phase 8.
ENV_QUICK_CHECK_PASS = "快检通过（launch-required 子集）"
ENV_QUICK_CHECK_FAIL = "✗ 快检失败: {kernel_names}"

# ===== 选择 (SEL-01..04, 08-07) =====
# Screen titles (08-UI-SPEC Screen 2 title bar: "选择: 模型" — the m
# toggle flips the visible table and the title with it).
SEL_SCREEN_TITLE_MODELS = "选择: 模型"
SEL_SCREEN_TITLE_DATASETS = "选择: 数据集"

# Status line (top-right, zero-one-many): the marked-counts readout in the
# same structure for 0, 1, and many marks; totals are the live registry
# counts (62/50 against the committed registries).
SEL_STATUS_LINE = "已标记: 模型 {n}/{models_total} · 数据集 {m}/{tasks_total}"

# Filter bar (08-UI-SPEC Screen 2): the label, the k9s type-to-filter
# placeholder (Keyboard & Interaction Contract), and the live (N/total)
# readout rendered right-aligned in the same bar.
SEL_FILTER_LABEL = "过滤: "
SEL_FILTER_PLACEHOLDER = "输入过滤词…"
SEL_FILTER_COUNT = "({n}/{total})"

# Unknown-axis warning line (dim, under the Input): rendered while valid
# terms still apply; {axes} is the sorted known-axis vocabulary (data).
SEL_FILTER_UNKNOWN_AXIS = "未知过滤轴: {axis}（可用: {axes}）"

# Empty edge — filter no match: the documented row with the Esc-clear hint.
SEL_FILTER_NO_MATCH = "无匹配行（0/{total}）— 调整过滤词，或 Esc 清除过滤"

# Loading state: the single row covering the registry/n_audit read seam
# before rows compose (08-UI-SPEC UI Considerations, selection loading).
SEL_LOADING_ROW = "加载中…"

# Empty edge — registry load failure: names the path (the tolerant-loader
# None result); the app stays alive.
SEL_REGISTRY_LOAD_FAILED = "✗ 注册表加载失败 — {registry_path} 不可读（容错 loader 返回空）"

# n_audit absent (SEL-04 column-level empty state): every presence cell
# renders this copy; the CLI audit command stays English verbatim.
SEL_N_AUDIT_MISSING = (
    "✗ n_audit.json 缺失 — 在场列不可用；"
    "CLI 重跑: python script/audit_n_frequencies.py"
)

# Model-table column headers (08-UI-SPEC Screen 2: 标 模型 类型 物种
# 规模(M) 数据). The mark column header is the single-char 标 (2 cells).
SEL_COL_MARK = "标"
SEL_COL_MODEL = "模型"
SEL_COL_TYPE = "类型"
SEL_COL_SPECIES = "物种"
SEL_COL_SIZE = "规模(M)"

# Dataset-table column headers (标 · 任务键 · Category · 类型 · 指标 ·
# 数据; Category is the registry's own English field name — data, I18N-01).
SEL_COL_TASK = "任务键"
SEL_COL_CATEGORY = "Category"
SEL_COL_METRIC = "指标"

# Presence column header (shared by both tables).
SEL_COL_PRESENCE = "数据"

# Presence cells (SEL-04): present = pass glyph + thousands-separated
# exact train/dev/test counts (formatting happens only in the screen);
# missing = the missing glyph + word. 缺失 is the requirement-verbatim
# wording (✓ 在场 / ✗ 缺失).
SEL_PRESENCE_PRESENT = "✓ {train}/{dev}/{test}"
SEL_PRESENCE_MISSING = "✗ 缺失"
# Presence unknown (registry/audit drift — a key absent from n_audit; every
# real model key lands here, models are not n_audit subjects). The
# Copywriting Contract does not define this cell; gap-filler per the
# glyph-first redundancy rule (◌ pending-glyph family, dim render).
SEL_PRESENCE_UNKNOWN = "◌ 未知"

# Selection-screen binding labels (08-UI-SPEC Screen 2 footer mockup).
SEL_MARK_LABEL = "标记"
SEL_SWITCH_LABEL = "数据集"
SEL_PRESET_LABEL = "预设"
SEL_MATRIX_LABEL = "矩阵"
SEL_TEMPLATE_LABEL = "模板"
SEL_SAVE_PRESET_LABEL = "保存预设"
SEL_FILTER_KEY_LABEL = "过滤"

# The env-screen s binding (08-UI-SPEC Keyboard map: "s | 环境检查 | switch
# to 选择 screen"). Landed with the selection screen (08-07).
SEL_OPEN_LABEL = "选择"

# Preset modal (08-UI-SPEC Keyboard map: tier-1 E2E 对 / tier-2 arena
# 代表 / 全部 / 自定义保存…). Derived labels for the built-ins; customs
# render their own saved name.
SEL_PRESET_TITLE = "预设"
SEL_PRESET_TIER_1 = "tier-1 E2E 对"
SEL_PRESET_TIER_2 = "tier-2 arena 代表"
SEL_PRESET_ALL = "全部"
# Empty edge — no saved customs: the documented entry with the save-flow
# hint (the s key names the save binding).
SEL_PRESET_NO_CUSTOMS = "尚无自定义预设 — 空格标记后按 s 保存当前选择"
# Success toast (preset applied, replacing semantics).
SEL_PRESET_APPLIED = "✓ 已应用预设 {preset}（模型 {n}·数据集 {m}）"
# Save-success toast — Copywriting Contract gap-filler (the contract pins
# only the applied/exported toasts; a destructive-adjacent save needs its
# own feedback), same shape as the applied toast.
SEL_PRESET_SAVED = "✓ 预设已保存: {name}（模型 {n}·数据集 {m}）"
# Warning — preset unknown keys (registry evolution tolerance): loud, lists
# every skipped key.
SEL_PRESET_UNKNOWN_KEYS = "⚠ 预设含 {n} 个未知键（注册表已演进？）: {keys} — 已跳过"
# Destructive — overwriting a saved custom preset (Enter/Esc confirm).
SEL_PRESET_OVERWRITE_CONFIRM = "同名预设已存在: {name} — Enter 覆盖 / Esc 取消"
# Save-preset name input placeholder.
SEL_PRESET_NAME_PLACEHOLDER = "输入预设名…"

# Template modal (08-UI-SPEC Keyboard map: 导入模板 / 导出模板 / 转
# sweep_priorities tier).
SEL_TEMPLATE_TITLE = "模板"
SEL_TEMPLATE_MENU_IMPORT = "导入模板"
SEL_TEMPLATE_MENU_EXPORT = "导出模板"
SEL_TEMPLATE_MENU_TIERS = "转 sweep_priorities tier"
SEL_TEMPLATE_PATH_PLACEHOLDER = "输入路径…"
# Collect-all problem list (SEL-03 fail-fast): the header with the count,
# then one numbered line per problem ({location} is the JSON pointer, or
# the path for load failures).
SEL_TEMPLATE_PROBLEMS = "✗ 模板校验失败 — 共 {n} 处问题："
SEL_TEMPLATE_PROBLEM_LINE = "{n}. {location}: {message}"
# Import-success toast — Copywriting Contract gap-filler (the truth pins
# "on success marks apply and a toast fires"; only the exported toast was
# worded), same shape as the applied toast.
SEL_TEMPLATE_IMPORTED = "✓ 模板已导入（模型 {n}·数据集 {m}）"
# Export-success toast (verbatim from the Copywriting Contract); the tier
# conversion export reuses it (it IS an export of the current selection).
SEL_TEMPLATE_EXPORTED = "✓ 模板已导出: {path}"

# Destructive — clearing all marks (Enter/Esc confirm). Landed for the
# record per the Copywriting Contract; NO Phase 8 trigger exists ("if
# surfaced" — the keyboard map defines no clear binding; presets replace,
# they do not need a destructive clear).
SEL_CLEAR_MARKS_CONFIRM = "清除全部标记？（模型 {n} · 数据集 {m}）— Enter 确认 / Esc 取消"

# ===== 矩阵总览 (matrix, SEL-01 auxiliary, 08-07) =====
MATRIX_TITLE = "矩阵总览（只读）— {models} 模型 × {datasets} 数据集"
MATRIX_SCROLL_HINT = "←/→ 横向滚动 · esc 返回"
# Cursor readout line (below the table): the FULL task key of the cursor
# column (long-text resolution for 62-char keys).
MATRIX_CURSOR_READOUT = "光标: {task_key}"
