# Investment Decision Report Format / 报告格式规范

## Rating Scale / 评级定义

| Rating | Chinese | Description |
|--------|---------|-------------|
| **Buy** | 买入 | 强烈看多，建议入场或加仓 |
| **Overweight** | 增持 | 看好前景，逐步增加仓位 |
| **Hold** | 持有 | 维持现有仓位，暂不操作 |
| **Underweight** | 减持 | 减少仓位，部分获利了结 |
| **Sell** | 卖出 | 退出仓位或不建议入场 |

## Report Template

```
# Investment Decision Report: {TICKER} ({COMPANY_NAME})
## Date: {DATE}

---

### Rating: [Buy / Overweight / Hold / Underweight / Sell]

> **一句话行动方案（中文）**
> One-line action summary (English)

---

### Executive Summary / 执行摘要
[简要行动方案：入场策略、仓位建议、关键风险水位、时间框架]
[Brief action plan: entry strategy, position sizing, key risk levels, time horizon]

---

### Investment Thesis / 投资论点
[基于分析师报告和辩论的详细理由]
[Detailed reasoning based on analyst reports and debates]

---

### Analyst Reports Summary / 分析师报告摘要

#### Technical Analysis (Score: X/10)
[Key findings from market-analyst]

#### Sentiment Analysis (Score: X/10)
[Key findings from sentiment-analyst]

#### Company News (Score: X/10)
[Key findings from company-news-analyst]

#### Macro & Policy (Score: X/10)
[Key findings from macro-analyst]

#### Fundamentals (Score: X/10)
[Key findings from fundamentals-analyst]

---

### Bull vs Bear Debate / 多空辩论

#### Bull Case（看多论点）
[Key bullish arguments with data]

#### Bear Case（看空论点）
[Key bearish arguments with data]

#### Debate Resolution / 辩论结论
[Who wins and why]

---

### Risk Assessment / 风险评估

#### Three-Way Risk Debate

| Perspective | Position | Key Argument |
|---|---|---|
| Aggressive | ... | ... |
| Conservative | ... | ... |
| Neutral (Adopted) | ... | ... |

#### Key Risk Factors

| Risk | Severity | Probability | Impact |
|---|---|---|---|
| ... | ... | ... | ... |

---

### Trade Recommendation / 交易建议

| Parameter | Value |
|---|---|
| Ticker | {TICKER} |
| Direction | Long / Short / Neutral |
| Rating | [Rating] |
| Entry Strategy | ... |
| Stop Loss | ... |
| Target 1 / 2 / 3 | ... |
| Risk/Reward Ratio | ... |
| Position Size | ... |
| Time Horizon | ... |

---

### Conviction Level / 置信度

| Factor | Score | Weight | Weighted |
|---|---|---|---|
| Fundamental Strength | X/10 | 30% | ... |
| Valuation Attractiveness | X/10 | 20% | ... |
| Sentiment Support | X/10 | 15% | ... |
| News/Catalyst Pipeline | X/10 | 15% | ... |
| Technical Timing | X/10 | 10% | ... |
| Risk/Reward Setup | X/10 | 10% | ... |
| **Weighted Total** | | **100%** | **X/10** |
```

## Conventions / 写作规范

1. **语言**: 分析师报告用英文撰写（便于数据搜索匹配），最终决策报告中英双语
2. **数字引用**: 所有数字需注明数据来源和日期
3. **辩论风格**: 保持对话式，不要简单罗列
4. **报告长度**: 最终报告约 2000-4000 词（不含附录）
5. **文件命名**: `{TICKER}_{DATE}.md`，如 `NVDA_2026-03-25.md`
