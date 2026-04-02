#!/usr/bin/env python3
"""
Soul Optimizer Evaluation Runner

Runs behavioral tasks against an openclaw agent (via `openclaw agent --message`),
grades responses, and produces a before/after comparison report.

No API key needed — uses the openclaw CLI directly.

Usage (recommended — guided full flow):
    python run_eval.py full --soul-path ~/.openclaw/workspace-ops/SOUL.md --soul-type all

Usage (manual two-step):
    python run_eval.py run --phase before --soul-path ~/.openclaw/workspace-ops/SOUL.md
    # ... optimize SOUL + openclaw gateway restart ...
    python run_eval.py run --phase after  --soul-path ~/.openclaw/workspace-ops/SOUL.md

Dependencies:
    pip install pyyaml
"""

import argparse
import json
import re
import subprocess
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


TASKS_DIR = Path(__file__).parent / "tasks"
SOUL_TYPE_HIERARCHY = {
    "all": {"all"},
    "qa": {"all", "qa"},
    "research": {"all", "research"},
    "subagent": {"all", "subagent"},
}


# ---------------------------------------------------------------------------
# Agent name derivation
# ---------------------------------------------------------------------------

def derive_agent_from_soul_path(soul_path: Path) -> str | None:
    """
    Derive the openclaw agent name from a SOUL.md file path.

    Rules (based on openclaw workspace naming convention):
        ~/.openclaw/workspace-ops/SOUL.md  ->  "ops"
        ~/.openclaw/workspace/SOUL.md      ->  None  (default main agent)

    Returns the agent name string, or None if the path points to the default
    workspace (no --agent flag needed for openclaw CLI).
    """
    for part in soul_path.resolve().parts:
        if part.startswith("workspace-"):
            return part[len("workspace-"):]
        if part == "workspace":
            return None
    return None


def resolve_agent(args: argparse.Namespace) -> tuple[str | None, str]:
    """
    Determine the agent name and a human-readable description.

    Priority:
      1. --agent explicitly provided  →  use as-is
      2. --soul-path provided          →  derive from workspace directory name
      3. neither                       →  use default main agent (no --agent flag)

    Returns (agent_name_or_None, description_string).
    """
    if args.agent:
        return args.agent, f"{args.agent} (explicit --agent)"

    soul_path = getattr(args, "soul_path", None)
    if soul_path:
        derived = derive_agent_from_soul_path(Path(soul_path))
        if derived:
            return derived, f"{derived} (derived from {Path(soul_path).parent.name})"
        else:
            return None, "main (default, derived from workspace)"

    return None, "main (default)"


# ---------------------------------------------------------------------------
# Task parsing
# ---------------------------------------------------------------------------

def parse_task_file(path: Path) -> dict:
    """Parse a task markdown file into frontmatter + sections."""
    raw = path.read_text(encoding="utf-8")

    fm_match = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
    if not fm_match:
        raise ValueError(f"No YAML frontmatter found in {path}")
    frontmatter = yaml.safe_load(fm_match.group(1))
    body = raw[fm_match.end():]

    sections: dict[str, str] = {}
    current_section = None
    current_lines: list[str] = []
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
            print(f"  Warning: skipping {path.name} — {e}", file=sys.stderr)
            continue
        if task["soul_type"] in applicable_types:
            tasks.append(task)
    return tasks


# ---------------------------------------------------------------------------
# openclaw agent execution
# ---------------------------------------------------------------------------

def call_openclaw(agent: str | None, message: str, timeout: int = 120) -> str:
    """Send a message to an openclaw agent via CLI and return the response."""
    cmd = ["openclaw", "agent", "--message", message]
    if agent:
        cmd += ["--agent", agent]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"openclaw agent exited with code {result.returncode}:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

def grade_response(task: dict, response: str) -> dict[str, float]:
    """Run a task's grade() function on a response string."""
    if not task["grade"]:
        return {}
    try:
        return task["grade"](response)
    except Exception as e:
        print(f"  Warning: grade() failed for {task['id']}: {e}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_phase_table(results: list[dict]) -> str:
    """Render a single-phase score table for terminal output."""
    lines = [
        "",
        "| Task | Criterion | Score |",
        "|---|---|---|",
    ]
    total = 0.0
    possible = 0.0
    for r in results:
        for criterion in sorted(r["scores"]):
            s = r["scores"][criterion]
            mark = "+" if s >= 1.0 else ("~" if s > 0 else "-")
            lines.append(f"| {r['task_name']} | {criterion} | {s:.1f} {mark} |")
            total += s
            possible += 1.0
    lines.append(f"| **Total** | | **{total:.1f} / {possible:.0f}** |")
    lines.append("")
    return "\n".join(lines)


def render_comparison_report(
    before_data: dict,
    after_data: dict,
    before_dir: Path,
    after_dir: Path,
) -> str:
    """Render a before/after comparison markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Soul Optimizer — Evaluation Report",
        "",
        f"**Date:** {now}  ",
        f"**Soul type:** `{before_data.get('soul_type', 'all')}`  ",
        "",
        "---",
        "",
        "## Results by Task",
        "",
    ]

    before_tasks = {t["id"]: t for t in before_data["tasks"]}
    after_tasks = {t["id"]: t for t in after_data["tasks"]}
    all_task_ids = list(dict.fromkeys(
        [t["id"] for t in before_data["tasks"]] + [t["id"] for t in after_data["tasks"]]
    ))

    grand_before = 0.0
    grand_after = 0.0
    grand_possible = 0.0

    for task_id in all_task_ids:
        bt = before_tasks.get(task_id, {})
        at = after_tasks.get(task_id, {})
        task_name = at.get("name") or bt.get("name") or task_id
        patterns = at.get("patterns") or bt.get("patterns") or []
        patterns_str = ", ".join(patterns) if patterns else "—"

        lines += [
            f"### {task_name} (`{task_id}`)",
            f"**Tests patterns:** {patterns_str}",
            "",
            "| Criterion | Before | After | Delta |",
            "|---|---|---|---|",
        ]

        b_scores = bt.get("scores", {})
        a_scores = at.get("scores", {})
        all_criteria = sorted(set(b_scores) | set(a_scores))

        task_before = 0.0
        task_after = 0.0

        for c in all_criteria:
            b = b_scores.get(c, 0.0)
            a = a_scores.get(c, 0.0)
            delta = a - b
            d_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}" if delta < 0 else "0.0"
            lines.append(f"| `{c}` | {b:.1f} | {a:.1f} | {d_str} |")
            task_before += b
            task_after += a
            grand_possible += 1.0

        td = task_after - task_before
        td_str = f"+{td:.1f}" if td > 0 else f"{td:.1f}" if td < 0 else "0.0"
        lines.append(f"| **Task total** | **{task_before:.1f}** | **{task_after:.1f}** | **{td_str}** |")
        lines.append("")

        # Response previews
        for label, phase_dir in [("Before", before_dir), ("After", after_dir)]:
            resp_file = phase_dir / "responses" / f"{task_id}.txt"
            if resp_file.exists():
                preview = textwrap.shorten(
                    resp_file.read_text(encoding="utf-8"), width=400, placeholder="...",
                )
                lines += [
                    "<details>",
                    f"<summary>{label} response (preview)</summary>",
                    "",
                    "```",
                    preview,
                    "```",
                    "",
                    "</details>",
                    "",
                ]

        lines += ["---", ""]
        grand_before += task_before
        grand_after += task_after

    pct_b = (grand_before / grand_possible * 100) if grand_possible else 0
    pct_a = (grand_after / grand_possible * 100) if grand_possible else 0

    lines += [
        "## Summary",
        "",
        "| | Score | % |",
        "|---|---|---|",
        f"| Before | {grand_before:.1f} / {grand_possible:.0f} | {pct_b:.0f}% |",
        f"| After  | {grand_after:.1f} / {grand_possible:.0f} | {pct_a:.0f}% |",
        f"| **Delta** | **{grand_after - grand_before:+.1f}** | **{pct_a - pct_b:+.0f}pp** |",
        "",
    ]

    delta = grand_after - grand_before
    if delta > 0:
        lines.append(
            f"> Optimization improved behavioral compliance by {delta:+.1f} points "
            f"({pct_a - pct_b:+.0f}pp)."
        )
    elif delta == 0:
        lines.append(
            "> No measurable behavioral change detected. "
            "Review whether applicable patterns were applied."
        )
    else:
        lines.append(
            f"> Behavioral compliance decreased by {abs(delta):.1f} points. "
            "Review the optimized SOUL for regressions."
        )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Core run logic (shared by `run` and `full`)
# ---------------------------------------------------------------------------

def run_phase(
    phase: str,
    soul_type: str,
    agent: str | None,
    eval_dir: Path,
    timeout: int,
) -> dict:
    """
    Execute all applicable tasks for a given phase, grade responses, save results.
    Returns the scores_data dict.
    """
    phase_dir = eval_dir / phase
    responses_dir = phase_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(soul_type)
    if not tasks:
        print(f"No tasks found for soul-type '{soul_type}' in {TASKS_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Running {len(tasks)} task(s) via openclaw agent (phase: {phase})...")
    print()

    results = []
    for task in tasks:
        print(f"  [{task['id']}] {task['name']}...", end=" ", flush=True)
        try:
            response = call_openclaw(agent, task["prompt"], timeout=timeout)
        except Exception as e:
            print(f"FAILED\n    {e}", file=sys.stderr)
            response = ""

        resp_file = responses_dir / f"{task['id']}.txt"
        resp_file.write_text(response, encoding="utf-8")

        scores = grade_response(task, response)
        task_total = sum(scores.values())
        task_possible = float(len(scores))
        print(f"{task_total:.1f} / {task_possible:.0f}")

        results.append({
            "id": task["id"],
            "name": task["name"],
            "patterns": task["applicable_patterns"],
            "scores": scores,
            "total": task_total,
            "possible": task_possible,
        })

    grand_total = sum(r["total"] for r in results)
    grand_possible = sum(r["possible"] for r in results)

    scores_data = {
        "phase": phase,
        "soul_type": soul_type,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tasks": results,
        "total": grand_total,
        "possible": grand_possible,
    }

    scores_file = phase_dir / "scores.json"
    scores_file.write_text(
        json.dumps(scores_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(render_phase_table([
        {"task_name": r["name"], "scores": r["scores"]} for r in results
    ]))
    print(f"Phase '{phase}' complete: {grand_total:.1f} / {grand_possible:.0f}")
    print(f"Results saved to: {scores_file}")

    return scores_data


def maybe_write_report(eval_dir: Path, after_data: dict) -> None:
    """Write comparison report if before-phase data exists."""
    before_dir = eval_dir / "before"
    before_scores_file = before_dir / "scores.json"
    if before_scores_file.exists():
        print("\nBefore-phase data found — generating comparison report...")
        before_data = json.loads(before_scores_file.read_text(encoding="utf-8"))
        after_dir = eval_dir / "after"
        report = render_comparison_report(before_data, after_data, before_dir, after_dir)
        report_path = eval_dir / "eval_report.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"Report written to: {report_path.resolve()}")
    else:
        print(
            f"\nNo before-phase data at {before_scores_file} — skipping comparison report.\n"
            "Run with --phase before first, then --phase after to get a comparison."
        )


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_run(args: argparse.Namespace) -> None:
    """Execute tasks for a single phase, grade, and save results."""
    agent, agent_desc = resolve_agent(args)
    print(f"Agent: {agent_desc}")

    scores_data = run_phase(
        phase=args.phase,
        soul_type=args.soul_type,
        agent=agent,
        eval_dir=Path(args.eval_dir),
        timeout=args.timeout,
    )

    if args.phase == "after":
        maybe_write_report(Path(args.eval_dir), scores_data)


def cmd_full(args: argparse.Namespace) -> None:
    """
    Guided full evaluation flow:
      1. Run before phase
      2. Prompt user to optimize SOUL + restart gateway
      3. Run after phase
      4. Auto-generate comparison report
    """
    agent, agent_desc = resolve_agent(args)
    eval_dir = Path(args.eval_dir)
    soul_path = getattr(args, "soul_path", None)

    print("=" * 60)
    print("Soul Optimizer — Full Evaluation")
    print("=" * 60)
    print(f"Agent:     {agent_desc}")
    print(f"Soul type: {args.soul_type}")
    print(f"Eval dir:  {eval_dir.resolve()}")
    print()

    # --- Phase: before ---
    print("[ Phase 1 / 2 ] Before optimization")
    print("-" * 40)
    before_data = run_phase(
        phase="before",
        soul_type=args.soul_type,
        agent=agent,
        eval_dir=eval_dir,
        timeout=args.timeout,
    )

    # --- Pause for optimization + restart ---
    print()
    print("=" * 60)
    print(f"Before-phase complete: {before_data['total']:.1f} / {before_data['possible']:.0f}")
    print()
    print("Next steps:")
    if soul_path:
        print(f"  1. Run soul-optimizer on:  {soul_path}")
    else:
        print("  1. Run soul-optimizer on your SOUL.md")
    print("  2. Run:  openclaw gateway restart")
    print("  3. Press Enter here when the gateway is back up")
    print("=" * 60)
    try:
        input("\nPress Enter to continue...\n")
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)

    # --- Phase: after ---
    print("[ Phase 2 / 2 ] After optimization")
    print("-" * 40)
    after_data = run_phase(
        phase="after",
        soul_type=args.soul_type,
        agent=agent,
        eval_dir=eval_dir,
        timeout=args.timeout,
    )

    # --- Comparison report (always generated in full mode) ---
    print()
    print("Generating comparison report...")
    before_dir = eval_dir / "before"
    after_dir = eval_dir / "after"
    report = render_comparison_report(before_data, after_data, before_dir, after_dir)
    report_path = eval_dir / "eval_report.md"
    report_path.write_text(report, encoding="utf-8")

    # Print inline summary
    delta = after_data["total"] - before_data["total"]
    possible = before_data["possible"]
    pct_b = (before_data["total"] / possible * 100) if possible else 0
    pct_a = (after_data["total"] / possible * 100) if possible else 0

    print()
    print("=" * 60)
    print("Evaluation complete")
    print(f"  Before: {before_data['total']:.1f} / {possible:.0f}  ({pct_b:.0f}%)")
    print(f"  After:  {after_data['total']:.1f} / {possible:.0f}  ({pct_a:.0f}%)")
    print(f"  Delta:  {delta:+.1f} ({pct_a - pct_b:+.0f}pp)")
    print(f"\nFull report: {report_path.resolve()}")
    print("=" * 60)


def cmd_report(args: argparse.Namespace) -> None:
    """(Re-)generate comparison report from existing phase data."""
    before_dir = Path(args.before)
    after_dir = Path(args.after)

    for label, d in [("before", before_dir), ("after", after_dir)]:
        sf = d / "scores.json"
        if not sf.exists():
            print(f"Error: {label} scores not found at {sf}", file=sys.stderr)
            sys.exit(1)

    before_data = json.loads((before_dir / "scores.json").read_text(encoding="utf-8"))
    after_data = json.loads((after_dir / "scores.json").read_text(encoding="utf-8"))

    report = render_comparison_report(before_data, after_data, before_dir, after_dir)
    output = Path(args.output)
    output.write_text(report, encoding="utf-8")
    print(f"Report written to: {output.resolve()}")


# ---------------------------------------------------------------------------
# Shared argument helpers
# ---------------------------------------------------------------------------

def add_run_args(p: argparse.ArgumentParser) -> None:
    """Add arguments shared by both `run` and `full` subcommands."""
    p.add_argument(
        "--soul-path",
        help=(
            "Path to the SOUL.md being evaluated. "
            "Used to auto-derive the agent name from the workspace directory "
            "(e.g. workspace-ops/SOUL.md -> --agent ops)."
        ),
    )
    p.add_argument(
        "--soul-type", default="all", choices=list(SOUL_TYPE_HIERARCHY.keys()),
        help="SOUL type — determines which tasks to run (default: all)",
    )
    p.add_argument(
        "--agent",
        help="openclaw agent name. If omitted, derived from --soul-path or defaults to main.",
    )
    p.add_argument(
        "--eval-dir", default="./eval_run",
        help="Directory for evaluation data (default: ./eval_run)",
    )
    p.add_argument(
        "--timeout", type=int, default=120,
        help="Per-task timeout in seconds (default: 120)",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate soul optimization via openclaw agent behavioral tasks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Recommended: guided full flow (auto-detects agent from SOUL path)
              python run_eval.py full --soul-path ~/.openclaw/workspace-ops/SOUL.md

              # Manual two-step
              python run_eval.py run --phase before --soul-path ~/.openclaw/workspace-ops/SOUL.md
              python run_eval.py run --phase after  --soul-path ~/.openclaw/workspace-ops/SOUL.md

              # Re-generate report from existing results
              python run_eval.py report
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- full ---
    p_full = sub.add_parser(
        "full",
        help="Guided full flow: before → wait for optimize+restart → after → report",
    )
    add_run_args(p_full)

    # --- run ---
    p_run = sub.add_parser(
        "run",
        help="Execute tasks for a single phase (before or after), grade, and save results",
    )
    p_run.add_argument(
        "--phase", required=True, choices=["before", "after"],
        help="Evaluation phase: 'before' (pre-optimization) or 'after' (post-optimization)",
    )
    add_run_args(p_run)

    # --- report ---
    p_report = sub.add_parser(
        "report",
        help="(Re-)generate comparison report from existing phase results",
    )
    p_report.add_argument(
        "--before", default="./eval_run/before",
        help="Path to before-phase directory (default: ./eval_run/before)",
    )
    p_report.add_argument(
        "--after", default="./eval_run/after",
        help="Path to after-phase directory (default: ./eval_run/after)",
    )
    p_report.add_argument(
        "--output", default="./eval_run/eval_report.md",
        help="Output report path (default: ./eval_run/eval_report.md)",
    )

    args = parser.parse_args()

    if args.command == "full":
        cmd_full(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "report":
        cmd_report(args)


if __name__ == "__main__":
    main()
