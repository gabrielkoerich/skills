---
name: beancount-analytics
description: Analyze Beancount ledgers with reusable CLI reports and question-driven queries. Use when user asks for last month/last 12 months reports, spending breakdowns, savings trends, or direct finance questions from a .bean ledger.
---

# Beancount Analytics

Generate fast financial summaries from a Beancount ledger, including:
- last month report
- last 12 months trend
- top expense categories
- direct question style queries

## Requirements

```bash
# Using pip
pip install beancount

# Using uv
uv install beancount
```

## Commands

| Command | Usage |
|---|---|
| Last month | `python3 scripts/report.py --ledger /path/main.bean --period last-month` |
| Last 12 months | `python3 scripts/report.py --ledger /path/main.bean --period last-12-months` |
| Top expenses | `python3 scripts/report.py --ledger /path/main.bean --period last-month --top 10` |
| JSON output | `python3 scripts/report.py --ledger /path/main.bean --period last-12-months --json` |
| Ask directly | `python3 scripts/ask.py --ledger /path/main.bean --question "How much did I spend last month?"` |

## Periods

- `last-month`: previous calendar month
- `last-12-months`: trailing 12 calendar months including current month
- `month:YYYY-MM`: specific month

## Data Model

The scripts read Beancount transactions and aggregate postings where account starts with:
- `Income:`
- `Expenses:`

Output includes:
- total income
- total expenses
- net savings (`income - expenses`)
- top expense categories

## Suggested Workflow

1. Run `report.py` for `last-month` for an executive snapshot.
2. Run `report.py` for `last-12-months` to inspect consistency and trend.
3. Use `ask.py` for direct ad-hoc questions.
4. If you need custom SQL-like analysis, run `bean-query` directly from your finance repo.

## Examples

```bash
python3 scripts/report.py --ledger /path/to/ledger/main.bean --period last-month
python3 scripts/report.py --ledger /path/to/ledger/main.bean --period last-12-months
python3 scripts/ask.py --ledger /path/to/ledger/main.bean --question "Show top expenses last month"
```
