# Investment Research Skills / AI 投研分析技能集

> 两个 Claude Code Skill，覆盖从快速分析到深度研究的投研需求。

## 两个 Skill

| Skill | 命令 | 模式 | 适用场景 |
|-------|------|------|----------|
| **`/invest`** | `/invest NVDA` | 4-step 精简版 | 快速分析，单人+少量 agent |
| **`/investor`** | `/investor NVDA` | 6-phase 团队版 | 深度研究，12-agent 协作 |

### /invest — 快速投研分析

4 步完成：Lead 跑数据 → 5 并行研究 agent → 多空辩论 → 决策报告

```
/invest NVDA              # 美股
/invest 600519            # A 股（→ 600519.SS）
/invest 0700.HK           # 港股
```

### /investor — 12-Agent 投研团队

6 阶段流水线：5 分析师 → 多空辩论(2-3轮) → 研判 → 交易方案 → 3方风控辩论 → 最终报告

```
/investor NVDA 2026-03-27
/investor 600519
```

> `/investor` 需要 `--agent-teams` 模式启动。

## 项目结构

```
investment/
├── .claude/
│   ├── agents/                        # Agent 定义（13个，session 启动时自动注册）
│   │   ├── bull.md                    # ← /invest
│   │   ├── bear.md                    # ← /invest
│   │   ├── market-analyst.md          # ← /investor
│   │   ├── sentiment-analyst.md       # ← /investor
│   │   ├── company-news-analyst.md    # ← /investor
│   │   ├── macro-analyst.md           # ← /investor
│   │   ├── fundamentals-analyst.md    # ← /investor
│   │   ├── bull-researcher.md         # ← /investor
│   │   ├── bear-researcher.md         # ← /investor
│   │   ├── trader.md                  # ← /investor
│   │   ├── risk-aggressive.md         # ← /investor
│   │   ├── risk-conservative.md       # ← /investor
│   │   └── risk-neutral.md            # ← /investor
│   ├── skills/
│   │   ├── invest/                    # /invest skill（4-step 精简版，自包含）
│   │   │   ├── SKILL.md
│   │   │   └── references/
│   │   │       ├── report-format.md
│   │   │       └── agent-prompts.md
│   │   └── investor/                  # /investor skill（12-agent 团队版，自包含）
│   │       ├── SKILL.md
│   │       └── references/
│   │           ├── report-format.md
│   │           ├── workflow.md
│   │           └── markets.md
│   └── settings.local.json
├── scripts/                           # 共享数据脚本
│   ├── fetch_market_data.py           # 美股/港股行情（yfinance）
│   ├── fetch_fundamentals.py          # 美股/港股基本面（yfinance）
│   ├── fetch_sec_filings.py           # SEC 8-K/10-K/10-Q（EDGAR）
│   ├── fetch_ashare_market.py         # A 股行情（AKShare）
│   └── fetch_ashare_fundamentals.py   # A 股基本面（AKShare）
├── reports/                           # 报告输出目录
├── examples/
│   └── NVDA_sample_report.md
├── LEGAL.md
└── LICENSE
```

## 安装

```bash
# 1. Clone
git clone git@code.alipay.com:bujue.zzt/investment-team-skill.git ~/repos/investment

# 2. 安装依赖
pip install yfinance akshare

# 3. 启动（/investor 需要 --agent-teams）
cfuse --agent-teams
```

Skills 和 agents 已在 `.claude/` 目录下，session 启动时自动注册。

## 支持市场

| 市场 | 输入格式 | 数据源 | 示例 |
|------|----------|--------|------|
| 美股 | 字母代码 | yfinance + SEC EDGAR | NVDA, AAPL |
| 上交所 A 股 | 6位(6xx) | AKShare | 600519, 601318 |
| 深交所 A 股 | 6位(0xx/3xx) | AKShare | 000858, 300750 |
| 港股 | 数字.HK | yfinance | 0700.HK, 9988.HK |

## 报告示例

报告输出到 `reports/{TICKER}_{DATE}.md`。完整示例见 [examples/NVDA_sample_report.md](examples/NVDA_sample_report.md)。

## 依赖

- Claude Code with agent-teams support
- Python 3.8+
- `yfinance` + `akshare`
- Internet access

## Disclaimer

AI-powered investment research for **educational and research purposes only**. Not financial advice.

## License

MIT
