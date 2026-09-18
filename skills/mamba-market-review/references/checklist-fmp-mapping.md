# The 10-Point Checklist → FMP Endpoints

**Recommended plan: FMP Premium** ($49/mo billed annually). Starter only includes *annual* fundamentals and ratios, but items 3-6 below need quarterly data to show a trend rather than a single once-a-year number — Premium's "Full Fundamentals and Ratios" is what unlocks the `period=quarter` parameter these calls rely on. Premium's 750 calls/min is also comfortably enough for a ~150-ticker session; the rate limit isn't the reason to go higher. The one gap Premium doesn't close is institutional ownership (item 9 below) — see that section for how the skill works around it rather than needing Ultimate.

FMP has been migrating endpoints from `/api/v3/...` to a flatter `/stable/...` namespace. Which one works depends on the user's plan/key. Try `/stable/` first; if it 404s, fall back to the `/api/v3/` path listed alongside it. All calls take `apikey={FMP_API_KEY}` as a query param.

For each item: pull it, and if the field is genuinely missing/null for a ticker (not just "I didn't check"), fall back to the WebSearch query shown and say in the output that this item came from a web search rather than FMP.

## 1. Trend
**Endpoint:** `/stable/quote?symbol={T}` (or `/api/v3/quote/{T}`)
**Fields:** `price` vs `priceAvg50` and `priceAvg200`. Price above both = uptrend; below both = downtrend; between them = mixed/transitioning. This single call also gives you `changesPercentage`, `yearHigh`, `yearLow` for free — grab those too, they're useful context for the same row.
**WebSearch fallback:** `"{TICKER} stock price 50 day 200 day moving average trend"`

## 2. Relative Strength
FMP doesn't have a direct RS-rating endpoint. Approximate it: pull the stock's trailing return (e.g. 3-month) and the same for a benchmark (`SPY` for broad market, or `QQQ` for tech-heavy names), then compare.
**Endpoint:** `/stable/historical-price-eod/full?symbol={T}` (or `/api/v3/historical-price-full/{T}`) for both the ticker and the benchmark, compute % change over the lookback window yourself.
**WebSearch fallback:** `"{TICKER} relative strength vs S&P 500 3 month performance"`

## 3. Revenue Growth
**Endpoint:** `/stable/financial-growth?symbol={T}&period=quarter` (or `/api/v3/financial-growth/{T}?period=quarter`)
**Field:** `revenueGrowth` (most recent quarter, YoY). Pull a few periods back to see if growth is accelerating or decelerating, not just the latest number in isolation.
**WebSearch fallback:** `"{TICKER} quarterly revenue growth YoY latest earnings"`

## 4. Margin Trend
**Endpoint:** `/stable/ratios?symbol={T}&period=quarter&limit=8` (or `/api/v3/ratios/{T}?period=quarter&limit=8`)
**Fields:** `grossProfitMargin`, `operatingProfitMargin`, `netProfitMargin` across the returned periods — look at direction over the last 4-8 quarters, not just the current value.
**WebSearch fallback:** `"{TICKER} operating margin trend last few quarters"`

## 5. Earnings Growth
**Endpoint:** `/stable/financial-growth?symbol={T}&period=quarter` (same call as #3)
**Field:** `epsgrowth` (or `netIncomeGrowth`). Also worth a quick check of `/stable/earnings-surprises?symbol={T}` for whether recent quarters have been beating or missing estimates — a stock growing earnings but consistently missing its own guidance is a different story than one beating and raising.
**WebSearch fallback:** `"{TICKER} EPS growth latest quarter earnings beat or miss"`

## 6. Free Cash Flow
**Endpoint:** `/stable/cash-flow-statement?symbol={T}&period=quarter&limit=8` (or `/api/v3/cash-flow-statement/{T}`)
**Field:** `freeCashFlow`. Check the trend across periods and whether it's consistently positive — a company can show revenue/earnings growth while FCF deteriorates (heavy capex, working capital drag), which is exactly the kind of divergence this checklist item exists to catch.
**WebSearch fallback:** `"{TICKER} free cash flow trend"`

## 7. Debt
**Endpoint:** `debtToEquityRatio` comes from `/stable/ratios?symbol={T}&period=quarter` (item #4's endpoint, **not** key-metrics — verified live: key-metrics has no `debtToEquity`/`debtToEquityRatio` field on this plan, it 200s but omits it). `netDebtToEBITDA` comes from `/stable/key-metrics?symbol={T}&period=quarter` as originally documented (verified present there).
**Fields:** `debtToEquityRatio` (from ratios), `netDebtToEBITDA` (from key-metrics). Rising leverage alongside flat/falling FCF (item 6) is the combination worth flagging red. Note: for banks/financials, D/E and net-debt/EBITDA run structurally high (balance-sheet leverage is the business model) — don't flag a bank red on these two alone without noting the sector context.
**WebSearch fallback:** `"{TICKER} debt to equity ratio balance sheet"`

## 8. Valuation
**Endpoint:** `/stable/ratios?symbol={T}&period=quarter` (same family as #4) or `/stable/key-metrics?symbol={T}&period=quarter`
**Fields:** `priceToEarningsRatio` (verified live field name on `/stable/ratios` — **not** `priceEarningsRatio` or `peRatio`, both of which are absent from the response), `priceToSalesRatio`, `evToEBITDA` (on key-metrics). Valuation only means something in context — compare against the ticker's own recent history if you can pull a few periods, or against sector peers already in the day's universe, rather than judging the multiple in isolation.
**WebSearch fallback:** `"{TICKER} PE ratio valuation vs sector average"`

## 9. Institutional Ownership — plan gap, treat as a spot-check not a full scan
**Endpoint:** `/stable/institutional-ownership/symbol-ownership?symbol={T}` (or `/api/v3/institutional-ownership/symbol-ownership?symbol={T}`)
**Fields:** `ownershipPercent`, and the change in `investorsHolding` / `numberOf13Fshares` period over period if the endpoint returns a history — rising institutional ownership is a supportive signal, sharp reductions are worth a flag.

On the FMP Starter/Premium tiers, ownership/holdings data isn't listed as an included feature (it appears to sit under the Ultimate tier's "holdings" bucket instead) — try the endpoint first each run since FMP's plan boundaries do shift, but expect it to come back empty/unauthorized on Premium. **Don't fall back to WebSearch for this on every ticker in the universe** — at 150+ names that's 150+ searches just for one checklist item, which is slow and low-value for names nobody cares about. Instead:
- **Run the full 10-point checklist on all 8 other API-backed items as normal.**
- **Only spot-check institutional ownership via WebSearch for names that already stood out** on the other items — multi-red-flag names, notable movers, and watchlist entries from the Roll-Up. For everything else, mark this item `n/a` rather than guessing or skipping the row silently.
- If the user later upgrades to a tier that includes the endpoint, drop this restriction and go back to checking it on every name like the other 9 items.

**WebSearch fallback (spot-check only, per above):** `"{TICKER} institutional ownership percentage recent 13F changes"`

## 10. Becoming More or Less "Needed" (moat / structural relevance)
This one is qualitative and FMP alone won't answer it — treat items 3-9 as supporting evidence (durable revenue growth + stable/expanding margins + growing institutional interest tends to correlate with a strengthening competitive position) but synthesize the actual judgment from:
**Endpoint:** `/stable/profile?symbol={T}` (or `/api/v3/profile/{T}`) for the business description as a starting point, plus `/stable/analyst-estimates?symbol={T}&period=quarter` for whether forward estimates are being revised up or down — **the `period` query param is required**, the call 400s with "Invalid or missing query parameter - period" without it (verified live).
**WebSearch fallback (primary source for this one, not just a fallback):** `"{TICKER} competitive moat market share 2026"` or `"is {COMPANY} losing market share to competitors"` — this is the item most worth spending an actual web search on rather than trying to infer purely from financials, since "more/less needed" is really asking about competitive dynamics that don't show up in a single quarter's numbers.

## Batching notes

With 150+ tickers in a full 3pm session, avoid one-request-per-metric-per-ticker:
- **`/stable/quote?symbol=AAPL,MSFT,NVDA` does NOT batch** — verified live, comma-separated symbols on `/stable/quote` silently return `[]` (200 OK, empty body, no error). Use **`/stable/batch-quote?symbols=AAPL,MSFT,NVDA`** instead (plural `symbols` param, different endpoint name) — verified live, returns all requested quotes in one call.
- Fundamentals endpoints (`financial-growth`, `ratios`, `cash-flow-statement`, `key-metrics`) take one `symbol` at a time on this plan — no bulk variant found, budget one call per ticker per statement.
- Cache the benchmark (`SPY`/`QQQ`) historical pull once per session rather than re-fetching it for every ticker's relative-strength calc.
- If FMP rate-limits partway through a run on a lower-tier plan, keep whatever you got, note in Data Notes which tickers were skipped, and don't burn the rest of the session retrying — a briefing with a few gaps beats one that never finishes.
