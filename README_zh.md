# openclaw-craft-skills

> [English](README.md)

基于 [openclaw](https://github.com/openclaw/openclaw) 的精选 skill 合集，通过提炼 Claude Code 生产环境中的 prompt 工程模式而构建。

每个 skill 专注于某一改进方向——角色边界清晰化、行为可靠性、反自我欺骗、操作禁令分级——同时严格保留 agent 原有的性格与职责，不做任何修改。

---

## Skills 列表

| Skill | 描述 |
|---|---|
| [soul-optimizer](skills/soul-optimizer/SKILL.md) | 基于 Claude Code 生产级 prompt 模式，优化 openclaw `SOUL.md` 的执行可靠性，不改变 agent 的角色与性格。 |

### soul-optimizer

分析并优化 openclaw 的 `SOUL.md`，有选择地应用 Claude Code 的 6 大生产级 prompt 模式。保留 agent 的角色、性格和价值观，强化其行为执行骨架。

**适用场景：** 当你想要改进已有的 `SOUL.md` 时——添加更明确的边界声明、反借口清单、分层操作禁令，或主动探索策略。

**核心约束：** 模式 5（结构化 JSON handoff）设有门控条件：仅在多 session 编排系统中的子 Agent SOUL 上应用，对话型助手 SOUL 不适用。

**来源于 Claude Code 的 prompt 模式：**
- `src/constants/prompts.ts` — `getSimpleDoingTasksSection()`、`getActionsSection()`、`getOutputEfficiencySection()`
- `src/tools/AgentTool/built-in/verificationAgent.ts` — 反自我欺骗清单
- `src/tools/AgentTool/built-in/exploreAgent.ts` — 广撒网-收敛探索策略

---

## 安装

### openclaw（主要平台）

Skills 的存放路径为 `~/.openclaw/workspace/skills/<skill-name>/SKILL.md`。

```bash
# 克隆仓库
git clone https://github.com/BeanBunWang/openclaw-craft-skills.git

# 安装指定 skill
cp -r openclaw-craft-skills/skills/soul-optimizer ~/.openclaw/workspace/skills/soul-optimizer
```

也可以用软链接，便于后续更新：

```bash
ln -s "$(pwd)/openclaw-craft-skills/skills/soul-optimizer" ~/.openclaw/workspace/skills/soul-optimizer
```

安装后重启 gateway 使其生效：

```bash
openclaw gateway restart
```

### Claude Code

```bash
git clone https://github.com/BeanBunWang/openclaw-craft-skills.git ~/.claude/openclaw-craft-skills
```

在 Claude Code 设置中将 skills 路径指向 `~/.claude/openclaw-craft-skills/skills/`。

### Cursor

```bash
git clone https://github.com/BeanBunWang/openclaw-craft-skills.git ~/.cursor/openclaw-craft-skills
```

在 Cursor 设置中添加 skills 路径：`~/.cursor/openclaw-craft-skills/skills/`。

---

## 使用方式

安装到 openclaw 后，在任意已连接的频道（WhatsApp、Telegram、Slack 等）中输入：

```
/soul-optimizer
```

---

## Skill 文件结构

每个 skill 遵循标准的 SKILL.md 格式：

```
skills/
└── skill-name/
    └── SKILL.md    # YAML frontmatter（name、description 必填）+ 指令说明
```

frontmatter 中的 `description` 字段是主要的触发机制——agent 根据此字段决定是否调用该 skill。

---

## 贡献指南

欢迎提交新 skill。步骤如下：

1. 在 `skills/` 下新建目录：`skills/your-skill-name/`
2. 创建 `SKILL.md`，包含 YAML frontmatter（`name` 和 `description` 为必填项）
3. 保持说明内容简洁，建议不超过 500 行
4. 在本 README 的 Skills 表格中添加对应条目
5. 提交 PR

**本仓库 skill 的设计原则：**
- 从生产源码提炼，而非来自臆想
- 优先使用可观测的行为规则，而非抽象的性格描述
- 每条规则须包含激活条件（"当 X 时，执行 Y"）
- 注明每个模式针对的具体失效模式

---

## 背景

本合集中的 skill 基于 Claude Code 开源代码库的 2026-03-31 快照，原始模式来源：

- `src/constants/prompts.ts`
- `src/tools/AgentTool/built-in/*.ts`

参考资料：*Claude Code Prompt 工程专题 2026 · 6 大模式解析*

---

## 许可证

[MIT](LICENSE)
