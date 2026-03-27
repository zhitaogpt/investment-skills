# Investment Team Skill / 多 Agent 投研团队

> A Claude Code Skill that launches a **12-Agent investment research team** to analyze any stock in 6 phases and produce a comprehensive investment decision report.

```
/investor NVDA
```

One command. 12 AI agents. 6 phases. Full investment analysis.

## What It Does

This skill simulates a professional investment bank / hedge fund research workflow:

```
Phase 1: Data Collection (5 analysts in parallel)
    ├── Market Analyst      → Technical indicators (MACD, RSI, BB, MA)
    ├── Sentiment Analyst   → Social media & analyst ratings
    ├── Company News        → News events, insider trading
    ├── Macro Analyst       → GDP, rates, policy, geopolitics
    └── Fundamentals        → Financials, valuation, peer comparison

Phase 2: Bull vs Bear Debate (1-2 rounds)
    ├── Bull Researcher     → Builds bullish case
    └── Bear Researcher     → Builds bearish case & rebuttals

Phase 3: Research Judgment (Lead as Research Manager)

Phase 4: Trade Plan Design
    └── Trader              → Entry/exit/sizing/stops

Phase 5: Risk Control Debate (3-way)
    ├── Aggressive Risk     → Upside opportunities
    ├── Conservative Risk   → Downside protection
    └── Neutral Risk        → Balanced assessment

Phase 6: Final Decision & Report (Lead as Portfolio Manager)
```

## Sample Output

Here's what a report looks like (excerpt):

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

See [examples/NVDA_sample_report.md](examples/NVDA_sample_report.md) for a complete report.

## Installation

### 1. Clone to your skills directory

```bash
git clone https://github.com/YOUR_USERNAME/investment-team-skill.git ~/.claude/skills/investment-team
```

### 2. Install Python dependency

```bash
pip install yfinance
```

### 3. Start using it

```bash
# Start Claude Code with agent-teams mode
claude --agent-teams

# Then type:
/investor NVDA
```

That's it. The skill handles everything else automatically on first run.

## Usage

### Basic Commands

```bash
/investor NVDA                # Analyze US stock (default: today's date)
/investor NVDA 2026-03-27     # Analyze with specific date
/investor 600519              # Analyze A-share (auto → 600519.SS, Kweichow Moutai)
/investor 000858              # Analyze A-share (auto → 000858.SZ, Wuliangye)
/investor 0700.HK             # Analyze HK stock (Tencent)
```

### Supported Markets

| Market | Format | Examples |
|--------|--------|----------|
| US Stocks | Letters | NVDA, AAPL, MSFT, GOOGL |
| Shanghai A-Shares | 6-digit (6xx) | 600519, 601318, 600036 |
| Shenzhen A-Shares | 6-digit (0xx/3xx) | 000858, 300750, 000001 |
| HK Stocks | Number.HK | 0700.HK, 9988.HK, 3690.HK |

### Auto-Setup (First Run)

On first use in a new project, the skill automatically:
1. Creates `.claude/agents/` with 11 agent definitions
2. Copies data scripts to `scripts/`
3. Generates `AGENTS.md` and `CLAUDE.md`
4. Installs yfinance if needed
5. Creates `reports/` directory

Subsequent runs skip setup and go directly to analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 1: Data Collection (Parallel)       │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐ ┌──────────┐  │
│  │Market  │ │Sentimnt│ │Company │ │ Macro │ │Fundamntl │  │
│  │Analyst │ │Analyst │ │ News   │ │Analyst│ │ Analyst  │  │
│  └───┬────┘ └───┬────┘ └───┬────┘ └──┬────┘ └────┬─────┘  │
│      └──────────┼──────────┼─────────┼───────────┘         │
│                 ▼                                           │
│           Phase 2: Bull vs Bear Debate                      │
│         ┌────────────────────────┐                          │
│         │   Bull ⟷ Bear Debate  │                          │
│         └───────────┬────────────┘                          │
│                     ▼                                       │
│           Phase 3: Research Judgment (Lead)                  │
│                     ▼                                       │
│           Phase 4: Trade Plan                               │
│         ┌───────────────────────┐                           │
│         │       Trader          │                           │
│         └───────────┬───────────┘                           │
│                     ▼                                       │
│           Phase 5: Risk Control Debate                      │
│    ┌────────────┐ ┌──────────────┐ ┌───────────┐           │
│    │ Aggressive │ │Conservative  │ │ Neutral   │           │
│    └─────┬──────┘ └─────┬────────┘ └────┬──────┘           │
│          └──────────────┼───────────────┘                   │
│                         ▼                                   │
│           Phase 6: Final Decision + Report                  │
│         ┌───────────────────────────┐                       │
│         │   Lead (Portfolio Mgr)    ��                       │
│         │  → Final Rating + Report  │                       │
│         └───────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Customization

### Adding a New Agent

1. Create a new `.md` file in `agents/` with frontmatter:
   ```yaml
   ---
   name: your-agent-name
   description: "Agent description"
   tools: Bash, Read, Glob, Grep, SendMessage, TaskUpdate, TaskList, TaskGet
   model: sonnet
   ---
   ```
2. Define the agent's role, responsibilities, and output format
3. Update `SKILL.md` workflow to include the new agent in the appropriate phase

### Modifying Conviction Weights

In the final report, the conviction score uses these default weights:

| Factor | Default Weight |
|--------|---------------|
| Fundamental Strength | 30% |
| Valuation Attractiveness | 20% |
| Sentiment Support | 15% |
| News/Catalyst Pipeline | 15% |
| Technical Timing | 10% |
| Risk/Reward Setup | 10% |

Adjust these in `references/report-format.md` to match your investment style.

## Data Sources

- **Technical data**: yfinance (stock prices, technical indicators)
- **Fundamental data**: yfinance (financials, valuation metrics)
- **News & sentiment**: WebSearch (real-time web search)
- **Macro data**: WebSearch (economic indicators, policy news)

## Requirements

- Claude Code with `--agent-teams` support
- Python 3.8+
- `yfinance` package (`pip install yfinance`)
- Internet access (for WebSearch and yfinance data)

## Disclaimer

This tool generates AI-powered investment research simulations for **educational and research purposes only**. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

## License

MIT
