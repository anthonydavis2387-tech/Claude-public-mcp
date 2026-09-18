# Snapshots and the Dashboard

## Snapshot files (for day-over-day comparison)

Save one JSON file per run to `reports/{YYYY-MM-DD}/{session-slug}.json`, where `session-slug` is one of `evening-futures`, `midnight`, or `full-study`. Example path: `reports/2026-09-17/full-study.json`.

Schema:

```json
{
  "date": "2026-09-17",
  "session": "full-study",
  "generated_at": "2026-09-17T20:03:00Z",
  "futures": [
    {"symbol": "ES", "last": 6721.5, "chg_pct": 0.42, "trend_flag": "green"}
  ],
  "tickers": [
    {
      "symbol": "NVDA",
      "lists": ["dow30", "nasdaq100", "megacap_leaders", "semiconductor_ai"],
      "flags": {
        "trend": "green", "relative_strength": "green", "revenue_growth": "green",
        "margin_trend": "neutral", "earnings_growth": "green", "free_cash_flow": "green",
        "debt": "neutral", "valuation": "red", "institutional_ownership": "green", "moat": "green"
      },
      "red_flag_count": 1,
      "notes": "valuation stretched vs 1yr avg P/E"
    }
  ],
  "rollup": {
    "movers": ["..."],
    "multi_red_flag": ["..."],
    "improving": ["..."],
    "watchlist": ["..."]
  }
}
```

Keep every field machine-readable (the flag values, not prose) so Step 5's comparison logic can diff two snapshots directly instead of re-parsing text. `notes` is the one free-text field — use it for anything that doesn't fit a flag.

To build Step 5's comparison, find the most recent prior file under `reports/*/{same-session-slug}.json` (sort by date, take the last one before today), load both, and diff:
- `tickers[].flags` — any key that changed value
- `tickers[].red_flag_count` — delta
- `rollup.*` — set differences (who's new, who dropped off)
- `futures[].last` — % change from the prior snapshot's `last` for the same symbol

No pruning logic needed yet — plain files under `reports/` are cheap and the history itself is useful (that's also what feeds the dashboard's recent-history strip below). If this grows unwieldy after months of runs, that's a future cleanup, not something to solve now.

## Dashboard artifact

The dashboard is a Claude Artifact (a published HTML page) that gets **updated in place** after every run rather than re-created, so the user has one stable link. Read the `artifact-design` skill (and `dataviz` if the page includes charts/sparklines) before building or rebuilding this page's HTML — don't freehand the styling.

**Finding the existing dashboard:** check for `reports/.dashboard-url.txt` in this skill's directory.
- **If it exists:** read the URL from it, then use the Artifact tool's `read` action on that URL to pull the current published page before republishing (the Artifact tool requires having read a page in-session before you can update it — this applies even though a prior run published it, because a fresh scheduled session has no memory of that). Then `publish` again with that same `url` so it updates in place instead of creating a new artifact.
- **If it doesn't exist (first run ever):** build the page fresh and `publish` it with no `url`. Take the URL the publish call returns and write it to `reports/.dashboard-url.txt`, then make sure that file gets committed so future runs (which may be fresh sessions with no memory of this one) can find it. Tell the user the URL once, the first time — don't repeat it on every subsequent run, since the whole point is that it doesn't change.

**Page content:** the latest briefing (reuse the Step 6 structure, laid out for a screen rather than plain text) plus a compact recent-history strip — e.g. red-flag counts and a couple of headline futures over the last 5-10 sessions of each type, pulled straight from the `reports/` files already on disk rather than recomputing anything. This is meant to answer "how's it trending lately," not to be a full re-derivation of the comparison in Step 5. Add a **Market News & Research** section too — see `references/news-and-research.md` for what goes in it and how to embed it.

**Ticker labeling — every symbol needs its company name.** A bare ticker (`CEG`, `WELL`, `HONA`) isn't self-explanatory even to a regular user — put the company name next to it wherever a ticker appears on the page (flagged-names tables, futures cards, roll-up lists, the study/what's-next prose, quick links), not just in one lookup table. FMP's quote/batch-quote response already includes a `name` field for every symbol pulled during the run — carry it through rather than re-fetching it separately.

**Full universe directory — a full-study (or midnight) session scans more names than the flagged-names table shows.** Don't let "notable movers" and "multi-red-flag" tables be the only place a name appears — a user who wants to check a specific ticker that didn't get flagged has nowhere to look otherwise. Include a complete, searchable directory section (ticker, company name, list membership, price, %chg, red-flag count) covering every name scanned that session, not just the standouts. At 100+ rows this needs a client-side search/filter to stay usable — plain inline JS filtering table rows by a text input is fine within the Artifact sandbox (no external script needed); keep it wrapped in try/catch per the artifact-design guidance on defensive scripting. The 7pm futures-only check doesn't need this section (nothing to search beyond the already-compact futures tape).

Keep the page itself simple: it's a personal daily-glance dashboard, not a product. The Artifact sandbox only allows scripts from a small CDN allowlist (cdnjs, jsdelivr, Tailwind's CDN, jQuery) — third-party widget embeds like TradingView's live script (served from `s3.tradingview.com`) are not on that list and will silently fail to load, so don't attempt to embed one. `references/news-and-research.md` covers what to build instead. Beyond that, resist the urge to add live data-fetching or interactivity to the artifact itself (per artifact-capabilities guidance, that would need a declared runtime capability) — regenerating and republishing static HTML after each run is sufficient and much simpler to keep correct.
