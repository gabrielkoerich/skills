---
name: notes-review
description: Analyze personal markdown notes and journals with qmd-powered semantic search plus weekly/monthly reflection reports. Use for questions like what was accomplished, what is pending, and whether work aligns with goals.
---

# Notes Review

Review your notes to answer questions like:
- what did I do last week/month?
- what was accomplished?
- what still needs to be done?
- am I on track for my goals?

**Requirements:** python3
**Recommended:** qmd CLI for semantic/local search

## Commands

| Command | Usage |
|---|---|
| Last week review | `python3 scripts/review.py --notes-dir /path/notes --period last-week` |
| Last month review | `python3 scripts/review.py --notes-dir /path/notes --period last-month` |
| Include goals check | `python3 scripts/review.py --notes-dir /path/notes --period last-month --goals-dir /path/goals` |
| JSON output | `python3 scripts/review.py --notes-dir /path/notes --period last-week --json` |
| Ask directly | `python3 scripts/ask.py --notes-dir /path/notes --question "What did I accomplish last week?"` |
| Ask with qmd | `python3 scripts/ask.py --notes-dir /path/notes --question "What themes repeated this month?" --use-qmd` |

## Periods

- `last-week`: trailing 7 days
- `last-month`: trailing 30 days
- `month:YYYY-MM`: specific calendar month

## How It Works

1. `review.py` gives deterministic period summaries from dated markdown files.
2. `ask.py` routes structured questions (`accomplished`, `pending`, `last week/month`) to `review.py`.
3. `ask.py` routes open-ended reflective questions to `qmd search` when available (or with `--use-qmd`).

## What It Extracts (`review.py`)

From markdown notes it extracts:
- checked tasks (`- [x]`) as completed work
- unchecked tasks (`- [ ]`) as pending work
- bullets under headings like `Done`, `Wins`, `Accomplished`
- bullets under headings like `Todo`, `Next`, `Pending`

If `--goals-dir` is provided, it estimates goal alignment by checking overlap between goal keywords and recent notes.

## Examples

```bash
python3 scripts/review.py --notes-dir /path/to/notes --period last-week
python3 scripts/review.py --notes-dir /path/to/notes --period last-month --goals-dir /path/to/goals
python3 scripts/ask.py --notes-dir /path/to/notes --question "Am I on track with goals this month?" --goals-dir /path/to/goals
python3 scripts/ask.py --notes-dir /path/to/notes --question "What changed in priorities this month?" --use-qmd
```
