# Phase 2: Data Contracts & Test Harness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-09
**Phase:** 2-Data Contracts & Test Harness
**Areas discussed:** Schema 严格度, 已知失败测试机制, Advisory 发现处置, 测试数据面

*Note: questions presented as plain-text numbered lists this session (AskUserQuestion option text rendered with control-character corruption for this user — established workaround from the Phase 1 discussion session).*

---

## Schema 严格度

| Option | Description | Selected |
|--------|-------------|----------|
| 全严格 (Recommended) | 四 schema 均 additionalProperties: false + 全字段必填 — 任何漂移立即失败，新字段必须先改 schema（强制版本化，评审友好） | ✓ |
| 核心严/生产者宽 | models_comparison / tasks_index（终端产物）严格；model_performance / task_performance（生产者写入）宽松 | |
| 全宽松 | 四个都只约束必需字段+类型 — 前向兼容最好，形状漂移检测弱 | |

**User's choice:** 全严格
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| 封闭枚举 | 从现有 50 数据集提取指标名作枚举；新指标需同步改 schema；拼错立即抓到 | ✓ |
| 格式约束 (Recommended) | 只要求非空字符串（可选小写规范化 pattern）；新指标零摩擦 | |
| You decide | 由 Claude 判断并说明理由 | |

**User's choice:** 封闭枚举
**Notes:** 用户比推荐项选择了更严格的方案 — 与全严格选择一致的严格度偏好。

## 已知失败测试机制

| Option | Description | Selected |
|--------|-------------|----------|
| xfail(strict=True) (Recommended) | 断言正确行为，当前失败标 xfail；意外转绿即套件失败，强制 Phase 4 显式移除标记 | ✓ |
| 普通 skip + 原因 | 测试存在但跳过；Phase 4 需手动记得移除 | |
| 独立 known_issues 模块 | 集中放置已知缺陷测试；可发现性好但缺少转绿强制力 | |

**User's choice:** xfail(strict=True)
**Notes:** —

## Advisory 发现处置

| Option | Description | Selected |
|--------|-------------|----------|
| xfail 测试先行 (Recommended) | WR-02/WR-03 本阶段捕获为 xfail(strict) 测试，Phase 4 修复转绿；不改代码 | ✓ |
| 现在就修 | 数字冻结前加固比较器/归一化；违背本阶段"造契约不改代码"纪律，需重验 D-06 | |
| 完全延后 | 不写测试，Phase 4/5 修复时再补 | |

**User's choice:** xfail 测试先行
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| 分流 (Recommended) | IN-03/IN-04 零风险微修本阶段落；WR-01→P5（CI gitleaks）、IN-01→P4（比较器改动）、IN-02→backlog | ✓ |
| 全部 backlog 延后 | Phase 2 纯粹只做契约+测试 | |
| 全部并入 Phase 2 | 含 WR-01 令牌钉正则与 IN-02 崩溃防护 | |

**User's choice:** 分流
**Notes:** —

## 测试数据面

| Option | Description | Selected |
|--------|-------------|----------|
| 仅合成 fixture 树 | golden 与确定性都用手工最小模型集；快、与真实数据漂移解耦；真实漂移等 Phase 5 CI | |
| 合成 + 真实树确定性 (Recommended) | golden 用合成树；确定性对真实提交数据跑链两次断言字节一致 + 重生成==提交树（~40s×2） | ✓ |
| You decide | 由 Claude 判断 | |

**User's choice:** 合成 + 真实树确定性
**Notes:** —

## Claude's Discretion

- Schema 位置与版本：`schemas/` 目录、JSON Schema draft 2020-12、四文件 + `$id`
- 枚举自校验：单元测试断言 metric 枚举 ≡ 提交数据实际指标集
- 测试布局：`tests/`（pytest）；配置与 dev group 进 pyproject.toml
- Makefile 经 `uv run` 调用（免激活）；`make data` 从仓库根可用
- JS 索引生成器补 `node:test` 最小单测
- conftest.py 放线程钉扎 + pytest.approx 容差（TEST-02）
- xfail reason 带 finding ID（如 `AUD-01-P0 …`）

## Deferred Ideas

- WR-01 gitleaks 令牌前缀钉正则 — Phase 5
- IN-01 比较器纯整数差异标签 — Phase 4
- IN-02 索引生成器缺目录崩溃防护 — milestone backlog
