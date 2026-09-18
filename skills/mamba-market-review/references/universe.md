# Ticker Universe

Starting-point lists for the daily review. **Treat everything here except the Dow 30 and futures list as a snapshot that goes stale** — index membership and sector-leader lists change. Where noted, prefer fetching the live list from FMP over trusting the hardcoded names below.

## Futures (40 symbols)

Equity index (5): `ES` `NQ` `YM` `RTY` `VX`
Rates (5): `ZB` `ZN` `ZF` `ZT` `SR3`
Energy (5): `CL` `BZ` `NG` `RB` `HO`
Metals (5): `GC` `SI` `HG` `PL` `PA`
Ags (10): `ZC` `ZS` `ZW` `ZM` `ZL` `KC` `SB` `CC` `CT` `LE`
Currencies (8): `6E` `6J` `6B` `6A` `6C` `6S` `6N` `DX`
Crypto (2): `BTC` `ETH`

This list is stable in composition (the contracts themselves don't change) but symbols/roots can vary slightly by data provider — confirm the exact FMP or broker symbol format for futures before the first real run (e.g. some providers want a continuous-contract suffix like `ESUSD` or `CLUSD`).

**Plan gap, confirmed live:** on the current FMP key, `/stable/quote?symbol={ROOT}USD` only works for a handful of these — `ESUSD` (E-mini S&P), `GCUSD` (gold), `SIUSD` (silver), `BTCUSD`, `ETHUSD` returned data. Every other root tried (`NQUSD`, `YMUSD`, `RTYUSD`, `CLUSD`, `DXUSD`, `ZBUSD`, `ZNUSD`) returned HTTP 402 "Special Endpoint... not available under your current subscription" — the futures/commodities tape beyond a few index/metal/crypto contracts appears to sit behind a higher FMP tier than what the checklist's endpoints need. Until that's confirmed/upgraded, expect most of the 40-symbol futures list to need the WebSearch fallback rather than FMP, and say so in Data Notes rather than silently omitting those rows.

## Dow 30

`AAPL` `AMGN` `AMZN` `AXP` `BA` `CAT` `CRM` `CSCO` `CVX` `DIS` `GS` `HD` `HON` `IBM` `JNJ` `JPM` `KO` `MCD` `MMM` `MRK` `MSFT` `NKE` `NVDA` `PG` `SHW` `TRV` `UNH` `V` `VZ` `WMT`

Membership changes rarely (roughly once a year via S&P Dow Jones Indices committee action). Still worth a periodic sanity check, but safe to treat as close to authoritative.

## Nasdaq 100 — verify before relying on this

Reconstitutes annually every December, with occasional mid-year swaps for M&A/delisting. **Don't trust a hand-maintained list of exactly 100 names for real screening** — instead, when `FMP_API_KEY` is available, pull the live list from FMP's Nasdaq constituents endpoint (`/stable/nasdaq-constituent` or the equivalent `/api/v3/nasdaq_constituent` on older plan tiers) at the start of the run and use that.

The names below are a high-confidence offline fallback (large, well-established members unlikely to have rotated out) for when no API key is configured — it is **not a complete or exact current membership list**, and skips the smaller/newer names near the bottom of the index that turn over most often:

`AAPL` `MSFT` `GOOGL` `GOOG` `AMZN` `META` `NVDA` `TSLA` `AVGO` `COST` `NFLX` `AMD` `PEP` `ADBE` `CSCO` `TMUS` `CMCSA` `INTU` `TXN` `QCOM` `AMGN` `AMAT` `BKNG` `HON` `ADP` `GILD` `MDLZ` `ADI` `VRTX` `REGN` `PANW` `SNPS` `CDNS` `MELI` `KLAC` `LRCX` `MAR` `CTAS` `ORLY` `PYPL` `MNST` `FTNT` `ABNB` `CRWD` `DXCM` `PCAR` `ROP` `NXPI` `PAYX` `ODFL` `KDP` `AEP` `EXC` `XEL` `CSX` `CHTR` `MRVL` `WDAY` `TTD` `EA` `VRSK` `FAST` `CPRT` `IDXX` `ANSS` `DDOG` `TEAM` `ZS` `MCHP` `ON` `GEHC` `ILMN` `WBD` `BIIB` `EBAY` `LULU` `DASH` `MDB` `CDW` `ROST` `KHC` `TTWO` `CSGP` `BKR` `CTSH` `ALGN` `SIRI`

## Russell Top 100 — approximate by market cap, fetch live when possible

There's no clean, widely available "Russell Top 100" list to hardcode — FTSE Russell's own published index is the "Russell Top 200," and full Russell 1000/3000 constituent + weight data is typically behind a paid data license that FMP's standard tiers don't include. Treat "Russell Top 100" here as **the ~100 largest US-listed companies by market cap**, which is a reasonable proxy for what the routine actually wants (the biggest, most liquid names outside the mega-cap names already covered by Dow 30 / Nasdaq 100).

Preferred approach: use FMP's stock screener endpoint (`/stable/company-screener` or `/api/v3/stock-screener`), filtered to NYSE + NASDAQ, sorted by `marketCap` descending, limit 100. Cross-reference against Dow 30 and Nasdaq 100 from above and drop duplicates (Step 2 in SKILL.md) so you're not re-checking the same mega-caps three times — the point of this list is the large names *outside* those two, e.g. Berkshire Hathaway, JPMorgan peers, big banks/insurers/energy/healthcare names that aren't Dow or Nasdaq components.

No offline fallback list is included here deliberately — a hand-written "top 100 by market cap" list would be wrong within months and give false confidence. If no API access is available for this section, say so in the briefing's Data Notes and skip it rather than presenting a guessed list as current.

## Sector Watchlists (20 each) — starting points, edit freely

These are meant to be personalized. Edit this file directly to match what the user actually wants to track; the defaults below are just a reasonable seed.

**Software / Cloud (20):**
`MSFT` `CRM` `ADBE` `NOW` `INTU` `ORCL` `SAP` `WDAY` `TEAM` `SNOW` `DDOG` `CRWD` `PANW` `FTNT` `ZS` `NET` `MDB` `HUBS` `DOCU` `PLTR`

**Mega-Cap Leaders (20):**
`AAPL` `MSFT` `GOOGL` `AMZN` `NVDA` `META` `TSLA` `BRK.B` `AVGO` `JPM` `V` `WMT` `UNH` `XOM` `MA` `PG` `JNJ` `HD` `COST` `LLY`

**Semiconductor / AI (20):**
`NVDA` `AVGO` `AMD` `TSM` `QCOM` `TXN` `INTC` `AMAT` `LRCX` `KLAC` `MU` `ADI` `MRVL` `NXPI` `MCHP` `ON` `SWKS` `MPWR` `ARM` `ASML`

## Dedup note

Cross-list overlap is expected and fine (e.g. `NVDA` sits in Dow 30, Nasdaq 100, Mega-Cap Leaders, and Semiconductor/AI). Per SKILL.md Step 2, run the 10-point checklist on each ticker once, and list every basket it belongs to when presenting results rather than repeating the full row four times.
