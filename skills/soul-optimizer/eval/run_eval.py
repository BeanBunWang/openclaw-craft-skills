#!/usr/bin/env python3
"""
Soul Optimizer Evaluation Runner

Runs soul-type-specific behavioral tasks against two SOUL.md files (before/after optimization)
using any OpenAI-compatible API, then produces a markdown comparison report.

Usage:
    python run_eval.py --before SOUL.md.backup --after SOUL.md --soul-type all

Environment variables:
    OPENAI_API_KEY   Required. Your API key.
    OPENAI_BASE_URL  Optional. Override endpoint for Anthropic, Ollama, OpenRouter, etc.
"""

import argparse
import os
import re
import sys
import textwrap
import types
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)


TASKS_DIR = Path(__file__).parent / "tasks"
SOUL_TYPE_HIERARCHY = {
    "all": {"all"},
    "qa": {"all", "qa"},
    "research": {"all", "research"},
    "subagent": {"all", "subagent"},
}


def parse_task_file(path: Path) -> dict:
    """Parse a task markdown file into frontmatter + sections."""
    raw = path.read_text(encoding="utf-8")

    # Extract YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
    if not fm_match:
        raise ValueError(f"No YAML frontmatter found in {path}")
    frontmatter = yaml.safe_load(fm_match.group(1))
    body = raw[fm_match.end():]

    # Extract sections
    sections = {}
    current_section = None
    current_lines = []
    for line in body.splitlines():
        heading = re.match(r"^## (.+)", line)
        if heading:
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = heading.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()

    # Extract Python grade() function from Automated Checks section
    grade_fn = None
    checks_raw = sections.get("Automated Checks", "")
    code_match = re.search(r"```python\n(.*?)```", checks_raw, re.DOTALL)
    if code_match:
        code = code_match.group(1)
        module = types.ModuleType(f"grade_{frontmatter['id']}")
        exec(compile(code, str(path), "exec"), module.__dict__)  # noqa: S102
        grade_fn = getattr(module, "grade", None)

    return {
        "id": frontmatter["id"],
        "name": frontmatter["name"],
        "soul_type": frontmatter.get("soul_type", "all"),
        "applicable_patterns": frontmatter.get("applicable_patterns", []),
        "prompt": sections.get("Prompt", ""),
        "expected_behavior": sections.get("Expected Behavior", ""),
        "grading_criteria": sections.get("Grading Criteria", ""),
        "grade": grade_fn,
    }


def load_tasks(soul_type: str) -> list[dict]:
    """Load and filter tasks applicable to the given soul_type."""
    applicable_types = SOUL_TYPE_HIERARCHY.get(soul_type, {"all", soul_type})
    tasks = []
    for path in sorted(TASKS_DIR.glob("task_*.md")):
        try:
            task = parse_task_file(path)
        except Exception as e:
            print(f"Warning: skipping {path.name} — {e}", file=sys.stderr)
            continue
        if task["soul_type"] in applicable_types:
            tasks.append(task)
    return tasks


def call_llm(client: OpenAI, model: str, system: str, user: str) -> str:
    """Call the LLM with system + user message, return text response."""
    response = client.chat.completions.create(
        model=model,
        max_tokens=512,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


def run_task(client: OpenAI, model: str, soul: str, task: dict) -> tuple[str, dict[str, float]]:
    """Run a single task against one SOUL, return (response_text, scores)."""
    response = call_llm(client, model, soul, task["prompt"])
    scores: dict[str, float] = {}
    if task["grade"]:
        try:
            scores = task["grade"](response)
        except Exception as e:
            print(f"Warning: grade() failed for {task['id']}: {e}", file=sys.stderr)
    return response, scores


def render_report(
    before_path: str,
    after_path: str,
    model: str,
    soul_type: str,
    results: list[dict],
) -> str:
    """Render the evaluation results as a markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Soul Optimizer — Evaluation Report",
        "",
        f"**Date:** {now}  ",
        f"**Before:** `{before_path}`  ",
        f"**After:** `{after_path}`  ",
        f"**Model:** `{model}`  ",
        f"**Soul type:** `{soul_type}`  ",
        "",
        "---",
        "",
        "## Results by Task",
        "",
    ]

    total_before = 0.0
    total_after = 0.0
    total_possible = 0.0

    for r in results:
        task = r["task"]
        patterns = ", ".join(task["applicable_patterns"]) if task["applicable_patterns"] else "—"
        lines += [
            f"### {task['name']} (`{task['id']}`)",
            f"**Tests patterns:** {patterns}",
            "",
            "| Criterion | Before | After | Delta |",
            "|---|---|---|---|",
        ]

        task_before = 0.0
        task_after = 0.0
        all_criteria = set(r["before_scores"]) | set(r["after_scores"])

        for criterion in sorted(all_criteria):
            b = r["before_scores"].get(criterion, 0.0)
            a = r["after_scores"].get(criterion, 0.0)
            delta = a - b
            delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}" if delta < 0 else "0.0"
            lines.append(f"| `{criterion}` | {b:.1f} | {a:.1f} | {delta_str} |")
            task_before += b
            task_after += a
            total_possible += 1.0

        task_delta = task_after - task_before
        delta_str = f"+{task_delta:.1f}" if task_delta > 0 else f"{task_delta:.1f}" if task_delta < 0 else "0.0"
        lines += [
            f"| **Task total** | **{task_before:.1f}** | **{task_after:.1f}** | **{delta_str}** |",
            "",
        ]

        # Collapsed response previews
        lines += [
            "<details>",
            "<summary>Before response (preview)</summary>",
            "",
            "```",
            textwrap.shorten(r["before_response"], width=400, placeholder="..."),
            "```",
            "",
            "</details>",
            "",
            "<details>",
            "<summary>After response (preview)</summary>",
            "",
            "```",
            textwrap.shorten(r["after_response"], width=400, placeholder="..."),
            "```",
            "",
            "</details>",
            "",
            "---",
            "",
        ]

        total_before += task_before
        total_after += task_after

    total_delta = total_after - total_before
    pct_before = (total_before / total_possible * 100) if total_possible else 0
    pct_after = (total_after / total_possible * 100) if total_possible else 0

    lines += [
        "## Summary",
        "",
        f"| | Score | % |",
        f"|---|---|---|",
        f"| Before | {total_before:.1f} / {total_possible:.0f} | {pct_before:.0f}% |",
        f"| After  | {total_after:.1f} / {total_possible:.0f} | {pct_after:.0f}% |",
        f"| **Delta** | **{total_delta:+.1f}** | **{pct_after - pct_before:+.0f}pp** |",
        "",
    ]

    if total_delta > 0:
        lines.append(f"> Optimization improved behavioral compliance by {total_delta:+.1f} points ({pct_after - pct_before:+.0f}pp).")
    elif total_delta == 0:
        lines.append("> No measurable behavioral change detected. Review whether applicable patterns were applied.")
    else:
        lines.append(f"> Behavioral compliance decreased by {abs(total_delta):.1f} points. Review the optimized SOUL for regressions.")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate soul optimization by running behavioral tasks via OpenAI-compatible API."
    )
    parser.add_argument("--before", required=True, help="Path to original SOUL.md (or SOUL.md.backup)")
    parser.add_argument("--after", required=True, help="Path to optimized SOUL.md")
    parser.add_argument(
        "--soul-type",
        default="all",
        choices=list(SOUL_TYPE_HIERARCHY.keys()),
        help="SOUL type — determines which tasks to run (default: all)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--output",
        default="eval_report.md",
        help="Output report path (default: eval_report.md)",
    )
    args = parser.parse_args()

    # Validate inputs
    before_path = Path(args.before)
    after_path = Path(args.after)
    if not before_path.exists():
        print(f"Error: --before file not found: {before_path}", file=sys.stderr)
        sys.exit(1)
    if not after_path.exists():
        print(f"Error: --after file not found: {after_path}", file=sys.stderr)
        sys.exit(1)
    if not TASKS_DIR.exists():
        print(f"Error: tasks directory not found: {TASKS_DIR}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    before_soul = before_path.read_text(encoding="utf-8")
    after_soul = after_path.read_text(encoding="utf-8")

    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )

    tasks = load_tasks(args.soul_type)
    if not tasks:
        print(f"No tasks found for soul-type '{args.soul_type}' in {TASKS_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Running {len(tasks)} task(s) against model '{args.model}'...")
    results = []
    for task in tasks:
        print(f"  [{task['id']}] {task['name']}...")
        before_response, before_scores = run_task(client, args.model, before_soul, task)
        after_response, after_scores = run_task(client, args.model, after_soul, task)
        results.append({
            "task": task,
            "before_response": before_response,
            "after_response": after_response,
            "before_scores": before_scores,
            "after_scores": after_scores,
        })

    report = render_report(
        str(before_path),
        str(after_path),
        args.model,
        args.soul_type,
        results,
    )

    output_path = Path(args.output)
    output_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
