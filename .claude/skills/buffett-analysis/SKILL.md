---
name: buffett-analysis
description: "巴菲特价值投资分析技能 — 用巴菲特/芒格的投资哲学系统评估一只股票的长期投资价值。8步流程：能力圈检验 → 护城河分析 → 管理层评估 → 财务深潜 → 内在价值计算 → 清单验证 → 案例对标 → 最终裁决。触发场景：(1) 用户输入 /buffett TICKER 分析股票 (2) 用户要求用巴菲特方法/价值投资方法分析某只股票 (3) 用户提到护城河分析、内在价值、安全边际、Owner Earnings (4) 用户问巴菲特会怎么看某只股票。支持 A 股(600519)、美股(NVDA)、港股(0700.HK)。"
---

# buffett-analysis — 巴菲特价值投资分析

> /buffett TICKER [DATE]

8 步完成：能力圈 → 护城河 → 管理层 → 财务 → 估值 → 清单 → 案例 → 裁决

**哲学：用巴菲特的第一性原理评估长期投资价值。只有辩论阶段 spawn agent，其余 Lead 自己完成。**

---

## 命令格式

```
/buffett NVDA              # 美股
/buffett 600519 2026-04-12 # A 股
/buffett 0700.HK           # 港股
```

---

## Ticker 格式化

| 用户输入 | 规则 | 格式化结果 |
|---------|------|-----------|
| 纯字母（如 NVDA） | 美股，保持不变 | NVDA |
| 6位数字开头为 6 | A 股上证，追加 .SS | 600519.SS |
| 6位数字开头为 0 或 3 | A 股深证，追加 .SZ | 000858.SZ |
| 数字+.HK | 港股，保持不变 | 0700.HK |

---

## 环境准备

1. 检查脚本是否存在：
   ```bash
   test -f scripts/fetch_market_data.py && echo EXISTS || echo MISSING
   ```
2. 若 MISSING，执行：`pip install yfinance akshare`
3. 多空辩论 agent 位于 `.claude/agents/bull.md` 和 `.claude/agents/bear.md`

---

## 核心理念

Lead 在分析前内化以下巴菲特/芒格原则：

1. "价格是你付出的，价值是你得到的。"
2. **能力圈**：只分析你能理解的生意，不懂就放入"太难"一堆。
3. **护城河持久性 > 增长速度**：宁选增长慢但护城河在扩宽的公司。
4. **Owner Earnings > GAAP 利润**：关注真正属于股东的现金流。
5. **安全边际 ≥ 30%**：以大幅低于内在价值的价格买入。
6. **逆向思维**：先问"什么会导致这笔投资失败？"
7. **10 年持有视角**：如果不打算持有十年，十分钟都不要持有。
8. "以合理价格买入极好的公司，远胜于以极好价格买入合理的公司。"
9. **管理层诚信不可妥协**：与流氓共事，没有好的结果。
10. **耐心是美德**：宁可错过，不可做错。

---

## 8 步工作流

### Step 1: 能力圈检验（Lead）

**目标**：确认 Lead 能够理解这家公司的商业模式。

**操作**：
- 使用 `mcp__websearch__GoogleSearch` 搜索公司商业模式
- A 股：调用 `mcp__cn-financial__get_company_profile` + `mcp__cn-financial__get_company_info`
- 美股/港股：搜索 + `python3 scripts/fetch_market_data.py {TICKER}`

**输出**：
- 用 3 句大白话描述公司如何赚钱
- 可理解性评分（1-10）：一个 12 岁小孩能听懂吗？
- **若评分 < 4：输出"超出能力圈 — 巴菲特会放入'太难'一堆"，直接 STOP，生成最简 Pass 报告。**

---

### Step 2: 护城河分析（Lead）

**目标**：评估竞争优势的宽度和持久性。

**操作**：
- 运行数据脚本（A 股：`python3 scripts/fetch_ashare_market.py {TICKER}`；美股/港股：`python3 scripts/fetch_market_data.py {TICKER}`）
- `mcp__websearch__GoogleSearch`：竞争地位、市场份额、定价权历史
- A 股：`mcp__cn-financial__get_competitors` + `mcp__cn-financial__get_segments_revenue`

**评分标准（5 类护城河各 0-3 分）**：

| 护城河类型 | 0 分 | 1 分 | 2 分 | 3 分 |
|-----------|------|------|------|------|
| 品牌溢价 | 无品牌认知 | 有知名度 | 可定价高于同行 | 顶级定价权 |
| 网络效应 | 无 | 弱双边 | 强双边 | 赢家通吃 |
| 转换成本 | 无锁定 | 轻度粘性 | 高迁移成本 | 深度嵌入 |
| 成本优势 | 无 | 小规模优势 | 显著低于同行 | 结构性低成本 |
| 监管壁垒 | 无 | 低门槛牌照 | 高门槛许可 | 垄断特许 |

- 判断趋势：护城河在**扩宽 / 稳定 / 收窄**？
- 综合护城河评分（1-10）
- 参考：`references/buffett-scoring-rubric.md`

---

### Step 3: 管理层评估（Lead）

**目标**：评估管理层品格与资本配置能力。

**操作**：
- `mcp__websearch__GoogleSearch`：CEO 背景、资本配置历史、丑闻
- A 股：`mcp__cn-financial__get_insider_trading`

**评估维度**：
- (a) 诚信与透明度
- (b) 资本配置往绩（回购/分红/并购/投资）
- (c) 股东利益一致性（持股比例、薪酬结构）

**芒格过滤器**："避免品格有问题的人，无论他们多有才华。"

**输出**：管理层质量评分（1-10）

---

### Step 4: 财务深潜（Lead）

**目标**：用数字验证商业模式质量。

**数据获取**：
- A 股：
  - `mcp__cn-financial__get_income_statement`（12 季度）
  - `mcp__cn-financial__get_balance_sheet`（4 季度）
  - `mcp__cn-financial__get_cash_flow_statement`（12 季度）
  - `mcp__cn-financial__get_financial_indicators`（12 期）
  - `mcp__cn-financial__get_growth_rates`（12 期）
  - `mcp__cn-financial__get_per_share_data`（12 期）
- 美股/港股：`python3 scripts/fetch_fundamentals.py {TICKER}`

**计算 Owner Earnings**（参考 `references/owner-earnings-valuation.md`）：
```
Owner Earnings = 净利润 + 折旧摊销 - 维持性资本支出
```

**5 项财务测试**：

| 测试项 | 通过标准 |
|-------|---------|
| ROE 一致性 | >15% 连续 5 年+ |
| 资产负债率 | D/E < 0.5 |
| 利润率趋势 | 稳定或上升 |
| Owner Earnings 增长 | > GDP + 通胀（~7%） |
| FCF 转化率 | >80% |

**输出**：财务实力（1-10）、盈利可预测性（1-10）

---

### Step 5: 内在价值计算（Lead）

**目标**：用多种方法估算内在价值并计算安全边际。

**方法 1：Owner Earnings DCF**
- 折现率 10%
- 三种情景（乐观/基准/保守）
- 参照 `references/owner-earnings-valuation.md`

**方法 2：EPV（盈利能力价值）**
```
EPV = 正常化 Owner Earnings / 10%
```

**方法 3：历史倍数对标**
- 参照 `references/case-studies.md` 中巴菲特历史买入倍数

**交叉验证**：三种方法取中位数作为最终内在价值估计。

**安全边际计算**：
```
安全边际 = (内在价值 - 当前价格) / 内在价值
```

**输出**：安全边际评分（1-10）

| 安全边际 | 评分 |
|---------|------|
| ≥50% | 10 |
| 40-49% | 8-9 |
| 30-39% | 6-7 |
| 20-29% | 4-5 |
| 10-19% | 2-3 |
| <10% | 1 |

---

### Step 6: 清单验证（Lead）

**目标**：用结构化清单防止遗漏关键风险。

**操作**：逐项核对 `references/buffett-checklist.md`

**A 部分（10 项必备）**：记录每项 Pass/Fail
**B 部分（12 项红旗）**：记录触发项

**汇总**："A 部分 X/10 通过，B 部分 Y 项红旗触发"

**评分映射**：
- A 全通过 + 0 红旗 → 10
- 每 fail 一项 A → -1
- 每触发一项 B → -0.5

---

### Step 7: 案例对标（Lead）

**目标**：将目标公司与巴菲特历史投资进行模式匹配。

**操作**：
- 读取 `references/case-studies.md`
- 基于 Steps 1-6 分析结果，识别 2-3 个最可比的巴菲特历史投资

**对比维度**：
- 护城河类型
- 入场估值
- 财务特征
- 成长阶段
- 行业地位

**输出**：
- 类比叙事："这类似于巴菲特在 19XX 年投资 XXX，因为..."
- 指出那些投资成功/失败的关键因素

---

### Step 8: 辩论与裁决

#### 8a: 多空辩论

- Spawn `bull` agent 和 `bear` agent（来自 `.claude/agents/`）
- 提供 Steps 1-7 全部数据
- 进行 2 轮辩论（遵循 invest skill 辩论协议）

#### 8b: "巴菲特会怎么说？"

Lead 撰写 300-500 字第一人称叙事，模仿巴菲特奥马哈年度致股东信风格：
- 用朴素比喻解释为何买/不买
- 引用具体巴菲特名言
- 提及具体数字和逻辑

#### 8c: 最终裁决

**综合评分计算**（加权平均）：

| 维度 | 权重 |
|------|------|
| 能力圈可理解性 | 5% |
| 护城河强度 | 20% |
| 管理层质量 | 15% |
| 财务实力 | 15% |
| 盈利可预测性 | 10% |
| 安全边际 | 20% |
| 清单通过率 | 10% |
| 案例匹配度 | 5% |

**特殊规则**：
- 护城河 < 5 → 最高评为 Hold
- 管理层 < 3 → 强制 Pass
- 安全边际 < 3 → 最高评为 Hold

**输出**：最终评级 — Strong Buy / Buy / Hold / Pass

---

## 报告输出格式

报告保存至：`reports/buffett-analysis/{TICKER}-buffett-{YYYYMMDD}.md`

```markdown
# {公司名} ({TICKER}) — 巴菲特价值投资分析

**最终评级：{Strong Buy / Buy / Hold / Pass}**
**综合评分：{X.X}/10**
**分析日期：{YYYY-MM-DD}**

---

## 巴菲特评分卡

| 维度 | 评分 | 权重 | 加权得分 |
|------|------|------|---------|
| 能力圈可理解性 | X/10 | 5% | X.XX |
| 护城河强度 | X/10 | 20% | X.XX |
| 管理层质量 | X/10 | 15% | X.XX |
| 财务实力 | X/10 | 15% | X.XX |
| 盈利可预测性 | X/10 | 10% | X.XX |
| 安全边际 | X/10 | 20% | X.XX |
| 清单通过率 | X/10 | 10% | X.XX |
| 案例匹配度 | X/10 | 5% | X.XX |
| **综合** | | **100%** | **X.XX** |

---

## Step 1: 能力圈检验
{3 句话商业模式描述}

## Step 2: 护城河分析
{5 类护城河评分 + 趋势判断}

## Step 3: 管理层评估
{诚信/资本配置/股东一致性分析}

## Step 4: 财务深潜
{Owner Earnings 计算 + 5 项测试结果}

## Step 5: 内在价值计算
{三种方法估值 + 安全边际}

## Step 6: 清单验证
{A 部分 + B 部分汇总}

## Step 7: 案例对标
{历史投资类比}

## Step 8: 辩论与裁决

### 多空辩论摘要
{Bull/Bear 核心论点}

### 巴菲特会怎么说？
{300-500 字第一人称叙事}

### 最终裁决
{评级 + 理由}

---

## 免责声明
本报告仅供学习研究参考，不构成投资建议。
```

---

## 评级定义

| 评级 | 综合分 | 含义 |
|------|--------|------|
| Strong Buy | ≥8.0 | "以合理价格买入极好的公司" — 重仓 |
| Buy | 6.5-7.9 | 好公司 + 合理价格，值得建仓 |
| Hold | 5.0-6.4 | 公司不错但价格不够便宜 |
| Pass | <5.0 | 放入"太难"一堆 |

---

## 参考文件

| 文件 | 说明 |
|------|------|
| `references/buffett-scoring-rubric.md` | 护城河和综合评分的详细打分标准 |
| `references/owner-earnings-valuation.md` | Owner Earnings 计算方法与 DCF 模板 |
| `references/buffett-checklist.md` | 巴菲特投资清单（A 部分必备 + B 部分红旗） |
| `references/case-studies.md` | 巴菲特历史经典投资案例库 |

---

## 免责声明

本分析技能仅用于投资研究学习，不构成任何投资建议，投资有风险，决策需谨慎。
