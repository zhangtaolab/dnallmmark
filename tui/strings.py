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
land their screens.
"""

# ===== App (Header / app chrome) =====
APP_TITLE = "DNALLM-Mark 控制台"

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
