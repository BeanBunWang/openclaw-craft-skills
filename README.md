# openclaw-craft-skills

A curated collection of skills for [openclaw](https://github.com/openclaw/openclaw) agents, built by extracting and adapting production prompt engineering patterns from Claude Code's source.

Each skill targets a specific improvement category — role clarity, behavioral reliability, anti-rationalization, and operational boundaries — while leaving the agent's original personality and responsibilities untouched.

---

## Skills

### soul-optimizer

**What it does:** Analyzes and optimizes an openclaw `SOUL.md` to improve execution reliability. Applies Claude Code's 6 production prompt patterns selectively — preserving the agent's role, personality, and values while strengthening its behavioral skeleton.

**When to use:** When you want to improve an existing `SOUL.md` — adding clearer boundaries, anti-rationalization guards, tiered prohibitions, or proactive exploration strategies — without changing what the agent *is*.

**Key constraint:** Pattern 5 (structured JSON handoff) is gated: applied only to sub-agents in multi-session orchestration setups, not to conversational assistant souls.

**Source patterns:**
- Claude Code `src/constants/prompts.ts` — `getSimpleDoingTasksSection()`, `getActionsSection()`, `getOutputEfficiencySection()`
- Claude Code `src/tools/AgentTool/built-in/verificationAgent.ts` — anti-rationalization checklist
- Claude Code `src/tools/AgentTool/built-in/exploreAgent.ts` — broad-to-narrow search strategy

---

## Installation

Skills live at `~/.openclaw/workspace/skills/<skill-name>/SKILL.md`.

To install a skill from this repo, copy the skill folder into your openclaw workspace:

```bash
# Install soul-optimizer
cp -r soul-optimizer ~/.openclaw/workspace/skills/soul-optimizer
```

Or symlink for easier updates:

```bash
ln -s "$(pwd)/soul-optimizer" ~/.openclaw/workspace/skills/soul-optimizer
```

After copying, restart the openclaw gateway or reload skills:

```bash
openclaw gateway restart
```

---

## Usage

Once installed, invoke the skill from any connected channel:

```
/soul-optimizer
```

Or reference it by name in a prompt when working with agent configuration files.

---

## Skill Structure

Each skill follows the standard openclaw skill layout:

```
skill-name/
└── SKILL.md          # Required: frontmatter (name, description) + instructions
```

The `description` field in the frontmatter is the primary trigger mechanism — Claude decides whether to invoke a skill based on this field.

---

## Contributing

Contributions welcome. To add a new skill:

1. Create a folder under the repo root: `your-skill-name/`
2. Add a `SKILL.md` with YAML frontmatter (`name` and `description` required)
3. Follow the existing skill structure — keep instructions focused and under 500 lines
4. Update this README with a brief entry in the Skills section
5. Open a PR

**Design principles for skills in this repo:**
- Extract from production sources, not from aspirational ideas
- Prefer observable behavior rules over abstract traits
- Include activation conditions for each rule ("when X, do Y")
- Document which failure mode each pattern is preventing

---

## Background

These skills are based on patterns observed in Claude Code's open-source codebase (snapshot: 2026-03-31). The original patterns live in:

- `src/constants/prompts.ts`
- `src/tools/AgentTool/built-in/*.ts`

Reference: *Claude Code Prompt Engineering 2026 — 6 Production Patterns*
