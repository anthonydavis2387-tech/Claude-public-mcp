# World Watch (5pm MT, Sun–Thu)

Replaces the old 5pm futures-only check and the midnight scan. Two outputs, both deliberately light:

1. **Phone reminder**: the run's final reply is the push notification, so end the run with one short message: "Time to review the futures." plus the top 5 futures moves (S&P, Nasdaq, WTI, gold, Bitcoin) and up to 3 one-line world headlines. `scripts/world_watch.py` prints exactly this text; use it as the final reply.
2. **World Watch page**: a separate artifact (URL in `reports/.worldwatch-url.txt`), updated in place. Not the main dashboard, which this session never touches.

## Budget

- 1 FMP call (made by the script: headline futures plus US-listed iShares country funds).
- About 4–5 WebSearches: Asia (Nikkei/Hang Seng/Shanghai/Kospi), Europe close (STOXX 600/DAX/FTSE), oil and Middle East, Latin America (Rio Times covers it daily). Add one for anything big and specific (a central bank move, an election).
- No stock universe, no research cache, no analyzer, no snapshot comparison.

## Steps

1. Run the ~5 searches. Write `reports/world-watch/{date}.json` in the shape below. Every number in the text must come from a search result, and every region lists the source URL(s) it used. If a region had no usable result, say so in its headline and leave it without sources rather than guessing.
2. `python3 skills/mamba-market-review/scripts/world_watch.py reports/world-watch/{date}.json /tmp/world-watch.html` (needs FMP_API_KEY).
3. Read the page at the URL in `reports/.worldwatch-url.txt` (the Artifact tool requires this), then publish `/tmp/world-watch.html` to that same `url`.
4. Commit the notes JSON and push to the branch.
5. Final reply = the reminder line the script printed. Nothing else.

```json
{
  "push_headlines": ["one line", "one line", "one line"],
  "on_notice": ["2-3 things to keep an eye on overnight, one sentence each"],
  "regions": {
    "asia":    {"headline": "...", "detail": "2-3 sentences with index levels/moves", "sources": [{"name": "...", "url": "https://..."}]},
    "china":   {...}, "europe": {...}, "latam": {...}, "mideast": {...}
  }
}
```

Known data quirk: FMP's `BZUSD` (Brent) jumps on contract rolls (it showed −9% on a −2.5% day), so the script leaves it out. Quote Brent from the news source instead.
