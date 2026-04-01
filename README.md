# openclaw-craft-skills

> [中文版](README_zh.md)

A curated collection of skills for [openclaw](https://github.com/openclaw/openclaw) agents, built by extracting and adapting production prompt engineering patterns from Claude Code's source.

Each skill targets a specific improvement category — role clarity, behavioral reliability, anti-rationalization, and operational boundaries — while leaving the agent's original personality and responsibilities untouched.

---

## Skills

| Skill | Description |
|---|---|
| [soul-optimizer](skills/soul-optimizer/SKILL.md) | Optimize an openclaw `SOUL.md` to improve execution reliability using Claude Code's production prompt patterns, without changing the agent's role or personality. |

### soul-optimizer

Analyzes and optimizes an openclaw `SOUL.md` by selectively applying Claude Code's 6 production prompt patterns. Preserves the agent's role, personality, and values while strengthening its behavioral skeleton.

**When to use:** When you want to improve an existing `SOUL.md` — adding clearer boundaries, anti-rationalization guards, tiered prohibitions, or proactive exploration strategies.

**Key constraint:** Pattern 5 (structured JSON handoff) is gated: applied only to sub-agents in multi-session orchestration setups, not to conversational assistant souls.

**What each of the 6 patterns actually adds to your SOUL.md:**

| Pattern | What gets added | Gate |
|---|---|---|
| P1 — Concise Task Reporting | `## Reporting Results`: sub-agent reports only "what was done / key output / blockers" — no reasoning trace | Sub-agents only |
| P2 — Role Isolation | `## Boundaries`: "EXCLUSIVELY responsible for" declaration + explicit list of out-of-scope operations | All SOULs |
| P3 — Anti-Rationalization | `## Self-Check Before Completing`: role-specific self-deception triggers (e.g. "looks fine") paired with mandatory counter-actions | Verification / QA SOULs only |
| P4 — Tiered Prohibitions | `## Hard Limits`: flat "don't do X" rules restructured into NEVER / CONFIRM / AUTO tiers; irreversible actions placed at top | All SOULs |
| P5 — Structured JSON Handoff | `## Output Format`: explicit JSON schema for machine-readable handoff to coordinator (status / result / key_points / confidence / next_action) | Sub-agents only, when parent parses output programmatically |
| P6 — Proactive Exploration | `## Before Acting, Explore First`: cast wide before acting, try multiple search paths, cite source locations for all conclusions | Information-retrieval / research SOULs |

**Source patterns from Claude Code:**
- `src/constants/prompts.ts` — `getSimpleDoingTasksSection()`, `getActionsSection()`, `getOutputEfficiencySection()`
- `src/tools/AgentTool/built-in/verificationAgent.ts` — anti-rationalization checklist
- `src/tools/AgentTool/built-in/exploreAgent.ts` — broad-to-narrow search strategy

---

## Installation

### openclaw (primary)

Skills live at `~/.openclaw/workspace/skills/<skill-name>/SKILL.md`.

```bash
# Clone the repo
git clone https://github.com/BeanBunWang/openclaw-craft-skills.git

# Install a specific skill
cp -r openclaw-craft-skills/skills/soul-optimizer ~/.openclaw/workspace/skills/soul-optimizer
```

Or symlink for easier updates:

```bash
ln -s "$(pwd)/openclaw-craft-skills/skills/soul-optimizer" ~/.openclaw/workspace/skills/soul-optimizer
```

Reload the gateway after installing:

```bash
openclaw gateway restart
```

### Claude Code

```bash
git clone https://github.com/BeanBunWang/openclaw-craft-skills.git ~/.claude/openclaw-craft-skills
```

Point Claude Code's skills path to `~/.claude/openclaw-craft-skills/skills/` in your settings.

### Cursor

```bash
git clone https://github.com/BeanBunWang/openclaw-craft-skills.git ~/.cursor/openclaw-craft-skills
```

In Cursor settings, add the skills path: `~/.cursor/openclaw-craft-skills/skills/`.

---

## Usage

Once installed in openclaw, invoke the skill from any connected channel:

```
/soul-optimizer
```

---

## Skill Structure

Each skill follows the standard SKILL.md layout:

```
skills/
└── skill-name/
    └── SKILL.md    # frontmatter (name, description) + instructions
```

The `description` field in the frontmatter is the primary trigger mechanism — the agent decides whether to invoke a skill based on this field.

---

## Contributing

To add a new skill:

1. Create a folder under `skills/`: `skills/your-skill-name/`
2. Add a `SKILL.md` with YAML frontmatter (`name` and `description` required)
3. Keep instructions focused and under 500 lines
4. Update this README with an entry in the Skills table
5. Open a PR

**Design principles for skills in this repo:**
- Extract from production sources, not aspirational ideas
- Prefer observable behavior rules over abstract traits
- Include activation conditions for each rule ("when X, do Y")
- Document which failure mode each pattern prevents

---

## Background

These skills are based on patterns observed in Claude Code's open-source codebase (snapshot: 2026-03-31). The original patterns live in:

- `src/constants/prompts.ts`
- `src/tools/AgentTool/built-in/*.ts`

Reference: *Claude Code Prompt Engineering 2026 — 6 Production Patterns*

---

## License

[MIT](LICENSE)
