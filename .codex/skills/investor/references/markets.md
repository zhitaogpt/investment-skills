# Multi-Market Support / 多市场支持说明（Codex 兼容版）

## Supported Markets / 支持的市场

| Market | Examples | Ticker Format | Currency | Data Source |
|---|---|---|---|---|
| US Stocks | NVDA, AAPL, MSFT | Pure letters | USD | yfinance |
| A-Shares (Shanghai) | 600519, 601318 | 6xxxxx → `{code}.SS` | CNY | AKShare |
| A-Shares (Shenzhen) | 000858, 300750 | 0xxxxx/3xxxxx → `{code}.SZ` | CNY | AKShare |
| HK Stocks | 0700.HK, 9988.HK | `{code}.HK` | HKD | yfinance |

## Ticker Auto-Formatting Rules / 代码自动格式化规则

脚本或主 agent 应自动识别并格式化 ticker：

```text
Input        →  Formatted      →  Market
─────────────────────────────────────────
NVDA         →  NVDA           →  US
AAPL         →  AAPL           →  US
600519       →  600519.SS      →  Shanghai A-share
000858       →  000858.SZ      →  Shenzhen A-share
300750       →  300750.SZ      →  Shenzhen A-share (ChiNext)
0700.HK      →  0700.HK        →  Hong Kong
9988.HK      →  9988.HK        →  Hong Kong
```

## Usage Examples / 使用示例

以下仅为意图示例，不表示存在原生命令：

```text
分析 NVDA
分析 AAPL，日期 2026-03-27
分析 600519          # 贵州茅台 → 600519.SS
分析 000858          # 五粮液 → 000858.SZ
分析 300750          # 宁德时代 → 300750.SZ
分析 0700.HK         # 腾讯控股
分析 9988.HK         # 阿里巴巴
```

## Data Differences by Market / 各市场数据差异

### US Stocks
- Best data coverage: full financials, analyst estimates, insider trading
- yfinance data: generally comprehensive
- News: extensive English-language coverage
- Trading hours: 9:30–16:00 ET

### A-Shares (China)
- Data source: AKShare，通常比 yfinance 更适合 A 股
- Market data: `scripts/fetch_ashare_market.py`
- Fundamentals: `scripts/fetch_ashare_fundamentals.py`
- Data coverage: often sourced from East Money APIs
- News: 搜索时建议同时使用中文公司名与代码
- Trading hours: 9:30–11:30, 13:00–15:00 CST

### HK Stocks
- Data coverage: generally good, but some fields differ from US format
- Price data: usually reliable
- Fundamentals: often available but completeness may vary
- Currency: HKD；注意双重上市与汇率影响
- Trading hours: 9:30–12:00, 13:00–16:00 HKT

## Tips for Analysts / 分析提示

1. A-shares：搜索新闻时建议同时用中文公司名与股票代码。
2. HK stocks：部分公司与美股 ADR / 双重上市主体有关，应检查映射关系。
3. Currency awareness：估值、目标价、止损止盈都应明确币种。
4. Data gaps：若单一数据源返回缺失值，应明确说明并用搜索补足。
5. Market hours：结论应基于分析日期前最近一个有效交易日的数据。
