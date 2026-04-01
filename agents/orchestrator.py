#!/usr/bin/env python3
"""
Claim360 Multi-Agent Code Review Orchestrator
==============================================

Runs three specialised agents concurrently against the Claim360 Email App:

  Agent 1 — Frontend Reviewer
      Reviews React components, UI/UX quality, responsiveness,
      and API integration.

  Agent 2 — Backend & Database Engineer
      Audits FastAPI routes, database models, security, and performance.

  Agent 3 — QA & Production Engineer
      Writes tests, validates the deployment config, and confirms
      the application is production-ready.

Usage
-----
  # From the project root:
  python agents/orchestrator.py

  # Or with explicit options:
  python agents/orchestrator.py --agents all
  python agents/orchestrator.py --agents frontend,backend
  python agents/orchestrator.py --agents qa

Requirements
------------
  pip install claude-agent-sdk anyio
  ANTHROPIC_API_KEY must be set in the environment.
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

import anyio

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
AGENTS_DIR = Path(__file__).parent.resolve()
REPORTS_DIR = AGENTS_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Add agents package to path so relative imports work when running as a script
sys.path.insert(0, str(AGENTS_DIR))

from agents import backend_agent, frontend_agent, qa_agent  # noqa: E402

# ---------------------------------------------------------------------------
# Runner helpers
# ---------------------------------------------------------------------------

AGENT_REGISTRY = {
    "frontend": {
        "label": "Frontend Reviewer",
        "emoji": "🎨",
        "module": frontend_agent,
        "report": "frontend_report.md",
    },
    "backend": {
        "label": "Backend & Database Engineer",
        "emoji": "⚙️ ",
        "module": backend_agent,
        "report": "backend_report.md",
    },
    "qa": {
        "label": "QA & Production Engineer",
        "emoji": "🔬",
        "module": qa_agent,
        "report": "qa_report.md",
    },
}


async def _run_single(key: str) -> tuple[str, str | Exception]:
    """Run one agent and return (key, result_or_exception)."""
    info = AGENT_REGISTRY[key]
    print(f"  {info['emoji']} [{info['label']}] started")
    try:
        result = await info["module"].run(cwd=str(PROJECT_ROOT))
        print(f"  {info['emoji']} [{info['label']}] ✅ completed")
        return key, result
    except Exception as exc:  # noqa: BLE001
        print(f"  {info['emoji']} [{info['label']}] ❌ error: {exc}")
        return key, exc


async def run_agents(selected: list[str]) -> dict:
    """
    Execute the selected agents concurrently.

    Returns a mapping of agent key → result (str) or Exception.
    """
    tasks = [_run_single(key) for key in selected]
    pairs = await asyncio.gather(*tasks, return_exceptions=False)
    return dict(pairs)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _result_snippet(result: str | Exception, max_chars: int = 400) -> str:
    if isinstance(result, Exception):
        return f"❌ **Error:** `{result}`"
    snippet = result.strip()[:max_chars]
    if len(result.strip()) > max_chars:
        snippet += "…"
    return snippet


def write_summary(results: dict, duration: float, selected: list[str]) -> Path:
    """Write a human-readable summary report and return its path."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Claim360 Multi-Agent Code Review — Summary",
        "",
        f"**Generated:** {now}  ",
        f"**Duration:** {duration:.1f} seconds  ",
        f"**Agents run:** {', '.join(selected)}",
        "",
        "---",
        "",
    ]

    for key in selected:
        info = AGENT_REGISTRY[key]
        result = results.get(key, "(not run)")
        status = "✅ Completed" if not isinstance(result, Exception) else "❌ Failed"
        report_link = info["report"]

        lines += [
            f"## {info['emoji']} Agent {list(AGENT_REGISTRY).index(key) + 1}: {info['label']}",
            "",
            f"**Status:** {status}  ",
            f"**Detailed report:** [`agents/reports/{report_link}`]({report_link})",
            "",
            "**Result excerpt:**",
            "",
            _result_snippet(result),
            "",
            "---",
            "",
        ]

    lines += [
        "## Next Steps",
        "",
        "1. Review each agent's detailed report in `agents/reports/`",
        "2. Run the backend tests: `cd backend && python -m pytest tests/ -v`",
        "3. Re-deploy to Render after reviewing the suggested changes",
        "4. Address any remaining **Critical** or **High** severity items",
        "",
    ]

    summary_path = REPORTS_DIR / "summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Claim360 multi-agent code review orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agents/orchestrator.py                    # run all three agents
  python agents/orchestrator.py --agents frontend  # run only the frontend agent
  python agents/orchestrator.py --agents backend,qa
        """,
    )
    parser.add_argument(
        "--agents",
        default="all",
        help=(
            "Comma-separated list of agents to run: frontend, backend, qa. "
            "Use 'all' to run all three (default)."
        ),
    )
    return parser.parse_args()


def resolve_agents(spec: str) -> list[str]:
    if spec.strip().lower() == "all":
        return list(AGENT_REGISTRY.keys())
    selected = [s.strip().lower() for s in spec.split(",")]
    unknown = [s for s in selected if s not in AGENT_REGISTRY]
    if unknown:
        print(f"❌ Unknown agent(s): {unknown}. Valid choices: {list(AGENT_REGISTRY)}")
        sys.exit(1)
    return selected


async def main() -> None:
    args = parse_args()
    selected = resolve_agents(args.agents)

    # -----------------------------------------------------------------------
    # Banner
    # -----------------------------------------------------------------------
    print()
    print("=" * 62)
    print("  🚀  CLAIM360 MULTI-AGENT CODE REVIEW SYSTEM")
    print("=" * 62)
    print(f"  Project root : {PROJECT_ROOT}")
    print(f"  Reports dir  : {REPORTS_DIR}")
    print(f"  Agents       : {', '.join(selected)}")
    print("=" * 62)
    print()

    # -----------------------------------------------------------------------
    # Run agents
    # -----------------------------------------------------------------------
    start = datetime.now()
    print("Running agents concurrently…\n")

    results = await run_agents(selected)

    duration = (datetime.now() - start).total_seconds()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    summary_path = write_summary(results, duration, selected)

    print()
    print("=" * 62)
    print("  ✅  ALL AGENTS FINISHED")
    print(f"  ⏱️   Total time  : {duration:.1f}s")
    print(f"  📄  Summary     : {summary_path}")
    print("=" * 62)

    # Exit with non-zero if any agent raised an exception
    if any(isinstance(r, Exception) for r in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    anyio.run(main)
