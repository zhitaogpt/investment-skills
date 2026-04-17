---
name: invest
description: "Codex 兼容的任务驱动投研技能：针对单一股票或 ETF，按数据收集、研究分析、多空对照、决策报告四步输出中文投资研究结果。支持 A 股、美股、港股。"
---

# invest — Codex 兼容的任务驱动投研技能

> 当用户要求分析某只股票、ETF、A 股、美股或港股的投资价值时使用本 skill。

默认由当前 Codex 主 agent 主导执行：数据收集 → 研究分析 → 多空观点对照 → 决策报告。

## 触发方式

用户不需要输入 `/invest` 命令。只要用户表达了以下任一意图，即可触发本 skill：

- 分析某个标的的投资价值
- 生成投研报告
- 给出买入 / 持有 / 卖出判断
- 对某个股票做多空分析
- 输出交易计划与风险提示

以下示例仅作为参数说明，不表示平台存在 slash command：

```text
/invest NVDA
/invest 600519 2026-04-12
/invest 0700.HK
```

## 输入解析

### Ticker 格式化

| 输入 | 识别市场 | 转换 | 示例 |
|---|---|---|---|
| 纯字母 | 美股 | 不变 | NVDA |
| 6 位，6 开头 | A 股上交所 | +`.SS` | 600519 → 600519.SS |
| 6 位，0/3 开头 | A 股深交所 | +`.SZ` | 000858 → 000858.SZ |
| 数字 + `.HK` | 港股 | 不变 | 0700.HK |
| 已含 `.SS/.SZ/.HK` | 对应市场 | 不变 | 600519.SS |

### 日期处理

- 若用户提供日期，使用该日期。
- 若未提供，默认使用当天日期。
- 日期格式统一为 `YYYY-MM-DD`。

## 依赖与前置检查

在真正执行分析前，先检查以下脚本是否存在：

- `scripts/fetch_market_data.py`
- `scripts/fetch_fundamentals.py`
- `scripts/fetch_sec_filings.py`
- `scripts/fetch_ashare_market.py`
- `scripts/fetch_ashare_fundamentals.py`

如果脚本缺失，应明确告知用户缺哪些文件，而不是假设它们存在。

如果依赖包缺失，可提示需要安装，例如：

```bash
pip3 install yfinance akshare
mkdir -p reports/
```

仅当确有必要且获得授权时再执行安装。

## 数据路由

### A 股
当 TICKER 为 6 位纯数字或带 `.SS/.SZ` 后缀时：

```bash
python3 scripts/fetch_ashare_market.py {CODE} {DATE} 90
python3 scripts/fetch_ashare_fundamentals.py {CODE}
```

### 美股 / 港股
当 TICKER 为纯字母或带 `.HK` 后缀时：

```bash
python3 scripts/fetch_market_data.py {TICKER} {DATE} 30
python3 scripts/fetch_fundamentals.py {TICKER}
python3 scripts/fetch_sec_filings.py {TICKER} 30   # 仅美股
```

## 执行原则

- 默认由主 agent 完成关键路径，不要默认启用子 agents。
- 只有当用户明确要求使用 sub-agents、delegation、parallel agent work 时，才使用 `spawn_agent`。
- `.codex/agents/*.md` 是角色参考资料，不是自动注册的 agent 类型。
- 若启用子 agents，应把角色说明压缩成 prompt，而不是假设存在 `bull`、`bear`、`market-analyst` 之类原生类型。
- 最终结果优先直接回复给用户；只有用户要求落盘时再写入 `reports/`。

## 4-Step Workflow

### Step 1: 数据收集

主 agent 自己执行数据收集，并提取结构化摘要 `{data_summary}`，至少包含：

- 当前价、近期涨跌幅
- RSI / MACD / 均线等技术指标
- PE / PB / 营收增速 / 利润增速 / 负债率
- 分析师评级、目标价、内部人交易、机构持仓（若有）
- 重大公告 / filing / 新闻摘要（若有）

如果数据不全，要明确说明缺口，不要伪造。

### Step 2: 研究分析

默认由主 agent 从以下 5 个维度顺序分析：

1. 公司与行业
2. 市场情绪与舆情
3. 宏观与政策环境
4. 技术面与交易结构
5. 财务与估值

如用户明确要求并行委派，可参考这些文件构造子 agent prompt：

- `.codex/agents/company-news-analyst.md`
- `.codex/agents/sentiment-analyst.md`
- `.codex/agents/macro-analyst.md`
- `.codex/agents/market-analyst.md`
- `.codex/agents/fundamentals-analyst.md`

子 agent 返回后，由主 agent 统一整合，不要要求它们写文件。

### Step 3: 多空观点对照

默认由主 agent 自己完成，多头与空头都由主 agent 明确列出。

推荐输出结构：

- 多头核心论点 3–5 条
- 空头核心论点 3–5 条
- 针对最关键分歧逐条对照
- 判断哪些分歧是“事实分歧”，哪些是“估值 / 预期分歧”

如用户明确要求多 agent，可参考：

- `.codex/agents/bull.md`
- `.codex/agents/bear.md`

这时可用 `spawn_agent` 创建两个子 agent，分别扮演多头 / 空头研究员；若要继续 rebuttal，可用 `send_input` 给已有 agent 追加新一轮指令。

### Step 4: 决策与报告

主 agent 完成以下内容：

#### 4a. 研判结论
- 投资方向：看多 / 中性 / 看空
- 评级：买入 / 增持 / 持有 / 减持 / 卖出
- 关键理由：3–5 条
- 置信度：1–10

#### 4b. 交易方案
- 分 2–3 批建仓或减仓
- 每一批的价格区间与仓位比例
- 触发条件式止损
- 触发条件式止盈
- 催化剂时间线
- 悲观情景下的最大回撤估算

#### 4c. 风险评估
从三个风控视角评估：

- 激进派：是否过于保守、是否存在踏空风险
- 保守派：最大回撤、下行风险、止损是否足够
- 中性派：综合两方观点，给出折中方案

可参考：

- `.codex/agents/risk-aggressive.md`
- `.codex/agents/risk-conservative.md`
- `.codex/agents/risk-neutral.md`

#### 4d. 报告输出
最终报告应使用中文。默认直接在对话中返回；只有用户明确要求时才保存到：

```text
reports/{TICKER}_{DATE}.md
```

## 建议输出格式

```markdown
# 投资研究报告：{TICKER}
## 日期：{DATE}

### 评级
### 执行摘要
### 核心数据概览
### 公司与行业分析
### 情绪与宏观分析
### 技术面分析
### 财务与估值分析
### 多空观点对照
### 风险评估
### 交易建议
### 置信度
### 风险免责声明
```

## 角色参考文件

可按需读取以下角色说明文件作为参考材料：

- `.codex/agents/bull.md`
- `.codex/agents/bear.md`
- `.codex/agents/company-news-analyst.md`
- `.codex/agents/fundamentals-analyst.md`
- `.codex/agents/macro-analyst.md`
- `.codex/agents/market-analyst.md`
- `.codex/agents/sentiment-analyst.md`
- `.codex/agents/risk-aggressive.md`
- `.codex/agents/risk-conservative.md`
- `.codex/agents/risk-neutral.md`

## Codex 兼容规则

- 不要假设 `/invest` 是平台原生命令。
- 不要假设存在 Team、Mailbox、Task、team-lead、TeamDelete 等 Claude 专属对象。
- 不要假设 `.codex/agents/*.md` 会自动注册为 agent 类型。
- 若使用多 agents，使用 Codex 的 `spawn_agent`、`send_input`、`wait_agent`、`close_agent` 手工编排。
- 没有用户明确授权时，不要因为“想并行”就擅自启用子 agents。
- 不要修改 `.claude` 原始版本；本目录是 Codex 兼容副本。

---

*Disclaimer: AI-powered investment research for educational purposes only. Not financial advice.*
