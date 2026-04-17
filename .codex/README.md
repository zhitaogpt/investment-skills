# .codex 目录说明

本目录是从项目内 `.claude/` 体系拆分出来的 **Codex 兼容副本层**。

目标：

- 保留 `.claude` 原始内容不变
- 在 `.codex` 中提供一套更适合 Codex 使用的 skill / role 组织方式
- 把 Claude 风格的团队编排语义，改写成 Codex 可执行的主 agent + 可选子 agent 工作流

## 目录结构

```text
.codex/
├── README.md
├── agents/
│   ├── bull.md
│   ├── bear.md
│   ├── bull-researcher.md
│   ├── bear-researcher.md
│   ├── market-analyst.md
│   ├── sentiment-analyst.md
│   ├── company-news-analyst.md
│   ├── macro-analyst.md
│   ├── fundamentals-analyst.md
│   ├── trader.md
│   ├── risk-aggressive.md
│   ├── risk-conservative.md
│   └── risk-neutral.md
└── skills/
    ├── invest/
    │   └── SKILL.md
    └── investor/
        └── SKILL.md
```

## 设计原则

### 1. 不修改 `.claude`

`.claude` 仍然保留给原始 Claude 风格工作流使用。

### 2. `.codex/agents/*.md` 只是参考资料

这些文件：

- 不是自动注册的 agent 类型
- 不是 Codex 原生内建能力
- 不能直接当作 `agent_type=bull` 之类调用

它们的作用是：

- 给主 agent 提供分析框架
- 给子 agent prompt 提供 persona / checklist / 输出格式素材

### 3. 主 agent 负责关键路径

Codex 兼容版默认采用：

- 主 agent 收集数据
- 主 agent 整合分析
- 主 agent 做最终裁决
- 主 agent 输出最终报告

### 4. 只有用户明确要求时才使用子 agents

如果用户明确要求：

- delegation
- parallel agents
- sub-agents
- 多 agent 协作

才使用：

- `spawn_agent`
- `send_input`
- `wait_agent`
- `close_agent`

否则默认不并行委派。

## `invest` 与 `investor` 的区别

### `invest`
轻量版、单标的、四步流程：

1. 数据收集
2. 研究分析
3. 多空观点对照
4. 决策与报告

适合：

- 快速但结构化的单标的分析
- 需要一个明确结论和交易建议
- 不一定需要完整阶段化推演

### `investor`
重型版、系统化、多阶段流程：

1. 数据收集与分析框架建立
2. 五维研究整合
3. 多空观点对照
4. 研判裁决
5. 交易方案与风控对照
6. 最终决策与报告

适合：

- 更完整的投资决策报告
- 更强调过程、裁决与风险控制
- 需要更强的研究组织结构

## Claude → Codex 概念映射

| Claude 风格概念 | Codex 兼容映射 |
|---|---|
| `/invest` / `/investor` | 只是触发示例，不是原生命令 |
| TeamCreate | 无原生对应；改为主 agent 自行组织流程 |
| TaskCreate | 无原生对应；改为 workflow phases / analysis dimensions |
| team-lead | 主 agent |
| mailbox | 主 agent 收集各子 agent 的返回结果 |
| SendMessage | `send_input` |
| 并行 agent 调度 | `spawn_agent` + `wait_agent` |
| team shutdown / TeamDelete | 按需 `close_agent` |
| 自定义 subagent_type | 用 prompt 注入 persona，而非依赖自动注册 |
| session 自动注册 `.claude/agents/*.md` | 不支持；改为读取 `.codex/agents/*.md` 作为参考材料 |

## 兼容性结论

当前 `.codex` 已完成的兼容性改造包括：

- 去除 Claude 专属 team / mailbox / task 语义
- 去除“自动注册 agent 类型”的假设
- 去除对 slash command 的依赖
- 改成主 agent 优先、子 agent 可选的 Codex 编排模型
- 保留原有投研方法论与角色设定

## 维护建议

后续若更新 `.claude/skills` 或 `.claude/agents`：

1. 先更新原始版本
2. 再决定是否同步修改 `.codex` 副本
3. 优先维护语义兼容，而不是逐字同步

换句话说，`.codex` 应该被视为：

> 面向 Codex 的可执行版本，而不是 `.claude` 的机械镜像。
