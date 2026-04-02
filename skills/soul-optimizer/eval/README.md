# Soul Optimizer — Evaluation Suite

Behavioral benchmark for measuring before/after improvement from soul-optimizer.

Runs targeted tasks against your openclaw agent via `openclaw agent --message`, grades the responses automatically, and produces a scored comparison report. No API key needed.

---

## Prerequisites

```bash
pip install pyyaml
```

That's it. The script calls `openclaw agent` directly — your existing openclaw setup handles the LLM calls.

---

## Quick Start (Recommended)

The `full` command guides you through the entire flow in one session:

```bash
python eval/run_eval.py full \
  --soul-path ~/.openclaw/workspace-ops/SOUL.md \
  --soul-type all
```

**What happens:**

1. Runs all applicable tasks against your agent → baseline scores printed
2. Pauses and shows instructions:
   ```
   Next steps:
     1. Run soul-optimizer on: ~/.openclaw/workspace-ops/SOUL.md
     2. Run: openclaw gateway restart
     3. Press Enter here when the gateway is back up
   ```
3. After you press Enter, runs tasks again with the optimized SOUL
4. Auto-generates `eval_run/eval_report.md` with full before/after comparison

---

## Agent Name — Auto-Derived from SOUL Path

Pass `--soul-path` and the script automatically figures out which agent to target:

| SOUL.md path | Agent used |
|---|---|
| `~/.openclaw/workspace-ops/SOUL.md` | `--agent ops` |
| `~/.openclaw/workspace-support/SOUL.md` | `--agent support` |
| `~/.openclaw/workspace/SOUL.md` | default main (no `--agent` flag) |

You can still override with `--agent my-agent` if needed.

---

## Manual Two-Step (Alternative)

If you prefer to run before and after in separate terminal sessions:

```bash
# Step 1 — baseline (before optimization)
python eval/run_eval.py run \
  --phase before \
  --soul-path ~/.openclaw/workspace-ops/SOUL.md \
  --soul-type all

# ... run soul-optimizer, then: openclaw gateway restart ...

# Step 2 — after optimization (report auto-generated)
python eval/run_eval.py run \
  --phase after \
  --soul-path ~/.openclaw/workspace-ops/SOUL.md \
  --soul-type all
# -> eval_run/eval_report.md is generated automatically
```

---

## How It Works

```
eval/tasks/
├── task_01_boundary.md              P2, P4  — soul_type: all
├── task_02_anti_rationalization.md   P3      — soul_type: qa
├── task_03_exploration.md            P6      — soul_type: research
└── task_04_reporting.md              P1      — soul_type: subagent
```

Each task file contains:
- A test **prompt** sent to the agent via `openclaw agent --message`
- A `grade(response)` function that checks the response for specific behavioral signals
- Scores are 0.0–1.0 per criterion

---

## `--soul-type` Values

| Value | Tasks run | Use when |
|---|---|---|
| `all` | task_01 only | Any SOUL (conversational assistant, etc.) |
| `qa` | task_01 + task_02 | QA, fact-checking, or verification SOULs |
| `research` | task_01 + task_03 | Research, information-retrieval SOULs |
| `subagent` | task_01 + task_04 | Sub-agents reporting to a coordinator |

---

## Terminal Output (example)

```
Agent: ops (derived from workspace-ops)

Running 2 task(s) via openclaw agent (phase: before)...

  [task_01_boundary] Boundary Adherence... 1.0 / 4
  [task_02_anti_rationalization] Anti-Rationalization... 2.0 / 4

| Task                    | Criterion              | Score |
|-------------------------|------------------------|-------|
| Boundary Adherence      | explicit_decline       | 0.0 - |
| Boundary Adherence      | no_partial_compliance  | 1.0 + |
| ...                     | ...                    | ...   |
| **Total**               |                        | 3.0 / 8 |

Phase 'before' complete: 3.0 / 8
```

---

## Output Directory Structure

```
eval_run/
├── before/
│   ├── responses/
│   │   ├── task_01_boundary.txt
│   │   └── task_02_anti_rationalization.txt
│   └── scores.json
├── after/
│   ├── responses/
│   │   ├── task_01_boundary.txt
│   │   └── task_02_anti_rationalization.txt
│   └── scores.json
└── eval_report.md                  <- auto-generated
```

---

## Re-generating the Report

If you change grading logic or want to regenerate after the fact:

```bash
python eval/run_eval.py report \
  --before eval_run/before \
  --after  eval_run/after \
  --output eval_run/eval_report.md
```

---

## Adding Custom Tasks

Copy any file from `tasks/` as a template. Required frontmatter:

```yaml
---
id: task_XX_your_task
name: Human-Readable Name
category: soul_eval
soul_type: all       # all / qa / research / subagent
applicable_patterns: [P2]
---
```

The `grade(response: str) -> dict[str, float]` function must return criterion names mapped to 0.0–1.0 scores.
