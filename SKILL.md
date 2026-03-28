---
name: investor
description: "多 Agent 投研团队 — 12 个 AI Agent 协作完成 6 阶段投资分析，自动生成投资决策报告"
user_invocable: true
---

# Investment Research Team Skill / 多 Agent 投研团队

> `/investor <TICKER> [日期]` — 启动 12-Agent 投研团队，6 阶段分析，自动输出投资决策报告

## Command Format / 命令格式

```
/investor NVDA                    # 分析美股 NVDA（默认今天）
/investor NVDA 2026-03-27         # 分析美股 NVDA 指定日期
/investor 600519                  # 分析 A 股贵州茅台（自动识别为 600519.SS）
/investor 000858                  # 分析 A 股五粮液（自动识别为 000858.SZ）
/investor 0700.HK                 # 分析港股腾讯
```

---

## Step 0: Auto-Setup（首次运行时自动执行）

在开始分析之前，检测当前项目是否已完成 setup。执行以下检查：

**检测条件**：`.claude/agents/market-analyst.md` 文件是否存在

**如果不存在**（首次运行），自动执行 setup：

```bash
# 1. 创建目录
mkdir -p .claude/agents/ scripts/ reports/

# 2. 获取 skill 安装目录（此 SKILL.md 所在目录）
SKILL_DIR="<this skill's directory>"

# 3. 复制 Agent 定义文件
cp "$SKILL_DIR"/agents/*.md .claude/agents/

# 4. 复制数据脚本
cp "$SKILL_DIR"/scripts/*.py scripts/

# 5. 检查依赖
pip3 install yfinance akshare 2>/dev/null || pip install yfinance akshare 2>/dev/null

# 6. 生成 AGENTS.md（如果不存在）
# → 见下方 AGENTS.md ���板

# 7. 生成或更新 CLAUDE.md（如果不存在）
# → 见下方 CLAUDE.md 模板
```

**如果已存在**：跳过 setup，直接进入 Phase 1。

### AGENTS.md 模板（setup 时生成）

```markdown
# Investment Research Team - Agent Teams Orchestration Guide

## Team Overview

模拟真实投行/对冲基金的投研团队协作流程。通过 Claude Code agent-teams 模式实现多 Agent 并行协作。

## How It Works

本团队使用 Claude Code 的 native agent-teams 模式：
- Lead（你）：收到用户任务后，通过 TeamCreate 创建团队，通过 Agent tool 派遣队友
- Teammates：在后台运行，通过 mailbox（SendMessage）与 Lead 通信
- TaskList：所有人共享的任务列表

## Available Custom Agent Types

| Agent Type | Role | Description |
|---|---|---|
| market-analyst | 技术面分析师 | 价格走势、技术指标 |
| sentiment-analyst | 舆情分析师 | 社交媒体情绪、分析师评级 |
| company-news-analyst | 公司新闻分析师 | 公司新闻、行业动态、内部人交易 |
| macro-analyst | 宏观政策分析师 | 宏观经济、货币/财政政策、产业政策 |
| fundamentals-analyst | 基本面分析师 | 财报、估值、同行对比 |
| bull-researcher | 看多研究员 | 构建多头论证，可运行脚本和 WebSearch 验证数据 |
| bear-researcher | 看空研究员 | 构建空头论证，可运行脚本和 WebSearch 验证数据 |
| trader | 交易员 | 制定交易方案 |
| risk-aggressive | 激进风控 | 支持高风险高回报 |
| risk-conservative | 保守风控 | 强调资本保全 |
| risk-neutral | 中性风控 | 平衡风险与收益 |

## Workflow Rules

1. Phase 1 必须并行派遣 5 个分析师
2. Phase 2 辩论 2-3 轮：Round 1 (bull → bear) → Round 2 (bull rebuttal → bear closing) → Round 3 (optional)
3. Phase 2 辩论者拥有 Bash/WebSearch/WebFetch 工具，可实时查证数据
4. Phase 5 风控辩论串行：aggressive → conservative → neutral
5. 分析用英文，最终报告中英双语
6. 所有 teammate 通信必须通过 SendMessage
```

### CLAUDE.md 模板（setup 时生成，如果不存在）

```markdown
# Investment Research Team

基于多 Agent 协作的投研团队。使用 agent-teams 模式运行。

## How to Run

claude --agent-teams
# 然后输入：分析 NVDA，分析日期 2026-03-27

## Data Tools

**A 股数据路由**（6 位纯数字代码或 .SS/.SZ 后缀）：
- scripts/fetch_ashare_market.py {CODE} [DATE] [DAYS] — A 股行情和技术指标（akshare）
- scripts/fetch_ashare_fundamentals.py {CODE} — A 股基本面财务数据（akshare）

**美股/港股数据路由**（纯字母或 .HK 后缀）：
- scripts/fetch_market_data.py {TICKER} [DATE] [DAYS] — 股价和技术指标（yfinance）
- scripts/fetch_fundamentals.py {TICKER} — 基本面财务数据（yfinance）

- WebSearch — 新闻、舆情等实时数据

## Output

报告输出到 reports/{TICKER}_{DATE}.md
```

---

## Ticker 格式处理

收到用户的 TICKER 输入后，按以下规则格式化：

| 输入格式 | 识别为 | 转换结果 | 示例 |
|----------|--------|----------|------|
| 纯字母 | 美股 | 不变 | NVDA → NVDA |
| 6 位数字，6 开头 | 上交所 A 股 | 加 .SS | 600519 → 600519.SS |
| 6 位数字，0/3 开头 | 深交所 A 股 | 加 .SZ | 000858 → 000858.SZ |
| 数字 + .HK | 港股 | 不变 | 0700.HK → 0700.HK |
| 已有后缀 (.SS/.SZ/.HK) | 对应市场 | 不变 | 600519.SS → 600519.SS |

将格式化后的 TICKER 用于后续所有分析步骤。

---

## 6-Phase Workflow（严格按顺序执行）

当用户输入 `/investor {TICKER} [DATE]` 时，解析参数：
- `{TICKER}` — 股票代码（按上方规则格式化）
- `{DATE}` — 分析日期，默认今天（格式 YYYY-MM-DD）

然后执行以下 6 个阶段：

### Phase 1 — 创建团队 & 数据收集（并行）

**Step 1**: 使用 `TeamCreate` 创建团队：
```json
{"team_name": "invest-{TICKER}", "description": "Investment research for {TICKER}"}
```

**Step 2**: 使用 `TaskCreate` 创建 5 个分析任务：
- "Technical analysis for {TICKER}" (owner: market-analyst)
- "Sentiment analysis for {TICKER}" (owner: sentiment-analyst)
- "Company news analysis for {TICKER}" (owner: company-news-analyst)
- "Macro & policy analysis for {TICKER}" (owner: macro-analyst)
- "Fundamental analysis for {TICKER}" (owner: fundamentals-analyst)

**Step 3**: 使用 `Agent` tool **并行派遣 5 个分析师**（单条消息中发起 5 个 Agent 调用，全部 `run_in_background: true`）：

> **A 股数据路由规则**：当 TICKER 为 6 位纯数字（如 600519）或含 .SS/.SZ 后缀时，使用 `fetch_ashare_*.py` 脚本；否则使用 `fetch_market_data.py` / `fetch_fundamentals.py`。

- **market-analyst**:
  - A 股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_ashare_market.py {TICKER} {DATE} 30` 获取数据，然后撰写完整的技术面分析报告。完成后用 SendMessage 将报告发送给 team-lead。"
  - 美股/港股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_market_data.py {TICKER} {DATE} 30` 获取数据，然后撰写完整的技术面分析报告。完成后用 SendMessage 将报告发送给 team-lead。"
- **sentiment-analyst**: "分析 {TICKER}，分析日期 {DATE}。通过 WebSearch 搜索该股票的社交媒体情绪和分析师评级，撰写舆情分析报告。完成后用 SendMessage 将报告发送给 team-lead。"
- **company-news-analyst**: "分析 {TICKER}，分析日期 {DATE}。通过 WebSearch 搜索该公司最新新闻、行业动态、内部人交易，撰写公司新闻分析报告。完成后用 SendMessage 将报告发送给 team-lead。"
- **macro-analyst**: "分析 {TICKER}，分析日期 {DATE}。通过 WebSearch 搜索宏观经济、货币政策、产业政策相关信息，撰写宏观政策分析报告。完成后用 SendMessage 将报告发送给 team-lead。"
- **fundamentals-analyst**:
  - A 股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_ashare_fundamentals.py {TICKER}` 获取财务数据，然后撰写基本面分析报告。完成后用 SendMessage 将报告发送给 team-lead。"
  - 美股/港股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_fundamentals.py {TICKER}` 获取财务数据，然后撰写基本面分析报告。完成后用 SendMessage 将报告发送给 team-lead。"

**等待所有 5 个分析师通过 mailbox 发回报告。**

### Phase 2 — 多空辩论（串行，2-3 轮）

收齐 5 份报告后，启动多轮辩论。辩论者现在拥有 Bash、WebSearch、WebFetch 工具，可以在辩论中实时查证数据。

> **数据路由规则同 Phase 1**: A 股（6 位数字或 .SS/.SZ 后缀）使用 `fetch_ashare_*.py`；美股/港股使用 `fetch_market_data.py` / `fetch_fundamentals.py`。请在派遣辩论者时附上此规则。

**Round 1 — 构建论点**:
1. 派遣 `bull-researcher`（包含 5 份报告摘要 + TICKER），让其构建看多论点。提醒 bull: "这是 Round 1，分析标的为 {TICKER}，分析日期 {DATE}。请构建你的核心多头论点。你可以运行 fetch 脚本（见下方数据路由规则）或 WebSearch 来验证数据。"
2. 等待 bull 通过 mailbox 发回看多论证
3. 派遣 `bear-researcher`（包含 5 份报告摘要 + bull 的完整论点 + TICKER），让其构建看空论点并反驳。提醒 bear: "这是 Round 1，分析标的为 {TICKER}，分析日期 {DATE}。请构建你的核心空头论点并直接反驳 Bull 的论点。你可以运行 fetch 脚本（见下方数据路由规则）或 WebSearch 来验证或反驳 Bull 的数据。"
4. 等待 bear 通过 mailbox 发回看空论证

**Round 2 — Rebuttal & Closing**:
5. 派遣 `bull-researcher`（包含 bear Round 1 的完整论点 + TICKER），让其进行 rebuttal。提醒 bull: "这是 Round 2 Rebuttal，分析标的为 {TICKER}，分析日期 {DATE}。Bear 提出了以下论点，请逐一反驳，并用数据验证 Bear 的主张是否成立。"
6. 等待 bull 通过 mailbox 发回 rebuttal
7. 派遣 `bear-researcher`（包含 bull Round 2 的 rebuttal + TICKER），让其做 closing argument。提醒 bear: "这是 Round 2 Closing Argument，分析标的为 {TICKER}，分析日期 {DATE}。Bull 进行了反驳，请做出最终总结陈词，聚焦最关键的风险因素。"
8. 等待 bear 通过 mailbox 发回 closing argument

**Round 3 — Final Statement（可选，仅当双方分歧极大时）**:
9. 检查是否需要 Round 3: 比较 bull confidence score 与 bear risk score。如差距 >= 5 或双方在核心事实上矛盾，则触发 Round 3。
10. 如触发 Round 3: 分别派遣 bull 和 bear，要求各写一轮 400-600 字的 final statement。提醒: "这是 Round 3 Final Statement，标的 {TICKER}。请聚焦最关键的 2-3 个因素，简洁陈述。"
- 如不触发: 直接进入 Phase 3

### Phase 3 — 研判裁决（Lead 自己完成）

阅读辩论记录，作为 **Research Manager** 做出研判结论。不需要派遣 Agent，你自己写。

输出：
- 投资方向（看多/看空/中性）
- 关键理由（3-5 条）
- 置信度（1-10）

### Phase 4 — 交易方案

派遣 `trader`，将研判结论发送给他：
- 基于研判结论，制定具体的交易方案
- 包含入场价格、止损位、止盈目标、仓位比例、时间框架
- 完成后用 SendMessage 发送给 team-lead

### Phase 5 — 风控辩论（串行，1 轮）

交易方案出来后，三方串行辩论：
1. 派遣 `risk-aggressive`（包含交易方案），等待其 mailbox 回复
2. 派遣 `risk-conservative`（包含交易方案 + 激进派观点），等待其 mailbox 回复
3. 派遣 `risk-neutral`（包含交易方案 + 激进派 + 保守派观点），等待其 mailbox 回复

### Phase 6 — 最终决策 & 报告

1. **Lead 综合所有信息**，以 **Portfolio Manager** 身份做出最终决策
2. 生成最终投资决策报告，格式参考 `references/report-format.md`
3. 保存报告到 `reports/{TICKER}_{DATE}.md`
4. 使用 `SendMessage` 向所有队友发送 shutdown 请求
5. 等待确认后，使用 `TeamDelete` 清理团队
6. 告知用户报告已生成

---

## Final Report Format

最终报告必须包含以下部分（中英双语）：

```markdown
# Investment Decision Report: {TICKER} ({COMPANY_NAME})
## Date: {DATE}

### Rating: [Buy / Overweight / Hold / Underweight / Sell]

### Executive Summary / 执行摘要
### Investment Thesis / 投资论点
### Analyst Reports Summary / 分析师报告摘要
### Bull vs Bear Debate / 多空辩论
### Risk Assessment / 风险评估
### Trade Recommendation / 交易建议
### Conviction Level / 置信度
```

完整模板见 `references/report-format.md`。

## Rating Scale

| Rating | Description |
|--------|-------------|
| **Buy** | 强烈看多，建议入场或加仓 |
| **Overweight** | 看好前景，逐步增加仓位 |
| **Hold** | 维持现有仓位，暂不操作 |
| **Underweight** | 减少仓位，部分获利了结 |
| **Sell** | 退出仓位或不建议入场 |

---

*Disclaimer: This tool generates AI-powered investment research simulations for educational purposes only. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions.*
