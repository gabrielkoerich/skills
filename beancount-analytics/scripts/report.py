#!/usr/bin/env python3
"""Generate monthly and 12-month reports from a Beancount ledger."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple


MonthKey = Tuple[int, int]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Beancount monthly analytics report")
    p.add_argument("--ledger", required=True, help="Path to Beancount .bean file")
    p.add_argument(
        "--period",
        required=True,
        help="last-month | last-12-months | month:YYYY-MM",
    )
    p.add_argument("--top", type=int, default=7, help="Top expense categories to include")
    p.add_argument("--json", action="store_true", help="Emit JSON")
    return p.parse_args()


def month_start(d: dt.date) -> dt.date:
    return d.replace(day=1)


def add_months(d: dt.date, months: int) -> dt.date:
    year = d.year + ((d.month - 1 + months) // 12)
    month = ((d.month - 1 + months) % 12) + 1
    return dt.date(year, month, 1)


def parse_period(period: str, today: dt.date) -> Tuple[dt.date, dt.date, List[MonthKey]]:
    this_month = month_start(today)

    if period == "last-month":
        start = add_months(this_month, -1)
        end = this_month
    elif period == "last-12-months":
        start = add_months(this_month, -11)
        end = add_months(this_month, 1)
    elif period.startswith("month:"):
        ym = period.split(":", 1)[1]
        year, month = ym.split("-")
        start = dt.date(int(year), int(month), 1)
        end = add_months(start, 1)
    else:
        raise ValueError(f"unknown period: {period}")

    months: List[MonthKey] = []
    cursor = start
    while cursor < end:
        months.append((cursor.year, cursor.month))
        cursor = add_months(cursor, 1)

    return start, end, months


def load_entries(path: str):
    try:
        from beancount.loader import load_file
    except Exception:
        print("error: beancount is required. Install with: pip install beancount", file=sys.stderr)
        raise SystemExit(1)

    entries, errors, _opts = load_file(path)
    if errors:
        print(f"warning: {len(errors)} parsing issue(s) detected", file=sys.stderr)
    return entries


def aggregate(entries, start: dt.date, end: dt.date):
    try:
        from beancount.core.data import Transaction
    except Exception:
        print("error: beancount is required. Install with: pip install beancount", file=sys.stderr)
        raise SystemExit(1)

    monthly_income: Dict[MonthKey, Decimal] = defaultdict(lambda: Decimal("0"))
    monthly_expenses: Dict[MonthKey, Decimal] = defaultdict(lambda: Decimal("0"))
    category_expenses: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    currencies = set()

    for entry in entries:
        if not isinstance(entry, Transaction):
            continue
        if not (start <= entry.date < end):
            continue

        mk = (entry.date.year, entry.date.month)

        for posting in entry.postings:
            units = posting.units
            if units is None:
                continue
            account = posting.account
            amount = units.number
            currency = units.currency
            currencies.add(currency)

            if account.startswith("Income:"):
                monthly_income[mk] += -amount
            elif account.startswith("Expenses:"):
                monthly_expenses[mk] += amount
                category_expenses[account] += amount

    return monthly_income, monthly_expenses, category_expenses, sorted(currencies)


def to_float(d: Decimal) -> float:
    return float(d.quantize(Decimal("0.01")))


def render_human(
    period: str,
    months: Iterable[MonthKey],
    income_map,
    expense_map,
    category_expenses,
    top_n: int,
    currencies: List[str],
) -> str:
    lines: List[str] = []
    lines.append(f"Period: {period}")
    lines.append(f"Currencies seen: {', '.join(currencies) if currencies else 'n/a'}")
    lines.append("")

    total_income = Decimal("0")
    total_expenses = Decimal("0")

    lines.append("Monthly summary")
    for y, m in months:
        income = income_map[(y, m)]
        expenses = expense_map[(y, m)]
        savings = income - expenses
        total_income += income
        total_expenses += expenses
        lines.append(
            f"- {y:04d}-{m:02d}: income={to_float(income):,.2f} expenses={to_float(expenses):,.2f} savings={to_float(savings):,.2f}"
        )

    total_savings = total_income - total_expenses

    lines.append("")
    lines.append("Totals")
    lines.append(f"- income:   {to_float(total_income):,.2f}")
    lines.append(f"- expenses: {to_float(total_expenses):,.2f}")
    lines.append(f"- savings:  {to_float(total_savings):,.2f}")

    lines.append("")
    lines.append(f"Top {top_n} expense categories")
    top = sorted(category_expenses.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    if not top:
        lines.append("- n/a")
    else:
        for account, amount in top:
            lines.append(f"- {account}: {to_float(amount):,.2f}")

    return "\n".join(lines)


def render_json(period: str, months, income_map, expense_map, category_expenses, top_n: int):
    monthly = []
    total_income = Decimal("0")
    total_expenses = Decimal("0")

    for y, m in months:
        income = income_map[(y, m)]
        expenses = expense_map[(y, m)]
        savings = income - expenses
        total_income += income
        total_expenses += expenses
        monthly.append(
            {
                "month": f"{y:04d}-{m:02d}",
                "income": to_float(income),
                "expenses": to_float(expenses),
                "savings": to_float(savings),
            }
        )

    top = sorted(category_expenses.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    payload = {
        "period": period,
        "monthly": monthly,
        "totals": {
            "income": to_float(total_income),
            "expenses": to_float(total_expenses),
            "savings": to_float(total_income - total_expenses),
        },
        "top_expenses": [
            {"account": account, "amount": to_float(amount)} for account, amount in top
        ],
    }
    return json.dumps(payload, indent=2)


def main() -> int:
    args = parse_args()
    today = dt.date.today()

    try:
        start, end, months = parse_period(args.period, today)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    entries = load_entries(args.ledger)
    income_map, expense_map, category_expenses, currencies = aggregate(entries, start, end)

    if args.json:
        print(
            render_json(
                args.period,
                months,
                income_map,
                expense_map,
                category_expenses,
                args.top,
            )
        )
    else:
        print(
            render_human(
                args.period,
                months,
                income_map,
                expense_map,
                category_expenses,
                args.top,
                currencies,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
