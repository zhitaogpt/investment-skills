---
name: invest
description: "任务驱动的投研分析技能 — 4 步完成数据收集、研究、辩论、决策，自动生成中文投资报告。使用场景：(1) 用户输入 /invest TICKER 分析股票 (2) 用户要求分析某只股票的投资价值 (3) 用户需要投资决策报告。支持 A 股(600519)、美股(NVDA)、港股(0700.HK)。"
---

# invest — 任务驱动的投研分析

> `/invest TICKER [DATE]`

4 步完成：Lead 跑数据 → 并行研究 → 多空辩论 → 决策报告

## Command Format

```
/invest NVDA              # 美股，默认今天
/invest 600519 2026-04-12 # A 股指定日期
/invest 0700.HK           # 港股
```

## Ticker 格式化

| 输入 | 转换 | 示例 |
|------|------|------|
| 纯字母 | 美股，不变 | NVDA |
| 6 位，6 开头 | +.SS | 600519 → 600519.SS |
| 6 位，0/3 开头 | +.SZ | 000858 → 000858.SZ |
| 数字+.HK | 不变 | 0700.HK |

**A 股判定**：6 位纯数字或含 `.SS`/`.SZ` 后缀。

## Setup（首次自动执行）

检测：`test -f scripts/fetch_market_data.py && echo EXISTS || echo MISSING`

如果 MISSING：
```bash
mkdir -p reports/
pip3 install yfinance akshare 2>/dev/null || pip install yfinance akshare 2>/dev/null
```

> Agent 定义（`bull.md`、`bear.md`）在 `.claude/agents/` 目录中，session 启动时自动注册。

## 4-Step Workflow

### Step 1: 数据收集（Lead 直接执行）

不需要 agent。Lead 自己跑脚本。

**A 股**：
```bash
python3 scripts/fetch_ashare_market.py {CODE} {DATE} 90
python3 scripts/fetch_ashare_fundamentals.py {CODE}
```

**美股/港股**：
```bash
python3 scripts/fetch_market_data.py {TICKER} {DATE} 30
python3 scripts/fetch_fundamentals.py {TICKER}
python3 scripts/fetch_sec_filings.py {TICKER} 30   # 仅美股
```

Lead 从脚本输出中提取 `{data_summary}`：
- 当前价、涨跌幅、RSI/MACD/均线
- PE/PB、营收增速、利润增速、负债率
- 分析师评级、目标价、内部人交易、机构持仓

### Step 2: 信息研究（5 并行 agents）

单条消息并行派遣 5 个 agent（全部 `run_in_background: true`），使用 `.claude/agents/` 中的 agent 定义（`subagent_type` 参数）。

Agent 定义文件包含完整的角色 persona、搜索清单、输出格式和引用规则。dispatch prompt **只需传递上下文数据**，不要重复 agent 定义中已有的内容。

| Agent | subagent_type | dispatch prompt 传递的上下文 |
|-------|---------------|---------------------------|
| A — 公司行业 | `company-news-analyst` | `{data_summary}` + TICKER + DATE |
| B — 市场情绪 | `sentiment-analyst` | `{data_summary}` + TICKER + DATE + 脚本路由说明 |
| C — 宏观政策 | `macro-analyst` | `{data_summary}` + TICKER + DATE + 行业名称 |
| D — 技术面 | `market-analyst` | `{data_summary}` + TICKER + DATE + Step 1 行情数据（如有） |
| E — 财务估值 | `fundamentals-analyst` | `{data_summary}` + TICKER + DATE + Step 1 基本面数据（如有） |

**dispatch prompt 模板**（以 Agent E 为例）：
```
分析 {TICKER}，分析日期 {DATE}。

## 关键数据
{data_summary}

## Step 1 基本面数据
{fundamentals_data_from_script}

请按照你的 agent 定义完成完整的财务分析和估值计算。

**重要：不要写任何文件（不要用 Write 工具保存报告）。直接将分析结果作为文本返回即可。最终报告由 Lead 统一生成。**
```

**数据路由补充说明**（A 股 vs 美股，附在 Agent B/D/E 的 prompt 中）：
- A 股: 脚本用 `fetch_ashare_*.py`
- 美股/港股: 脚本用 `fetch_market_data.py` / `fetch_fundamentals.py`

等待 5 个 agent 全部返回。

### Step 3: 多空辩论（2 并行 agents，2-3 轮）

辩论者使用自定义 agent 类型 `bull` / `bear`，拥有 Bash + WebSearch，可在辩论中实时查证数据。

**Round 1 — 构建论点**：
单条消息并行 spawn `bull` 和 `bear`（`run_in_background: true`，命名为 `bull` 和 `bear`），prompt 包含：
- `{data_summary}` + 5 份研究报告
- 数据脚本路由说明
- 指令：构建 3-5 个核心论点，每个有数据支撑，引用来源

等待两个 agent 都返回。

**Round 2 — Rebuttal（默认执行）**：
收齐双方 Round 1 论点后，**并行**用 `SendMessage` 向两个 idle agent 发送 rebuttal 指令：
- 向 bull: "Bear 在 Round 1 提出了以下论点: {bear_round1_argument}。请逐一反驳，并用数据验证 Bear 的主张是否成立。"
- 向 bear: "Bull 在 Round 1 提出了以下论点: {bull_round1_argument}。请逐一反驳，并用数据验证 Bull 的主张是否成立。"

不需要重复 Round 1 上下文（agent 保留记忆）。等待两个 agent 都返回。

**Round 3 — Final Statement（可选）**：
如果 bull confidence score 与 bear risk score 差距 >= 5，或双方在核心事实上矛盾，触发 Round 3。并行 SendMessage 给 bull 和 bear，要求聚焦最关键的 2-3 个因素，简洁陈述（400-600 词）。

**Research Manager 裁决（Lead 自己完成）**：
收齐所有轮次辩论后，Lead 以 Research Manager 身份逐维度裁决：
- 按标的调整维度（如：估值、周期/趋势、内部人信号、地缘政治、第二增长曲线等）
- 每个维度判定：**Bull 胜 / Bear 胜 / 平局** + 关键理由
- 给出综合判断

### Step 4: 决策 & 报告（Lead 完成）

Lead 一次性完成以下所有内容：

**4a. 研判**：投资方向 + 3-5 条关键理由 + 置信度 (1-10)

**4b. 交易方案**（分批建仓 + 触发条件）：
- **分批建仓策略**: 分 2-3 批，标注每批的价格区间、仓位比例、触发条件
- **触发条件式止损**: 不仅设价格止损，还列出基本面止损条件（如：净利增速低于 X%、合约价涨幅不足 X%、大股东公告减持 >X% 股份）
- **触发条件式止盈**: TP1 减仓比例 + 止损上移、TP2 清仓、极端估值清仓
- **催化剂时间线**: 列出未来 3-6 个月关键事件及预期影响
- **最大回撤估算**: 悲观情景（PE 压缩 + 增速放缓）的大致股价底

**4c. 风险评估**（Lead 自己从三个角度审视，详细版）：

| 风控角色 | 评估内容 |
|---------|---------|
| 激进派 | 是否过于保守？踏空风险？建议仓位和建仓区间 |
| 保守派 | 最大回撤？止损够不够？建议仓位和建仓区间 |
| 中性派（采纳） | 综合裁决 — 采纳哪方框架 + 吸收另两方有效论点 |

**Portfolio Manager 综合**：采纳中性派框架，给出核心风险排序、风险缓释措施。

**4d. 写报告**：中文，保存到 `reports/{TICKER}_{中文名称}_{DATE}.md`

报告格式见 `references/report-format.md`。置信度评分使用 **8 维模型**（基本面强度、增长确定性、估值吸引力、内部人信号、舆情支撑、新闻/催化剂、技术面时机、风险收益结构）。

## Rating Scale

| 评级 | 含义 |
|------|------|
| 买入 | 强烈看多，建议入场或加仓 |
| 增持 | 看好前景，逐步增加仓位 |
| 持有 | 维持现有仓位，暂不操作 |
| 减持 | 减少仓位，部分获利了结 |
| 卖出 | 退出仓位或不建议入场 |

---

*Disclaimer: AI-powered investment research for educational purposes only. Not financial advice.*
