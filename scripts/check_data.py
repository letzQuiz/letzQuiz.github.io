#!/usr/bin/env python3
"""Validate quiz data before the site is built. Exits non-zero on any problem.

Checks:
  1. every _data/questions*.json is valid JSON and each question has
     question, answer, date and category (an empty answer is only a
     warning, so a deploy isn't blocked while it waits to be filled in);
  2. every category is an id from _data/quiz_sections.yml;
  3. every question date matches a quiz post (layout: normal-quiz, or a
     post with questions_date), and every normal-quiz post has questions;
  4. no two posts build to the same URL;
  5. every _data/events.yml entry has date, start and venue, and nothing
     still says TODO_OWNER.

Usage: python3 scripts/check_data.py   (needs PyYAML: pip install pyyaml)
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_QUESTION_FIELDS = ("question", "answer", "date", "category")
REQUIRED_EVENT_FIELDS = ("date", "start", "venue")


def day(value):
    """Normalise a YAML/JSON date (date, datetime or string) to YYYY-MM-DD."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()[:10]


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def front_matter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    return (yaml.safe_load(match.group(1)) or {}) if match else {}


def post_url(path, fm):
    """Mirror `permalink: /:categories/:title/` from _config.yml."""
    if fm.get("permalink"):
        return fm["permalink"]
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    slug = fm.get("slug") or name
    categories = fm.get("categories") or []
    if isinstance(categories, str):
        categories = categories.split()
    parts = [slugify(c) for c in categories] + [slug]
    return "/" + "/".join(parts) + "/"


def main():
    errors = []
    warnings = []

    sections = yaml.safe_load((ROOT / "_data/quiz_sections.yml").read_text(encoding="utf-8"))
    section_ids = {s["id"] for s in sections}

    # Posts: which dates have a quiz page, and which URLs they build to.
    quiz_dates = {}
    urls = {}
    for path in sorted((ROOT / "_posts").glob("*.md")):
        fm = front_matter(path)
        url = post_url(path, fm)
        if url in urls:
            errors.append(f"{path.name}: same URL {url} as {urls[url]}")
        urls[url] = path.name
        if fm.get("layout") == "normal-quiz":
            post_day = day(fm.get("date") or path.name[:10])
            quiz_dates.setdefault(post_day, []).append(path.name)
        if fm.get("questions_date"):
            quiz_dates.setdefault(day(fm["questions_date"]), []).append(path.name)

    # Questions.
    question_counts = {}
    for path in sorted((ROOT / "_data").glob("questions*.json")):
        try:
            questions = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON ({exc})")
            continue
        if not isinstance(questions, list):
            errors.append(f"{path.name}: expected a list of questions")
            continue
        for i, q in enumerate(questions, start=1):
            where = f"{path.name} #{i}"
            if not isinstance(q, dict):
                errors.append(f"{where}: not an object")
                continue
            missing = [f for f in REQUIRED_QUESTION_FIELDS if f not in q]
            empty = [f for f in REQUIRED_QUESTION_FIELDS if f in q and not str(q[f]).strip()]
            if missing:
                errors.append(f"{where}: missing {', '.join(missing)}")
            # An empty answer renders as a blank reveal; warn so it gets filled, but don't block a deploy.
            if empty == ["answer"]:
                warnings.append(f"{where}: empty answer")
            elif empty:
                errors.append(f"{where}: empty {', '.join(empty)}")
            if q.get("category") and q["category"] not in section_ids:
                errors.append(f"{where}: unknown category {q['category']!r} (use one of {sorted(section_ids)})")
            if q.get("date"):
                q_day = day(q["date"])
                question_counts[q_day] = question_counts.get(q_day, 0) + 1
                if q_day not in quiz_dates:
                    errors.append(f"{where}: date {q_day} matches no quiz post")

    for post_day, names in sorted(quiz_dates.items()):
        if not question_counts.get(post_day):
            errors.append(f"{', '.join(names)}: no questions dated {post_day}")

    # Events.
    events_path = ROOT / "_data/events.yml"
    events_text = events_path.read_text(encoding="utf-8")
    if "TODO_OWNER" in events_text:
        errors.append("events.yml: still contains TODO_OWNER")
    for i, event in enumerate(yaml.safe_load(events_text) or [], start=1):
        missing = [f for f in REQUIRED_EVENT_FIELDS if not str(event.get(f, "") or "").strip()]
        if missing:
            errors.append(f"events.yml entry {i}: missing {', '.join(missing)}")

    for warning in warnings:
        print(f"warning: {warning}")

    if errors:
        print(f"Data check failed ({len(errors)} problem{'s' if len(errors) != 1 else ''}):")
        for error in errors:
            print(f"  - {error}")
        return 1

    total = sum(question_counts.values())
    print(f"Data check passed: {total} questions, {len(quiz_dates)} quiz pages, {len(urls)} posts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
