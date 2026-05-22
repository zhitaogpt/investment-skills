# Investment Research Skills / AI 投研分析技能集

> 四个 Claude Code Skill，覆盖快速分析、深度研究、巴菲特价值投资和港股 IPO 分析场景。

## 四个 Skill

| Skill | 命令 | 适用场景 |
|-------|------|----------|
| **`/invest`** | `/invest NVDA` | 快速投研，4步精简版，单人+少量 agent |
| **`/investor`** | `/investor NVDA` | 深度研究，6阶段 12-agent 团队协作 |
| **`/buffett-analysis`** | `/buffett-analysis 600875` | 巴菲特价值投资框架，8步深度分析+多空辩论 |
| **`/hk-ipo`** | `/hk-ipo 商米科技` | 港股 IPO 打新分析，基本面+估值+风险 |

### /invest — 快速投研分析

4 步完成：Lead 跑数据 → 5 并行研究 agent → 多空辩论 → 决策报告

```
/invest NVDA              # 美股
/invest 600519            # A 股
/invest 0700.HK           # 港股
```

### /investor — 12-Agent 投研团队

6 阶段流水线：5 分析师 → 多空辩论 → 研判 → 交易方案 → 3方风控辩论 → 最终报告

```
/investor NVDA 2026-03-27
/investor 600519
```

> `/investor` 需要 `--agent-teams` 模式启动。

### /buffett-analysis — 巴菲特价值投资分析

8 步巴菲特框架：能力圈 → 护城河 → 管理层 → 财务深潜 → 内在价值 → 清单验证 → 案例对标 → 多空辩论裁决。自动拉取最新财报数据，内置 Owner Earnings DCF 和 EPV 估值模型。

```
/buffett-analysis 600875          # A 股
/buffett-analysis BRK-B           # 美股
/buffett-analysis 长江电力         # 支持中文名
```

### /hk-ipo — 港股 IPO 打新分析

基本面+行业+估值+风险四维分析，支持公司名或代码查询。

```
/hk-ipo 商米科技
/hk-ipo 02450
```

## 项目结构

```
investment/
├── .claude/
│   ├── agents/                        # Agent 定义（13个）
│   │   ├── bull.md / bear.md          # ← /invest 多空辩论
│   │   ├── market-analyst.md          # ← /investor 技术面
│   │   ├── sentiment-analyst.md       # ← /investor 舆情
│   │   ├── company-news-analyst.md    # ← /investor 新闻
│   │   ├── macro-analyst.md           # ← /investor 宏观
│   │   ├── fundamentals-analyst.md    # ← /investor 基本面
│   │   ├── bull-researcher.md         # ← /investor 多方
│   │   ├── bear-researcher.md         # ← /investor 空方
│   │   ├── trader.md                  # ← /investor 交易方案
│   │   ├── risk-aggressive.md         # ← /investor 激进风控
│   │   ├── risk-conservative.md       # ← /investor 保守风控
│   │   └── risk-neutral.md            # ← /investor 中性风控
│   ├── skills/
│   │   ├── invest/                    # /invest 快速投研
│   │   │   ├── SKILL.md
│   │   │   └── references/
│   │   ├── investor/                  # /investor 12-agent 深度研究
│   │   │   ├── SKILL.md
│   │   │   └── references/
│   │   ├── buffett-analysis/          # /buffett-analysis 巴菲特价值分析
│   │   │   ├── SKILL.md
│   │   │   └── references/
│   │   │       ├── buffett-checklist.md
│   │   │       ├── buffett-scoring-rubric.md
│   │   │       ├── owner-earnings-valuation.md
│   │   │       └── case-studies.md
│   │   └── hk-ipo-research/           # /hk-ipo 港股 IPO 分析
│   │       ├── SKILL.md
│   │       └── references/
│   └── settings.local.json
├── scripts/                           # 共享数据脚本
│   ├── fetch_market_data.py           # 美股/港股行情（yfinance）
│   ├── fetch_fundamentals.py          # 美股/港股基本面（yfinance）
│   ├── fetch_sec_filings.py           # SEC 8-K/10-K/10-Q（EDGAR）
│   ├── fetch_ashare_market.py         # A 股行情（AKShare）
│   └── fetch_ashare_fundamentals.py   # A 股基本面（AKShare）
├── reports/                           # 报告输出（gitignored）
│   ├── buffett-analysis/              # 巴菲特分析报告
│   └── hk-ipo/                        # 港股 IPO 报告
├── LEGAL.md
└── LICENSE
```

## 安装

```bash
# 1. Clone
git clone git@github.com:zhitaogpt/investment-skills.git ~/repos/investment

# 2. 安装依赖
pip install yfinance akshare

# 3. 启动（/investor 需要 --agent-teams）
claude --agent-teams
```

Skills 和 agents 已在 `.claude/` 目录下，session 启动时自动注册。

## 支持市场

| 市场 | 输入格式 | 数据源 | 示例 |
|------|----------|--------|------|
| 美股 | 字母代码 | yfinance + SEC EDGAR | NVDA, AAPL, BRK-B |
| 上交所 A 股 | 6位(6xx) | AKShare | 600519, 601318 |
| 深交所 A 股 | 6位(0xx/3xx) | AKShare | 000858, 300750 |
| 港股 | 数字.HK | yfinance | 0700.HK, 9988.HK |

## 报告示例

巴菲特分析报告示例：
- [东方电气 (600875) 巴菲特分析](reports/buffett-analysis/600875.SS-buffett-20260521.md)
- [东方电气 vs GE Vernova 对比](reports/buffett-analysis/600875-vs-GEV-comparison-20260521.md)
- [银行股对比分析](reports/buffett-analysis/bank-comparison-20260521.md)

## 依赖

- Claude Code with agent-teams support
- Python 3.8+
- `yfinance` + `akshare`
- Internet access

## Disclaimer

AI-powered investment research for **educational and research purposes only**. Not financial advice.

## License

MIT
