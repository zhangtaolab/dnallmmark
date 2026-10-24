# Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers - Discussion Log

> **Audit trail only.** Decisions live in CONTEXT.md.

**Date:** 2026-10-09 (two sessions: pre-restructure partial + resumed directive-adjusted)
**Areas discussed:** 对账策略与数据树, AST 锚迁移, dev 前端处置 (+ directive re-scope; 嵌套归一 deferred)

*Session 1 (pre-restructure, interrupted by roadmap surgery):* GPU env 载体 (1: 新建专用 venv), 锁定载体 (1: pyproject [gpu]+uv.lock), E2E 对 (用户点名 plant-dnamamba-6mer + PlantHelixSeek × PlantCAD2__on_off) — 全部带入 ROADMAP Phase 3 注记。

*Session 2 (resumed; directive: 代码修订优先、不跑模型):*

## 对账策略与数据树
| Option | Selected |
|--------|----------|
| merge dev→autorun，数据取我方 | ✓ |
| 数据取 dev | |
| rebase/重建 | |
**Notes:** 不跑模型期间我方数据是唯一契约验证集合；dev 数据留 E2' 重生成；script/ 逐文件审。

## AST 锚迁移
| Option | Selected |
|--------|----------|
| 转向导出链契约断言 | ✓ |
| 重锚 run_finetune.py 生产点 | |
**Notes:** fixture 可验、不绑管线结构、与 F3② 修复对齐；旧锚随 F10 退役同提交文档化。

## dev 前端处置
| Option | Selected |
|--------|----------|
| 并入后针对该 diff 定向评审 | ✓ |
| 直接并入不审 | |
| 前端取我方 | |
**Notes:** 对照 Phase 1 前端审计基线；发现路由 Phase 4。

## Directive re-scope (maintainer, session start)
不跑模型 → PIPE-02 构建/PIPE-03 E2E/嵌套归一 deferred 至 DNALLM 稳定；pyproject [gpu] 定义与 PlantHelixSeek 元数据作为代码保留。
