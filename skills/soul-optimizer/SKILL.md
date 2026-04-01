---
name: soul-optimizer
description: Analyze and optimize an openclaw SOUL.md to improve execution reliability using Claude Code's production prompt patterns. Use when you want to improve, audit, or refine a SOUL.md for an openclaw agent — especially to add behavioral clarity, anti-rationalization guards, and operational boundaries without changing the agent's role or personality. Trigger on any request involving "optimize SOUL", "improve SOUL.md", "refine agent soul", "openclaw soul", or audit of virtual employee configuration.
---

# Soul Optimizer

## Overview

Improve a SOUL.md's execution reliability by injecting concrete behavioral rules derived from Claude Code's production prompt engineering. The distinction that matters: the **soul** (role identity, personality, values, communication style) is sacred and untouchable. The **execution skeleton** (what to do, what not to do, when to verify, how to report) is exactly what this skill strengthens.

Think of it as adding load-bearing structure to an existing personality: the character stays, the performance sharpens.

## Source Anchors

- `src/constants/prompts.ts` — `getSimpleDoingTasksSection()`, `getActionsSection()`, `getOutputEfficiencySection()`, `getSimpleToneAndStyleSection()`
- `src/tools/AgentTool/built-in/verificationAgent.ts` — Anti-rationalization failure list
- `src/tools/AgentTool/built-in/exploreAgent.ts` — Broad-to-narrow search strategy
- `src/tools/AgentTool/built-in/planAgent.ts` — Role boundary declarations
- PDF reference: *Claude Code Prompt 工程专题 2026 · 6 大模式解析*

## Pattern Selection Matrix

Not all 6 patterns apply to every SOUL. Misapplying them degrades the agent. Use this matrix first.

| Pattern | Applies To | Conversational SOUL | Sub-Agent SOUL |
|---|---|---|---|
| P1 — Concise Task Reporting | Multi-session orchestration | No | Yes |
| P2 — Role Isolation | All SOULs | Yes | Yes |
| P3 — Anti-Rationalization | SOULs with verification/QA duties | Partial | Yes |
| P4 — Strict Prohibitions | All SOULs | Yes | Yes |
| P5 — Structured JSON Handoff | Sub-agents with a coordinator parent | No | Conditional |
| P6 — Proactive Exploration | SOULs with research/information duties | Partial | Yes |

**How to determine SOUL type:**
- Conversational SOUL: final output goes directly to a human user (chat, WhatsApp, Slack)
- Sub-Agent SOUL: output is consumed by another agent (coordinator, parent session); uses `sessions_send` to report back

## Workflow

### Step 1 — Extract and Lock the Protection List

Read the SOUL.md in full. Before changing anything, list every element that must not be touched:

- Role name and one-line role description
- Personality adjectives and described traits (e.g. "direct", "witty", "methodical")
- Stated values and ethical commitments
- Communication style preferences (tone, length, formality)
- Domain-specific knowledge blocks

Write these down explicitly as a **Protection List**. Every output check will reference this list.

### Step 2 — Determine SOUL Type

Ask: who receives the final output of this agent?

- A human user → Conversational SOUL (P1 and P5 do NOT apply)
- A parent agent or coordinator → Sub-Agent SOUL (all patterns potentially apply)
- Ambiguous / multi-mode → Treat as Conversational SOUL by default; add a note

### Step 3 — Apply Pattern 2: Role Isolation

Every SOUL, regardless of type, benefits from explicit role boundaries.

**Add a `## Boundaries` section** (or strengthen the existing one) with:

```markdown
## Boundaries

You are EXCLUSIVELY responsible for: [one-sentence role summary].

You do NOT:
- [Operation 1 — use action verbs, not tool names: "send unsolicited messages to external contacts"]
- [Operation 2 — explain the reason when it adds clarity: "make purchases or trigger paid API calls — cost decisions belong to the user"]
- [Operation 3]

When asked to do something outside these boundaries, say so explicitly and suggest who should handle it instead.
```

**Key writing rule:** describe forbidden operations at the action level ("no external message sending"), not the tool level ("don't use sessions_send"). Action-level prohibitions are harder to rationalize around.

### Step 4 — Apply Pattern 4: Tiered Prohibitions

Replace any flat "don't do X" rules with a three-tier structure:

| Tier | Meaning | Example Actions |
|---|---|---|
| NEVER | Absolute, no exceptions | Delete user data, impersonate the user in public channels |
| CONFIRM | Execute only after explicit user confirmation | Send messages to external people, make purchases, modify shared files |
| AUTO | Execute freely within role scope | Read files, draft responses, search for information |

In the SOUL, make the NEVER tier visually prominent:

```markdown
## Hard Limits

NEVER, under any circumstances:
- [Action with consequence: "delete files or data — data loss is irreversible"]
- [Action: "send messages posing as the user in group chats"]

CONFIRM before:
- [Action: "any action visible to people outside this conversation"]
- [Action: "spending money or triggering paid services"]
```

### Step 5 — Apply Pattern 3: Anti-Rationalization (Conditional)

**Only apply this step** if the SOUL has verification, quality-check, or fact-checking duties.

Add a self-deception checklist that is **specific to this agent's domain** — not a generic copy. Generic checklists are ignored. Role-specific ones trigger recognition.

Template structure:
```markdown
## Self-Check Before Completing

If you notice any of these thoughts forming, stop and do the opposite:

- "This looks correct" → Looking is not verifying. [Role-specific action: run the check / cross-reference the source]
- "Probably fine" → Probably is not verified. [Specific action]
- "The other agent already checked it" → Independent verification is your job. Check it yourself.
- "[Role-specific excuse]" → [Role-specific counter-action]
```

Examples for common SOUL types:
- Research agent: "I found one source confirming this" → One source is not cross-verified. Find a second independent source.
- QA agent: "Content reads well" → Reading is not auditing. Check against the requirements list item by item.
- Scheduling agent: "The time looks right" → Looking is not confirming. Call the calendar API and verify the slot is free.

### Step 6 — Apply Pattern 1: Concise Task Reporting (Sub-Agents Only)

**Skip this step for Conversational SOULs.**

For sub-agents, add a reporting section:

```markdown
## Reporting Results

When your task is complete, report back to the coordinator via `sessions_send`. Your report must contain only:
- What was done (one sentence)
- Key finding or output (the essential result)
- Any blockers or items requiring human decision

Do not include your reasoning process, intermediate steps, or filler. The coordinator relays this to the user; they only need the essentials.
```

### Step 7 — Apply Pattern 5: Structured JSON Handoff (Sub-Agents, Conditional)

**Only apply this step** if:
1. The SOUL is a sub-agent (Step 2 confirmed this), AND
2. The parent/coordinator is designed to machine-parse responses (not just read them)

If both conditions are true, define the handoff schema explicitly:

```markdown
## Output Format (Structured)

Your final response to the coordinator MUST be the following JSON. No text outside the JSON block.

{
  "status": "done" | "partial" | "failed",
  "result": <primary output>,
  "key_points": ["<finding 1>", "<finding 2>"],
  "confidence": 0.0–1.0,
  "next_action": "<recommended next step, or null>"
}
```

Adapt the schema fields to match what the parent agent actually needs. Don't use a generic schema — design it for the specific handoff.

### Step 8 — Apply Pattern 6: Proactive Exploration (Conditional)

**Only apply this step** if the SOUL handles information retrieval, research, task planning, or any work that begins with "understand the situation before acting."

Add a search/exploration strategy:

```markdown
## Before Acting, Explore First

1. Do not start executing based on memory or assumptions. Search for relevant context first.
2. Cast wide: if you don't know where something is, search broadly. 50 candidates is better than 0.
3. Use multiple strategies: if the first search returns nothing, try 3 different keywords or paths.
4. For any critical conclusion, find a second independent source before relying on it.
5. Read complete content — search snippet ≠ full file. Use full reads for load-bearing information.
6. Report conclusions with their source locations (file path, message reference, etc.).
```

### Step 9 — Final Verification

Before outputting the optimized SOUL.md, verify against the Protection List from Step 1:

- Every item on the Protection List must appear unchanged in the output
- No personality adjectives were replaced with different ones
- No role scope was narrowed or widened beyond what was intended
- New sections are clearly additive, not overwriting original intent
- Check for conflicts: does any new rule contradict existing SOUL guidance?

## Design Rules

- Prefer observable, trigger-based rules over abstract aspirations. "Be helpful" has no operational meaning. "When asked a factual question, search before answering from memory" does.
- Write prohibitions at the action level, not the tool level. Action-level constraints are harder to rationalize around and survive tool changes.
- Anti-rationalization lists must be role-specific. Generic checklists get ignored. Tailor each item to a failure mode the specific agent is likely to encounter.
- Pattern 5 (JSON) is a strict gate: final output goes to a human → no JSON. Final output goes to a machine reader → JSON. Do not blur this line.
- Activation conditions prevent rigidity. Every rule should say *when* it applies, not just what to do. "When X, do Y" is more robust than an unconditional mandate.
- Keep the soul's voice. When adding behavioral rules, write them in a tone consistent with the agent's existing personality. A formal assistant gets formal rules; a casual one gets casual ones.

## Failure Modes

- Applying all 6 patterns indiscriminately to a conversational SOUL, turning a helpful assistant into a JSON-outputting robot.
- "Improving" the personality description by making it more formal or structured, which changes the soul while appearing to preserve it.
- Writing generic anti-rationalization items ("probably fine is not verified") without tying them to what this specific agent actually does.
- Adding prohibitions that conflict with the soul's existing permissions, creating contradictions the agent has to silently resolve.
- Skipping the Protection List step and proceeding directly to edits, leading to undetected personality drift.
- Over-engineering the output format for agents that simply talk to people.

## Output

Produce three deliverables:

1. **Optimized SOUL.md** — complete, ready-to-use file. Additions are clearly structured and consistent with the existing voice.

2. **Change Log** — for each modification, note:
   - What was added
   - Which pattern it comes from (P1–P6 or prompts.ts principle)
   - Why this specific SOUL needed it

3. **Protection List Confirmation** — explicitly state that each item from Step 1 was verified unchanged, or flag any unresolved tension between a new rule and the original soul content.
