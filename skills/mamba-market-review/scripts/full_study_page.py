"""Rebuild the dashboard from the currently published page plus today's snapshot (2pm full study).
Usage: python3 full_study_page.py PUBLISHED.html SNAPSHOT.json PRIOR.json ANALYZER_DATA.json OUT.html CTX.json
CTX.json: {"today_label": "Wed Oct 28, 2026", "long_label": "Wednesday, October 28, 2026", "short": "Oct 28", "prior_short": "Oct 27",
           "analyzer_url": ..., "charts": ["VRT", ...]}
Keeps the page's styles, scripts, nav, futures note, TRAP section, sector table block; swaps every data-driven section.
Prose lives in full_study_prose.py (written per session from the facts)."""
import html as H, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import full_study_prose as PR
src, snapf, priorf, anaf, out, ctxf = sys.argv[1:7]
h = open(src).read(); S = json.load(open(snapf)); P = json.load(open(priorf)); A = json.load(open(anaf)); C = json.load(open(ctxf))
T = {t['symbol']: t for t in S['tickers']}; PT = {t['symbol']: t for t in P['tickers']}
F = {f['symbol']: f for f in S['futures']}; PF = {f['symbol']: f for f in P['futures']}
esc = lambda s: H.escape(s or '', quote=False)
LISTS = {'dow30': 'Dow 30', 'nasdaq100': 'Nasdaq 100', 'sp500_top100': 'S&P 500 Top 100', 'large_cap_proxy': 'Large-Cap Proxy', 'software_cloud': 'Software/Cloud', 'megacap_leaders': 'Mega-Cap Leaders', 'semiconductor_ai': 'Semiconductor/AI'}
POINTS = {'ES', 'NQ', 'YM', 'RTY', 'ZB', 'ZN', 'ZF', 'ZT', 'DX'}
DEC3 = {'ZB', 'ZN', 'ZF', 'ZT', 'NG', 'RB', 'HO', 'HG'}
def sg(x): return '0.00%' if round(x, 2) == 0 else f'{x:+.2f}%'
def cls(x): return 'up' if round(x, 2) > 0 else 'down' if round(x, 2) < 0 else 'flat'
def fpx(sym, v):
    s = f'{v:,.{3 if sym in DEC3 else 2}f}'
    return s + ' pts' if sym in POINTS else s if sym == 'VIX' else '$' + s
def sec(h, start, end_tag='</section>', after=0):
    i = h.index(start, after); j = h.index(end_tag, i) + len(end_tag); return i, j
def put(h, start, new, end_tag='</section>'):
    i, j = sec(h, start, end_tag); return h[:i] + new + h[j:]

# ---------- futures cards ----------
NAMES = {'ES': 'E-Mini S&amp;P 500', 'NQ': 'Nasdaq 100', 'YM': 'Mini Dow', 'RTY': 'Micro Russell 2000', 'ZB': '30Y T-Bond', 'ZN': '10Y T-Note', 'ZF': '5Y T-Note', 'ZT': '2Y T-Note', 'CL': 'WTI Crude', 'BZ': 'Brent Crude', 'NG': 'Natural Gas', 'RB': 'RBOB Gasoline', 'HO': 'Heating Oil', 'GC': 'Gold', 'SI': 'Silver', 'HG': 'Copper', 'PL': 'Platinum', 'PA': 'Palladium', 'ZM': 'Soybean Meal', 'CC': 'Cocoa', 'DX': 'US Dollar Index', 'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'VIX': 'CBOE Volatility Index'}
def trend_txt(f):
    return {'green': 'above 50d and 200d', 'red': 'below 50d and 200d', 'neutral': 'mixed vs 50d/200d'}[f['trend_flag']]
cards = ''.join(f'<div class="fcard"><span class="src-tag">FMP</span><div class="sym">{s} ({NAMES[s]})</div><div class="px mono">{fpx(s, F[s]["last"])}</div><div class="chg {cls(F[s]["chg_pct"])} mono">{sg(F[s]["chg_pct"])}</div><div class="sym" style="margin-top:4px;font-size:10px">{trend_txt(F[s])}</div></div>' for s in NAMES)
i = h.index('<div class="futures-row">'); j = h.index('</section>', i)
h = h[:i] + f'<div class="futures-row">{cards}</div>' + h[j:]
h = re.sub(r'(<h2>Futures Tape</h2><span class="section-note">)[^<]*(</span>)', lambda m: m.group(1) + f'2:00pm MT, {C["long_label"]} (close). FMP futures quotes; daily % vs prior settle.' + m.group(2), h, count=1)

# ---------- edition bar ----------
h = re.sub(r'<div class="edition-bar"><span>.*?</span>', lambda m: f'<div class="edition-bar"><span>2pm MT full study session, {C["today_label"]} (market close) &mdash; all futures, Bitcoin, Dow 30, live Nasdaq 100, live S&amp;P 500 Top 100, the large-cap proxy and the three sector baskets, {len(T)} unique names. Compared against the {C["prior_short"]} full study.</span>', h, count=1, flags=re.S)

# ---------- lead (keep the nav block) ----------
i, j = sec(h, '<section id="lead" class="lead-section">')
lead = h[i:j]; nav = re.search(r'<nav class="page-nav".*?</nav>', lead, re.S).group(0)
head = lead[:lead.index('<p class="intro">')]
h = h[:i] + head + PR.lead(S, P, T, PT) + nav + '</section>' + h[j:]

# ---------- at a glance ----------
chg = [t['chg_pct'] for t in T.values()]; adv = sum(c > 0 for c in chg); dec = sum(c < 0 for c in chg); n = len(T)
avg = round(sum(chg) / n, 2); r4 = sum(t['red_flag_count'] >= 4 for t in T.values()); z0 = sum(t['red_flag_count'] == 0 for t in T.values())
h = put(h, '<section><div class="section-head"><div class="section-top-row"><span class="kicker-label">By the Numbers</span>', f'<section><div class="section-head"><div class="section-top-row"><span class="kicker-label">By the Numbers</span></div><h2 style="margin-top:2px">At a Glance</h2></div><div class="stats"><div class="stat"><div class="n mono">{n}</div><div class="l">Unique names scanned</div></div><div class="stat good"><div class="n mono">{z0}</div><div class="l">Zero red flags</div></div><div class="stat warn"><div class="n mono">{r4}</div><div class="l">4+ red flags</div></div><div class="stat accent"><div class="n mono">{sg(avg)}</div><div class="l">Average move, full universe</div></div></div></section>')

# ---------- macro backdrop ----------
h = put(h, '<section><div class="section-head"><div class="section-top-row"><span class="kicker-label">Setup</span>', PR.macro(S, P, F, C))

# ---------- bitcoin ----------
h = put(h, '<section id="bitcoin">', PR.bitcoin(S, F, C))

# ---------- spotlight (keep the generated sector table block) ----------
i, j = sec(h, '<section id="spotlight">'); old = h[i:j]
sb = re.search(r'<div class="spotlight" id="sector-table".*?</table></div>(?:<p class="sector-note"[^>]*>.*?</p>)?</div>', old, re.S).group(0)
h = h[:i] + PR.spotlight(S, P, T, PT) + sb + '</section>' + h[j:]

# ---------- movers ----------
srt = sorted(T.values(), key=lambda t: (-t['chg_pct'], t['symbol']))
def mrow(t): return f'<tr><td><span class="tk">{esc(t["symbol"])}</span></td><td class="uname">{esc(t["name"])}</td><td class="px-cell">${t["price"]:,.2f}</td><td class="px-cell {cls(t["chg_pct"])} mono">{sg(t["chg_pct"])}</td></tr>'
mt = lambda ts: '<div class="table-wrap"><table><thead><tr><th>Ticker</th><th>Company</th><th>Price</th><th>Chg</th></tr></thead><tbody>' + ''.join(mrow(t) for t in ts) + '</tbody></table></div>'
losers = sorted(T.values(), key=lambda t: (t['chg_pct'], t['symbol']))[:10]
movers = f'<section id="movers"><div class="section-head"><span class="kicker-label">Sentiment</span><h2 style="margin-top:2px">Market Movers &amp; Sentiment</h2></div><div class="stats"><div class="stat good"><div class="n mono">{adv}</div><div class="l">Advancing ({adv / n * 100:.1f}%)</div></div><div class="stat warn"><div class="n mono">{dec}</div><div class="l">Declining ({dec / n * 100:.1f}%)</div></div><div class="stat"><div class="n mono">{n - adv - dec}</div><div class="l">Unchanged</div></div><div class="stat accent"><div class="n mono">{sg(avg)}</div><div class="l">Average move, full universe</div></div></div>{PR.movers_read(S, P, T, PT)}<div class="rollup-grid movers-grid"><div class="rcard"><h3 class="gain">Top Gainers</h3>{mt(srt[:10])}</div><div class="rcard"><h3 class="loss">Top Losers</h3>{mt(losers)}</div></div></section>'
h = put(h, '<section id="movers">', movers)

# ---------- flagged (pre-split "Why" cells; install_flag_split.py turns them into columns) ----------
ITEM = {'trend': 'Trend', 'relative_strength': 'Relative Strength', 'revenue_growth': 'Revenue Growth', 'margin_trend': 'Margin Trend', 'earnings_growth': 'Earnings Growth', 'free_cash_flow': 'Free Cash Flow', 'debt': 'Debt', 'valuation': 'Valuation', 'institutional_ownership': 'Institutional Ownership', 'moat': 'Moat'}
def lists_txt(t): return ', '.join(LISTS[l] for l in t['lists'])
rows = []
for t in sorted([t for t in T.values() if t['red_flag_count'] >= 4], key=lambda t: (-t['red_flag_count'], t['symbol'])):
    d = t['detail']; red = [ITEM[k] for k, v in t['flags'].items() if v == 'red']; grn = [ITEM[k] for k, v in t['flags'].items() if v == 'green']
    mv = d.get('moat_verdict'); moat = f'Moat ({mv}): {esc(d.get("moat_summary"))}' if mv and d.get('moat_summary') else ''
    why = f'Red on: {", ".join(red)}. Green on: {", ".join(grn) if grn else ""}.' + (' ' + moat if moat else '')
    ds = H.escape(f'{t["symbol"].lower()} {t["name"].lower()} {lists_txt(t).lower()}', quote=True)
    rows.append(f'<tr data-search="{ds}" data-lists="{" ".join(t["lists"])}" data-red="{t["red_flag_count"]}"><td><span class="tk">{esc(t["symbol"])}</span><span class="tk-lists">{esc(lists_txt(t))}</span></td><td class="uname">{esc(t["name"])}</td><td class="redcount">{t["red_flag_count"]}</td><td class="px-cell {cls(t["chg_pct"])}">${t["price"]:,.2f} &middot; {sg(t["chg_pct"])}</td><td class="note-cell">{why}</td></tr>')
i = h.index('<section id="flagged">'); j = h.index('</section>', i) + 10
fl = h[i:j]
fl = re.sub(r'(<span class="section-note">)[^<]*(</span>)', lambda m: m.group(1) + f'{r4} of {n} names with 4+ of 10 checklist items red &mdash; filter by list or severity.' + m.group(2), fl, count=1)
fl = re.sub(r'<span class="dir-count" id="flagCount">[^<]*</span>', f'<span class="dir-count" id="flagCount">{r4} shown</span>', fl)
k = fl.index('<thead>'); e = fl.index('</thead>') + 8
fl = fl[:k] + '<thead><tr><th>Ticker</th><th>Company</th><th>Red</th><th>Price / Chg</th><th>Why</th></tr></thead>' + '<tbody id="flagBody">\n' + '\n'.join(rows) + '\n</tbody></table></div></section>'
h = h[:i] + fl + h[j:]

# ---------- universe directory ----------
FL8 = [('trend', 'Trend', 'T'), ('relative_strength', 'Relative Strength', 'RS'), ('revenue_growth', 'Revenue Growth', 'Rv'), ('margin_trend', 'Margin Trend', 'Mg'), ('earnings_growth', 'Earnings Growth', 'EP'), ('free_cash_flow', 'Free Cash Flow', 'FC'), ('debt', 'Debt', 'Db'), ('valuation', 'Valuation', 'Vl')]
FC = {'green': 'fg', 'red': 'fr', 'neutral': 'fn'}
drows = []
for t in sorted(T.values(), key=lambda t: t['symbol']):
    d = t['detail']; s = t['symbol']; rc = t['red_flag_count']
    dots = ''.join(f'<span class="fdot {FC.get(t["flags"][k], "fx")}" title="{nm}">{ab}</span>' for k, nm, ab in FL8)
    ytd = d.get('ytd_pct'); ytdc = f'<td class="px-cell {cls(ytd)} mono">{sg(ytd)}</td>' if ytd is not None else '<td class="px-cell mono" title="Recently listed: not enough history">n/a</td>'
    ds = H.escape(f'{s.lower()} {t["name"].lower()} {lists_txt(t).lower()}', quote=True)
    drows.append(f'<tr class="drow" data-sym="{esc(s)}" data-search="{ds}" data-lists="{" ".join(t["lists"])}" data-red="{rc}" data-chg="{t["chg_pct"]}" data-price="{t["price"]}" data-name="{H.escape(t["name"].lower(), quote=True)}" data-exchange="{d.get("exchange")}" data-ytd="{"" if ytd is None else ytd}"><td class="watch-cell"><input type="checkbox" class="watchbox" data-sym="{esc(s)}" aria-label="Watch {esc(s)}"></td><td><button class="expbtn" data-sym="{esc(s)}" aria-label="Expand">&#9656;</button><span class="tk">{esc(s)}</span><a class="tv-link" href="https://www.tradingview.com/symbols/{d.get("exchange")}-{esc(s)}/" target="_blank" rel="noopener" title="View {esc(s)} on TradingView">&#8599;</a></td><td class="uname">{esc(t["name"])}</td><td class="ulists">{esc(lists_txt(t))}</td><td class="flagsrow">{dots}</td><td class="px-cell">${t["price"]:,.2f}</td><td class="px-cell {cls(t["chg_pct"])}">{sg(t["chg_pct"])}</td>{ytdc}<td class="redcount {"ud-zero" if rc <= 1 else "ud-mid" if rc <= 3 else "ud-high"}">{rc}</td></tr>')
i = h.index('<tbody id="dirBody">') + len('<tbody id="dirBody">'); j = h.index('</tbody>', i)
h = h[:i] + '\n' + '\n'.join(drows) + '\n' + h[j:]
h = re.sub(r'All \d+ names scanned this session', f'All {n} names scanned this session', h, count=1)
h = re.sub(r'<span class="dir-count" id="dirCount">[^<]*</span>', f'<span class="dir-count" id="dirCount">{n} shown</span>', h)
isl = {s: {k: v for k, v in a.items() if k != 'annual'} for s, a in A.items()}
i = h.index('<script id="directory-detail-data" type="application/json">'); i = h.index('>', i) + 1; j = h.index('</script>', i)
h = h[:i] + json.dumps(isl, separators=(',', ':')).replace('</', '<\\/') + h[j:]

# ---------- roll-up, comparison, study, news, findings, footer ----------
h = put(h, '<section id="rollup">', PR.rollup(S, P, T, PT, C))
h = put(h, '<section id="vs-previous">', PR.vs_previous(S, P, T, PT, F, PF, C))
h = put(h, '<section class="study" id="whats-next">', PR.whats_next(S, P, T, PT))
charts = ''
for sym in C['charts']:
    t = T[sym]; cl = C['closes'][sym]; a, b = cl[0], t['price']
    lo, hi = min(cl + [b]), max(cl + [b]); pts = cl[:-1] + [b]
    xs = [2 + 236 * k / (len(pts) - 1) for k in range(len(pts))]; ys = [60 - 56 * (v - lo) / (hi - lo or 1) for v in pts]
    pct = round((round(b, 2) / round(a, 2) - 1) * 100, 2); col = 'var(--green)' if pct >= 0 else 'var(--red)'
    poly = ' '.join(f'{x:.1f},{y:.1f}' for x, y in zip(xs, ys))
    charts += f'<div class="rcard"><h3 style="color:var(--ink)">{esc(sym)} &middot; {esc(t["name"])}</h3><svg viewBox="0 0 240 64" width="100%" role="img" aria-label="{sym} {len(pts)}-session closing prices, {sg(pct)} over the window"><polyline fill="none" stroke="{col}" stroke-width="1.8" points="{poly}"/></svg><div class="sym mono" style="font-size:11px;color:var(--ink-faint)">{len(pts)} sessions: ${a:,.2f} &rarr; ${b:,.2f} ({sg(pct)})</div></div>'
news = PR.news(S, P, T, PT, C)
h = put(h, '<section id="news">', news + f'<div class="section-head" style="margin-top:22px"><h3 class="sans" style="font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-faint)">90-session closes, drawn from FMP daily history</h3></div><div class="rollup-grid">{charts}</div></section>')
h = put(h, '<section id="findings">', PR.findings(S, P, T, PT, C))
h = re.sub(r'(<footer><span>Generated by the .*?Full Study, 2:00pm MT, )[^<]*(</span><span>Snapshot: <code[^>]*>)[^<]*(</code>)', lambda m: m.group(1) + C['today_label'] + m.group(2) + f'reports/{S["date"]}/full-study.json' + m.group(3), h, count=1, flags=re.S)
open(out, 'w').write(h)
print('wrote', out, len(h))
