# Multi-Market Support / 多市场支持说明

## Supported Markets / 支持的市场

| Market | Examples | Ticker Format | Currency | Data Source |
|--------|----------|---------------|----------|-------------|
| **US Stocks** | NVDA, AAPL, MSFT | Pure letters | USD | yfinance (direct) |
| **A-Shares (Shanghai)** | 600519, 601318 | 6xxxxx → {code}.SS | CNY | yfinance (.SS suffix) |
| **A-Shares (Shenzhen)** | 000858, 300750 | 0xxxxx/3xxxxx → {code}.SZ | CNY | yfinance (.SZ suffix) |
| **HK Stocks** | 0700.HK, 9988.HK | {code}.HK | HKD | yfinance (.HK suffix) |

## Ticker Auto-Formatting Rules / 代码自动格式化规则

Scripts automatically detect and format tickers:

```
Input        →  Formatted      →  Market
─────────────────────────────────────────
NVDA         →  NVDA           →  US
AAPL         →  AAPL           →  US
600519       →  600519.SS      →  Shanghai A-share
000858       →  000858.SZ      →  Shenzhen A-share
300750       →  300750.SZ      →  Shenzhen A-share (ChiNext)
0700.HK      →  0700.HK       →  Hong Kong
9988.HK      →  9988.HK       →  Hong Kong
```

## Usage Examples / 使用示例

```bash
# US stocks
/investor NVDA
/investor AAPL 2026-03-27

# A-shares (auto-formatted)
/investor 600519          # 贵州茅台 → 600519.SS
/investor 000858          # 五粮液 → 000858.SZ
/investor 300750          # 宁德时代 → 300750.SZ

# HK stocks
/investor 0700.HK         # 腾讯控股
/investor 9988.HK         # 阿里巴巴
```

## Data Differences by Market / 各市场数据差异

### US Stocks
- **Best data coverage**: Full financials, analyst estimates, insider trading
- **yfinance data**: Comprehensive (all fields populated)
- **News**: Extensive English-language coverage
- **Trading hours**: 9:30-16:00 ET

### A-Shares (China)
- **Data coverage**: Basic financials available; some fields may be N/A
- **yfinance data**: Price data good; fundamental data may be limited
- **News**: Search should include Chinese keywords for better coverage
- **Trading hours**: 9:30-11:30, 13:00-15:00 CST
- **Note**: yfinance A-share data quality varies; cross-reference with WebSearch

### HK Stocks
- **Data coverage**: Generally good; some fields may differ from US format
- **yfinance data**: Price data reliable; fundamentals mostly available
- **Currency**: HKD (watch for USD-denominated dual-listed stocks)
- **Trading hours**: 9:30-12:00, 13:00-16:00 HKT

## Tips for Analysts / 分析师提示

1. **A-shares**: When searching news, use both English and Chinese company names
2. **HK stocks**: Some are dual-listed (e.g., 9988.HK = BABA); check for cross-listing data
3. **Currency awareness**: All price targets and valuations should specify currency
4. **Data gaps**: If yfinance returns N/A for a field, supplement with WebSearch
5. **Market hours**: Data is based on the most recent trading day before the analysis date
