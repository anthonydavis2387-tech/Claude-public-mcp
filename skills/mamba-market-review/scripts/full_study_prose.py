"""Prose for the 2pm dashboard, written from the snapshot so every number is copied, not retyped.
House style (references/style-and-accuracy.md): signed 2-decimal moves right after each ticker, "$" on prices,
" pts" on ES/NQ/YM/RTY/ZB/ZN/ZF/ZT/DX, GICS sector names with the fund ticker."""
import html as H, re
POINTS = {'ES', 'NQ', 'YM', 'RTY', 'ZB', 'ZN', 'ZF', 'ZT', 'DX'}
DEC3 = {'ZB', 'ZN', 'ZF', 'ZT', 'NG', 'RB', 'HO', 'HG'}
e = lambda s: H.escape(s or '', quote=False)
def sg(x): return '0.00%' if round(x, 2) == 0 else f'{x:+.2f}%'
def short(n):
    n = n.strip()
    for _ in range(4):
        n = re.sub(r'(,? (Inc\.?|Corporation|Corp\.?|Company|Co\.|Ltd\.?|plc|PLC|N\.V\.|Holdings|Holding|Incorporated|Limited|Group|Common Stock|Class [A-C].*|American Depositary.*|Technologies Inc\.?|&|and))$', '', n).strip().rstrip(',')
    return re.sub(r'^The ', '', n)
OV = {'HONA': 'Honeywell Aerospace', 'BRK-B': 'Berkshire Hathaway', 'SPCX': 'Space Exploration Technologies', 'GEHC': 'GE HealthCare', 'CME': 'CME Group', 'TSM': 'Taiwan Semiconductor', 'ODFL': 'Old Dominion Freight Line', 'AJG': 'Arthur J. Gallagher', 'WM': 'Waste Management', 'HOOD': 'Robinhood Markets', 'ITW': 'Illinois Tool Works', 'META': 'Meta Platforms', 'MDT': 'Medtronic', 'LHX': 'L3Harris', 'AMZN': 'Amazon', 'BDX': 'Becton Dickinson', 'MCO': "Moody's", 'GOOG': 'Alphabet (Class C)', 'GOOGL': 'Alphabet (Class A)', 'FTNT': 'Fortinet', 'NOW': 'ServiceNow', 'ADP': 'Automatic Data Processing', 'COF': 'Capital One', 'SNDK': 'SanDisk', 'VRT': 'Vertiv', 'NET': 'Cloudflare', 'TTWO': 'Take-Two Interactive', 'LITE': 'Lumentum', 'BSX': 'Boston Scientific', 'TER': 'Teradyne', 'ON': 'ON Semiconductor', 'WELL': 'Welltower', 'PWR': 'Quanta Services', 'XOM': 'Exxon Mobil', 'MPC': 'Marathon Petroleum', 'DDOG': 'Datadog', 'MRNA': 'Moderna', 'HCA': 'HCA Healthcare', 'NEM': 'Newmont', 'BKNG': 'Booking Holdings', 'MMM': '3M', 'CVNA': 'Carvana', 'LOW': "Lowe's", 'DELL': 'Dell Technologies', 'GEV': 'GE Vernova', 'STX': 'Seagate Technology', 'EOG': 'EOG Resources', 'COP': 'ConocoPhillips', 'MCD': "McDonald's", 'GWW': 'W.W. Grainger', 'MCK': 'McKesson', 'QCOM': 'Qualcomm', 'UBER': 'Uber Technologies', 'APP': 'AppLovin'}
def nm(T, s): return OV.get(s) or short(T[s]['name'])
def mv(T, s): return f'{nm(T, s)} ({s}) {sg(T[s]["chg_pct"])}'
def lst(items): return ', '.join(items)
def fx(F, s):
    f = F[s]; d = 3 if s in DEC3 else 2; v = f'{f["last"]:,.{d}f}'
    return (v + ' pts') if s in POINTS else v if s == 'VIX' else '$' + v
def basket(T, key):
    v = [t for t in T.values() if key in t['lists']]; return v, round(sum(t['chg_pct'] for t in v) / len(v), 2), sum(t['chg_pct'] > 0 for t in v)
def sector_avgs(T):
    d = {}
    for t in T.values():
        d.setdefault(t['detail']['sector'], []).append(t)
    return {k: (len(v), round(sum(x['chg_pct'] for x in v) / len(v), 2), sum(x['red_flag_count'] >= 4 for x in v)) for k, v in d.items()}
def top(T, key, k, rev=True, extra=None):
    v = [t for t in T.values() if key in t['lists'] and (extra is None or extra(t))]
    return sorted(v, key=lambda t: (-t['chg_pct'] if rev else t['chg_pct'], t['symbol']))[:k]
def last_eps(T, s):
    h = ((T[s]['detail'].get('trap') or {}).get('eps_hist') or [{}])[0]
    return h.get('date'), h.get('actual'), h.get('est')
def reported(T, s, days):
    d, a, est = last_eps(T, s)
    return (d, a, est) if d in days and a is not None and est is not None else None
def stats(S, P, T, PT):
    chg = [t['chg_pct'] for t in T.values()]; n = len(T)
    o = dict(n=n, adv=sum(c > 0 for c in chg), dec=sum(c < 0 for c in chg), avg=round(sum(chg) / n, 2), pavg=round(sum(t['chg_pct'] for t in PT.values()) / len(PT), 2),
             r4=sum(t['red_flag_count'] >= 4 for t in T.values()), pr4=sum(t['red_flag_count'] >= 4 for t in PT.values()),
             z=sum(t['red_flag_count'] == 0 for t in T.values()), pz=sum(t['red_flag_count'] == 0 for t in PT.values()))
    o['new4'] = sorted(s for s in T if s in PT and T[s]['red_flag_count'] >= 4 and PT[s]['red_flag_count'] < 4)
    o['off4'] = sorted(s for s in T if s in PT and T[s]['red_flag_count'] < 4 and PT[s]['red_flag_count'] >= 4)
    ch = [(T[s]['red_flag_count'] - PT[s]['red_flag_count'], s) for s in T if s in PT]
    o['inc'] = [(d, s) for d, s in sorted(ch, key=lambda x: (-x[0], x[1])) if d > 0][:8]
    o['dec_'] = [(d, s) for d, s in sorted(ch, key=lambda x: (x[0], x[1])) if d < 0][:8]
    on, off = {}, {}
    for s in T:
        if s in PT:
            for k, v in T[s]['flags'].items():
                a = PT[s]['flags'][k]
                if a != 'red' and v == 'red': on[k] = on.get(k, 0) + 1
                if a == 'red' and v != 'red': off[k] = off.get(k, 0) + 1
    o['on'], o['off'] = on, off
    o['rs'] = sum(t['flags']['relative_strength'] == 'red' for t in T.values()); o['prs'] = sum(t['flags']['relative_strength'] == 'red' for t in PT.values())
    return o
def kv(d): return ', '.join(f'{v} {k.replace("_", " ")}' for k, v in sorted(d.items(), key=lambda x: (-x[1], x[0])))
def bm(S, P):
    a = S['tickers'][0]['detail']; b = P['tickers'][0]['detail']
    sp = next(t['detail']['benchmark_3m_pct'] for t in S['tickers'] if t['detail']['benchmark_used'] == 'SPY'); pq = next(t['detail']['benchmark_3m_pct'] for t in P['tickers'] if t['detail']['benchmark_used'] == 'QQQ')
    return dict(sp=sp, qq=next(t['detail']['benchmark_3m_pct'] for t in S['tickers'] if t['detail']['benchmark_used'] == 'QQQ'),
                psp=next(t['detail']['benchmark_3m_pct'] for t in P['tickers'] if t['detail']['benchmark_used'] == 'SPY'), pqq=pq)
def secfunds(S):
    f = S['sector_funds']; up = sorted([(v['chg_pct'], k, v['fund']) for k, v in f.items() if v['chg_pct'] > 0], reverse=True)
    dn = sorted([(v['chg_pct'], k, v['fund']) for k, v in f.items() if v['chg_pct'] <= 0])
    return up, dn
def etf(S, k): return round(S['etf_proxies'][k]['chg'], 2)


DAYS = ('2026-11-09', '2026-11-10')
def epsr(T, s):
    r = reported(T, s, DAYS); m = lambda v: ('-' if v < 0 else '') + f'${abs(v):.2f}'; return f' (FMP dates its report {r[0][5:].replace("-", "/")}, EPS {m(r[1])} against {m(r[2])} expected)' if r else ''

def pv(T, PT, s): return f'{mv(T, s)} (Monday: {sg(PT[s]["chg_pct"])})'
def pm(PT, s): return f'{nm(PT, s)} ({s}) {sg(PT[s]["chg_pct"])}'
CAUSE = ('We found no dated Nov 10 close coverage explaining the day&rsquo;s moves, so no cause is stated for them.')
def worst(T, k, key=None):
    v = [t for t in T.values() if key is None or key(t)]
    return sorted(v, key=lambda t: (t['chg_pct'], t['symbol']))[:k]
def names_or_none(T, ss): return lst(f'{nm(T, s)} ({s})' for s in ss) or 'none'
def lead(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; st = stats(S, P, T, PT); n = st['n']; B = S['bitcoin']; M = S['macro']; b = bm(S, P)
    up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    sem, semavg, semup = basket(T, 'semiconductor_ai'); sw, swavg, swup = basket(T, 'software_cloud'); mg, mgavg, _ = basket(T, 'megacap_leaders')
    allsec = sorted(up + dn, reverse=True)
    p1 = (f'<p class="intro"><strong>A quiet, split session after Monday&rsquo;s rally: the index funds slipped, tech gave back ground, Treasuries sold off and the dollar firmed.</strong> The S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))}, the Dow fund (DIA) {sg(etf(S, "DIA"))} and the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))}. '
          f'<strong>{st["adv"]} of {n} names advanced ({st["adv"] / n * 100:.1f}%) and {st["dec"]} declined</strong>, and the average move was {sg(st["avg"])}, against {sg(st["pavg"])} on Monday. '
          f'S&amp;P 500 futures (ES) {fx(F, "ES")} ({sg(F["ES"]["chg_pct"])}), Nasdaq 100 futures (NQ) {fx(F, "NQ")} ({sg(F["NQ"]["chg_pct"])}), Mini Dow (YM) {fx(F, "YM")} ({sg(F["YM"]["chg_pct"])}) and Russell 2000 (RTY) {fx(F, "RTY")} ({sg(F["RTY"]["chg_pct"])}). '
          f'<strong>The VIX was {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])})</strong>, still above its 50-day average of {F["VIX"]["avg50"]:.2f}. <strong>Bonds fell</strong>: 30-year bond futures (ZB) {fx(F, "ZB")} ({sg(F["ZB"]["chg_pct"])}) and 10-year note futures (ZN) {fx(F, "ZN")} ({sg(F["ZN"]["chg_pct"])}); '
          f'FMP&rsquo;s {M["treasury_print_date"][5:].replace("-", "/")} treasury print puts the 10-year at {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on {M["ust10y_prev_date"][5:].replace("-", "/")}), the 2-year at {M["ust2y"]:.2f}% and the 30-year at {M["ust30y"]:.2f}%, and the dollar index (DX) was {fx(F, "DX")} ({sg(F["DX"]["chg_pct"])}). '
          f'<strong>Oil eased again</strong>: WTI crude (CL) {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}) and Brent (BZ) {fx(F, "BZ")} ({sg(F["BZ"]["chg_pct"])}), with natural gas (NG) {fx(F, "NG")} ({sg(F["NG"]["chg_pct"])}); <strong>metals fell</strong>: gold (GC) {fx(F, "GC")} ({sg(F["GC"]["chg_pct"])}), silver (SI) {fx(F, "SI")} ({sg(F["SI"]["chg_pct"])}) and copper (HG) {fx(F, "HG")} ({sg(F["HG"]["chg_pct"])}). '
          f'<strong>Bitcoin is ${B["price"]:,.2f} ({sg(B["chg_pct"])})</strong> and Ether {fx(F, "ETH")} ({sg(F["ETH"]["chg_pct"])}). {CAUSE}</p>')
    wk = worst(T, 8); ld = sorted(T.values(), key=lambda t: (-t['chg_pct'], t['symbol']))[:8]
    p2 = (f'<p class="intro"><strong>{len(up)} of 11 S&amp;P 500 sectors rose; {allsec[0][1]} led and {allsec[-1][1]} fell hardest.</strong> By sector, <strong>' + lst(f'{k} ({f}) {sg(c)}' for c, k, f in allsec) + '</strong>. '
          f'Our {sa["Information Technology"][0]} Information Technology names averaged {sg(sa["Information Technology"][1])} (with {sa["Information Technology"][2]} of them at 4 or more red flags), our {sa["Financials"][0]} Financials names {sg(sa["Financials"][1])} and our {sa["Energy"][0]} Energy names {sg(sa["Energy"][1])}. '
          f'The Semiconductor/AI basket averaged {sg(semavg)} ({semup} of its 20 names rose), the Software/Cloud basket {sg(swavg)} ({swup} of its 20 names rose), the Nasdaq 100 basket {sg(basket(T, "nasdaq100")[1])}, the Mega-Cap Leaders basket {sg(mgavg)} and the Dow 30 basket {sg(basket(T, "dow30")[1])} ({basket(T, "dow30")[2]} of 30 names rose). '
          f'The market leaders were split: {lst(mv(T, s) for s in ("NVDA", "MSFT", "AAPL", "GOOGL", "META", "AMZN", "AVGO", "TSLA"))}. '
          f'<strong>The biggest gainers</strong>: ' + lst(mv(T, t['symbol']) for t in ld) + f'; Take-Two Interactive reversed Monday&rsquo;s {sg(PT["TTWO"]["chg_pct"])}. '
          f'<strong>The weakest names</strong> were: ' + lst(mv(T, t['symbol']) for t in wk) + '.</p>')
    of = names_or_none(T, st['off4']); nw = names_or_none(T, st['new4'])
    inc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['inc'][:4])
    dc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['dec_'][:4])
    new = S['data_notes']['new_names']; dr = S['data_notes']['dropped_names']
    tr = sum(t['flags']['trend'] == 'red' for t in T.values()); ptr = sum(t['flags']['trend'] == 'red' for t in PT.values())
    p3 = (f'<p class="intro">On the checklist, <strong>{st["r4"]} of {n} names carry 4 or more red flags, against {st["pr4"]} on Monday</strong> ({st["z"]} names are clean, against {st["pz"]}). Trend red flags went from {ptr} to {tr} and relative-strength red flags from {st["prs"]} to {st["rs"]}. Names moving onto the 4+ list: {nw}. Names leaving it: {of}. '
          f'The biggest increases: {inc}. The biggest decreases: {dc}. ' + (f'{lst(nm(T, s) + " (" + s + ")" for s in new)} entered the universe and {lst(next((x["name"] for x in P["tickers"] if x["symbol"] == s), s) + " (" + s + ")" for s in dr)} dropped out. ' if new or dr else 'No names entered or left the universe. ') +
          f'The benchmark 3-month returns moved (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%). '
          f'Bitcoin was ${B["price"]:,.2f} ({sg(B["chg_pct"])}) at the close, {(B["price"] / B["avg200"] - 1) * 100:.1f}% above its 200-day average and {abs((B["price"] / B["avg50"] - 1) * 100):.1f}% {"below" if B["price"] < B["avg50"] else "above"} its 50-day.</p>')
    pulls = [(sg(fs["Information Technology"]["chg_pct"]), 'Information Technology Sector Fund (XLK)'), (f'{M["ust10y"]:.2f}%', '10-Year Treasury Yield'), (f'{st["adv"]} / {n}', 'Names Advancing'), (f'{st["r4"]} / {n}', 'Names With 4+ Red Flags')]
    pr = '<div class="pull-row">' + ''.join(f'<div class="pull"><div class="pn mono">{a}</div><div class="pl">{b_}</div></div>' for a, b_ in pulls) + '</div>'
    return p1 + p2 + p3 + pr

def macro(S, P, F, C):
    M = S['macro']; B = S['bitcoin']; ff = lambda s: f'{fx(F, s)} ({sg(F[s]["chg_pct"])})'
    return (f'<section><div class="section-head"><div class="section-top-row"><span class="kicker-label">Setup</span></div><h2 style="margin-top:2px">Macro Backdrop</h2><span class="section-note">2:00pm MT, {C["long_label"]} (close). FMP futures quotes; daily % versus the prior settle. Yields are FMP&rsquo;s treasury print ({M["treasury_print_date"]}).</span></div><div class="macro-grid">'
            f'<div class="mcard"><h3>Rates &amp; the Fed</h3><p class="big red">Bond futures lower, yields up</p><p>Cash Treasury yields (FMP, {M["treasury_print_date"]} print): 2-year {M["ust2y"]:.2f}%, 10-year {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on {M["ust10y_prev_date"][5:].replace("-", "/")}), 30-year {M["ust30y"]:.2f}%. Futures: 30-year bond futures (ZB) {ff("ZB")}, 10-year note futures (ZN) {ff("ZN")}, 5-year (ZF) {ff("ZF")}, 2-year (ZT) {ff("ZT")}. The long end fell most. We found no dated coverage of the Fed or rate odds, so we state none.</p></div>'
            f'<div class="mcard"><h3>Equities</h3><p class="big red">Stock futures slightly lower</p><p>S&amp;P 500 futures (ES) {ff("ES")}, Nasdaq 100 futures (NQ) {ff("NQ")}, Mini Dow (YM) {ff("YM")}, Russell 2000 (RTY) {ff("RTY")}. The VIX is {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}). {CAUSE}</p></div>'
            f'<div class="mcard"><h3>Oil &amp; Energy</h3><p class="big">Crude lower, natural gas higher</p><p>WTI (CL) {ff("CL")}, Brent (BZ) {ff("BZ")}, RBOB gasoline (RB) {ff("RB")}, heating oil (HO) {ff("HO")}, natural gas (NG) {ff("NG")}. The Energy sector fund (XLE) {sg(S["sector_funds"]["Energy"]["chg_pct"])}.</p></div>'
            f'<div class="mcard"><h3>Metals, Dollar &amp; Crypto</h3><p class="big red">Metals lower, dollar higher</p><p>Gold (GC) {ff("GC")}, silver (SI) {ff("SI")}, platinum (PL) {ff("PL")}, palladium (PA) {ff("PA")}, copper (HG) {ff("HG")}; cocoa (CC) {ff("CC")}; dollar index (DX) {ff("DX")}. Bitcoin (BTC) {ff("BTC")}, Ether (ETH) {ff("ETH")}.</p></div></div></section>')

def bitcoin(S, F, C):
    B = S['bitcoin']; p = B['price']; ab200 = (p / B['avg200'] - 1) * 100; v50 = (p / B['avg50'] - 1) * 100; fromhi = (1 - p / B['year_high']) * 100
    c = lambda x: 'up' if x > 0 else 'down'
    assert p > B['avg200'] and p < B['avg50']
    trend = f'Price is above its 200-day average and below its 50-day (50-day <strong class="mono">${B["avg50"]:,.2f}</strong>, 200-day <strong class="mono">${B["avg200"]:,.2f}</strong>): {ab200:.1f}% above the 200-day, {fromhi:.1f}% below the 52-week high and {abs(v50):.1f}% below the 50-day.'
    eth = F['ETH']
    return (f'<section id="bitcoin"><div class="section-head"><div class="section-top-row"><span class="kicker-label">Crypto</span><h2>Bitcoin</h2><span class="section-note">Live price at 2:00pm MT (Tuesday Nov 10); BTC trades 24/7. 52-wk range and 50d/200d averages from FMP <code class="mono">quote</code>; 7/30/90-day moves from <code class="mono">historical-price-eod/full?symbol=BTCUSD</code>.</span></div></div>'
            f'<div class="btc-card"><div><div class="btc-price mono">${p:,.2f}</div><div class="btc-chg-row"><span class="btc-chg {c(B["chg_pct"])} mono">{sg(B["chg_pct"])} today</span><span class="btc-sep">&middot;</span><span class="btc-range">52-wk range: <strong class="mono">${B["year_low"]:,.2f}</strong> &ndash; <strong class="mono">${B["year_high"]:,.2f}</strong></span></div><p class="btc-trend-note">{trend}</p></div>'
            f'<div class="btc-moves"><div class="btc-move"><div class="bm-label">7-Day</div><div class="bm-val {c(B["r7"])} mono">{sg(B["r7"])}</div></div><div class="btc-move"><div class="bm-label">30-Day</div><div class="bm-val {c(B["r30"])} mono">{sg(B["r30"])}</div></div><div class="btc-move"><div class="bm-label">90-Day</div><div class="bm-val {c(B["r90"])} mono">{sg(B["r90"])}</div></div><div class="btc-move"><div class="bm-label">Ether</div><div class="bm-val {c(eth["chg_pct"])} mono">{fx(F, "ETH")} ({sg(eth["chg_pct"])})</div></div></div>'
            f'<div class="btc-context">Bitcoin is {sg(B["chg_pct"])} on the day, with 7-day, 30-day and 90-day moves of {sg(B["r7"])}, {sg(B["r30"])} and {sg(B["r90"])}. It traded between ${B["day_low"]:,.2f} and ${B["day_high"]:,.2f} today, while the dollar index (DX) was {sg(F["DX"]["chg_pct"])} and Nasdaq 100 futures (NQ) {sg(F["NQ"]["chg_pct"])}; Ether fell more, and Strategy (MSTR) {sg(S_T(S)["MSTR"]["chg_pct"])}. Price is still {ab200:.1f}% above its 200-day average, the closest it has been this month. We found no dated spot Bitcoin ETF flow figure, so none is quoted; FMP is the price source here.</div></div></section>')
def S_T(S): return {t['symbol']: t for t in S['tickers']}


def sec_worst(T, sector, k):
    return sorted((t for t in T.values() if t['detail']['sector'] == sector), key=lambda t: (t['chg_pct'], t['symbol']))[:k]


def spotlight(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    f = lambda k: f'{k} ({fs[k]["fund"]}) {sg(fs[k]["chg_pct"])}'
    sem, semavg, semup = basket(T, 'semiconductor_ai'); sw, swavg, swup = basket(T, 'software_cloud')
    sl = sorted(sem, key=lambda t: (-t['chg_pct'], t['symbol']))
    ai = ("GEV", "BE", "NBIS", "CRWV", "VRT", "PWR")
    swl = sorted(sw, key=lambda t: (t['chg_pct'], t['symbol']))
    p1 = (f'{f("Information Technology")} was the weakest of the 11 sector funds, the day after its {sg(P["sector_funds"]["Information Technology"]["chg_pct"])} gain. The Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 names higher, after {sg(basket(PT, "semiconductor_ai")[1])} on Monday, and the chip names split: {lst(mv(T, s) for s in ("NVDA", "AVGO", "AMD", "TSM"))}. NVIDIA fell for a second day ({sg(PT["NVDA"]["chg_pct"])} on Monday). '
          f'Our {sa["Information Technology"][0]} Information Technology names averaged {sg(sa["Information Technology"][1])}, with {sa["Information Technology"][2]} of them at 4 or more red flags. ' + CAUSE)
    p2 = (f'The Software/Cloud basket averaged {sg(swavg)} with only {swup} of its 20 names higher; the weakest were ' + lst(mv(T, t['symbol']) for t in swl[:4]) + f', while {mv(T, "NET")} rose. AI-infrastructure and power names gave back part of Monday&rsquo;s gains: {lst(mv(T, s) for s in ai)}; Monday&rsquo;s moves were {lst(s_ + " " + sg(PT[s_]["chg_pct"]) for s_ in ai)}.')
    p3 = (f'{f("Financials")} led, with {f("Energy")} and {f("Health Care")} close behind; {len(up)} of 11 sector funds rose. Our {sa["Financials"][0]} Financials names averaged {sg(sa["Financials"][1])} and our {sa["Health Care"][0]} Health Care names {sg(sa["Health Care"][1])}. '
          f'Insurers were among the gainers: {lst(mv(T, s) for s in ("CVS", "HUM", "ELV", "ALL"))}. The defensive tilt is modest: the large-cap proxy basket averaged {sg(basket(T, "large_cap_proxy")[1])} against {sg(basket(T, "nasdaq100")[1])} for the Nasdaq 100 basket.')
    en = sorted((t for t in T.values() if t['detail']['sector'] == 'Energy'), key=lambda t: (-t['chg_pct'], t['symbol']))
    p4 = (f'WTI crude (CL) {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}) eased again, yet {f("Energy")} rose and our {sa["Energy"][0]} Energy names averaged {sg(sa["Energy"][1])}. The strongest were gas and midstream names: ' + lst(mv(T, t['symbol']) for t in en[:4]) + f', with natural gas (NG) {fx(F, "NG")} ({sg(F["NG"]["chg_pct"])}); the weakest were refiners and services: ' + lst(mv(T, t['symbol']) for t in en[-3:]) + f'. Metals fell: gold (GC) {fx(F, "GC")} ({sg(F["GC"]["chg_pct"])}), and {mv(T, "NEM")}.')
    p5 = (f'{mv(T, "TTWO")}{epsr(T, "TTWO")}, a reversal from Monday&rsquo;s {sg(PT["TTWO"]["chg_pct"])}; {mv(T, "RKLB")}{epsr(T, "RKLB")}; {mv(T, "KKR")}{epsr(T, "KKR")}; {mv(T, "TDG")}{epsr(T, "TDG")}; {mv(T, "CRWV")}{epsr(T, "CRWV")}. '
          f'The EPS figures are FMP&rsquo;s earnings history against its consensus; we found no coverage describing the reactions, so we do not assert why any of them moved.')
    chip = lambda syms: '<div class="names">' + ', '.join(f'<span class="chip">{s}</span>' for s in syms) + '</div>'
    bt = ' style="border-top:1px solid var(--line)"'
    sec = lambda t, body, names, first=False: f'<div class="spotlight"{"" if first else bt}><h3>{t}</h3><p>{body}</p>{chip(names)}</div>'
    return (f'<section id="spotlight"><div class="section-head"><span class="kicker-label">Analysis</span><h2 style="margin-top:2px">Sector Spotlight</h2></div>'
            + sec('Tech Gives Back; NVIDIA Down Again', p1, ["NVDA", "AVGO", "AMD", "TSM"], True)
            + sec('Software and AI Power Names Slip', p2, [t['symbol'] for t in swl[:4]] + list(ai[:3]))
            + sec('Financials, Energy and Health Care Lead', p3, ["CVS", "HUM", "ELV", "ALL"])
            + sec('Gas and Pipelines Up as Crude Eases', p4, [t['symbol'] for t in en[:4]])
            + sec('Earnings: Reports Dated Nov 9&ndash;10', p5, ["TTWO", "RKLB", "KKR", "TDG", "CRWV"]))

def movers_read(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; n = st['n']
    bks = {k: basket(T, k)[1] for k in ('dow30', 'sp500_top100', 'nasdaq100', 'large_cap_proxy', 'software_cloud', 'semiconductor_ai', 'megacap_leaders')}
    return (f'<p class="movers-read"><strong>An even split.</strong> {st["adv"]} of {n} names rose and {st["dec"]} fell, and the average move was {sg(st["avg"])}. The S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))}, the Dow fund (DIA) {sg(etf(S, "DIA"))} and the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))}. '
            f'The Dow 30 basket averaged {sg(bks["dow30"])}, the S&amp;P 500 Top 100 basket {sg(bks["sp500_top100"])}, the Nasdaq 100 basket {sg(bks["nasdaq100"])} and the large-cap proxy basket {sg(bks["large_cap_proxy"])}, while the Software/Cloud basket averaged {sg(bks["software_cloud"])}, the Semiconductor/AI basket {sg(bks["semiconductor_ai"])} and the Mega-Cap Leaders basket {sg(bks["megacap_leaders"])}. '
            f'The gainers lean toward earnings reactions, health insurers and gas pipelines; the losers toward Monday&rsquo;s AI, software and gold-miner winners, with NVIDIA and Moderna the largest decliners and the VIX {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}). {CAUSE}</p>')

def rollup(S, P, T, PT, C):
    R = S['rollup']; wl = set(S['rollup']['watchlist'])
    li = lambda s, extra='': f'<li><strong>{e(s)}</strong> &middot; {e(T[s]["name"])} {sg(T[s]["chg_pct"])} ({T[s]["red_flag_count"]} red){extra}</li>'
    mv_ = ''.join(li(s) for s in R['movers']); mr = ''.join(li(s) for s in R['multi_red_flag'][:8])
    imp = ''.join(f'<li><strong>{e(s)}</strong> &middot; {e(T[s]["name"])} ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]} of 10 red)</li>' for s in R['improving'])
    new = set(S['data_notes']['new_names']); newly = {s for s in T if T[s]['red_flag_count'] >= 4 and s in PT and PT[s]['red_flag_count'] < 4}
    w = ''
    for s in R['watchlist']:
        tag = ' &middot; &#9733; on your watchlist' if s not in newly and s not in new else (' &middot; newly at 4+ red' if s in newly else ' &middot; new to the universe')
        if s in new and s not in newly: tag = ' &middot; new to the universe'
        w += li(s, tag)
    return (f'<section id="rollup"><div class="section-head"><span class="kicker-label">Digest</span><h2 style="margin-top:2px">Roll-Up</h2></div><div class="rollup-grid"><div class="rcard"><h3>Notable Movers (|% chg|)</h3><ul>{mv_}</ul></div>'
            f'<div class="rcard"><h3>Multiple Red Flags (top 8 shown; {len(R["multi_red_flag"])} at 4+)</h3><ul>{mr}</ul></div><div class="rcard"><h3>Improving vs {C["prior_short"]}</h3><ul>{imp}</ul></div><div class="rcard watch"><h3>Watchlist for Next Session</h3><ul>{w}</ul></div></div></section>')

def vs_previous(S, P, T, PT, F, PF, C):
    st = stats(S, P, T, PT); b = bm(S, P)
    nm_ = lambda ss: lst(f'{nm(T if s in T else {s: next(x for x in P["tickers"] if x["symbol"] == s)}, s)} ({s})' for s in ss) or 'none'
    inc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['inc'])
    dc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['dec_'])
    new = S['data_notes']['new_names']; dr = S['data_notes']['dropped_names']
    newer = sum(1 for s in T if s in PT and T[s]['detail'].get('latest_fiscal_period') != PT[s]['detail'].get('latest_fiscal_period'))
    ton = sum(st['on'].values()); toff = sum(st['off'].values())
    tn = sorted(s for s in T if s in PT and PT[s]['flags']['trend'] != 'red' and T[s]['flags']['trend'] == 'red'); tf = sorted(s for s in T if s in PT and PT[s]['flags']['trend'] == 'red' and T[s]['flags']['trend'] != 'red')
    para = (f'<p class="movers-read"><strong>The 4+ red-flag count {"rose" if st["r4"]>st["pr4"] else "fell" if st["r4"]<st["pr4"] else "held"} to {st["r4"]} from {st["pr4"]}, with {len(st["new4"])} names joining it and {len(st["off4"])} leaving; {ton} flags moved onto red and {toff} moved off red as the average stock moved {sg(st["avg"])}.</strong> '
            f'Flags moving onto red: {kv(st["on"])}. Flags moving off red: {kv(st["off"])}. Relative-strength red flags went from {st["prs"]} to {st["rs"]}; the benchmark 3-month returns moved (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%), so part of the change is a yardstick effect. '
            f'Names entering the 4+ group: {nm_(st["new4"])}. Names leaving it: {nm_(st["off4"])}. New to the universe: {nm_(new)}. Dropped out: {nm_(dr)}. Biggest red-flag increases: {inc}. Biggest decreases: {dc}. {newer} names show a newer reported quarter than on {C["prior_short"]}, which can move growth and margin flags by itself.</p>')
    order = ['ES', 'NQ', 'ZB', 'CL', 'GC', 'SI', 'BTC', 'ETH', 'VIX']
    rows = ''.join(f'<tr><td>{s} ({F[s]["name"] if False else {"ES": "E-Mini S&amp;P 500", "NQ": "Nasdaq 100", "ZB": "30Y T-Bond", "CL": "WTI Crude", "GC": "Gold", "SI": "Silver", "BTC": "Bitcoin", "ETH": "Ethereum", "VIX": "CBOE Volatility Index"}[s]})</td><td class="px-cell mono">{fx(F, s)}</td><td class="px-cell {"up" if F[s]["last"] > PF[s]["last"] else "down"} mono">{sg((F[s]["last"] / PF[s]["last"] - 1) * 100)}</td></tr>' for s in order)
    cards = (f'<div class="rollup-grid"><div class="rcard"><h3>Futures Since {C["prior_short"]} Close</h3><div class="table-wrap"><table style="min-width:0"><thead><tr><th>Contract</th><th>Last</th><th>Since {C["prior_short"]}</th></tr></thead><tbody>{rows}</tbody></table></div></div>'
             f'<div class="rcard"><h3>Trend Flips</h3><p style="font-size:13.5px;margin:0 0 8px"><strong>Newly red on trend ({len(tn)}):</strong> {nm_(tn)}.</p><p style="font-size:13.5px;margin:0"><strong>No longer red on trend ({len(tf)}):</strong> {nm_(tf)}.</p></div>'
             f'<div class="rcard"><h3>4+ Red Flags</h3><p style="font-size:13.5px;margin:0 0 8px">{st["pr4"]} names on {C["prior_short"]} &rarr; {st["r4"]} now.</p><p style="font-size:13.5px;margin:0 0 8px"><strong>Dropped off:</strong> {nm_(st["off4"])}.</p><p style="font-size:13.5px;margin:0"><strong>Newly on:</strong> {nm_(st["new4"])}.</p></div></div>')
    return f'<section id="vs-previous"><div class="section-head"><span class="kicker-label">Comparison</span><div class="section-top-row"><h2>Vs Previous Full Study ({C["prior_short"]})</h2><span class="section-note">One trading day apart; flags compared on the same rules</span></div></div>{para}{cards}</section>'


def whats_next(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; fs = S['sector_funds']; b = bm(S, P); n = st["n"]; M = S['macro']
    up, dn = secfunds(S); sa = sector_avgs(T)
    sem, semavg, semup = basket(T, 'semiconductor_ai')
    q1 = (f'Yesterday {sum(1 for v in P["sector_funds"].values() if v["chg_pct"] > 0)} of 11 sector funds rose and the average name moved {sg(st["pavg"])}; today {len(up)} of 11 rose and the average name moved {sg(st["avg"])}, with {st["adv"]} advancers against {st["dec"]} decliners. Information Technology ({fs["Information Technology"]["fund"]}) went from {sg(P["sector_funds"]["Information Technology"]["chg_pct"])} to {sg(fs["Information Technology"]["chg_pct"])}, while Financials ({fs["Financials"]["fund"]}) went from {sg(P["sector_funds"]["Financials"]["chg_pct"])} to {sg(fs["Financials"]["chg_pct"])}. Is a day like this a pause, a rotation, or neither, and what would you need to see over the next few sessions to tell the difference?')
    h1 = (f'Facts to weigh: the 10-year yield went from {M["ust10y_prev"]:.2f}% to {M["ust10y"]:.2f}% and 30-year bond futures (ZB) were {sg(F["ZB"]["chg_pct"])}; the dollar index (DX) was {sg(F["DX"]["chg_pct"])} while Nasdaq 100 futures (NQ) were {sg(F["NQ"]["chg_pct"])}, so your dollar-versus-indices rule held today. Think about which kinds of companies are most sensitive to a higher discount rate, and whether today&rsquo;s weakest names fit that description.')
    q2 = (f'{mv(T, "NVDA")} fell for a second straight day (Monday: {sg(PT["NVDA"]["chg_pct"])}), yet the Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 names higher, and {pv(T, PT, "AVGO")} and {pv(T, PT, "TSM")} rose again. NVIDIA carries {T["NVDA"]["red_flag_count"]} red flags on our checklist. Which of its 10 checklist points could explain two days of weakness, and which could not explain a move over just two days at all?')
    h2 = (f'Facts to weigh: open NVIDIA in the 10-Point Analyzer and compare its trend and relative-strength points with Broadcom&rsquo;s; the QQQ benchmark&rsquo;s 3-month return moved from {b["pqq"]:+.2f}% to {b["qq"]:+.2f}%. We found no coverage verifying why NVIDIA moved, so the reasons are yours to propose and test.')
    en = sorted((t for t in T.values() if t['detail']['sector'] == 'Energy'), key=lambda t: (-t['chg_pct'], t['symbol']))
    q3 = (f'WTI crude (CL) {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}) fell for a second day, yet {mv(T, "LNG")}, {mv(T, "TRGP")} and {mv(T, "KMI")} rose while {mv(T, "VLO")} and {mv(T, "PSX")} fell. Natural gas (NG) was {sg(F["NG"]["chg_pct"])}. What does each of these businesses actually sell, and why might they react differently to the same oil move?')
    h3 = (f'Facts to weigh: our {sa["Energy"][0]} Energy names averaged {sg(sa["Energy"][1])} and the Energy fund ({fs["Energy"]["fund"]}) was {sg(fs["Energy"]["chg_pct"])}. Look up whether each company earns more from the volume it moves or from the price of the commodity, and check Point 3 (revenue growth) for each in the Analyzer.')
    card = lambda n_, q, hh: f'<div class="qcard"><div class="qnum">Question {n_}</div><div class="q">{q}</div><div class="hint">{hh}</div></div>'
    return (f'<section class="study" id="whats-next"><div class="kicker">Study Session</div><h2>What&rsquo;s Next</h2><p class="setup">Three open questions from today&rsquo;s facts. Work through them yourself before the next session; the data doesn&rsquo;t settle any of them.</p><div class="qlist">{card("One", q1, h1)}{card("Two", q2, h2)}{card("Three", q3, h3)}</div><p class="closer">None of this is a recommendation. The point is to practice separating what the numbers show from the story that explains them.</p></section>')

def news(S, P, T, PT, C):
    F = {f['symbol']: f for f in S['futures']}; M = S['macro']
    macro = (f'<li>We found no dated Nov 10 close coverage of the Fed, yields or the stock moves, so no cause is stated for today&rsquo;s session; the numbers on this page are FMP quotes at the 2pm MT close.</li>'
             f'<li>FMP&rsquo;s newest treasury print ({M["treasury_print_date"]}) put the 10-year cash yield at {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on {M["ust10y_prev_date"][5:].replace("-", "/")}) and the 30-year at {M["ust30y"]:.2f}%. Index moves here are SPY, QQQ, DIA and IWM from FMP; futures are FMP quotes.</li>'
             f'<li>No dated spot Bitcoin ETF flow figure was found, so none is quoted.</li>')
    names = (f'<li><strong>Take-Two Interactive (TTWO)</strong> {sg(T["TTWO"]["chg_pct"])} and <strong>Rocket Lab USA (RKLB)</strong> {sg(T["RKLB"]["chg_pct"])} led the gainers, both with reports FMP dates Nov 9; <strong>TransDigm (TDG)</strong> {sg(T["TDG"]["chg_pct"])} and <strong>CoreWeave (CRWV)</strong> {sg(T["CRWV"]["chg_pct"])} have reports dated Nov 10.</li>'
             f'<li><strong>CVS Health (CVS)</strong> {sg(T["CVS"]["chg_pct"])}, <strong>Humana (HUM)</strong> {sg(T["HUM"]["chg_pct"])} and <strong>Elevance Health (ELV)</strong> {sg(T["ELV"]["chg_pct"])} rose together; no article describing the move was found.</li>'
             f'<li><strong>Moderna (MRNA)</strong> {sg(T["MRNA"]["chg_pct"])}, <strong>NVIDIA (NVDA)</strong> {sg(T["NVDA"]["chg_pct"])}, <strong>Nebius Group (NBIS)</strong> {sg(T["NBIS"]["chg_pct"])} and <strong>Carvana (CVNA)</strong> {sg(T["CVNA"]["chg_pct"])} were the largest decliners.</li>'
             '<li><strong>No company-specific catalyst was verified for any name above</strong>, so their moves are reported as price action.</li>')
    return (f'<section id="news"><div class="section-head"><span class="kicker-label">Research</span><h2 style="margin-top:2px">Market News &amp; Research</h2></div><div class="rollup-grid"><div class="rcard"><h3>Macro</h3><ul>{macro}</ul></div><div class="rcard"><h3>Names from today&rsquo;s movers</h3><ul>{names}</ul><p class="trap-note">Nothing here is independently verified news.</p></div></div>')


def findings(S, P, T, PT, C):
    dn = S['data_notes']; new = lst(f'{nm(T, s)} ({s})' for s in dn['new_names'])
    dropped = lst(next((x['name'] for x in P['tickers'] if x['symbol'] == s), s) + f' ({s})' for s in dn['dropped_names'])
    return (f'<section id="findings"><div class="findings"><div class="section-head" style="border:none"><span class="kicker-label">Corrections &amp; Methodology</span><h2 style="margin-top:2px">Pipeline Findings</h2></div><h3>Data sources</h3><ul>'
            f'<li>Universe: {len(T)} unique names &mdash; Dow 30, live Nasdaq 100 (101), live S&amp;P 500 top 100 by market cap, large-cap proxy (100; US-only screener; notes, preferreds and duplicate share classes (BRK-A, SOJE, SOMN, APOS) removed), and the three 20-name baskets. New versus {C["prior_short"]}: {new}. Dropped: {dropped}.</li>'
            f'<li>Prices, moving averages and 52-week ranges from FMP <code>/stable/batch-quote</code>; growth, ratios, key metrics and cash flow from the quarterly endpoints; EMAs, YTD and 3-month returns computed from <code>historical-price-eod/full</code>. TRAP #4 data from <code>trap_fundamentals.py</code>; annual-report data from <code>annual_review.py</code>. The pull and scoring use <code>full_study_pull.py</code>, <code>full_study_score.py</code> and <code>full_study_build.py</code>. The VIX is not returned by <code>batch-quote</code>, so it comes from <code>quote?symbol=^VIX</code>. Captured at the 2pm MT close.</li>'
            f'<li>Index moves are FMP ETF proxies (SPY, QQQ, DIA, IWM). Yields are FMP&rsquo;s <code>/stable/treasury-rates</code> with a {S["macro"]["treasury_print_date"]} print. Sector moves are the Select Sector SPDR funds (FMP daily close, {S["date"]}). Report dates and EPS against consensus quoted for individual names come from the TRAP #4 earnings history (FMP).</li></ul>'
            f'<h3>Gaps this session</h3><ul><li>Institutional ownership and moat: every name carries its cached research; HEICO (HEI) was researched fresh this session (about 23.5% institutional on Q1 2026 13Fs per VCPScanner, against 27.1% at MarketBeat, with a large family insider stake; Morningstar&rsquo;s moat rating is paywalled, so the &ldquo;durable&rdquo; verdict rests on its report headline). Vylor (VYLR) re-entered with its cached entry from Oct 20. The one-search &ldquo;anything changed&rdquo; refresh was not run for the other names.</li>'
            f'<li>Futures: FMP priced 23 of the 40 contracts through <code>batch-quote</code> (plus the VIX via <code>quote</code>); unpriced: VX, SR3, ZC, ZW, ZL, KC, LE, the currency futures (SB and CT return unrelated token quotes).</li>'
            f'<li>News: no dated Nov 10 close coverage explaining the day was found, and no Bitcoin ETF flow figure dated {C["short"]} was found. The institutional ownership endpoint still returns an empty array on this plan.</li></ul></div></section>')
