#!/usr/bin/env python3
"""Summarize markdown notes for weekly/monthly reflection."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

DATE_IN_NAME = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")
CHECKED = re.compile(r"^\s*[-*]\s+\[x\]\s+(.+)$", re.IGNORECASE)
UNCHECKED = re.compile(r"^\s*[-*]\s+\[\s\]\s+(.+)$", re.IGNORECASE)
BULLET = re.compile(r"^\s*[-*]\s+(.+)$")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+)\s*$")
WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9_]{3,}")

DONE_HEADINGS = {"done", "wins", "accomplished", "shipped", "completed"}
TODO_HEADINGS = {"todo", "next", "pending", "remaining", "backlog", "follow-up", "followup"}
STOPWORDS = {
    "this", "that", "with", "from", "were", "have", "will", "your", "about", "what", "when", "where",
    "which", "into", "last", "week", "month", "goal", "goals", "work", "need", "still", "todo", "done",
    "notes", "journal", "today", "yesterday", "project", "projects", "track", "right", "time", "plan",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Review markdown notes")
    p.add_argument("--notes-dir", required=True, help="Root notes directory")
    p.add_argument("--period", required=True, help="last-week | last-month | month:YYYY-MM")
    p.add_argument("--goals-dir", help="Optional goals directory")
    p.add_argument("--json", action="store_true", help="Emit JSON")
    return p.parse_args()


def parse_period(period: str, today: dt.date) -> Tuple[dt.date, dt.date]:
    if period == "last-week":
        return today - dt.timedelta(days=7), today + dt.timedelta(days=1)
    if period == "last-month":
        return today - dt.timedelta(days=30), today + dt.timedelta(days=1)
    if period.startswith("month:"):
        year, month = period.split(":", 1)[1].split("-")
        start = dt.date(int(year), int(month), 1)
        if int(month) == 12:
            end = dt.date(int(year) + 1, 1, 1)
        else:
            end = dt.date(int(year), int(month) + 1, 1)
        return start, end
    raise ValueError(f"unknown period: {period}")


def file_date(path: Path) -> Optional[dt.date]:
    m = DATE_IN_NAME.search(path.name)
    if not m:
        return None
    return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def collect_markdown(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.md") if p.is_file()]


def words(text: str) -> List[str]:
    return [w.lower() for w in WORD.findall(text) if w.lower() not in STOPWORDS]


def extract_items(path: Path) -> Tuple[List[str], List[str], List[str], List[str], Counter]:
    done: List[str] = []
    todo: List[str] = []
    highlights: List[str] = []
    followups: List[str] = []
    wc: Counter = Counter()

    current_heading = ""

    for raw in path.read_text(errors="ignore").splitlines():
        hm = HEADING.match(raw)
        if hm:
            current_heading = hm.group(1).strip().lower()
            wc.update(words(current_heading))
            continue

        cx = CHECKED.match(raw)
        if cx:
            item = cx.group(1).strip()
            done.append(item)
            wc.update(words(item))
            continue

        cu = UNCHECKED.match(raw)
        if cu:
            item = cu.group(1).strip()
            todo.append(item)
            wc.update(words(item))
            continue

        bm = BULLET.match(raw)
        if not bm:
            wc.update(words(raw))
            continue

        item = bm.group(1).strip()
        wc.update(words(item))

        normalized_heading = re.sub(r"[^a-z]+", " ", current_heading).strip()
        heading_words = set(normalized_heading.split())

        if heading_words & DONE_HEADINGS:
            highlights.append(item)
        elif heading_words & TODO_HEADINGS:
            followups.append(item)

    return done, todo, highlights, followups, wc


def top_keywords(counter: Counter, limit: int = 12) -> List[str]:
    return [w for w, _ in counter.most_common(limit)]


def goal_keywords(goals_dir: Path) -> Set[str]:
    tokens: Counter = Counter()
    for p in collect_markdown(goals_dir):
        tokens.update(words(p.read_text(errors="ignore")))
    return {w for w, _ in tokens.most_common(40)}


def dedup(items: Iterable[str], limit: int = 20) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for i in items:
        k = i.strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(i.strip())
        if len(out) >= limit:
            break
    return out


def main() -> int:
    args = parse_args()

    notes_root = Path(args.notes_dir)
    if not notes_root.exists():
        raise SystemExit(f"notes directory not found: {notes_root}")

    start, end = parse_period(args.period, dt.date.today())

    selected = []
    for p in collect_markdown(notes_root):
        d = file_date(p)
        if d is None:
            continue
        if start <= d < end:
            selected.append(p)

    done_all: List[str] = []
    todo_all: List[str] = []
    highlights_all: List[str] = []
    followups_all: List[str] = []
    token_counter: Counter = Counter()

    for p in selected:
        done, todo, highlights, followups, wc = extract_items(p)
        done_all.extend(done)
        todo_all.extend(todo)
        highlights_all.extend(highlights)
        followups_all.extend(followups)
        token_counter.update(wc)

    accomplishments = dedup(done_all + highlights_all)
    pending = dedup(todo_all + followups_all)
    focus = top_keywords(token_counter)

    goal_data = None
    if args.goals_dir:
        gdir = Path(args.goals_dir)
        if gdir.exists():
            gk = goal_keywords(gdir)
            covered = [w for w in focus if w in gk]
            score = 0.0 if not gk else len(covered) / max(len(gk), 1)
            on_track = score >= 0.10
            goal_data = {
                "score": round(score, 3),
                "on_track": on_track,
                "covered_keywords": covered,
                "sample_goal_keywords": sorted(list(gk))[:20],
            }

    payload = {
        "period": args.period,
        "start": start.isoformat(),
        "end_exclusive": end.isoformat(),
        "files_reviewed": len(selected),
        "accomplishments": accomplishments,
        "pending": pending,
        "focus_keywords": focus,
        "goal_alignment": goal_data,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Period: {args.period} ({start.isoformat()} to {end.isoformat()} exclusive)")
    print(f"Files reviewed: {len(selected)}")
    print("")

    print("Accomplishments")
    if accomplishments:
        for item in accomplishments[:20]:
            print(f"- {item}")
    else:
        print("- n/a")

    print("")
    print("Still pending")
    if pending:
        for item in pending[:20]:
            print(f"- {item}")
    else:
        print("- n/a")

    print("")
    print("Focus areas")
    if focus:
        print("- " + ", ".join(focus[:12]))
    else:
        print("- n/a")

    if goal_data is not None:
        print("")
        print("Goal alignment")
        status = "on track" if goal_data["on_track"] else "off track"
        print(f"- status: {status}")
        print(f"- score: {goal_data['score']}")
        if goal_data["covered_keywords"]:
            print("- covered goal keywords: " + ", ".join(goal_data["covered_keywords"]))
        else:
            print("- covered goal keywords: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
