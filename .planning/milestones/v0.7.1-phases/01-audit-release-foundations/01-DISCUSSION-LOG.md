# Phase 1: Audit & Release Foundations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-08
**Phase:** 1-Audit & Release Foundations
**Areas discussed:** 审计深度与去向, 锁版基准源, 可见性与token

---

## 审计深度与去向 (Audit depth & destination)

### Q1: AUDIT-01 审查深度

| Option | Description | Selected |
|--------|-------------|----------|
| 全新系统审查 | 并行审查代理分维度重审三子系统，CONCERNS.md 当输入而非结论，每条发现需复现验证+定级 | ✓ |
| 验证扩展为主 | 逐条验证 CONCERNS.md 已知问题仍可复现，补齐明显缺口即止 | |
| 混合定向 | 已知问题快速验证 + 定向深挖高风险区，其余浅审 | |

**User's choice:** 全新系统审查
**Notes:** 公开发布要求审计本身可信。

### Q2: 审计报告去向

| Option | Description | Selected |
|--------|-------------|----------|
| 公开进仓库 | 清理后的完整报告提交进仓库（AUDIT.md），修复完成前社区可见 | ✓ |
| 仅内部留存 | 完整报告只存 .planning，公开面只留 CHANGELOG 已修复项 | |
| 分层公开 | 完整报告内部 + 公开 KNOWN-ISSUES.md 只列已确认待修项 | |

**User's choice:** 公开进仓库
**Notes:** 透明度即本里程碑的卖点。

### Q3: 超出现有 REQ-ID 的发现怎么处理

| Option | Description | Selected |
|--------|-------------|----------|
| 分级归置 | 影响榜单正确性/页面功能的并入 Phase 4，其余进 backlog | ✓ |
| 全部并入修复 | 所有确认 bug 全部并入 Phase 4，一次修完 | |
| 只进 backlog | 严格冻结路线图，本里程碑只修已列需求 | |

**User's choice:** 分级归置
**Notes:** 背景：CONCERNS.md 已发现排序失效、三处嵌套遍历错误、管道配置跨模型泄漏、3/42 模型不可复现等超范围问题。

### Q4: 审计精力分配

| Option | Description | Selected |
|--------|-------------|----------|
| 正确性优先 | 深挖聚合数学、FLOPs 外推、管道配置变异、数据流一致性；可维护性只记录不定级 | ✓ |
| 四维均衡 | 正确性/可维护性/安全/性能均衡定级 | |
| 可维护性优先 | 面向外部读者能否看懂/复现来审 | |

**User's choice:** 正确性优先
**Notes:** 对应里程碑"正确性 > 可维护性"的优先级声明。

---

## 锁版基准源 (Dependency pin baseline)

### 事前核查

本机排查：系统 python（linuxbrew 3.14.7）无 pandas；miniconda envs（cuda130、vllm）无 pandas；`/home/forrest/Github/DNALLM/.venv` 是 pandas 3.0.6 + numpy 2.5.3（dev 分支适配环境，非原始数据生成环境）。uv 0.12.23 已装。

### Q1: 原始生成环境是否可访问

| Option | Description | Selected |
|--------|-------------|----------|
| 还在，可导出 | 原机器/环境可导出 pip freeze，锁版直接用实际版本 | |
| 没了 | 按下界锁版（pandas>=2.2,<3.0 最新 2.x）+ 重生成数值比对验证 | ✓ |
| 不确定 | 需要排查 | |

**User's choice:** 没了
**Notes:** 2026-03-31 版榜单数据的生成环境已不存在。

### Q2: 重生成比对标准

| Option | Description | Selected |
|--------|-------------|----------|
| 差异即调查 | 任何数值差异都停下查原因，查明后才能定锁 | ✓ |
| 严格一致才过 | 不一致就换版本重试直到一致 | |
| rank 级一致即可 | 名次不变就接受微小浮点差 | |

**User's choice:** 差异即调查
**Notes:** 用户先澄清了关键误解——"重生成"仅指 CPU 数据链（3 个脚本处理 42 份已提交 model_performance JSON），不重跑任何模型训练。

### Q3: 数据链环境位置

| Option | Description | Selected |
|--------|-------------|----------|
| 仓库内 uv venv | 仓库根 .venv，uv sync 一键重建，与 DNALLM/.venv 隔离 | ✓ |
| miniconda 新环境 | 与 pyproject/uv.lock 工作流脱节 | |
| 无所谓 | Claude 定 | |

**User's choice:** 仓库内 uv venv

### Q4: Python 版本

| Option | Description | Selected |
|--------|-------------|----------|
| 3.12 | 与 CI 矩阵下限一致（Claude 推荐） | |
| 3.13 | 更新，CI 矩阵上限 | ✓ |
| 3.14 | pandas 2.3.x 轮子可用性未验证，不推荐 | |

**User's choice:** 3.13
**Notes:** 用户先回复了单独一个"2"（澄清后确认是此题答案）。

---

## 可见性与token (Visibility & token)

### 事实澄清

用户问"你说的是哪个 token"——展示并解释了 README.md:116 的 Zenodo 记录 19135551 预览链接（`?preview=1&token=eyJ...`）：记录受限/未正式发布时的分享机制，token 仅授予该记录读取权限。

### Q1: token 处理

| Option | Description | Selected |
|--------|-------------|----------|
| 不改 | 有意为之的共享机制，保留 | ✓ |
| 发布记录+换干净链接 | publish 后 token 自然失效 | |
| 去掉 token 换访问说明 | 保持记录受限时的替代方案 | |

**User's choice:** 不改
**Notes:** 用户原话："这个不改，因为是要共享给大家的"。REL-05 的实质由"撤销 token"变更为"确认该链接为有意的共享机制并保留"；全历史密钥扫描仍保留，但目的变为确认除这条已知链接外无其他泄密。

### Q2: 仓库当前可见性

| Option | Description | Selected |
|--------|-------------|----------|
| 私有 | token 风险暂限于有读权限者 | |
| 已公开 | token 已暴露公网 | |
| 帮查 | 用 gh 查 | |

**User's choice:** （未答）
**Notes:** 按项目框架默认处理：当前私有、里程碑结束时公开；用户未纠正。

---

## Claude's Discretion

- AUDIT.md 的严重度分级方案（建议 P0/P1/P2）与报告结构
- 审查代理的切分方式（按子系统 × 维度）
- pyproject.toml / uv.lock / requirements.txt 导出结构
- `data-v1` 基线工件的具体形态（tag + golden 副本 vs 仅 tag）
- 许可证默认 MIT（README badge 已声明）——用户选择不讨论此题，采用默认并明示可推翻

## Deferred Ideas

- Zenodo 记录 19135551 正式 publish 后，将 README 链接替换为无 token 的干净记录 URL（预览 token 在 publish 时自然失效）——发布后的顺手项，非本里程碑必做
