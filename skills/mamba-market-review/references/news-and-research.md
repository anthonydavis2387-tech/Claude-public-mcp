# Market News & Research Section

This is the dashboard section covering news, quick links to charting/research tools, and (where useful) a couple of small self-drawn charts. Read this *after* `reports-and-dashboard.md` — this file only covers what goes inside that section, not the rest of the page.

## What NOT to do: live third-party widgets

Don't try to embed TradingView's (or any other provider's) live JS widget directly in the dashboard. The Artifact sandbox's CSP only allows external `<script>` sources from `cdnjs.cloudflare.com`, `cdn.jsdelivr.net/npm/`, Tailwind's play-CDN, and `code.jquery.com` — a script tag pointed at `s3.tradingview.com` (or any other provider's embed host) is silently blocked, not an error you'll see and fix. This applies to any similar provider (Yahoo Finance, MarketWatch, CNBC embeds, etc.) — none of the common finance-widget hosts are on that allowlist.

What actually works instead, in order of how "live" it feels:

## 1. Self-drawn charts (as live as it gets within the sandbox)

For a handful of the day's most relevant names/futures — not all 150+, just the ones already called out in the Roll-Up — pull recent daily closes from FMP (`/stable/historical-price-eod/full?symbol={T}`, same endpoint used for relative strength) and draw a small inline SVG sparkline or line chart directly in the page HTML. This is fully within the sandbox rules since it's plain inline SVG, no external script. Read the `dataviz` skill before drawing these — it covers axis/label conventions and the same-system color approach so the charts match the rest of the page rather than looking bolted on.

Keep this to the names that matter that day (multi-red-flag names, big movers, watchlist entries) — a sparkline on every ticker in the universe would bloat the page for no reason.

## 2. Curated headlines (refreshed each run, plain text + links)

Pull headlines via WebSearch, organized in two tiers:
- **Macro** (2-4 items): Fed/rates, major index moves, geopolitical events likely to matter to the futures tape.
- **Name-specific** (1 item per name that's in that day's Roll-Up callouts, not the whole universe): search `"{TICKER} news today"` for names flagged as multi-red-flag, notable movers, or newly on the watchlist.

Render each as a headline + one-line summary + a plain `<a href>` to the source. This is just text and links — no script needed, fully CSP-safe, and it's the actual news content rather than a widget frame around content you'd still have to read elsewhere.

## 3. Quick-links row (for anything that needs a real interactive chart or full-text article)

A short row of plain outbound links for the user to click through to when they want more than the dashboard itself provides — these are normal `<a>` tags, not embeds, so there's no CSP concern:
- TradingView chart for a name: `https://www.tradingview.com/symbols/{EXCHANGE}-{TICKER}/` (e.g. `NASDAQ-NVDA`)
- WSJ markets section: link to the publicly-accessible markets overview page, not a specific paywalled article
- A general finance search shortcut for whatever the user wants to dig into further

This is the honest way to get TradingView-quality interactivity onto the user's radar without pretending the dashboard can embed it.

## On WSJ specifically

Do not attempt to log into the user's WSJ account or scrape paywalled content, even if credentials are provided — most subscription terms of service prohibit automated/bot access regardless of whether the login is valid, and it would be a fragile integration to maintain besides. What's fair game: headlines and summaries that are publicly visible without a login (via WebSearch), included in the "Macro" tier above like any other public source. Full cover-to-cover WSJ reading stays the user's manual task, same as originally scoped — this section supplements it, it doesn't replace it.
