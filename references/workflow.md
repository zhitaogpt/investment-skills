# Investment Research Workflow — 6 阶段工作流

## Overview

本团队采用 6 阶段严格顺序工作流，模拟真实投行/对冲基金的投研协作。每个阶段有明确的输入输出和参与者。

## Phase 1 — 数据收集（并行）

**参与者**: 5 名分析师（并行运行）
**时间占比**: ~40%

| Agent | 职责 | 数据来源 |
|-------|------|----------|
| market-analyst | 技术面分析：价格走势、MACD/RSI/BB/MA/KDJ | `fetch_market_data.py` + WebSearch |
| sentiment-analyst | 舆情分析：社交媒体、分析师评级、机构 vs 散户情绪 | WebSearch |
| company-news-analyst | 公司新闻：公司事件、行业动态、内部人交易 | WebSearch |
| macro-analyst | 宏观政策：GDP/CPI/PMI、货币政策、产业政策、地缘政治 | WebSearch |
| fundamentals-analyst | 基本面：财报、估值指标、同行对比 | `fetch_fundamentals.py` + WebSearch |

**输出**: 5 份独立分析报告（英文）

### 执行方式

Lead 使用 `Agent` tool 并行派遣 5 个分析师，每个分析师在后台独立运行。分析师完成后通过 `SendMessage` 将报告发送给 Lead。

## Phase 2 — 多空辩论（串行，1-2 轮）

**参与者**: bull-researcher, bear-researcher
**输入**: Phase 1 的 5 份分析报告

### Round 1（必选）
1. 派遣 `bull-researcher`（附带 5 份报告摘要）→ 构建看多论点
2. 等待 bull 发回论证
3. 派遣 `bear-researcher`（附带 5 份报告摘要 + bull 的论点）→ 构建看空论点并反驳
4. 等待 bear 发回论证

### Round 2（可选）
5. 将 bear 的论点发送给 bull，让其反驳
6. 将 bull 的反驳发送给 bear，让其最终反驳

**输出**: 完整的多空辩论记录（每方 800-1200 词）

## Phase 3 — 研判裁决（Lead 独立完成）

**参与者**: Lead（Research Manager 角色）
**输入**: 5 份分析报告 + 多空辩论记录

Lead 阅读所有材料，作为 Research Manager 做出独立研判结论。不需要派遣 Agent。

**输出**: 研判结论（含投资方向、关键理由、置信度）

## Phase 4 — 交易方案

**参与者**: trader
**输入**: Phase 3 的研判结论

派遣 `trader`，将研判结论发送给他，制定具体可执行的交易方案。

**输出**: 交易方案（入场/止损/止盈/仓位/时间框架）

## Phase 5 — 风控辩论（串行，1 轮）

**参与者**: risk-aggressive, risk-conservative, risk-neutral
**输入**: 交易方案

三方串行辩论：
1. `risk-aggressive` — 评估上行机会，挑战保守假设
2. `risk-conservative` — 评估下行风险，建议更严格止损（含 aggressive 观点）
3. `risk-neutral` — 综合两方，给出最终风险评估（含两方观点）

**输出**: 三方风控评估

## Phase 6 — 最终决策 & 报告

**参与者**: Lead（Portfolio Manager 角色）
**输入**: 所有阶段的输出

1. Lead 综合所有信息，以 Portfolio Manager 身份做出最终决策
2. 生成最终投资决策报告（中英双语）
3. 保存报告到 `reports/{TICKER}_{DATE}.md`
4. 清理团队资源

**输出**: 最终投资决策报告

## Workflow Rules

1. **Phase 1 必须并行**: 5 个分析师在同一条消息中同时启动
2. **Phase 2 辩论有序**: bull 先发言 → bear 回应 → (可选) 再辩论
3. **Phase 3 Lead 独立**: 不派遣 Agent，Lead 自己分析决策
4. **Phase 5 风控串行**: aggressive → conservative → neutral
5. **报告语言**: 分析用英文（便于搜索），最终报告中英双语
6. **数据时效**: 所有数据围绕用户指定的分析日期
