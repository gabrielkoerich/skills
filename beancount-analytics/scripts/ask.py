#!/usr/bin/env python3
"""Question-driven wrapper for Beancount reports."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ask finance questions over a Beancount ledger")
    p.add_argument("--ledger", required=True, help="Path to Beancount .bean file")
    p.add_argument("--question", required=True, help="Natural language question")
    p.add_argument("--top", type=int, default=7, help="Top categories for relevant answers")
    return p.parse_args()


def run_report(ledger: str, period: str, top: int) -> int:
    script_dir = Path(__file__).resolve().parent
    cmd = [
        sys.executable,
        str(script_dir / "report.py"),
        "--ledger",
        ledger,
        "--period",
        period,
        "--top",
        str(top),
    ]
    return subprocess.call(cmd)


def run_top_category(ledger: str, period: str, category_keyword: str, top: int) -> int:
    script_dir = Path(__file__).resolve().parent
    cmd = [
        sys.executable,
        str(script_dir / "report.py"),
        "--ledger",
        ledger,
        "--period",
        period,
        "--top",
        str(max(top, 30)),
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return proc.returncode

    import json

    data = json.loads(proc.stdout)
    needle = category_keyword.lower()
    found = [
        row for row in data.get("top_expenses", []) if needle in row.get("account", "").lower()
    ]

    print(f"Question: spend on '{category_keyword}' ({period})")
    if not found:
        print("- No matching expense category in top results.")
        return 0

    total = sum(row["amount"] for row in found)
    for row in found:
        print(f"- {row['account']}: {row['amount']:,.2f}")
    print(f"- total matching spend: {total:,.2f}")
    return 0


def main() -> int:
    args = parse_args()
    q = args.question.lower().strip()

    period = "last-month"
    if "12" in q and "month" in q:
        period = "last-12-months"
    elif "last month" in q or "previous month" in q:
        period = "last-month"

    m = re.search(r"(?:spend|spent) on ([a-z0-9:_ -]+)", q)
    if m:
        category = m.group(1).strip().rstrip("?.!")
        return run_top_category(args.ledger, period, category, args.top)

    if any(word in q for word in ["report", "summary", "income", "expense", "expenses", "savings", "spent"]):
        return run_report(args.ledger, period, args.top)

    print("Could not map the question to a built-in query.")
    print("Try one of:")
    print("- How much did I spend last month?")
    print("- Show a report for the last 12 months")
    print("- How much did I spend on food last month?")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
