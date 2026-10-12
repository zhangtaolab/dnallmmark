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

# Missing-data routing (ENV-03/SEL-04; amended 10-03 per the 10-UI-SPEC
# Existing-Surface Amendments): the count, the [3] keycap hint routing
# to the data-manager screen (the nav digit 3 IS the one navigation
# path — the hint surfaces it, no alias key), and the CLI audit
# command — English verbatim (file paths and CLI commands are never
# translated, I18N-01). The Phase-10-panel note is retired: the panel
# exists now.
ENV_ROUTE_MISSING_DATASETS = (
    "⚠ {n} 个数据集目录缺失 — [3] 前往数据管理；"
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

# The env-screen s binding (08-UI-SPEC Keyboard map: "s | 环境检查 |
# switch to 选择 screen") was RETIRED by the 09-03 nav-shell migration:
# menu slot 2 supersedes it (one navigation path per target) — the
# action and this label constant were removed with it.

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
# Save-failure warning — OSError persisting under the config root (a
# read-only location, a full disk): the save flow degrades to a warning
# toast, never a crash (the OS error detail is data).
SEL_PRESET_SAVE_FAILED = "✗ 预设保存失败: {error}"
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
# Write-failure problem line (template export / tier conversion): OSError
# from an unwritable or invalid operator path (a parent that is a file, a
# read-only location, a full disk) — the OS error detail is data; the
# modal stays open and nothing was written.
SEL_TEMPLATE_WRITE_FAILED = "✗ 写入失败: {error}"

# Destructive — clearing all marks (Enter/Esc confirm). Landed for the
# record per the Copywriting Contract; NO Phase 8 trigger exists ("if
# surfaced" — the keyboard map defines no clear binding; presets replace,
# they do not need a destructive clear).
SEL_CLEAR_MARKS_CONFIRM = "清除全部标记？（模型 {n} · 数据集 {m}）— Enter 确认 / Esc 取消"

# ===== 自定义条目呈现 (SEL_ custom additions, CUST-06/D-09/D-10/D-14, 09-06) =====
# The w/e binding labels, the toggle/no-op toasts, the disabled-mark
# warning, and the badge/count copy — 09-UI-SPEC Copywriting Contract
# verbatim. The 停用 toast carries the loader-level note (D-09: the
# disable is real run-removal, not a cosmetic dim).
SEL_WIZARD_LABEL = "接入"
SEL_TOGGLE_LABEL = "停用"
SEL_TOGGLE_DISABLED_TOAST = "✓ 已停用 {key}（运行不再加载，loader 级）"
SEL_TOGGLE_ENABLED_TOAST = "✓ 已启用 {key}"
SEL_TOGGLE_OFFICIAL_NOOP = "官方条目不可停用"
# Warning — spacebar on a disabled custom row (T-09-13: a mark the sweep
# can never see is blocked at entry, never discovered at launch).
SEL_DISABLED_MARK_WARNING = "⚠ {key} 已停用 — 运行不会加载该条目，标记无效"
# The D-10 custom badge — the ◇ prefix on the key cell (bold + accent for
# enabled; the dim variant pairs with the suffix for disabled; glyph +
# weight carry the meaning under NO_COLOR).
SEL_CUSTOM_BADGE = "◇"
SEL_DISABLED_SUFFIX = "（已停用）"
# Count-line segment (D-10) — appended (dim) iff at least one custom entry
# is LANDED; counts cover both states (visible = counted; the sweep-visible
# enabled count is derivable from the markers). Zero customs omits the
# segment entirely (the Phase 8 look, byte-identical).
SEL_COUNT_CUSTOM_SEGMENT = (
    "官方 {official_models}/{official_datasets} · 自定义 {custom_models}/{custom_datasets}"
)

# ===== 矩阵总览 (matrix, SEL-01 auxiliary, 08-07) =====
MATRIX_TITLE = "矩阵总览（只读）— {models} 模型 × {datasets} 数据集"
MATRIX_SCROLL_HINT = "←/→ 横向滚动 · esc 返回"
# Cursor readout line (below the table): the FULL task key of the cursor
# column (long-text resolution for 62-char keys).
MATRIX_CURSOR_READOUT = "光标: {task_key}"

# ===== 接入向导 (WIZ_, CUST-01..03, 09-01 service tier) =====
# The validation-report chrome + problem wordings the service composes;
# the 09-04/09-05 wizard screens render the numbered lines. Report rows
# verbatim from the 09-UI-SPEC Copywriting Contract; field labels follow
# the wizard step tables (registry field names stay English verbatim,
# I18N-01). The service returns machine (field_key, message) pairs — the
# labels below are the screens' field_key → label map.

# Validation report header + numbered problem line (09-UI-SPEC
# Copywriting Contract verbatim; field-definition order).
WIZ_PROBLEMS_HEADER = "✗ 校验失败 — 共 {n} 处问题："
WIZ_PROBLEM_LINE = "{i}. {field_label}: {problem}"

# Model wizard field labels (WIZM_) — key → label over the model
# field-definition order.
WIZM_FIELD_LABELS = {
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
}

# Dataset wizard field labels (WIZD_) — key → label over the dataset
# field-definition order (train/dev/test label the split FILE inputs of
# step 2; Task_type renders as its UI-SPEC step-3 wording 任务类型).
WIZD_FIELD_LABELS = {
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
}

# Problem wordings — the {problem} segment of WIZ_PROBLEM_LINE. The
# collision / path-missing / needs-numeric rows match the 09-UI-SPEC
# validation-report example verbatim (ASCII parens); interpolated values
# ({key}/{path}/{value}…) are data.
WIZ_PROBLEM_REQUIRED = "必填项，不能为空"
WIZ_PROBLEM_NOT_OBJECT = "录入内容必须是对象 (收到 {type})"
WIZ_PROBLEM_KEY_FORMAT = "键名不能包含路径分隔符 ({key})"
WIZ_PROBLEM_COLLISION_OFFICIAL = "与官方条目冲突 ({key})"
WIZ_PROBLEM_COLLISION_CUSTOM = "与既有自定义条目冲突 ({key})"
WIZ_PROBLEM_PATH_MISSING = "路径不存在 ({path})"
WIZ_PROBLEM_NEEDS_NUMERIC = "需为数字 ({value})"
WIZ_PROBLEM_NEEDS_INTEGER = "需为整数 ({value})"
WIZ_PROBLEM_ENUM = "取值无效 ({value})，可选: {allowed}"
# Split-file problems ({file} is the split file name, {column} the
# collected label column).
WIZ_PROBLEM_SPLIT_FILE_MISSING = "文件不存在 ({file})"
WIZ_PROBLEM_SPLIT_UNREADABLE = "无法解析 ({file}: {reason})"
WIZ_PROBLEM_SPLIT_NO_HEADER = "文件为空，无表头 ({file})"
WIZ_PROBLEM_SPLIT_NO_SEQUENCE = "表头缺少 sequence 列 ({file})"
WIZ_PROBLEM_SPLIT_NO_LABEL_COLUMN = "表头缺少标签列 {column} ({file})"
WIZ_PROBLEM_SPLIT_ZERO_ROWS = "无数据行 (0 行)"
WIZ_PROBLEM_SPLIT_COUNT_MISMATCH = "声明 {declared} 行，与实际 {counted} 行不符"

# ===== 接入向导 chrome (WIZ_, CUST-01/02 UI, 09-04) =====
# The wizard modal's own chrome copy (09-UI-SPEC Copywriting Contract
# verbatim). Kind names slot into 新增{kind} (模型/数据集); {indicator}
# renders the "{n}/{total}" step number — Typography amendment #9 styles
# that segment accent+bold (the screen composes the markup; this module
# never carries markup).
WIZ_KIND_MODELS = "模型"
WIZ_KIND_DATASETS = "数据集"
WIZ_BORDER_TITLE = "新增{kind} — 步骤 {indicator} · {step}"
# Model wizard step names (the border-title {step} values, in order).
WIZM_STEPS = ("基本信息", "架构与分词", "来源链接", "quirk 勾选")
# Dataset wizard step names (the same slot, the dataset instance).
WIZD_STEPS = ("基本信息", "数据文件", "任务与指标", "溯源信息")
# The step-2 split-file-name Inputs' shared placeholder (the UI-SPEC
# wording renders the trio as train / dev / test 文件名).
WIZ_SPLIT_FILE_PLACEHOLDER = "文件名"
# Quirk checklist labels (D-02: exactly the three named quirks,
# unchecked default; execution-side mapping is Phase 11's).
WIZ_QUIRK_NO_SAFETENSORS = "不使用 safetensors"
WIZ_QUIRK_FP32_ONLY = "仅支持 fp32"
WIZ_QUIRK_SPECIAL_HEAD = "需要特殊头 (head)"
# Type-aware control advisory lines (D-03 — ADVISORY only, the collect-all
# pass is authoritative; fool-proofing never blocks onboarding).
WIZ_PATH_EXISTS = "✓ 路径存在"
WIZ_PATH_MISSING_ADVISORY = "✗ 路径不存在（仍可继续，提交时统一校验）"
WIZ_NUMERIC_HINT = "✗ 需为数字"
# Footer hint (the modal's own 1-row keycap hint, migration table). The
# last step substitutes the submit keycap for the next-step one.
WIZ_FOOTER_HINT = "[enter] 下一步  [b] 上一步  [esc] 取消"
WIZ_FOOTER_HINT_LAST = "[enter] 提交校验  [b] 上一步  [esc] 取消"
# Binding labels (the hint's keycap segments; Binding descriptions use
# the same wording).
WIZ_NEXT_LABEL = "下一步"
WIZ_BACK_LABEL = "上一步"
WIZ_SUBMIT_LABEL = "提交校验"
WIZ_CANCEL_LABEL = "取消"
# Destructive — wizard esc-cancel with entered values (ConfirmModal gate;
# {n} is the filled-step count). Blank forms cancel silently.
WIZ_CANCEL_CONFIRM = "放弃本次录入？已填 {n} 步 — Enter 放弃 / Esc 继续"
# Validation report chrome: the report view's border title and the
# return-to-form hint (the 09-UI-SPEC report mockup).
WIZ_REPORT_TITLE = "新增{kind} — 校验"
WIZ_REPORT_BACK_HINT = "[esc] 返回修改"
# The gauntlet phase's pending view (this plan's minimal placeholder —
# the real panel is 09-05): its title is the Copywriting Contract's
# gauntlet title verbatim; the back hint is the gauntlet mockup's esc row.
WIZ_GAUNTLET_BACK_HINT = "[esc] 返回"
GAUNTLET_TITLE = "接入 gauntlet — {key}"
# Step-1-only affordances (D-11; auto-default #7 placement) — the binding
# labels; the views themselves are 09-05 against the on_import/on_export
# seams.
WIZ_IMPORT_LABEL = "从文件导入"
WIZ_EXPORT_LABEL = "导出自定义注册表"

# ===== 接入 gauntlet 面板 (GAUNTLET_, 09-05, CUST-04 UI + D-08/D-11) =====
# The gauntlet panel's rows / banner / toasts (09-UI-SPEC Copywriting
# Contract verbatim). Format fields: {item} is the item label below,
# {cells} the planned-cell count parsed from the service's
# ``planned_cells=N`` detail token, {summary} the item's remaining detail
# tokens joined verbatim (data, never translated), {key} the candidate
# registry key, {path} a filesystem path, {n} a count, {kind} 模型/数据集.
# GAUNTLET_ROW_PENDING is the one derived row (the copy table defines no
# panel-specific pending line): the ENV pending glyph composition with the
# row's item identity — every gauntlet mockup row carries its item label.
GAUNTLET_ITEM_DRY_RUN = "dry-run 预检"
GAUNTLET_ITEM_AUDIT = "audit 对账"
GAUNTLET_ROW_PENDING = "◌ {item} 待检"
GAUNTLET_ROW_RUNNING = "⠋ {item} …运行中"
GAUNTLET_ROW_DRY_RUN_PASS = "✓ dry-run 预检 — {cells} cell(s) 计划成功"
GAUNTLET_ROW_PASS = "✓ {item} — {summary}"
GAUNTLET_ROW_FAIL = "✗ {item} — {summary}"
# The prominent CUST-04 failure banner — the 官方注册表零触碰 guarantee is
# contract wording (binding constraint 11), never paraphrased.
GAUNTLET_BANNER_FAIL = "✗ gauntlet 未通过 — {key} 未落盘（官方注册表零触碰）"
GAUNTLET_ROW_LANDED = "✓ 已落盘: {key} → {path}"
# The land success toast reuses GAUNTLET_ROW_LANDED verbatim (the copy
# table names no separate toast — the landed row IS the success copy).
# Session undo (D-08): the [u] affordance is session-scoped (gone once the
# panel closes), explicit, immediately-after, toast-confirmed.
GAUNTLET_UNDO_AFFORDANCE = "[u] 会话内撤销"
GAUNTLET_UNDO_LABEL = "会话内撤销"   # binding description (affordance minus keycap)
GAUNTLET_UNDO_TOAST = "✓ 已撤销 {key}"
# Drill-down chrome (derived, the ENV detail-title idiom): the row's item
# label over the subprocess's own verbatim output lines (data, no copy).
GAUNTLET_DRILL_TITLE = "{item} — 详情"
GAUNTLET_DRILL_HINT = "[enter] 详情"
# D-11 import/export copy. The conflicts header names the collect-all
# count; problem lines reuse the SEL_TEMPLATE_PROBLEM_LINE shape. The
# exported toast deliberately differs from SEL_TEMPLATE_EXPORTED (that row
# says 模板已导出 — the registry export is its own wording).
GAUNTLET_IMPORT_CONFLICTS = "✗ 导入冲突 — 共 {n} 处："
GAUNTLET_IMPORTED_TOAST = "✓ 已导入 {n} 条（{kind}）"
GAUNTLET_EXPORTED_TOAST = "✓ 已导出: {path}"
GAUNTLET_EXPORT_EMPTY_TOAST = "尚无自定义条目可导出"
# Derived: the export path-prompt's problems header (write-failure lines
# through the same numbered report surface).
GAUNTLET_EXPORT_PROBLEMS = "✗ 导出失败 — 共 {n} 处："

# ===== 导航壳 (NAV_, 09-03, D-13/D-15) =====
# Top-menu slot names — the RATIFIED verbatim resource nouns (D-13,
# 09-UI-SPEC Navigation Shell): never renamed, never re-translated. The
# digit prefix and 未开放 suffix are composed by the bar from NAV_SLOTS.
NAV_LABEL_ENV = "环境检查"
NAV_LABEL_SELECTION = "模型·数据集"
NAV_LABEL_DATA = "数据管理"
NAV_LABEL_RUN_CONFIG = "运行配置"
NAV_LABEL_MONITOR = "任务监控"
NAV_LABEL_ABOUT = "关于"
# Placeholder suffix (slots 3/4/5 — implemented by their delivering
# phases) and the never-silent activation toast (D-13: 按相应相位实装).
NAV_PLACEHOLDER_SUFFIX = "未开放"
NAV_PLACEHOLDER_TOAST = "该功能区于 Phase {n} 提供"

# ===== 关于屏 (ABOUT_, D-13 slot 6, 09-03) =====
# The five fixed row labels (D-13: 软件版本/数据版本/里程碑阶段/依赖版本/
# 仓库地址) + the title. Values are service-derived (tui/services/about);
# absent dependencies render the 未安装 value (dim, per-package tolerant).
ABOUT_TITLE = "关于 DNALLM-Mark"
ABOUT_ROW_SOFTWARE = "软件版本"
ABOUT_ROW_DATA = "数据版本"
ABOUT_ROW_MILESTONE = "里程碑阶段"
ABOUT_ROW_DEPS = "依赖版本"
ABOUT_ROW_REPO = "仓库地址"
# 软件版本 value with a resolved git sha (sha omitted → bare version).
ABOUT_VALUE_SOFTWARE_WITH_SHA = "{version} (git {sha})"
# 数据版本 value: official-only counts + the 自定义 landed counts + the
# n_audit 在场 signal (the honest machine-derivable data-state wording).
ABOUT_VALUE_DATA = (
    "官方注册表 {om} 模型 / {od} 数据集 · 自定义 {cm}/{cd} · {audit}"
)
ABOUT_N_AUDIT_PRESENT = "n_audit.json 在场"
ABOUT_N_AUDIT_ABSENT = "n_audit.json 缺失"
ABOUT_DEP_ABSENT = "未安装"
# 里程碑阶段 value — the one static milestone constant (Auto-Default #13:
# milestone metadata, not a machine probe; updated per milestone).
ABOUT_MILESTONE_STAGE = "v1.2 TUI任务 — 已交付: Phase 7-8 · 本相位: 9 自定义接入"

# ===== 数据管理屏 (DL_, Phase 10, 10-03; D-12/D-13 + I18N-01) =====
# The data-manager screen chrome + Zenodo 整包 entry copy (10-UI-SPEC
# Copywriting Contract verbatim). Format fields: {n}/{total}/
# {present}/{missing} counts, {HH:MM} the probe moment, {error} a
# diagnostic, {key} a dataset key. Record ids (19135551), dataset
# keys, n_audit, and XDG state stay English verbatim.

DL_SCREEN_TITLE = "数据管理"
DL_MISSING_TITLE = "缺失数据集 ({n}) — 来自 n_audit"
DL_MISSING_COL_KEY = "数据集"
DL_MISSING_COL_ROWS = "n_audit 基线行数"
DL_MISSING_EMPTY = "✓ 无缺失数据集 — 全部 {total} 个数据集在场"

# The Zenodo 整包 four probe states (D-12; glyph+color dual channel on
# every one — probing/not-public dim, public ✓ success, failed ⚠
# warning; `z` on a disabled state is never silent).
DL_ZENODO_PROBING = "⠋ Zenodo 公开探测中 …"
DL_ZENODO_NOT_PUBLIC = "[z] Zenodo 整包 · 未公开（探测于 {HH:MM}）"
DL_ZENODO_PUBLIC = "✓ Zenodo 整包已公开 — [z] 整包下载"
DL_ZENODO_FAILED = "⚠ Zenodo 探测失败: {error}（稍后重试）"
DL_ZENODO_DISABLED_TOAST = (
    "Zenodo 记录 19135551 尚未公开 — 公开后此入口自动激活")
# The bundle queue row's 任务 cell label + the z keycap's action noun.
DL_BUNDLE_TASK_NAME = "zenodo-19135551（整包）"
DL_ZENODO_KEY_LABEL = "Zenodo 整包"

# Bottom-bar keycap labels (D-15, each ≤ 4 CJK chars; 详情 reuses the
# existing ENV_DETAIL_LABEL — the shared-label precedent, one
# vocabulary for the same verb across screens).
DL_ENQUEUE_LABEL = "入队"
DL_RETRY_LABEL = "重试"
DL_CANCEL_LABEL = "取消"
DL_ENQUEUE_ALL_LABEL = "全部入队"

# Derived gap-fillers (the SEL_PRESENCE_UNKNOWN precedent — the
# contract names no wording for these rows): the title-line presence
# summary the UI-SPEC layout requires, and the R-02 shape-D
# disabled-with-explanation toast (the drill-down carries the
# download_url — always diagnosable).
DL_PRESENCE_SUMMARY = "在场 {present}/{total} · 缺失 {missing}"
DL_DISABLED_TOAST = (
    "⚠ {key} 上游为镜像布局，不支持一键下载 — download_url 见详情")
# WR-06: the channel-unavailable reasons that are NOT the shape-D
# mirror layout (no mirror, malformed values, an unreadable registry)
# get their own neutral toast naming the machine reason — never the
# factually wrong mirror-layout copy.
DL_UNKNOWN_TOAST = (
    "⚠ {key} 下载通道暂不可用: {reason} — 详情见下钻")

# ===== 下载队列 (QUEUE_, Phase 10, 10-03; D-02..D-09) =====
# The queue table chrome, the five-state cells, the reconcile cells,
# the restart note, the mismatch banner, the toasts, and the two
# destructive cancel confirms (10-UI-SPEC Copywriting Contract
# verbatim).

QUEUE_TITLE = "下载队列 ({n}) — 串行 · 状态持久化于 XDG state"
QUEUE_COL_TASK = "任务"
QUEUE_COL_STATE = "状态"
QUEUE_COL_PROGRESS = "进度"
QUEUE_COL_RECONCILE = "行数对账"
QUEUE_EMPTY = "队列为空 — 按 [d] 入队缺失数据集"

# The five state cells (D-02 verbatim; glyph+color dual channel — the
# leading glyph is the NO_COLOR carrier).
QUEUE_STATE_PENDING = "◌ 待下载"
QUEUE_STATE_DOWNLOADING = "⠋ 下载中"
QUEUE_STATE_DONE = "✓ 完成"
QUEUE_STATE_FAILED = "✗ 失败"
QUEUE_STATE_MISMATCH = "⚠ 对账不一致"

# Reconcile cells (D-09; the running cell covers the automatic
# post-landing transient — auto-default #14).
QUEUE_RECONCILE_PASS = "✓ {n} 行一致"
QUEUE_RECONCILE_RUNNING = "⠋ 对账中 …"
QUEUE_RECONCILE_MISMATCH = "⚠ {n}≠{m}"

# Restart recovery note (D-06; dim render on recovered rows).
QUEUE_RESTART_NOTE = "上次中断 — 通道将续传"

# The prominent mismatch banner (D-07/D-09) — 不自动删除 is contract
# wording, never paraphrased.
QUEUE_BANNER_MISMATCH = (
    "⚠ 对账不一致 — {key}: n_audit 基线 {n} 行, 实测 {m} 行（不自动删除）")

# Toasts: enqueue feedback, the reconcile-pass presence flip, the
# retry no-op, and the probed CLI-absent state (modelscope stays
# English — a CLI name, never translated).
QUEUE_TOAST_ENQUEUED = "✓ 已入队: {key}"
QUEUE_TOAST_ENQUEUED_ALL = "✓ 已入队 {n} 个缺失数据集"
QUEUE_TOAST_ALREADY_QUEUED = "{key} 已在队列中"
QUEUE_FLIP_TOAST = "✓ {key} 下载完成且对账一致 — 在场已更新"
QUEUE_RETRY_NOOP = "仅 失败/对账不一致 项可重试"
QUEUE_CLI_UNAVAILABLE = (
    "✗ modelscope CLI 不可用 — 请先安装 (pip install modelscope)")
# WR-04: the refused enqueue when the queue state file cannot be
# written (read-only state root, full disk, quota) — never silent,
# never a lie about the channel.
QUEUE_PERSIST_FAILED_TOAST = (
    "✗ 队列状态写入失败: {key} 未入队 — 检查磁盘空间与权限")
# CR-02: the driver-stall companion in the same vocabulary — a CLAIM
# that cannot persist exits the driver (never the claim->refuse->recheck
# livelock); the entry stays pending for the fixed-rail re-kick.
QUEUE_PERSIST_DRIVER_TOAST = (
    "✗ 队列状态写入失败，驱动已停止: {key} — 修复磁盘/权限后重新入队驱动")

# Progress cell, indeterminate (auto-default #3: never a fabricated
# percent from unparsed output).
QUEUE_PROGRESS_INDETERMINATE = "⠋ …"

# Destructive — the two x-cancel confirms (Enter/Esc; the downloading
# copy names the channel's own resume retention, D-06).
QUEUE_CONFIRM_CANCEL_PENDING = "移出队列 {key}？— Enter 移出 / Esc 继续"
QUEUE_CONFIRM_CANCEL_DOWNLOADING = (
    "取消下载 {key}？已下载部分将由通道续传保留 — Enter 取消 / Esc 继续")

# Derived gap-filler: the x-on-non-cancellable no-op toast (mirrors
# the retry toast's shape; the contract pins the retry row only).
QUEUE_CANCEL_NOOP = "仅 待下载/下载中 项可取消"

# The g re-audit binding's label (show=False binding, auto-default #7
# — D-15's bottom bar is verbatim without it).
QUEUE_REAUDIT_LABEL = "重新审计"

# ===== 选择屏 d-入队 amendments (SEL_, Phase 10, 10-03; D-14) =====
# The selection-screen enqueue keycap + the present-row no-op toast
# (10-UI-SPEC 选择屏 amendments; 入队 is ONE vocabulary with the
# data-manager screen's d — interaction semantic 8).
SEL_ENQUEUE_LABEL = "入队"
SEL_ENQUEUE_PRESENT_TOAST = "该数据集已在场"
