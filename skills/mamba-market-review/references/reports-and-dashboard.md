# Snapshots and the Dashboard

## Snapshot files (for day-over-day comparison)

Save one JSON file per run to `reports/{YYYY-MM-DD}/{session-slug}.json`, where `session-slug` is one of `morning-macro` (8am), `evening-futures` (5pm), `midnight`, or `full-study` (2pm). Example path: `reports/2026-09-17/full-study.json`.

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
      "notes": "valuation stretched vs 1yr avg P/E",
      "detail": {
        "price": 219.34, "avg50": 213.57, "avg200": 197.95, "year_high": 236.54, "year_low": 164.27,
        "momentum_50d_pct": 2.7, "benchmark_3m_pct": -0.77, "benchmark_used": "QQQ",
        "revenue_growth_pct": 17.9, "revenue_growth_prev_pct": 19.8, "eps_growth_pct": 2.92,
        "gross_margin_pct": 75.0, "gross_margin_4q_ago_pct": 73.4, "op_margin_pct": 66.2, "op_margin_4q_ago_pct": 63.2,
        "fcf_last4q": [21400000000, 48587000000, 34904000000, 22115000000],
        "debt_to_equity": 0.17, "net_debt_to_ebitda": 0.23,
        "pe_ratio": 19.9, "ps_ratio": 49.4, "ev_to_ebitda": 65.7
      }
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

**`detail` is required, not optional** — it's what feeds the 10-Point Analyzer companion page below. Saving only the categorical flags (green/red/neutral) is not enough; keep the real numbers behind each flag (the ones already pulled from FMP mid-run — this is free, not an extra fetch) so a future session can rebuild the analyzer from the snapshot alone, without re-deriving anything.

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

**Full universe directory — a full-study (or midnight) session scans more names than the flagged-names table shows.** Don't let "notable movers" and "multi-red-flag" tables be the only place a name appears — a user who wants to check a specific ticker that didn't get flagged has nowhere to look otherwise. Include a complete, searchable directory section (ticker, company name, list membership, price, %chg, red-flag count) covering every name scanned that session, not just the standouts. At 100+ rows this needs client-side search/filter/sort to stay usable, not just free-text search — a dropdown to filter by list membership (Dow 30 / Nasdaq 100 / S&P 500 / sector basket / etc.) and by red-flag count (0, 1+, 2+, ...), plus clickable column headers to sort by ticker, company, price, %chg, or red-flag count. Plain inline JS is fine within the Artifact sandbox (no external script needed) — keep it wrapped in try/catch per the artifact-design guidance on defensive scripting. The 5pm futures-only check and 8am morning macro update don't need this section (nothing to search beyond the already-compact futures tape).

**The Full Universe Directory needs per-name reasoning, not just a red-flag count.** A bare number ("2 red flags") doesn't tell the user which two of the 8 API-backed checklist items are red or why. Give every row two things: (1) a compact "10-Pt Flags" column showing all 8 checklist points as small colored letter badges (green/red/amber/gray for na) so the pattern is visible at a glance across all 200+ rows without clicking anything, and (2) a click-to-expand detail row (a caret/expand button in the ticker cell) that reveals the real numbers behind each of the 8 points (same level of detail as the 10-Point Analyzer — price vs. moving averages, growth percentages, margin now vs. 4 quarters ago, FCF by quarter, D/E, P/E, etc.) plus a one- or two-line auto-generated "why" summary (which items are red, which are green) for that specific name. This needs the same embedded JSON-blob-plus-inline-JS approach as the Analyzer page (a `<script type="application/json">` data island, expand/collapse via plain JS, no runtime capability needed) — reuse the Analyzer's per-point rendering logic rather than re-inventing it, since it's the same 8 numbers either way. Institutional ownership and moat stay qualitative/plan-gated as elsewhere; note that in the expanded detail rather than pretending there's a number for them.

**The flagged-names table needs the same filter treatment as the directory, not just a static list.** Search box, a list-membership dropdown, and a red-flag-count dropdown (this table is already 4+ only, so its red-flag filter just needs a "4+ / 5 only" style split rather than the directory's full 0-4+ range) — same pattern, same `data-search`/`data-lists`/`data-red` attributes on each row, its own small filter script. Don't skip this just because the table is shorter than the full directory; a user actively narrowing down the flagged names by sector or severity is a real use case (e.g. "just show me the flagged utilities").

**Every dollar price gets a `$` sign — no exceptions.** Stock prices, futures prices denominated in dollars, Bitcoin/crypto prices, market caps — all of them, everywhere they appear on the page (directory rows, flagged-names table, futures cards, Bitcoin section, roll-up prose). A bare number reads as ambiguous even when the context implies currency. The only numbers that should NOT get a `$` are percentages, ratios (P/E, D/E), counts, and non-dollar levels like a Treasury yield or the Dollar Index itself (those are index points, not dollars).

**Lead with the market, not the pipeline.** The page's opening section (give it a real title — "The Bottom Line," "Today's Read," or similar, not a vague label) must be genuine market content a reader came for: the macro setup, what's flagged and why, what to watch — written the way a market briefing's lead paragraph would be, not a changelog of what got fixed in this session's data pipeline. Endpoint corrections, screener bugs, data-quality fixes, and scope decisions belong exclusively in the Pipeline Findings section at the bottom, where a reader who wants that detail can find it and everyone else can skip it. If a run involved bug fixes, do not let that fact bleed into the lead section's framing (no "Corrected run" style openers) — the lead section's job is to answer "what do I need to know about the market today," full stop.

**Design system: broadsheet editorial, not a SaaS dashboard.** The user asked for the page to feel like reading a serious financial newspaper rather than an app. Built as an *original* editorial design in that genre — never use any real publication's actual name, logo, masthead typeface, or copy their specific trademarked layout; this stays "Mamba Market Review" with its own invented identity (masthead, tagline, edition-bar) styled in that tradition. Concretely: `Playfair Display` for headlines/mastheads, `PT Serif` for body copy, `Source Sans 3` for UI chrome/labels/data-table text, `IBM Plex Mono` for tabular numerals — all via Google Fonts. Ink-on-newsprint palette (warm cream background, near-black ink, a single oxblood/maroon accent) instead of the boutique-SaaS gold/plum from earlier versions. Flat, rule-based separation (hairline `border-bottom`s, an occasional `3px double` rule for major section breaks) instead of card shadows and rounded corners — `--shadow: none` — reserve rounded pill buttons only for genuinely interactive controls (voice bar, filter selects), since those should still read as UI even inside an editorial page. A drop cap on the lead section's first paragraph, a small-caps "kicker" label above each section headline (e.g. "Markets", "Crypto", "Analysis", "Corrections & Methodology" — categorize by what the section actually is), and a couple of large pull-quote numbers pulled from that session's own facts are the signature editorial touches; keep them serving real content, not decorating for its own sake. Keep the 10-Point Analyzer companion page's palette/type in sync with the dashboard's — same tokens, applied a bit more plainly since it's a lookup tool rather than a briefing.

Keep the page itself simple: it's a personal daily-glance dashboard, not a product. The Artifact sandbox only allows scripts from a small CDN allowlist (cdnjs, jsdelivr, Tailwind's CDN, jQuery) — third-party widget embeds like TradingView's live script (served from `s3.tradingview.com`) are not on that list and will silently fail to load, so don't attempt to embed one. `references/news-and-research.md` covers what to build instead. Beyond that, resist the urge to add live data-fetching or interactivity to the artifact itself (per artifact-capabilities guidance, that would need a declared runtime capability) — regenerating and republishing static HTML after each run is sufficient and much simpler to keep correct.

**Read-aloud and voice command bar.** A fixed bottom bar with buttons to read the full briefing, the Bitcoin section, the flagged names, and the What's Next questions aloud via the browser's built-in `speechSynthesis` (Web Speech API) — no external service, no runtime capability needed, works everywhere.

**Voice quality:** the Web Speech API only exposes whatever voices the visitor's OS/browser ships — there's no way to reach a higher-quality TTS provider (ElevenLabs, etc.) from inside the Artifact sandbox, since that would mean a client-side fetch to a third-party host the CSP doesn't allow (and exposing an API key client-side besides). Do the best that's actually possible instead: default `rate` to ~0.85 and `pitch` to ~0.72 — noticeably slower and lower than any browser's un-tuned default, landing on a deep, laid-back, smooth cadence rather than a brisk announcer read. The user asked at one point for a specific celebrity's voice (a well-known deep, laid-back male voice) — that's not something to build: there's no voice-cloning path available client-side in this sandbox, and even if there were, labeling a synthetic voice with a real person's name misrepresents it as theirs. What they actually wanted was the vibe, which the rate/pitch tuning above delivers as an original, unnamed style rather than an impression of anyone specific — don't attach a real person's name to it.

**Ten voice profiles, not one auto-pick.** The user asked for a curated set of ~10 clear, human, English-speaking voice options spanning different accents/genders (explicitly including African-accented English), with celebrity voices as a reference point for what they meant. Two hard constraints shaped what actually got built, and both are worth restating if this ever needs revisiting: (1) the Web Speech API has no ethnicity field — `lang` (locale, e.g. `en-ZA`, `en-IN`) and a free-text `name` are all it exposes, so **accent/locale is the only honest, available proxy for "English ethnicities,"** not a race/ethnicity attribute that doesn't exist in this API on any platform; (2) actual celebrity voices can't be reproduced here — there's no voice-cloning capability available client-side in the Artifact sandbox, and labeling a synthetic voice with a real person's name would misrepresent it as their voice, which is a hard no regardless of sandbox capability (impersonation). So: **10 fixed profile slots** — American (M/F), British (M/F), Australian (M/F), Indian English (M/F), African English (M — South African/Nigerian/Kenyan locales), Irish (F) — each resolved at runtime to the best real matching voice on the visitor's device via locale + name-based gender heuristics, filtered to English-only (`lang` starts with `en`) and through a blocklist of known novelty/effects voices (Albert, Zarvox, Bells, Whisper, and similar non-human-register macOS joke voices) so every option is actually clear human speech. A profile with no real match on that device shows as "not available on this browser" rather than silently substituting something misleading; a close-but-not-exact match is labeled "Closest match: X" rather than passed off as the real thing. All 10 slots always render so the user sees the full intended menu even on a browser that can only fill half of them. Rate/pitch sliders remain, applying on top of whichever profile is selected. Selection persists to `localStorage` by profile id (re-resolved against `getVoices()` on load, since raw voice objects/names aren't guaranteed stable across sessions) — per-viewer only, not readable by Claude or synced across devices. Also wire an optional voice-command toggle via `SpeechRecognition`/`webkitSpeechRecognition` (feature-detect and disable the mic button with an explanatory `title` if unsupported — this is Chrome/Edge/Safari-only, not Firefox, and can fail silently if the Artifact's embedding context blocks microphone permission; the read-aloud buttons must work regardless of whether voice commands do). Match simple keyword commands (bitcoin/btc, flag, next, brief/dashboard/review, stop) rather than requiring exact phrasing. **The spoken text is hand-written per section to read naturally (numbers spelled out, "%" read as "percent," no markup) — it is not scraped from the DOM.** That means it goes stale exactly like every other section: regenerate all four spoken strings from that session's actual numbers every time the dashboard is rebuilt, the same as the visible text. Keep each section's spoken text short enough to actually listen to (a paragraph or two, not a full read of every row).

**Bitcoin gets its own section, not just a futures-tape row.** It's the one asset in the universe that trades 24/7, so a single "BTC +X%" card in the futures grid undersells it. Give it a dedicated section with: current price, today's %chg, 52-week range, a plain-language trend read (price vs. 50d/200d averages), and a small grid of 7-day / 30-day / 90-day moves so the user can see momentum at a few timeframes, not just one. Pull the historical closes from `/stable/historical-price-eod/full?symbol=BTCUSD` (same endpoint used for relative strength) and compute the lookback returns directly — no separate endpoint needed. A couple of lines of WebSearch context (ETF flow trends, a notable move) round it out, same sourcing rules as the Market News & Research section. Label the section clearly as reflecting the live price at generation time when the rest of the page is showing a prior close (e.g. a weekend run) — the two timestamps aren't the same and shouldn't be presented as if they were.

## 10-Point Analyzer (companion page)

A second, linked Artifact that lets the user look up any single name from that session's universe and see the full numeric detail behind all 10 checklist points — not just the flag, the actual numbers (price vs. moving averages, revenue/EPS growth %, margin now vs. 4 quarters ago, FCF by quarter, D/E and net-debt/EBITDA, P/E and P/S, and plain-language notes for institutional ownership/moat explaining why those two are usually gaps). The main dashboard's tables only have room to surface the standouts; this page is where "why is this one flagged" actually gets answered for any of the 200+ names scanned, not just the ones that made the roll-up.

**Mechanics mirror the main dashboard exactly, in a second file:** check `reports/.analyzer-url.txt` the same way as `reports/.dashboard-url.txt` — read and update in place if it exists, publish fresh and save the URL if it doesn't. Link the two pages to each other (a back-link on the analyzer, a forward-link in the dashboard's intro and Quick Links). Rebuild it every session that has a full ticker universe (full-study, midnight) using that session's `detail` fields straight from the snapshot being written — the analyzer's data is a straight dump of `tickers[].detail`, no separate computation. Skip it for the evening futures-only check (nothing to look up beyond the futures tape already on the main page).

Implementation-wise this is a single static page: embed the ticker data as a JSON blob in a `<script type="application/json">` tag and render the list/detail interaction with plain inline JS (a searchable ticker list on one side, a detail panel on the other) — no runtime capability needed, since nothing has to be fetched live. A name outside that session's universe isn't in the data and can't be looked up from the page itself; say so on the page and point back to asking Claude directly for a live one-off pull.
