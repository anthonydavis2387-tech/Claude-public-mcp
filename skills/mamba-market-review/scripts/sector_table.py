"""Build the dashboard's sector table: all 11 GICS sectors, measured by their official S&P 500 sector funds.

Usage: python3 sector_table.py SNAPSHOT.json page.html out.html
  1. For the snapshot's date, gets each Select Sector SPDR fund's close and the prior close from FMP daily closes
     (falls back to the live quote during the session) and saves them in the snapshot as `sector_funds`.
  2. Writes the table into the page (replacing the earlier copy, or the old hand-written "Average move and red-flag
     load by sector" table): sector (standard GICS name, linked to the Analyzer's sector view), its fund, the fund's
     close and day move (the official sector performance), then the dashboard names in that sector, their average
     move, average red flags and how many carry 4+.
  Prints the one-line summary ("8 of 11 sectors rose ...") to use in prose, so the text and the table agree.
"""
import html, json, os, re, sys, urllib.parse, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sectors import SECTOR_FUNDS, gics

BLOCK = re.compile(r'<div class="spotlight" id="sector-table".*?</table></div>(?:<p class="sector-note">.*?</p>)?</div>', re.S)
OLD = re.compile(r'<div class="spotlight" style="border-top:1px solid var\(--line\)"><h3>Average move and red-flag load by sector</h3>.*?</table></div></div>', re.S)


def fmp(path, **kw):
    kw['apikey'] = os.environ['FMP_API_KEY']
    with urllib.request.urlopen('https://financialmodelingprep.com/stable/' + path + '?' + urllib.parse.urlencode(kw, safe=','), timeout=60) as r:
        return json.loads(r.read())


def fund_moves(day):
    out = {}
    quotes = None
    for sector, f in SECTOR_FUNDS:
        h = fmp('historical-price-eod/light', symbol=f, to=day) or []
        h = sorted((x['date'], x['price']) for x in h if x.get('price'))
        if h and h[-1][0] == day and len(h) > 1:
            close, prev, src = h[-1][1], h[-2][1], 'FMP daily close'
        else:   # the day's close is not posted yet: use the live quote
            if quotes is None:
                quotes = {q['symbol']: q for q in fmp('batch-quote', symbols=','.join(x for _, x in SECTOR_FUNDS))}
            q = quotes[f]
            close, prev, src = q['price'], q['previousClose'], 'FMP quote'
        out[sector] = {'fund': f, 'close': round(close, 2), 'prev_close': round(prev, 2),
                       'chg_pct': round((close / prev - 1) * 100, 2), 'source': src}
    return out


def build(snap, analyzer_url):
    funds = snap['sector_funds']
    by = defaultdict(list)
    for t in snap['tickers']:
        sec = gics((t.get('detail') or {}).get('sector') or t.get('sector'))
        if sec and t.get('chg_pct') is not None:
            by[sec].append(t)
    rows = []
    for sector, _ in sorted(SECTOR_FUNDS, key=lambda x: -funds[x[0]]['chg_pct']):
        f, names = funds[sector], by.get(sector, [])
        avg = round(sum(t['chg_pct'] for t in names) / len(names), 2) if names else None
        red = round(sum(t.get('red_flag_count') or 0 for t in names) / len(names), 1) if names else None
        red4 = sum(1 for t in names if (t.get('red_flag_count') or 0) >= 4)
        sg = lambda v: '&mdash;' if v is None else ('0.00%' if round(v, 2) == 0 else f"{'+' if v > 0 else '-'}{abs(v):.2f}%")
        cl = lambda v: '' if v is None or round(v, 2) == 0 else (' up' if v > 0 else ' down')
        link = f'{analyzer_url}#sector-{sector.replace(" ", "-")}' if analyzer_url else '#'
        rows.append(f'<tr><td><a href="{link}">{html.escape(sector)}</a></td><td class="px-cell mono">{f["fund"]}</td>'
                    f'<td class="px-cell mono">${f["close"]:,.2f}</td><td class="px-cell{cl(f["chg_pct"])} mono">{sg(f["chg_pct"])}</td>'
                    f'<td class="px-cell mono">{len(names)}</td><td class="px-cell{cl(avg)} mono">{sg(avg)}</td>'
                    f'<td class="px-cell mono">{"&mdash;" if red is None else red}</td><td class="px-cell mono">{red4}</td></tr>')
    up = [s for s, _ in SECTOR_FUNDS if funds[s]['chg_pct'] > 0]
    best = max(SECTOR_FUNDS, key=lambda x: funds[x[0]]['chg_pct'])
    worst = min(SECTOR_FUNDS, key=lambda x: funds[x[0]]['chg_pct'])
    fmt = lambda s: f"{s[0]} ({s[1]}) {'+' if funds[s[0]]['chg_pct'] > 0 else '-'}{abs(funds[s[0]]['chg_pct']):.2f}%"
    summary = f"{len(up)} of 11 sectors rose, led by {fmt(best)}; the weakest was {fmt(worst)}."
    src = sorted({funds[s]['source'] for s, _ in SECTOR_FUNDS})
    block = ('<div class="spotlight" id="sector-table" style="border-top:1px solid var(--line)"><h3>The 11 S&amp;P 500 sectors today</h3>'
             f'<p>{html.escape(summary)}</p>'
             '<div class="table-wrap"><table style="min-width:0"><thead><tr><th>Sector</th><th>Sector fund</th><th>Fund close</th><th>Day</th>'
             '<th>Dashboard names</th><th>Their avg chg</th><th>Avg red flags</th><th>4+ red</th></tr></thead><tbody>' + ''.join(rows) +
             '</tbody></table></div>'
             f'<p class="sector-note" style="font-size:12.5px;color:var(--ink-faint);margin-top:8px">The official sector move is the S&amp;P 500 '
             f'Select Sector SPDR fund ({", ".join(src)}, {html.escape(snap["date"])}). The last four columns cover only the names in this '
             'dashboard&rsquo;s universe, so their average can differ from the sector&rsquo;s. Sector names follow the standard GICS '
             'classification (FMP&rsquo;s labels are mapped: Consumer Cyclical = Consumer Discretionary, Consumer Defensive = Consumer Staples, '
             'Financial Services = Financials, Healthcare = Health Care, Technology = Information Technology, Basic Materials = Materials).</p></div>')
    return block, summary


def main(snap_path, page_path, out_path):
    snap = json.load(open(snap_path))
    snap['sector_funds'] = fund_moves(snap['date'])
    raw = open(snap_path).read()
    json.dump(snap, open(snap_path, 'w'), indent=1 if raw.startswith('{\n') else None)
    url_p = os.path.join(HERE, '..', 'reports', '.analyzer-url.txt')
    block, summary = build(snap, open(url_p).read().strip() if os.path.exists(url_p) else '')
    s = open(page_path).read()
    if BLOCK.search(s):
        s = BLOCK.sub(lambda _: block, s, count=1)
    elif OLD.search(s):
        s = OLD.sub(lambda _: block, s, count=1)
    else:
        raise SystemExit('no sector table found on the page to replace')
    open(out_path, 'w').write(s)
    print(summary)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
