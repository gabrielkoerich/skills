#!/usr/bin/env python3
"""Question-driven wrapper for notes review."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ask reflection questions over notes")
    p.add_argument("--notes-dir", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--goals-dir")
    p.add_argument("--use-qmd", action="store_true", help="Force qmd semantic search mode")
    p.add_argument("--qmd-collection", help="Optional qmd collection name")
    p.add_argument("--qmd-results", type=int, default=8, help="Max qmd hits to display")
    return p.parse_args()


def run_review(notes_dir: str, period: str, goals_dir: str | None) -> int:
    script_dir = Path(__file__).resolve().parent
    cmd = [
        sys.executable,
        str(script_dir / "review.py"),
        "--notes-dir",
        notes_dir,
        "--period",
        period,
    ]
    if goals_dir:
        cmd.extend(["--goals-dir", goals_dir])
    return subprocess.call(cmd)


def run_qmd(question: str, collection: str | None, results: int) -> int:
    if shutil.which("qmd") is None:
        print("qmd is not installed. Run: ./setup.sh qmd")
        return 1

    cmd = ["qmd", "search", question, "--json", "-n", str(results)]
    if collection:
        cmd.extend(["-c", collection])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if "SQLITE_CANTOPEN" in stderr or "unable to open database file" in stderr:
            print("qmd is installed but not initialized.")
            print("Initialize qmd first, for example:")
            print("  qmd collection add /path/to/notes --name notes --mask '**/*.md'")
            print("  qmd embed")
        elif stderr:
            print(stderr)
        else:
            print("qmd query failed")
        return proc.returncode

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("qmd returned non-JSON output")
        return 1

    if isinstance(payload, dict):
        hits = payload.get("results", [])
    elif isinstance(payload, list):
        hits = payload
    else:
        hits = []

    print(f"Question: {question}")
    print("")
    print("qmd context hits")
    if not hits:
        print("- no results")
        return 0

    for hit in hits[:results]:
        path = (
            hit.get("path")
            or hit.get("file")
            or hit.get("filepath")
            or hit.get("source")
            or "unknown"
        )
        snippet = (
            hit.get("snippet")
            or hit.get("preview")
            or hit.get("content")
            or hit.get("text")
            or ""
        )
        snippet = " ".join(str(snippet).split())
        if len(snippet) > 220:
            snippet = snippet[:217] + "..."
        score = hit.get("score")

        if score is None:
            print(f"- {path}")
        else:
            print(f"- {path} (score: {score})")
        if snippet:
            print(f"  {snippet}")

    return 0


def main() -> int:
    args = parse_args()
    q = args.question.lower().strip()

    period = "last-week"
    if "month" in q:
        period = "last-month"

    wants_goals = any(x in q for x in ["goal", "track", "right track", "on track"])
    wants_structured = any(
        x in q
        for x in [
            "accomplish",
            "accomplished",
            "did i do",
            "done",
            "pending",
            "need to do",
            "todo",
            "track",
            "goal",
        ]
    )

    if wants_structured:
        return run_review(args.notes_dir, period, args.goals_dir if wants_goals else None)

    if args.use_qmd or shutil.which("qmd") is not None:
        return run_qmd(args.question, args.qmd_collection, args.qmd_results)

    print("Could not map this question to a built-in notes query and qmd is unavailable.")
    print("Try either:")
    print("- Structured: What did I accomplish last week?")
    print("- Or install qmd and run with --use-qmd for open-ended questions.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
