#!/usr/bin/env python3
"""Add a single `category` field to every question in _data/questions*.json.

The original `tags` field is kept untouched for reference. Questions that
already have a `category` are left alone, so the script is safe to re-run
and manual overrides survive.

Usage: python3 scripts/normalize_questions.py
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "_data"

# original tag (lower-case) -> category id (see _data/quiz_sections.yml)
TAG_TO_CATEGORY = {
    "general knowledge": "general",
    "sport": "sport",
    "olympics": "sport",
    "tv": "screen",
    "tv series": "screen",
    "movies": "screen",
    "books": "screen",
    "literature": "screen",
    "games": "screen",
    "comics": "screen",
    "music": "misc",
    "fun-with-flags": "misc",
}
DEFAULT_CATEGORY = "misc"


def category_for(tags):
    if isinstance(tags, list):
        tags = tags[0] if tags else ""
    return TAG_TO_CATEGORY.get(str(tags).strip().lower(), DEFAULT_CATEGORY)


def normalize(question):
    if "category" in question:
        return question
    out = {}
    for key, value in question.items():
        out[key] = value
        if key == "tags":
            out["category"] = category_for(value)
    if "category" not in out:
        out["category"] = DEFAULT_CATEGORY
    return out


def main():
    for path in sorted(DATA_DIR.glob("questions*.json")):
        questions = json.loads(path.read_text(encoding="utf-8"))
        normalized = [normalize(q) for q in questions]
        path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(normalized)} questions")


if __name__ == "__main__":
    main()
