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
# kernel id (English, data) with its ENV_KERNEL_LABELS label, and the modal
# footer's esc binding label.
ENV_DETAIL_TITLE = "{kernel_id} — {label}"
ENV_DETAIL_BACK_LABEL = "返回"

# Quick check (ENV-04/D-09): the strings land NOW for Phase 11's launch
# screen to consume — no UI surface or call site exists in Phase 8.
ENV_QUICK_CHECK_PASS = "快检通过（launch-required 子集）"
ENV_QUICK_CHECK_FAIL = "✗ 快检失败: {kernel_names}"
