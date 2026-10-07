# Let'z Quiz!

Source of https://letzquiz.github.io, a Jekyll site with the Minimal Mistakes
theme (`remote_theme`). Pushing to `main` builds and deploys it through
GitHub Actions; it also rebuilds daily so past events drop off.

Run it locally:

```bash
bundle install
bundle exec jekyll serve
```

## Monthly routine

1. **When the date is set:** add the quiz to `_data/events.yml` (date, start,
   venue, area, status) and push. The homepage card, `events.ics` and the
   search-engine Event markup update by themselves.
2. **After the quiz:** run `python3 scripts/new_quiz.py`, fill in
   `_data/questions_YYYY_MM.json` (every question needs `question`, `answer`,
   `date` and a `category`: `general`, `screen`, `sport` or `misc`), set the
   question count in the post's `excerpt`, optionally add a poster as
   `assets/images/posters/YYYY-MM-DD.webp`, then push.
3. **Nothing to remove:** past events disappear automatically.

Before pushing, `python3 scripts/check_data.py` (needs `pip install pyyaml`)
runs the same data check as CI.

## Where things live

| What | Where |
| --- | --- |
| Upcoming quizzes | `_data/events.yml` |
| Questions | `_data/questions_YYYY_MM.json` |
| Quiz page sections | `_data/quiz_sections.yml` |
| Brand colours, fonts, all custom CSS | `assets/css/main.scss` |
| Menu | `_data/navigation.yml` |
| Ad unit | `_includes/ad-slot.html` |
