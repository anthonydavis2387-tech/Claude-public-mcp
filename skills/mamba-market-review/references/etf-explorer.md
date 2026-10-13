# ETF Explorer

A companion page for researching 100 ETFs: what each fund is for, its stats and returns, its sector mix, and its full
holdings. Holdings that are dashboard names link to the 10-Point Analyzer. The page also answers "which ETFs hold this
stock?"

- Fund list: `etf/etf_list.json`. Each entry has `s`, `cat`, `core` and `why`; `core` marks the Core 50. The user chose
  all 100. Change the list only when the user asks.
- Holdings: `scripts/etf_holdings.py` writes `etf/holdings/{SYM}.json` and the reverse map `etf/holdings-index.json`.
  - The source is each fund's latest SEC N-PORT filing. That's free, but it's quarterly and published about 60 days
    after the quarter ends. Refresh holdings weekly; the SEC data changes about once a month at most.
  - It needs network access to `www.sec.gov`, `data.sec.gov` and `efts.sec.gov`.
  - The SEC requires a contact email in the User-Agent. The user approved theirs, and it is set in the script. Keep
    requests at 10 per second or fewer. A request without a contact gets the whole IP blocked for a while.
  - Special cases:
    - SPY uses IVV's holdings and MDY uses IJH's (same index; SPY and MDY are unit trusts that don't file N-PORT).
    - DIA's weights are computed from the Dow 30 share prices.
    - Commodity and crypto trusts (GLD, SLV, IBIT, ETHA, USO, UNG, CPER, DBC, DBA, UUP) are `direct`: they hold the
      asset itself, so there's no holdings list.
    - Funds too new for the SEC's ticker file are found by full-text search on their name (`NAME_FIX` corrects names
      that FMP truncates).
  - Tickers are matched by CUSIP (from FMP profiles, cached in `etf/cusips.json`), then by normalized name against the
    dashboard universe, then against the SEC's company list.
- Page: `scripts/etf_explorer.py out.html` pulls fresh fund stats and returns from FMP, computes "most similar"
  funds from holdings overlap, and renders `scripts/etf_explorer_template.html`. Publish the page to the URL in
  `reports/.etf-url.txt` (read the artifact first, as always).

## Refresh

1. `python3 skills/mamba-market-review/scripts/etf_holdings.py` (all funds; pass symbols to refresh only some).
2. `python3 skills/mamba-market-review/scripts/etf_explorer.py /tmp/etf-explorer.html`, then publish that file to the
   `.etf-url.txt` URL.
3. Commit `etf/`, then push.
