---
name: mamba-market-review
description: Runs the user's personal daily "Mamba Mentality" market study routine (8am MT weekday macro + Bitcoin update, 2pm MT weekday full study at market close, 5pm MT Sun-Thu futures-only check, midnight MT lightweight futures + ~100-stock check) and produces one consolidated market briefing. Use this whenever the user asks to review the market, run their market review/briefing/scan, check futures, study stocks, mentions "Mamba" or their market routine, asks about Dow 30, Nasdaq 100, S&P 500, Russell Top 100, or their software/mega-cap/semiconductor watchlists, or wants a daily recap covering trend, relative strength, revenue growth, margins, earnings growth, free cash flow, debt, valuation, institutional ownership, or competitive moat ("more/less needed") across a stock universe. Also trigger on session-specific phrasing like "run my 8am check", "futures check", "midnight review", "full study session", or "what should I be watching today" in a trading/investing context.
---

# Mamba Market Review

Consolidates a personal daily market-study routine — four review sessions a day (all times Mountain) across futures, Bitcoin, the Dow 30, Nasdaq 100, S&P 500 Top 100, a large-cap proxy, and three 20-name sector watchlists — into one briefing, so the user doesn't have to manually pull each name one at a time.

## Step 1: Figure out which session this is

The routine has four checkpoints, all Mountain Time. Infer the session from the user's phrasing or the current time; ask only if genuinely ambiguous:

| Session | When | Days | Universe |
|---|---|---|---|
| **Morning macro + Bitcoin update** | 8am MT | Weekdays (Mon-Fri) | Macro headlines, Bitcoin status/movement, and whatever futures FMP + WebSearch fallback cover — no stock scan |
| **Futures-only check** | 5pm MT | Sun-Thu (skip Fri & Sat) | Futures only (40 symbols) |
| **Midnight check** | midnight MT | Nights leading into Mon-Fri | Futures (40) + a ~100-stock scan (Dow 30 + Nasdaq 100 + S&P 500 Top 100, deduped, capped/sampled to ~100 — this is the lightweight session, don't run the full 200+ universe here) |
| **Full study session** | 2pm MT (market close) | Weekdays (Mon-Fri) | Everything: all futures, Bitcoin, Dow 30, Nasdaq 100, S&P 500 Top 100, the large-cap proxy, and the three 20-name sector baskets |

If the user just says "run my market review" with no time context, default to the full study session — it's a superset and never wrong to over-deliver.

## Step 2: Load the universe and the checklist

- Read `references/universe.md` for the ticker lists (futures, Dow 30, Nasdaq 100, Russell Top 100 proxy, and the three sector baskets). It explains which lists are stable (Dow 30) vs. need periodic refresh (Nasdaq 100, Russell Top 100) and how to refresh them live via FMP's index-constituent endpoints when a key is available.
- Read `references/checklist-fmp-mapping.md` for the 10-point checklist (trend, relative strength, revenue growth, margin trend, earnings growth, free cash flow, debt, valuation, institutional ownership, "more/less needed") and exactly which Financial Modeling Prep (FMP) endpoint and field answers each point.

Dedupe tickers that appear in more than one list (e.g. NVDA is Dow 30 + Nasdaq 100 + mega-cap leader + semiconductor basket) — check it once, and note in the output every list it belongs to.

## Step 3: Pull the data

Primary source is the FMP API, read via the `FMP_API_KEY` environment variable (or however the user has stored their key — ask once if it's not obviously available, and remember the answer for the rest of the session rather than re-asking per ticker).

For each ticker, work through the 10-point checklist using the endpoint mapping in the reference file. Batch calls where FMP supports it (e.g. bulk quote endpoints take comma-separated symbols) instead of one request per ticker per metric — with ~150+ names in the full session, request efficiency matters.

If a key isn't configured, or a specific endpoint/field comes back empty for a ticker (common for newer listings or thinly-covered names), fall back to WebSearch/WebFetch for that one item only. Don't fail the whole run over one missing data point — pull what's available and flag the gap in the output instead of silently guessing or omitting it.

## Step 4: Score each name, but keep it scannable

Nobody reads a 10-line essay for 150 tickers. For each name, condense the checklist into a single compact row: a flag per item (✅ green / ➖ neutral / ⚠️ red), not prose. Save prose for the roll-up section (Step 5) and for any name that's genuinely notable.

A useful default heuristic: count the ⚠️ red flags per name.
- **0-1 red flags**: healthy, no special callout needed beyond the row.
- **2-3 red flags**: worth a line in "names flashing multiple red flags."
- **4+ red flags, or a hard stop-sign metric** (e.g. deeply negative FCF with rising debt, or a clear downtrend + weak relative strength together): call it out explicitly — these are the names most likely to actually matter to the user.

Use the same logic in reverse for "names improving" — look for names moving from red/neutral to green on 2+ items versus their own recent trend, not just names that already look good.

## Step 5: Load the previous snapshot for comparison

Before writing the briefing, look in `reports/` for the most recent snapshot from the **same session type** (compare the 2pm full study to the last 2pm full study, not to last night's midnight run — different universes aren't comparable). See `references/reports-and-dashboard.md` for the snapshot file layout and JSON schema.

If one exists, compute:
- Which tickers flipped a flag (especially green→red or red→green — a flag that got worse is more useful to know than one that's still red)
- Red-flag-count deltas per name
- Names that entered or dropped off "multiple red flags," "improving," or "watchlist" since last time
- For futures: the move since the last matching session, not just today's raw %chg

If there's no prior snapshot of this session type yet (first run), skip this section and say so — don't fabricate a comparison.

## Step 6: Assemble the briefing

Use this structure. Skip the "Stock Universe Scan" section entirely for the 5pm futures-only check and the 8am morning macro + Bitcoin update — neither scans stocks.

```
# Daily Market Briefing — [date] — [session name]

## Futures Tape
[compact table: symbol | last | % chg | trend flag | note]

## Bitcoin
(8am and 2pm sessions only — see references/reports-and-dashboard.md's
Bitcoin section spec: price, %chg, 52wk range, trend vs 50d/200d, 7/30/90-day
moves, brief context.)

## Stock Universe Scan
(only for midnight / 2pm sessions — organize by list: Dow 30, Nasdaq 100,
S&P 500 Top 100, large-cap proxy, Software/Cloud, Mega-Cap Leaders,
Semiconductor/AI. Note cross-listed names once, don't repeat full rows.)

## Roll-Up
- **Notable movers / breakouts:** ...
- **Multiple red flags:** ...
- **Improving:** ...
- **Watchlist for next session:** ...

## vs Previous Report
(from Step 5 — flag flips, red-flag-count deltas, watchlist churn since the
last same-type session. Omit this section on the first-ever run instead of
leaving it blank.)

## Macro / Headlines
(1-3 lines on major macro headlines relevant to today's session, pulled via
WebSearch — this is a supplement, not a replacement for the user's own WSJ
read-through, which stays a manual habit outside this skill's scope.)

## Data Notes
(which items came from FMP vs. WebSearch fallback, any tickers with gaps or
stale data, and a reminder if the Nasdaq 100 / Russell Top 100 lists in
references/universe.md look due for a refresh.)
```

Keep the whole thing tight enough to actually read in one sitting — that's the point of consolidating three manual sessions into one briefing.

## Step 7: Save the snapshot and update the dashboard

Two follow-up actions after the briefing text is done — see `references/reports-and-dashboard.md` for the exact mechanics of both:

1. **Save today's snapshot** to `reports/` so the *next* run of this session type has something to compare against (Step 5 depends on this — skipping it breaks comparison for next time).
2. **Publish/update the dashboard artifact** — a bookmarkable page showing the latest briefing, recent history, and a Market News & Research section (curated headlines, a few self-drawn charts for notable names, quick links out to TradingView/WSJ — see `references/news-and-research.md` for exactly what belongs there and, importantly, what NOT to try embedding). The reports-and-dashboard reference file covers how to find the existing dashboard URL (so you update the same page instead of spawning a new one each run) and what to do on the very first run when no dashboard exists yet.
