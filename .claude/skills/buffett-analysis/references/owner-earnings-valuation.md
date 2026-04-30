# Owner Earnings 估值方法论

> "对所有者而言，会计收益数字就是个起点，而不是终点。" — 沃伦·巴菲特，1986年致股东信

## 1. Owner Earnings 定义

巴菲特在1986年致股东信中提出的核心概念：

```
Owner Earnings = 净利润 (Net Income)
              + 折旧与摊销 (D&A)
              + 其他非现金费用 (Non-cash charges)
              - 维护性资本开支 (Maintenance CapEx)
              - 运营资金增量 (Incremental Working Capital, 如需)
```

**关键区别：维护性 CapEx vs 增长性 CapEx**

| 类型 | 定义 | 估算方法 |
|------|------|---------|
| 维护性 CapEx | 维持现有产能和竞争力所需的最低投入 | 约等于折旧（资产轻型企业）或总CapEx的60-80%（重资产企业） |
| 增长性 CapEx | 用于扩大产能、进入新市场的投入 | 总CapEx - 维护性CapEx |

**维护性CapEx估算启发式规则：**
- 资产轻型企业（软件/互联网/品牌消费）：维护CapEx ≈ D&A × 80%
- 中等资本密度（零售/金融）：维护CapEx ≈ 总CapEx × 70%
- 重资产企业（制造/基建/能源）：维护CapEx ≈ 总CapEx × 80%
- 高增长期企业：维护CapEx ≈ D&A（保守假设）

## 2. Owner Earnings DCF 模型

巴菲特使用10%作为最低回报率门槛（不用WACC）。

### 步骤：

**Step A：计算基期 Owner Earnings**
```
取最近4个季度（TTM）的 Owner Earnings
如果有非经常性项目（资产处置、一次性税务等），需调整
```

**Step B：确定增长假设（保守为王）**
```
增长率 = MIN(
  历史5年 Owner Earnings CAGR,
  分析师共识增速,
  名义GDP增速 + 通胀（对成熟企业）
)
```

三情景假设：
| 情景 | 增长率（前10年） | 永续增长率 | 适用条件 |
|------|----------------|-----------|---------|
| 保守 | GDP增速(3-4%) | 2% | 默认情景 |
| 基准 | 历史CAGR的70% | 2.5% | 中性估计 |
| 乐观 | 历史CAGR | 3% | 最乐观但合理 |

**Step C：折现计算**
```
内在价值 = Σ(Year 1-10 Owner Earnings / 1.10^t) + 终端价值 / 1.10^10

终端价值 = Year 10 Owner Earnings × (1 + 永续增长率) / (折现率 - 永续增长率)

每股内在价值 = (内在价值 - 净负债) / 稀释后总股本
```

### DCF计算表模板

| 年 | Owner Earnings | 折现因子(10%) | 现值 |
|-----|----------------|-------------|------|
| 基期 | ¥XX亿 | — | — |
| Y1 | ¥XX亿 | 0.909 | ¥XX亿 |
| Y2 | ¥XX亿 | 0.826 | ¥XX亿 |
| ... | ... | ... | ... |
| Y10 | ¥XX亿 | 0.386 | ¥XX亿 |
| 终端 | ¥XX亿 | 0.386 | ¥XX亿 |
| **合计** | | | **¥XX亿** |

## 3. 盈利能力价值（EPV）

基于Bruce Greenwald方法，是巴菲特风格的"无增长"估值：

```
EPV = 正常化 Owner Earnings / 资本成本(10%)

特许权价值 = EPV - 资产重置价值
  如果 > 0：说明存在护城河（正franchise value）
  如果 ≈ 0：说明是竞争性行业，无超额利润
  如果 < 0：说明公司在摧毁价值
```

EPV的优势：不需要预测增长，避免了最大的估值不确定性。

## 4. 安全边际计算

```
安全边际 = (内在价值 - 当前股价) / 内在价值 × 100%
```

| 安全边际 | 巴菲特态度 |
|---------|-----------|
| > 50% | 极度低估，"用50美分买1美元"——果断重仓 |
| 30-50% | 显著低估——值得买入 |
| 20-30% | 轻度低估——好公司可以接受 |
| 10-20% | 接近合理价——仅对最好的公司可容忍 |
| < 10% | 无安全边际——等待更好的���格 |
| 负值 | 高估——绝不买入 |

**特殊规则**：
- 高质量（护城河评分≥8）公司：最低安全边际可降至20%
- 普通质量公司：最低安全边际需30%
- 周期性/不确定公司：最低安全边际需40%

## 5. 快速估值 Sanity Checks

在做完整DCF之前，先做快速检查：

| 检查项 | 巴菲特标准 | 公式 |
|--------|-----------|------|
| P/Owner Earnings | < 15 为有吸引力 | 股价 / (Owner Earnings/股) |
| 盈利收益率 | > 10年国债 + 3% | Owner Earnings/股 / 股价 |
| P/B + ROE组合 | P/B < 1.5 且 ROE > 15% | 经典格雷厄姆标准 |
| PEG比率 | < 1.0 为理想 | PE / 盈利增速 |
| 回购收益率 | > 3% 为股东友好 | 年回购金额 / 总市值 |

## 6. 数据获取路由

### A股（6位代码或.SS/.SZ）

```
# 利润表 → 净利润
mcp__cn-financial__get_income_statement(symbol, num_quarters=12)

# 现金流量表 → 折旧、CapEx
mcp__cn-financial__get_cash_flow_statement(symbol, num_quarters=12)

# 资产负债表 → 净负债
mcp__cn-financial__get_balance_sheet(symbol, num_quarters=4)

# 财务指标 → ROE, 利润率
mcp__cn-financial__get_financial_indicators(symbol, num_periods=12)

# 每股数据 → EPS, BPS
mcp__cn-financial__get_per_share_data(symbol, num_periods=12)

# 估值指标 → PE, PB
mcp__cn-financial__get_valuation_metrics(symbol, num_periods=100)

# 增长率
mcp__cn-financial__get_growth_rates(symbol, num_periods=12)
```

### 美股/港股

```bash
python3 scripts/fetch_market_data.py {TICKER}
python3 scripts/fetch_fundamentals.py {TICKER}
```

或通过 WebSearch 获取 SEC filings / 年报数据。

### 所有市场通用

```
mcp__websearch__GoogleSearch: 搜索管理层背景、竞争格局、行业趋势
mcp__cn-financial__get_stock_news: A股个股新闻
mcp__cn-financial__get_company_announcements: 公告
```
