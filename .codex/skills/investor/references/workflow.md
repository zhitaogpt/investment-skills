# Investment Research Workflow — Codex 兼容 6 阶段工作流

## Overview

本工作流用于在 Codex 中执行系统化投研，模拟真实投行 / 对冲基金的研究流程，但不依赖任何 Claude 专属团队机制。

核心原则：

- 默认由主 agent 负责关键路径
- 只有用户明确要求多 agent 协作时，才使用子 agents
- 子 agents 只负责局部分析，主 agent 负责最终裁决与输出

## Phase 1 — 数据收集与五维分析准备

**参与角色**：主 agent；必要时可委派 5 个子 agents
**时间占比**：约 40%

| 维度 | 参考角色 | 典型数据来源 |
|---|---|---|
| 技术面 | market-analyst | `fetch_market_data.py` / `fetch_ashare_market.py` + 搜索 |
| 情绪面 | sentiment-analyst | 搜索、分析师评级、市场预期 |
| 公司与行业 | company-news-analyst | 搜索、公告、行业新闻 |
| 宏观政策 | macro-analyst | 搜索、宏观数据、政策文件 |
| 基本面与估值 | fundamentals-analyst | `fetch_fundamentals.py` / `fetch_ashare_fundamentals.py` + 搜索 |

**输出**：五个维度的结构化研究结论。

### 执行方式

- 默认：主 agent 顺序完成五个维度。
- 可选：若用户明确要求并行委派，则主 agent 用 `spawn_agent` 创建 2–5 个子 agents 分别处理不同维度。
- 子 agents 完成后，把结果返回给主 agent；不要要求子 agents 直接写最终报告文件。

## Phase 2 — 多空观点对照

**参与角色**：主 agent；必要时可选用 bull-researcher / bear-researcher 参考角色
**输入**：Phase 1 的五维研究结果

### 默认模式

主 agent 自己完成：
1. 列出多头核心论点
2. 列出空头核心论点
3. 对关键分歧逐条判断证据强弱

### 可选多 agent 模式

如果用户明确要求多 agent：
1. 用 `spawn_agent` 创建 bull researcher 子 agent
2. 用 `spawn_agent` 创建 bear researcher 子 agent
3. 等待双方返回 Round 1 论点
4. 如需 rebuttal，用 `send_input` 向已有 agent 发送对手论点
5. 结束后由主 agent 汇总，不要把裁决交给子 agent

**输出**：多空观点对照结论。

## Phase 3 — 研判裁决

**参与角色**：主 agent（Research Manager 视角）
**输入**：五维研究结果 + 多空观点对照

主 agent 阅读所有材料，独立做出研判，不委派关键裁决。

**输出**：
- 投资方向
- 关键理由
- 置信度
- 关键假设与待验证问题

## Phase 4 — 交易方案

**参与角色**：主 agent；必要时可参考 trader 角色
**输入**：Phase 3 的研判结论

主 agent 形成可执行交易方案：

- 入场 / 观望条件
- 仓位计划
- 止损 / 止盈
- 时间框架
- 催化剂日历

**输出**：交易方案。

## Phase 5 — 风控对照

**参与角色**：主 agent；必要时可参考 risk-aggressive / risk-conservative / risk-neutral
**输入**：交易方案 + 关键风险因素

默认由主 agent 从三个视角完成：
1. 激进视角：上行机会是否被低估
2. 保守视角：下行风险是否被低估
3. 中性视角：如何折中并形成最终风险框架

如果用户明确要求并行风控评估，可用多个子 agents 分别输出观点，但最终裁决仍由主 agent 完成。

**输出**：风险评估与风险调整后的建议。

## Phase 6 — 最终决策与报告

**参与角色**：主 agent（Portfolio Manager 视角）
**输入**：所有阶段的输出

主 agent：
1. 综合所有信息
2. 输出最终中文报告
3. 如用户要求，保存到 `reports/{TICKER}_{DATE}.md`
4. 如使用过子 agents，在完成汇总后按需 `close_agent`

**输出**：最终投资决策报告。

## Workflow Rules

1. 主 agent 负责关键路径与最终结论。
2. 子 agents 只在用户明确要求 delegation 时启用。
3. 多 agent 模式下，所有子结果都必须回流到主 agent 统一汇总。
4. 最终报告优先中文输出；若用户另有要求，可调整语言。
5. 所有结论都应围绕用户指定分析日期或默认当天日期。
6. 数据不足时必须明确说明，不得伪造。
