---
name: investor
description: "多 Agent 投研团队 — 12 个 AI Agent 协作完成 6 阶段投资分析，自动生成投资决策报告"
user_invocable: true
---

# Investment Research Team Skill / 多 Agent 投研团队

> 当用户要求进行系统化、多阶段投资研究时使用本 skill。

默认由当前 Codex agent 主导执行；只有当用户明确要求使用子 agent / delegation 时，才将非阻塞子任务并行委派。

## Command Format / 命令格式

```
/investor NVDA                    # 分析美股 NVDA（默认今天）
/investor NVDA 2026-03-27         # 分析美股 NVDA 指定日期
/investor 600519                  # 分析 A 股贵州茅台（自动识别为 600519.SS）
/investor 000858                  # 分析 A 股五粮液（自动识别为 000858.SZ）
/investor 0700.HK                 # 分析港股腾讯
```

---

## Setup

Agent 定义文件在 `.claude/agents/` 目录中，不会自动注册到 Codex；如需角色分工，请将角色说明作为参考材料读取。

首次运行前确保依赖已安装：
```bash
pip3 install yfinance akshare 2>/dev/null || pip install yfinance akshare 2>/dev/null
mkdir -p reports/
```

### 数据脚本路由

**A 股**（6 位纯数字或 .SS/.SZ 后缀）：
- `scripts/fetch_ashare_market.py {CODE} [DATE] [DAYS]` — 行情 + 技术指标
- `scripts/fetch_ashare_fundamentals.py {CODE}` — 基本面 + 资金流向

**美股/港股**（纯字母或 .HK 后缀）：
- `scripts/fetch_market_data.py {TICKER} [DATE] [DAYS]` — 股价 + 技术指标
- `scripts/fetch_fundamentals.py {TICKER}` — 基本面 + 评级 + 内部人交易
- `scripts/fetch_sec_filings.py {TICKER} [DAYS]` — SEC Filing（仅美股）

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

**Step 1**: 使用 `（Claude 专属团队机制，不适用于 Codex）` 创建团队：
```json
{"team_name": "invest-{TICKER}", "description": "Investment research for {TICKER}"}
```

**Step 2**: 使用 `（Claude 专属任务机制，不适用于 Codex）` 创建 5 个分析任务：
- "Technical analysis for {TICKER}" (owner: market-analyst)
- "Sentiment analysis for {TICKER}" (owner: sentiment-analyst)
- "Company news analysis for {TICKER}" (owner: company-news-analyst)
- "Macro & policy analysis for {TICKER}" (owner: macro-analyst)
- "Fundamental analysis for {TICKER}" (owner: fundamentals-analyst)

**Step 3**: 使用 `Agent` tool **并行派遣 5 个分析师**（单条消息中发起 5 个 Agent 调用，全部 `在 Codex 中仅当用户明确允许 delegation 时使用 spawn_agent 并行处理`）：

> **A 股数据路由规则**：当 TICKER 为 6 位纯数字（如 600519）或含 .SS/.SZ 后缀时，使用 `fetch_ashare_*.py` 脚本；否则使用 `fetch_market_data.py` / `fetch_fundamentals.py`。

- **market-analyst**:
  - A 股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_ashare_market.py {TICKER} {DATE} 30` 获取数据，然后撰写完整的技术面分析报告。完成后用 send_input 将报告发送给 team-lead。"
  - 美股/港股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_market_data.py {TICKER} {DATE} 30` 获取数据，然后撰写完整的技术面分析报告。完成后用 send_input 将报告发送给 team-lead。"
- **sentiment-analyst**: "分析 {TICKER}，分析日期 {DATE}。通过 WebSearch 搜索该股票的社交媒体情绪和分析师评级，撰写舆情分析报告。完成后用 send_input 将报告发送给 team-lead。"
- **company-news-analyst**: "分析 {TICKER}，分析日期 {DATE}。通过 WebSearch 搜索该公司最新新闻、行业动态、内部人交易，撰写公司新闻分析报告。完成后用 send_input 将报告发送给 team-lead。"
- **macro-analyst**: "分析 {TICKER}，分析日期 {DATE}。通过 WebSearch 搜索宏观经济、货币政策、产业政策相关信息，撰写宏观政策分析报告。完成后用 send_input 将报告发送给 team-lead。"
- **fundamentals-analyst**:
  - A 股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_ashare_fundamentals.py {TICKER}` 获取财务数据，然后撰写基本面分析报告。**估值部分必须完成三层计算**：(1) SOTP 分部估值（若公司有多元业务，为每个板块找同行 PE 并分别估值）；(2) DCF 现金流折现（列出逐年 FCF 折现表、终值计算、扣除净负债、三场景对比）；(3) 相对估值（同行 PE/PB 对比）。最后做**估值交叉验证**，将三种方法并列对比是否收敛。完成后用 send_input 将报告发送给 team-lead。"
  - 美股/港股: "分析 {TICKER}，分析日期 {DATE}。请运行 `python3 scripts/fetch_fundamentals.py {TICKER}` 获取财务数据，然后撰写基本面分析报告。**估值部分必须完成三层计算**：(1) SOTP 分部估值（若公司有多元业务，为每个板块找同行 PE 并分别估值）；(2) DCF 现金流折现（列出逐年 FCF 折现表、终值计算、扣除净负债、三场景对比）；(3) 相对估值（同行 PE/PB 对比）。最后做**估值交叉验证**，将三种方法并列对比是否收敛。完成后用 send_input 将报告发送给 team-lead。"

**等待所有 5 个分析师通过 mailbox 发回报告。**

### Phase 2 — 多空辩论（并行，2-3 轮）

收齐 5 份报告后，启动多轮辩论。辩论者拥有 Bash、WebSearch、WebFetch 工具，可在辩论中实时查证数据。

> **数据路由规则同 Phase 1**: A 股（6 位数字或 .SS/.SZ 后缀）使用 `fetch_ashare_*.py`；美股/港股使用 `fetch_market_data.py` / `fetch_fundamentals.py`。请在派遣辩论者时附上此规则。

> **Agent 复用规则**:
> - **Round 1**: 并行 spawn bull-researcher 和 bear-researcher（单条消息 2 个 Agent 调用，全部 `在 Codex 中仅当用户明确允许 delegation 时使用 spawn_agent 并行处理`）
> - Agent 完成 Round 1 后通过 send_input 发回报告，然后自动进入 idle 状态
> - **Round 2+**: 使用 `send_input` 向 idle 的 agent **并行**发送新一轮指令（包含对手 Round 1 论点 + 本轮任务）
> - Idle agent 收到消息后自动唤醒，保留 Round 1 的完整上下文
> - **prompt 中不需要重复前几轮内容**，只需发送新增的对手论点和本轮指令
> - **注意**: 不要使用 Agent tool 的 `resume` 参数或 spawn 新 agent，直接 send_input 即可

**Round 1 — 构建论点**（并行 spawn 两个 agent）:
1. **并行**派遣 `bull-researcher` 和 `bear-researcher`（单条消息中发起 2 个 Agent 调用，全部 `在 Codex 中仅当用户明确允许 delegation 时使用 spawn_agent 并行处理`）：
   - bull-researcher（包含 5 份报告摘要 + TICKER）: "这是 Round 1，分析标的为 {TICKER}，分析日期 {DATE}。请构建你的核心多头论点。你可以运行 fetch 脚本（见下方数据路由规则）或 WebSearch 来验证数据。完成后用 send_input 将报告发送给 team-lead。"
   - bear-researcher（包含 5 份报告摘要 + TICKER）: "这是 Round 1，分析标的为 {TICKER}，分析日期 {DATE}。请构建你的核心空头论点。你可以运行 fetch 脚本（见下方数据路由规则）或 WebSearch 来验证数据。完成后用 send_input 将报告发送给 team-lead。"
2. 等待 bull 和 bear **都**通过 mailbox 发回论证

**Round 2 — Rebuttal**（并行 send_input 给 idle agent）:
3. 收齐双方 Round 1 论点后，**并行**用 `send_input` 向两个 idle agent 发送 rebuttal 指令：
   - 向 bull-researcher: "这是 Round 2 Rebuttal。Bear 在 Round 1 提出了以下论点: {bear_round1_argument}。请逐一反驳，并用数据验证 Bear 的主张是否成立。完成后用 send_input 将 rebuttal 发送给 team-lead。"
   - 向 bear-researcher: "这是 Round 2 Rebuttal。Bull 在 Round 1 提出了以下论点: {bull_round1_argument}。请逐一反驳，并用数据验证 Bull 的主张是否成立。完成后用 send_input 将 rebuttal 发送给 team-lead。"
4. 等待 bull 和 bear **都**通过 mailbox 发回 rebuttal

**Round 3 — Final Statement（可选，仅当双方分歧极大时）**:
5. 检查是否需要 Round 3: 比较 bull confidence score 与 bear risk score。如差距 >= 5 或双方在核心事实上矛盾，则触发 Round 3。
6. 如触发 Round 3: **并行**用 `send_input` 向 bull 和 bear agent 发送 final statement 指令。提醒: "这是 Round 3 Final Statement。请聚焦最关键的 2-3 个因素，简洁陈述（400-600 字）。完成后用 send_input 发回。"
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
- 完成后用 send_input 发送给 team-lead

### Phase 5 — 风控辩论（并行，1 轮）

交易方案出来后，三方**并行**辩论（单条消息中发起 3 个 Agent 调用，全部 `在 Codex 中仅当用户明确允许 delegation 时使用 spawn_agent 并行处理`）：

1. **并行派遣 3 个风控员**：
   - `risk-aggressive`（包含交易方案 + 核心基本面数据 + 多空辩论结果）— 从激进角度评估，指出方案是否过于保守
   - `risk-conservative`（包含交易方案 + 核心风险因素 + 多空辩论结果）— 从保守角度评估，指出方案风险是否被低估
   - `risk-neutral`（包含交易方案 + 核心基本面 + 核心风险 + 多空辩论结果）— 平衡激进与保守，给出风险调整后最优方案

2. **等待所有 3 个风控员通过 mailbox 发回评估**

3. **Lead 综合三方观点**：在 Phase 6 中作为 Portfolio Manager 权衡三方建议，采纳中性风控的框架并根据激进/保守派的有效论点做出调整

### Phase 6 — 最终决策 & 报告

1. **Lead 综合所有信息**，以 **Portfolio Manager** 身份做出最终决策
2. 生成最终投资决策报告，格式参考 `references/report-format.md`
3. 保存报告到 `reports/{TICKER}_{DATE}.md`
4. 使用 `send_input` 向所有队友发送 shutdown 请求
5. 等待确认后，使用 `TeamDelete` 清理团队
6. 告知用户报告已生成

---

## Final Report Format

最终报告必须**用中文撰写**，包含以下部分：

```markdown
# 投资决策报告: {TICKER} ({COMPANY_NAME})
## 日期: {DATE}

### 评级: [买入 / 增持 / 持有 / 减持 / 卖出]

### 执行摘要
### 投资论点
### 分析师报告摘要
### 多空辩论
### 风险评估
### 交易建议
### 置信度
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

## Codex 兼容说明

- 本 skill 可作为 Codex skill 文档直接读取和执行。
- 不要假设 `/invest`、`/investor` 这样的斜杠命令真实存在；应根据用户自然语言请求触发。
- 不要假设 `.claude/agents/*.md` 会自动注册为可调用 agent；如需复用其中角色设定，应把这些文件当作参考文档读取。
- 默认由主 agent 串行完成关键路径。
- 仅当用户明确要求使用 sub-agents、delegation、parallel agents 时，才使用 Codex 的 spawn_agent / send_input / wait_agent。
- 最终输出应直接在对话中返回，或按用户要求写入 `reports/`。
