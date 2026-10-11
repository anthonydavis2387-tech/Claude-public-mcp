# Week in Review (Friday 5pm MT)

A recap page for the user to catch up on the week if they couldn't follow it day to day. One artifact holds every
week: the newest week shows by default, and older weeks sit in the "Week ending" picker. Do not touch the dashboard,
the 10-Point Analyzer, the stock universe or the research cache in this session.

- Page URL: `reports/.weekly-url.txt` (publish in place to that URL; read it first, as with every artifact).
- Script: `scripts/weekly_recap.py` with page template `scripts/weekly_recap_template.html`.
- Data: `reports/weekly/{week_end}.json` (one per week, built by the script) and the hand-written notes in
  `reports/weekly/notes/{week_end}.json`. `week_end` is the Friday (YYYY-MM-DD). For a holiday-shortened week, still
  use the Friday date.

## Steps

1. Read the watchlist from the dashboard database (`watchlist/state` on the dashboard artifact; names whose value is
   `true`).
2. Gather the week's headlines with about 6 WebSearches: one per weekday ("stock market today {Month D, YYYY}") plus one
   weekly wrap ("stock market week recap {Friday's date}"). Keep only facts a search result states, with its URL. When
   sources disagree on a number, use the one most sources agree on, or leave the number out.
3. Write `reports/weekly/notes/{week_end}.json`:
   ```json
   {"headline": "one line, the story of the week",
    "push": "one short sentence for the phone notification",
    "summary": "one paragraph, 4-7 plain sentences",
    "mood": "two to four words, e.g. Calm but rotating",
    "mood_detail": "one or two sentences tying the VIX, breadth and equal-weight vs S&P together",
    "days": [{"date": "YYYY-MM-DD", "headlines": ["..."], "sources": [{"name": "...", "url": "..."}]}],
    "themes": [{"title": "...", "text": "..."}],
    "questions": ["2-3 open questions for the user to reason through; no conclusions handed over"],
    "watchlist": ["SYM", "..."],
    "gaps": "optional note on missing days or data"}
   ```
   Every weekday gets an entry in `days`. Put tickers in parentheses after company names. Check the numbers you cite in
   `summary`, `themes` and `mood_detail` against the built data (step 4) and fix any that disagree.
4. Run `python3 skills/mamba-market-review/scripts/weekly_recap.py build {week_end} skills/mamba-market-review/reports/weekly/notes/{week_end}.json`.
   It pulls Friday-to-Friday closes from FMP for the indexes, sector funds, macro gauges, every dashboard name and the
   watchlist, reads that week's saved daily snapshots for the dashboard's own readings, and pulls next week's
   earnings (dashboard names only) and key US economic releases.
5. Run `python3 skills/mamba-market-review/scripts/weekly_recap.py render /tmp/week-in-review.html` and publish that file
   to the URL in `reports/.weekly-url.txt`. The script prints the phone-notification line.
6. Commit the notes file and the built week file, then push as the routine prompt describes.
7. The final reply is only the line the script printed; it becomes the phone notification.
