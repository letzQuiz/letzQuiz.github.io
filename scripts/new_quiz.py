#!/usr/bin/env python3
"""Create the post and data file for a quiz that just happened.

Asks for the date, title and venue, then writes
  _posts/YYYY-MM-DD-<slug>.md          (layout: normal-quiz)
  _data/questions_YYYY_MM.json         (one example question to replace)

Fill in the questions, set the excerpt's question count, then run
`python3 scripts/check_data.py` before pushing.

Usage: python3 scripts/new_quiz.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default or ""


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    quiz_day = date.fromisoformat(ask("Quiz date (YYYY-MM-DD)"))
    title = ask("Title")
    venue = ask("Venue", "Le Croque Bedaine")
    if not title:
        sys.exit("A title is needed.")

    post = ROOT / "_posts" / f"{quiz_day.isoformat()}-{slugify(title)}.md"
    data = ROOT / "_data" / f"questions_{quiz_day:%Y_%m}.json"
    for path in (post, data):
        if path.exists():
            sys.exit(f"{path.relative_to(ROOT)} already exists; not overwriting.")

    nice_day = f"{quiz_day.day} {quiz_day:%B %Y}"
    post.write_text(
        "---\n"
        "layout: normal-quiz\n"
        f'title:  "{title}"\n'
        f'location: "{venue}"\n'
        f'date: "{quiz_day.isoformat()}"\n'
        f'excerpt: "N questions from the {nice_day} pub quiz at {venue}."\n'
        "# header:\n"
        "#   teaser: /assets/images/posters/" + quiz_day.isoformat() + ".webp\n"
        "categories:\n"
        "  - Questions\n"
        "---\n",
        encoding="utf-8",
    )

    example = [{
        "question": "Replace me with the first question",
        "answer": "Replace me with its answer",
        "tags": "general knowledge",
        "category": "general",
        "date": quiz_day.isoformat(),
    }]
    data.write_text(json.dumps(example, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Created {post.relative_to(ROOT)} and {data.relative_to(ROOT)}.")
    print("Categories: general, screen, sport, misc (see _data/quiz_sections.yml).")


if __name__ == "__main__":
    main()
