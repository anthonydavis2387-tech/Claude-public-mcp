# Number style and the accuracy check (every page, every run)

The user reads these pages the way a subscriber reads a serious financial paper, and listens to them with the Listen
player. A number that is unsigned, missing its "$", or different from the data is a correction, not a nit. On
2026-10-14 the user found "KKR & Co. (KKR) 4.72%" in the lead paragraph (the stock fell 4.72%) and prices read aloud
without "dollars". This file is the house style that prevents both, and `scripts/fact_check.py` enforces it.

## House style

| What | Write | Never |
|---|---|---|
| A day's move after a ticker | `KKR & Co. (KKR) -4.72%` | `(KKR) 4.72%`, `(KKR) fell 4.72%`, `(KKR) lost 4.72%` |
| A move without a ticker | `silver (SI) -1.68%`, or give the ticker | `silver fell 1.68%` |
| Price and move together | `WTI crude (CL) $94.77 (+1.10%)` | `WTI rose 1.10% to $94.77` |
| Flat | `0.00%` | `+0.00%`, `-0.00%` |
| Decimals for moves | 2 (`+1.16%`), on every page, daily or weekly | mixing `+1.2%` and `+1.16%` |
| Minus sign | plain hyphen-minus `-` | the Unicode `−` or `&minus;` |
| Stock, ETF, crypto, commodity prices | `$87.19`, `$83,216.86`, `$4,187.40`, always 2 decimals | `87.19`, `$83,217` |
| EPS, dividends, estimates | `$2.34`, `EPS est $2.65` | `EPS 2.34` |
| Points, never dollars | contracts quoted in points (ES, NQ, YM, RTY, ZB, ZN, ZF, ZT, DX) carry ` pts`: `ES 7,793.50 pts`, `DX 101.78 pts` (read aloud as "points"); the VIX and cash index levels are plain: `VIX 15.25`, `S&P 500 7,811.51` | `$7,854.75`, a bare `7,793.50` for ES/NQ/DX |
| Sector names | the 11 standard GICS names only (below) | FMP's `Consumer Cyclical`, `Consumer Defensive`, `Financial Services`, `Healthcare`, `Technology`, `Basic Materials` |
| Levels and distances | yields `5.21%`, shares `73.2%`, `15.5% above the 200-day` | a sign on a level |
| Red-flag changes | `Citigroup (C) (2 → 5)` or `went from 2 to 5` | |

Why signs instead of verbs: the page and the audio must agree, and the player turns `-4.72%` into "down 4.72
percent". A verb in front of an unsigned number, or a list that carries the verb from its first item ("Citigroup lost
5.60%, KKR 4.72%"), loses the direction for every item after the first. A verb in front of a signed number reads
twice ("fell minus 4.72"), so use the sign alone.

Prices are spoken as "87 dollars and 19 cents" by the player only when the page shows the `$`, which is why the `$`
is never optional on a price and never added to points.

## Sectors: the 11 GICS names, measured by the official sector funds

On 2026-10-15 the user found "Consumer Cyclical" on the dashboard, no "Consumer Staples" (which the prose had cited),
and fewer than 11 sectors. The cause: prose described the *average of our scanned names* in a sector, under FMP's own
labels, as if it were the sector's performance. Rules since then:

- Only these names, in this spelling: Information Technology, Financials, Health Care, Consumer Discretionary,
  Communication Services, Industrials, Consumer Staples, Energy, Utilities, Real Estate, Materials.
  `scripts/sectors.py` holds them and `gics()` maps FMP labels; every script that saves or shows a sector uses it.
- A sector's move is its Select Sector SPDR fund (XLK, XLF, XLV, XLY, XLC, XLI, XLP, XLE, XLU, XLRE, XLB). Write it
  with the fund: `Health Care (XLV) +1.86%`. "N of 11 sectors rose" counts the funds.
- The average of our names in a sector is a different number. Say so every time: `our 33 Health Care names averaged
  +1.40%`. Never present it as the sector's move.
- The dashboard's sector table is generated, never hand-written, on every 2pm run:
  `python3 scripts/sector_table.py reports/{date}/full-study.json page.html out.html`. It saves the fund closes in
  the snapshot (`sector_funds`), writes all 11 sectors with fund close and day move beside our names' average, red
  flags and 4+ count, and prints the one-line summary to reuse in the prose so text and table agree.
- `fact_check.py` blocks FMP labels, a sector table with fewer than 11 rows, a fund move or "N of 11" that does not
  match `sector_funds`, and an "our N names" average that does not match the snapshot.

## Where the numbers come from

Every figure on the dashboard and Analyzer comes from this session's snapshot (`reports/{date}/full-study.json`):
the ticker's `price` and `chg_pct`, the `futures` block, `bitcoin`, `macro`, and `etf_proxies` (SPY/QQQ/DIA/IWM).
Copy them; never retype them from memory or from an earlier draft. Sector averages, breadth, red-flag counts and
day-over-day flag changes are computed from the snapshot (and the prior snapshot), not estimated. Prices are the 2pm MT
quotes taken at the close; the official closing print can differ by a few cents, and that is expected.

## The check: run it before every publish

```
python3 skills/mamba-market-review/scripts/fact_check.py page.html \
    --snapshot skills/mamba-market-review/reports/{date}/full-study.json \
    --prior skills/mamba-market-review/reports/{prior date}/full-study.json
```
for the dashboard and the 10-Point Analyzer (the 8am run uses the snapshot the page is built from), and
```
python3 skills/mamba-market-review/scripts/fact_check.py page.html --style-only
```
for World Watch, the ETF Explorer and Stop the Cap, whose numbers come from their own scripts.

It checks: every signed move after a ticker against the data; unsigned moves and verb-style moves; "$" on prices
and no "$" on points; futures cards (price, sign, color); the movers and flagged tables; the stat tiles (names
scanned, zero-flag and 4+ counts, advancers, decliners, average move); the sector table and sector averages in prose;
Treasury yields; Bitcoin; the 90-session chart captions; red-flag changes against the prior day; and every row of the
`directory-detail-data` and `analyzer-data` islands. Exit code 1 means errors: fix the page and run it again. Do not
publish until it prints `0 error(s)`. If it flags something that is correct (a new phrasing it does not know), fix the
checker in the same commit rather than publishing past it.

Pages that render their numbers in the browser (Analyzer detail panel, ETF Explorer, Stop the Cap) get their format
from their templates, which already follow this style. When a template changes, render the page in Chromium (Playwright),
take `document.body.innerText`, wrap it as `<p>` lines and run the `--style-only` check on that too.
