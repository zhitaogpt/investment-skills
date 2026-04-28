---
name: invest
description: "任务驱动的投研分析技能 — 3 步完成数据研究、多空辩论、决策报告，自动生成中文投资报告。使用场景：(1) 用户输入 /invest TICKER 分析股票 (2) 用户要求分析某只股票的投资价值 (3) 用户需要投资决策报告。支持 A 股(600519)、美股(NVDA)、港股(0700.HK)。"
---

# invest — 任务驱动的投研分析

> `/invest TICKER [DATE]`

3 步完成：Lead 研究数据 → 多空辩论 → 决策报告

**哲学：tasks = agents。只有需要独立对抗视角的辩论才 spawn agent，其余 Lead 自己完成。**

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

## 3-Step Workflow

### Step 1: 数据收集 & 信息研究（Lead 直接完成）

Lead 自己跑脚本 + WebSearch，不 spawn agent。

**1a. 跑数据脚本**

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

从脚本输出中提取 `{data_summary}`：
- 当前价、涨跌幅、RSI/MACD/均线
- PE/PB、营收增速、利润增速、负债率
- 分析师评级、目标价、内部人交易、机构持仓

**1b. WebSearch 信息研究**

用 `mcp__websearch__GoogleSearch` 顺序搜索以下 6 个维度，汇总为 `{research_summary}`：

| 维度 | 搜索关键词（示例） |
|------|------------------|
| 公司新闻 | "{TICKER} 最新新闻 2026"、"{公司名} 行业动态"、"{公司名} 内部人交易" |
| 市场情绪 | "{TICKER} 分析师评级 2026"、"{公司名} 机构持仓"、"{TICKER} 散户情绪" |
| 宏观政策 | "{行业} 政策 2026"、"{行业} 宏观经济"、"{行业} 监管动态" |
| 竞对分析 | "{行业} 竞争格局 2026"、"{公司名} 竞争对手"、"{细分赛道} 市占率"、"{公司名} vs {同行名}" |
| 技术面 | "{TICKER} 技术分析"、"{TICKER} 支撑阻力"、"{TICKER} 趋势" |
| 财务估值 | "{TICKER} 估值分析"、"{TICKER} DCF"、"{公司名} 同行对比" |

搜索规范：
- 始终包含当前年份+月份
- 首次搜索结果有限时至少尝试一次替代关键词
- 丢弃超过 3 个月的数据（除非是结构性事件）
- 所有引用标注来源

**竞对分析要点**（搜索后 Lead 自己整理）：

1. **行业竞争格局**：市场集中度（CR3/CR5）、寡头还是分散、进入壁垒高低
2. **直接竞对画像**：识别 2-5 家核心竞争对手，逐家梳理：
   - 业务重叠度（哪些产品/市场直接竞争）
   - 规模对比（营收、市值、市占率）
   - 优劣势对比（技术、渠道、成本、品牌）
3. **标的护城河评估**：相对竞对，标的的差异化优势和可持续性
4. **替代威胁**：技术路线替代风险（如新能源替代传统能源）、商业模式替代风险
5. **竞争趋势**：行业是走向集中还是分散？标的市占率在提升还是被侵蚀？

**1c. 完成估值计算**

基于脚本数据和搜索结果，Lead 自己完成三层估值：
1. **SOTP 分部估值**（多元业务公司）：每个板块找同行 PE，分别估值
2. **DCF 现金流折现**：逐年 FCF 折现表、终值计算、扣除净负债、三场景对比
3. **相对估值**：同行 PE/PB 对比
4. **估值交叉验证**：三种方法并列对比是否收敛

### Step 2: 多空辩论（2 agents，2-3 轮）

辩论者使用 `.claude/agents/` 中的 `bull` / `bear` agent 定义，拥有 Bash + WebSearch，可在辩论中实时查证数据。

**Round 1 — 构建论点**：
单条消息并行 spawn `bull` 和 `bear`（`run_in_background: true`，命名为 `bull` 和 `bear`），prompt 包含：
- `{data_summary}` + `{research_summary}` + 估值计算结果
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

### Step 3: 决策 & 报告（Lead 完成）

Lead 一次性完成以下所有内容：

**3a. 研判**：投资方向 + 3-5 条关键理由 + 置信度 (1-10)

**3b. 交易方案**（分批建仓 + 触发条件）：
- **分批建仓策略**: 分 2-3 批，标注每批的价格区间、仓位比例、触发条件
- **触发条件式止损**: 不仅设价格止损，还列出基本面止损条件（如：净利增速低于 X%、合约价涨幅不足 X%、大股东公告减持 >X% 股份）
- **触发条件式止盈**: TP1 减仓比例 + 止损上移、TP2 清仓、极端估值清仓
- **催化剂时间线**: 列出未来 3-6 个月关键事件及预期影响
- **最大回撤估算**: 悲观情景（PE 压缩 + 增速放缓）的大致股价底

**3c. 风险评估**（Lead 从三个角度审视）：

| 风控角色 | 评估内容 |
|---------|---------|
| 激进派 | 是否过于保守？踏空风险？建议仓位和建仓区间 |
| 保守派 | 最大回撤？止损够不够？建议仓位和建仓区间 |
| 中性派（采纳） | 综合裁决 — 采纳哪方框架 + 吸收另两方有效论点 |

**Portfolio Manager 综合**：采纳中性派框架，给出核心风险排序、风险缓释措施。

**3d. 写报告**：中文，保存到 `reports/{TICKER}_{中文名称}_{DATE}.md`

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