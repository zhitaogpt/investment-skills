# Investment Team Skill / 多 Agent 投研团队

> A Claude Code Skill that launches a **12-Agent investment research team** to analyze any stock in 6 phases — with multi-round bull/bear debate and real-time data verification — producing a comprehensive investment decision report.

## Quick Start

```bash
# 1. Clone
git clone git@code.alipay.com:bujue.zzt/investment-team-skill.git ~/.claude/skills/investment-team

# 2. Install dependencies
pip install yfinance akshare

# 3. Launch Claude Code and run
/investor NVDA              # US stock
/investor 600519            # A-share (贵州茅台)
/investor 0700.HK           # HK stock (腾讯)
```

First run auto-sets up agent definitions, data scripts, and config files. **Restart the session after first setup** so agent types get registered.

## What It Does

Simulates a professional investment research workflow with 12 AI agents:

```
Phase 1: Data Collection — 5 analysts in parallel
    ├── Market Analyst        → Price action, MACD, RSI, Bollinger Bands, MA
    ├── Sentiment Analyst     → Social media mood, analyst ratings
    ├── Company News Analyst  → Breaking news, insider trading, industry events
    ├── Macro Analyst         → GDP, rates, fiscal/monetary policy, geopolitics
    └── Fundamentals Analyst  → Financials, valuation, peer comparison, fund flow

Phase 2: Bull vs Bear Debate — 2-3 rounds with data verification
    ├── Round 1: Bull builds case → Bear rebuts with counter-evidence
    ├── Round 2: Bull rebuts Bear → Bear delivers closing argument
    └── Round 3: (optional) Final statements if high divergence
    └── Both sides can run scripts + WebSearch mid-debate to verify claims

Phase 3: Research Judgment — Lead synthesizes as Research Manager

Phase 4: Trade Plan
    └── Trader → Entry price, stop loss, targets, position sizing, timeframe

Phase 5: Risk Control Debate — 3-way serial
    ├── Aggressive Risk   → Upside opportunities, challenge conservative assumptions
    ├── Conservative Risk → Downside protection, capital preservation
    └── Neutral Risk      → Balanced risk-adjusted assessment

Phase 6: Final Decision & Report — Lead as Portfolio Manager
```

## Supported Markets

| Market | Format | Data Source | Examples |
|--------|--------|-------------|----------|
| US Stocks | Letters | yfinance + SEC EDGAR | NVDA, AAPL, GOOGL |
| Shanghai A-Shares | 6-digit (6xx) | AKShare | 600519, 601318 |
| Shenzhen A-Shares | 6-digit (0xx/3xx) | AKShare | 000858, 300750 |
| HK Stocks | Number.HK | yfinance | 0700.HK, 9988.HK |

```bash
/investor NVDA                # US stock, default today
/investor NVDA 2026-03-27     # US stock, specific date
/investor 600519              # auto → 600519.SS
/investor 000858              # auto → 000858.SZ
/investor 0700.HK             # HK stock
```

## Data Sources

| Source | Coverage | Data |
|--------|----------|------|
| **yfinance** | US / HK stocks | Price, technicals, financials, analyst recommendations, insider transactions, institutional holders, earnings dates, news |
| **AKShare** | A-shares | Price, technicals, financials, fund flow (资金流向), margin trading (融资融券) |
| **SEC EDGAR** | US stocks | 8-K, 10-K, 10-Q filings |
| **WebSearch** | All markets | Real-time news, sentiment, earnings call transcripts, macro data |

### Data Scripts

```
scripts/
├── fetch_market_data.py          # US/HK price & technicals (yfinance)
├── fetch_fundamentals.py         # US/HK fundamentals + ratings + insiders + news (yfinance)
├── fetch_sec_filings.py          # SEC 8-K/10-K/10-Q filings (EDGAR API)
├── fetch_ashare_market.py        # A-share price & technicals (AKShare)
└── fetch_ashare_fundamentals.py  # A-share fundamentals + fund flow + margin (AKShare)
```

## Auto-Setup (First Run)

On first `/investor` run in a new project, the skill automatically:

1. Symlinks `agents/` → `.claude/agents/` (agent definitions)
2. Symlinks `scripts/` → `scripts/` (data fetch scripts)
3. Generates `AGENTS.md` (team orchestration guide)
4. Generates `CLAUDE.md` (project context)
5. Installs `yfinance` and `akshare` if needed

After setup, **restart the session** — agent types are registered at session startup.

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│              Phase 1: Data Collection (Parallel)          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐ ┌────────┐  │
│  │Market  │ │Sentimnt│ │Company │ │ Macro │ │Fundmtl │  │
│  │Analyst │ │Analyst │ │ News   │ │Analyst│ │Analyst │  │
│  └───┬────┘ └───┬────┘ └───┬────┘ └──┬────┘ └───┬────┘  │
│      └──────────┼──────────┼─────────┼──────────┘        │
│                 ▼                                         │
│        Phase 2: Bull vs Bear Debate (2-3 rounds)         │
│      ┌──────────────────────────────┐                    │
│      │  Bull ⟷ Bear (data-backed)  │                    │
│      └─────────────┬────────────────┘                    │
│                    ▼                                      │
│        Phase 3: Research Judgment (Lead)                  │
│                    ▼                                      │
│        Phase 4: Trade Plan                               │
│      ┌─────────────────────────┐                         │
│      │        Trader           │                         │
│      └─────────────┬───────────┘                         │
│                    ▼                                      │
│        Phase 5: Risk Control Debate                      │
│   ┌────────────┐ ┌────────────┐ ┌───────────┐           │
│   │ Aggressive │→│Conservative│→│  Neutral  │           │
│   └────────────┘ └────────────┘ └─────┬─────┘           │
│                                       ▼                   │
│        Phase 6: Final Decision + Report                  │
│      ┌─────────────────────────────┐                     │
│      │   Lead (Portfolio Manager)  │                     │
│      │   → Rating + Full Report    │                     │
│      └─────────────────────────────┘                     │
└───────────────────────────────────────────────────────────┘
```

## Sample Output

Reports are saved to `reports/{TICKER}_{DATE}.md`. See [examples/NVDA_sample_report.md](examples/NVDA_sample_report.md) for a complete example.

```markdown
# Investment Decision Report: NVDA (NVIDIA Corporation)
## Date: 2026-03-25

### Rating: Overweight

> 逐步增加仓位，利用技术面超卖机会分批建仓
> Gradually increase position, taking advantage of technical oversold conditions

### Trade Recommendation
| Parameter          | Value                                    |
|--------------------|------------------------------------------|
| Direction          | Long                                     |
| Entry Strategy     | 3 tranches: $175 (33%), $171 (33%), $165 |
| Stop Loss          | $155.00 (hard stop, ~11% below current)  |
| Target             | $230-265 (31-51% upside)                 |
| Risk/Reward Ratio  | 1:3.0                                    |
| Time Horizon       | 6-9 months                               |
```

## Requirements

- Claude Code with agent-teams support
- Python 3.8+
- `yfinance` + `akshare` (`pip install yfinance akshare`)
- Internet access (for WebSearch, yfinance, AKShare, SEC EDGAR)

## Disclaimer

This tool generates AI-powered investment research simulations for **educational and research purposes only**. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions.

## License

MIT
