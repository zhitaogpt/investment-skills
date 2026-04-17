---
name: investor
description: "Codex 兼容的系统化投研技能：针对单一标的执行多阶段投资研究，覆盖数据、研究、观点对照、交易计划、风险评估与最终中文报告。"
user_invocable: true
---

# investor — Codex 兼容的系统化投研技能

> 当用户要求进行更完整、更系统、分阶段的投资研究时使用本 skill。

这个 skill 比 `invest` 更重，适合：

- 用户明确要求“系统化”“全面”“深度”投研
- 用户希望得到多阶段分析与交易方案
- 用户希望看到更完整的风险评估和最终投资决策框架

默认由当前 Codex 主 agent 主导执行全部关键路径。只有当用户明确要求使用子 agent / delegation / parallel work 时，才并行委派非阻塞子任务。

## 触发方式

用户不需要输入 `/investor`。以下自然语言请求都可以触发：

- 系统化分析 NVDA
- 给我一份完整的投资决策报告
- 从基本面、技术面、宏观、情绪几个角度全面分析某只股票
- 做一份多阶段投研结论并给出交易计划

以下示例仅作为参数说明：

```text
/investor NVDA
/investor NVDA 2026-03-27
/investor 600519
/investor 000858
/investor 0700.HK
```

## 输入解析

### Ticker 规范化

| 输入格式 | 识别为 | 转换结果 | 示例 |
|---|---|---|---|
| 纯字母 | 美股 | 不变 | NVDA |
| 6 位数字，6 开头 | 上交所 A 股 | 加 `.SS` | 600519 → 600519.SS |
| 6 位数字，0/3 开头 | 深交所 A 股 | 加 `.SZ` | 000858 → 000858.SZ |
| 数字 + `.HK` | 港股 | 不变 | 0700.HK |
| 已有 `.SS/.SZ/.HK` | 对应市场 | 不变 | 600519.SS |

### 日期处理

- 若用户提供日期，使用该日期。
- 若未提供，默认使用当天日期。
- 日期统一为 `YYYY-MM-DD`。

## 依赖与脚本路由

在执行前，优先检查脚本是否存在，并根据市场路由：

### A 股
- `scripts/fetch_ashare_market.py {CODE} [DATE] [DAYS]`
- `scripts/fetch_ashare_fundamentals.py {CODE}`

### 美股 / 港股
- `scripts/fetch_market_data.py {TICKER} [DATE] [DAYS]`
- `scripts/fetch_fundamentals.py {TICKER}`
- `scripts/fetch_sec_filings.py {TICKER} [DAYS]`（仅美股）

依赖缺失时可以提示：

```bash
pip3 install yfinance akshare
mkdir -p reports/
```

仅在必要且获得授权时再执行安装。

## 执行原则

- 默认由主 agent 串行完成关键路径。
- 用户若未明确要求 delegation，不要启用子 agents。
- `.codex/agents/*.md` 是角色参考资料，不是自动注册的 agent 类型。
- 若使用子 agents，必须由主 agent 负责汇总、裁决和最终输出。
- 默认直接在对话中输出最终报告；仅当用户要求时写入 `reports/`。

## 6-Phase Workflow

### Phase 1 — 数据收集与分析框架建立

主 agent 完成：

1. 规范化 TICKER 与日期
2. 识别市场并选择正确脚本路由
3. 收集价格、技术、基本面、公告 / filing、评级等核心数据
4. 建立以下 5 个分析维度：
   - Technical analysis
   - Sentiment analysis
   - Company news / industry analysis
   - Macro / policy analysis
   - Fundamental / valuation analysis

如果用户明确要求并行分析，可参考：

- `.codex/agents/market-analyst.md`
- `.codex/agents/sentiment-analyst.md`
- `.codex/agents/company-news-analyst.md`
- `.codex/agents/macro-analyst.md`
- `.codex/agents/fundamentals-analyst.md`

用 `spawn_agent` 委派这些维度，但最终仍由主 agent 统一汇总。

### Phase 2 — 五维研究整合

围绕以下五个维度形成结构化结论：

1. 技术面：趋势、动量、支撑阻力、放量缩量、技术风险
2. 情绪面：社交媒体、分析师评级、市场预期、拥挤度
3. 公司与行业：公司新闻、竞争格局、行业趋势、内部人交易
4. 宏观与政策：货币环境、政策约束、行业监管、汇率 / 利率 / 周期影响
5. 基本面与估值：收入、利润、现金流、资产负债、相对估值、DCF / SOTP 可行性

如果数据不足，应指出缺口与对结论的影响。

### Phase 3 — 多空观点对照

默认由主 agent 完成多头与空头两侧分析，并给出对照结论。

推荐过程：

1. 列出多头核心论点 3–5 条
2. 列出空头核心论点 3–5 条
3. 找出最关键的 2–4 个争议点
4. 对每个争议点判断：
   - 哪一方证据更充分
   - 争议来自事实、时间维度还是估值假设
   - 哪些问题仍需后续验证

如用户明确要求使用多 agents，可参考：

- `.codex/agents/bull-researcher.md`
- `.codex/agents/bear-researcher.md`

这时可用两个子 agents 分别扮演 bull / bear researcher。若需要第二轮 rebuttal，可用 `send_input` 发送对方观点并让其回应。若已不需要，完成后关闭子 agents。

### Phase 4 — 研判裁决

主 agent 以 Research Manager 身份给出：

- 投资方向：看多 / 看空 / 中性
- 关键理由：3–5 条
- 置信度：1–10
- 哪些结论最稳健
- 哪些结论最依赖假设

### Phase 5 — 交易方案与风控对照

主 agent 默认自己完成，必要时可参考 trader 与 risk 系列角色文件。

#### 交易方案至少包含

- 入场方案或观望条件
- 分批建仓 / 减仓计划
- 止损与止盈设计
- 时间框架
- 催化剂日历
- 悲观 / 基准 / 乐观情景下的路径判断

#### 风控评估至少包含

- 激进视角：是否错过趋势、仓位是否过轻
- 保守视角：最大回撤、估值杀伤、基本面失速风险
- 中性视角：综合建议与最终采纳方案

可参考：

- `.codex/agents/trader.md`
- `.codex/agents/risk-aggressive.md`
- `.codex/agents/risk-conservative.md`
- `.codex/agents/risk-neutral.md`

如果用户明确要求并行风险评估，可分别委派子 agents，但主 agent 必须做最终裁决。

### Phase 6 — 最终决策与报告

主 agent 以 Portfolio Manager 身份输出最终中文报告。

默认直接在对话中返回；若用户明确要求保存，则写入：

```text
reports/{TICKER}_{DATE}.md
```

## 推荐输出结构

```markdown
# 投资决策报告：{TICKER} ({COMPANY_NAME})
## 日期：{DATE}

### 评级
### 执行摘要
### 核心数据概览
### 五维研究摘要
### 多空观点对照
### 研判裁决
### 风险评估
### 交易建议
### 置信度
### 风险免责声明
```

## 角色参考文件

### 研究角色
- `.codex/agents/bull-researcher.md`
- `.codex/agents/bear-researcher.md`
- `.codex/agents/company-news-analyst.md`
- `.codex/agents/fundamentals-analyst.md`
- `.codex/agents/macro-analyst.md`
- `.codex/agents/market-analyst.md`
- `.codex/agents/sentiment-analyst.md`
- `.codex/agents/trader.md`

### 风控角色
- `.codex/agents/risk-aggressive.md`
- `.codex/agents/risk-conservative.md`
- `.codex/agents/risk-neutral.md`

## Codex 兼容规则

- 不要假设 `/investor` 是平台原生命令。
- 不要假设存在 TeamCreate、TaskCreate、mailbox、team-lead、TeamDelete 等 Claude 专属机制。
- 不要假设 `.codex/agents/*.md` 会自动注册。
- 若使用多 agents，使用 `spawn_agent`、`send_input`、`wait_agent`、`close_agent` 手工编排。
- 没有用户明确授权时，不要擅自并行委派。
- 最终裁决、报告输出、文件写入决定权都在主 agent。
- 不要修改 `.claude` 原始版本；本目录是 Codex 兼容副本。

---

*Disclaimer: This tool generates AI-powered investment research simulations for educational purposes only. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions.*
