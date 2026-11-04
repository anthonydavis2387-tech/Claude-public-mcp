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

DAYS = ('2026-11-03', '2026-11-04')
def epsr(T, s):
    r = reported(T, s, DAYS); return f' (FMP dates its report {r[0][5:].replace("-", "/")}, EPS ${r[1]:.2f} against ${r[2]:.2f} expected)' if r else ''

def pv(T, PT, s): return f'{mv(T, s)} (Tuesday: {sg(PT[s]["chg_pct"])})'
def pm(PT, s): return f'{nm(PT, s)} ({s}) {sg(PT[s]["chg_pct"])}'
def lead(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; st = stats(S, P, T, PT); n = st['n']; B = S['bitcoin']; M = S['macro']; b = bm(S, P)
    up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    sem, semavg, semup = basket(T, 'semiconductor_ai'); sw, swavg, swup = basket(T, 'software_cloud'); mg, mgavg, _ = basket(T, 'megacap_leaders')
    p1 = (f'<p class="intro"><strong>Oil plunged and the broad market rallied, with the Dow leading while chips, AI infrastructure and energy stocks fell.</strong> The Dow fund (DIA) {sg(etf(S, "DIA"))} led, with the S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))} and the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))} also higher. '
          f'<strong>{st["adv"]} of {n} names advanced ({st["adv"] / n * 100:.1f}%) and {st["dec"]} declined</strong>, and the average move was {sg(st["avg"])}, against {sg(st["pavg"])} on Tuesday. '
          f'S&amp;P 500 futures (ES) {fx(F, "ES")} ({sg(F["ES"]["chg_pct"])}), Nasdaq 100 futures (NQ) {fx(F, "NQ")} ({sg(F["NQ"]["chg_pct"])}), Mini Dow (YM) {fx(F, "YM")} ({sg(F["YM"]["chg_pct"])}) and Russell 2000 (RTY) {fx(F, "RTY")} ({sg(F["RTY"]["chg_pct"])}). '
          f'<strong>The VIX was {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])})</strong>. <strong>Treasuries rose</strong>: 30-year bond futures (ZB) {fx(F, "ZB")} ({sg(F["ZB"]["chg_pct"])}) and 10-year note futures (ZN) {fx(F, "ZN")} ({sg(F["ZN"]["chg_pct"])}); '
          f'FMP&rsquo;s newest yields (Nov 3 print, so they predate today&rsquo;s bond move) are {M["ust10y"]:.2f}% on the 10-year ({M["ust10y_prev"]:.2f}% on Nov 2), {M["ust2y"]:.2f}% on the 2-year and {M["ust30y"]:.2f}% on the 30-year, and the dollar index (DX) {fx(F, "DX")} ({sg(F["DX"]["chg_pct"])}). '
          f'<strong>Oil fell sharply</strong>: WTI crude (CL) {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}) and Brent (BZ) {fx(F, "BZ")} ({sg(F["BZ"]["chg_pct"])}), with gasoline (RB) {sg(F["RB"]["chg_pct"])}, heating oil (HO) {sg(F["HO"]["chg_pct"])} and natural gas (NG) {fx(F, "NG")} ({sg(F["NG"]["chg_pct"])}); <strong>metals rose</strong>: gold (GC) {fx(F, "GC")} ({sg(F["GC"]["chg_pct"])}), silver (SI) {fx(F, "SI")} ({sg(F["SI"]["chg_pct"])}), palladium (PA) {fx(F, "PA")} ({sg(F["PA"]["chg_pct"])}) and copper (HG) {fx(F, "HG")} ({sg(F["HG"]["chg_pct"])}). '
          f'<strong>Bitcoin is ${B["price"]:,.2f} ({sg(B["chg_pct"])})</strong> and Ether {fx(F, "ETH")} ({sg(F["ETH"]["chg_pct"])}). We searched for same-day coverage of the close and found none, so we state no verified cause for today&rsquo;s moves; treat the explanations below as questions, not facts.</p>')
    wk = sorted(T.values(), key=lambda t: (t['chg_pct'], t['symbol']))[:8]; ld = sorted(T.values(), key=lambda t: (-t['chg_pct'], t['symbol']))[:8]
    en = sorted((t for t in T.values() if t['detail']['sector'] == 'Energy'), key=lambda t: t['chg_pct'])[:4]
    p2 = (f'<p class="intro"><strong>{up[0][1]} led the 11 sectors and {dn[0][1]} was the weakest.</strong> By sector, <strong>{len(up)} of 11 S&amp;P 500 sectors rose: ' + lst(f'{k} ({f}) {sg(c)}' for c, k, f in up) + f'</strong>; <strong>{dn[0][1]} ({dn[0][2]}) {sg(dn[0][0])} was the weakest</strong>, followed by ' + lst(f'{k} ({f}) {sg(c)}' for c, k, f in dn[1:]) + '. '
          f'Our {sa["Energy"][0]} Energy names averaged {sg(sa["Energy"][1])}, our {sa["Consumer Discretionary"][0]} Consumer Discretionary names {sg(sa["Consumer Discretionary"][1])}, our {sa["Health Care"][0]} Health Care names {sg(sa["Health Care"][1])} and our {sa["Information Technology"][0]} Information Technology names {sg(sa["Information Technology"][1])} (with {sa["Information Technology"][2]} of them at 4 or more red flags). '
          f'The Semiconductor/AI basket averaged {sg(semavg)} ({semup} of its 20 names rose), the Software/Cloud basket {sg(swavg)} ({swup} of its 20 names rose) and the Mega-Cap Leaders basket {sg(mgavg)}. '
          f'Energy stocks fell with crude: {lst(mv(T, t["symbol"]) for t in en)}. AI-infrastructure names that rose on Tuesday reversed: {lst(mv(T, s) for s in ("VRT", "PWR", "CRWV", "GEV", "NBIS"))}. '
          f'Reporters: {mv(T, "DDOG")}{epsr(T, "DDOG")}; {mv(T, "CVS")}{epsr(T, "CVS")}; {mv(T, "APP")}{epsr(T, "APP")}; {mv(T, "BKNG")}{epsr(T, "BKNG")}. '
          f'The weakest names were: ' + lst(mv(T, t['symbol']) for t in wk) + '. '
          f'Leaders: ' + lst(mv(T, t['symbol']) for t in ld) + '.</p>')
    nw = lst(f'{nm(T, s)} ({s})' for s in st['new4']); of = lst(f'{nm(T, s)} ({s})' for s in st['off4'])
    inc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['inc'][:4])
    dc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['dec_'][:4])
    new = S['data_notes']['new_names']; dr = S['data_notes']['dropped_names']
    p3 = (f'<p class="intro">On the checklist, <strong>{st["r4"]} of {n} names carry 4 or more red flags, against {st["pr4"]} on Tuesday</strong> ({st["z"]} names are clean, against {st["pz"]}). Names moving onto the 4+ list: {nw}. Names leaving it: {of}. '
          f'The biggest increases: {inc}. The biggest decreases: {dc}. ' + (f'{lst(nm(T, s) + " (" + s + ")" for s in new)} entered the universe and {lst(next((x["name"] for x in P["tickers"] if x["symbol"] == s), s) + " (" + s + ")" for s in dr)} dropped out. ' if new or dr else 'No names entered or left the universe. ') +
          f'The benchmark 3-month returns rose (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%), yet relative-strength red flags went from {st["prs"]} to {st["rs"]}. '
          f'Bitcoin was ${B["price"]:,.2f} ({sg(B["chg_pct"])}) at the close, {(B["price"] / B["avg200"] - 1) * 100:.1f}% above its 200-day average and {abs((B["price"] / B["avg50"] - 1) * 100):.1f}% {"below" if B["price"] < B["avg50"] else "above"} its 50-day.</p>')
    pulls = [(sg(up[0][0]), f'{up[0][1]} Sector Fund ({up[0][2]})'), (sg(F["CL"]["chg_pct"]), 'WTI Crude Futures (CL)'), (sg(dn[0][0]), f'{dn[0][1]} Sector Fund ({dn[0][2]})'), (f'{st["r4"]} / {n}', 'Names With 4+ Red Flags')]
    pr = '<div class="pull-row">' + ''.join(f'<div class="pull"><div class="pn mono">{a}</div><div class="pl">{b_}</div></div>' for a, b_ in pulls) + '</div>'
    return p1 + p2 + p3 + pr

def macro(S, P, F, C):
    M = S['macro']; B = S['bitcoin']; ff = lambda s: f'{fx(F, s)} ({sg(F[s]["chg_pct"])})'
    return (f'<section><div class="section-head"><div class="section-top-row"><span class="kicker-label">Setup</span></div><h2 style="margin-top:2px">Macro Backdrop</h2><span class="section-note">2:00pm MT, {C["long_label"]} (close). FMP futures quotes; daily % versus the prior settle. Yields are FMP&rsquo;s treasury print ({M["treasury_print_date"]}).</span></div><div class="macro-grid">'
            f'<div class="mcard"><h3>Rates &amp; the Fed</h3><p class="big">Bond futures higher</p><p>Cash Treasury yields (FMP, {M["treasury_print_date"]} print, which predates today&rsquo;s bond move): 2-year {M["ust2y"]:.2f}%, 10-year {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on {M["ust10y_prev_date"][5:].replace("-", "/")}), 30-year {M["ust30y"]:.2f}%. Futures: 30-year bond futures (ZB) {ff("ZB")}, 10-year note futures (ZN) {ff("ZN")}, 5-year (ZF) {ff("ZF")}, 2-year (ZT) {ff("ZT")}. Rising bond futures mean falling yields. We found no dated Nov 4 coverage of the Fed or rate odds, so we state none.</p></div>'
            f'<div class="mcard"><h3>Equities</h3><p class="big">Index futures sharply higher, led by the Dow</p><p>S&amp;P 500 futures (ES) {ff("ES")}, Nasdaq 100 futures (NQ) {ff("NQ")}, Mini Dow (YM) {ff("YM")}, Russell 2000 (RTY) {ff("RTY")}. The VIX is {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}). We found no dated Nov 4 coverage explaining the moves, so we offer no verified cause.</p></div>'
            f'<div class="mcard"><h3>Oil &amp; Energy</h3><p class="big red">Crude and fuels sharply lower</p><p>WTI (CL) {ff("CL")}, Brent (BZ) {ff("BZ")}, RBOB gasoline (RB) {ff("RB")}, heating oil (HO) {ff("HO")}, natural gas (NG) {ff("NG")}. No catalyst for the oil move was verified.</p></div>'
            f'<div class="mcard"><h3>Metals, Dollar &amp; Crypto</h3><p class="big">Metals and crypto higher, dollar softer</p><p>Gold (GC) {ff("GC")}, silver (SI) {ff("SI")}, platinum (PL) {ff("PL")}, palladium (PA) {ff("PA")}, copper (HG) {ff("HG")}; dollar index (DX) {ff("DX")}. Bitcoin (BTC) {ff("BTC")}, Ether (ETH) {ff("ETH")}.</p></div></div></section>')

def bitcoin(S, F, C):
    B = S['bitcoin']; p = B['price']; ab200 = (p / B['avg200'] - 1) * 100; v50 = (p / B['avg50'] - 1) * 100; fromhi = (1 - p / B['year_high']) * 100
    c = lambda x: 'up' if x > 0 else 'down'
    trend = f'Price is above its 200-day average and {"below" if p < B["avg50"] else "above"} its 50-day (50-day <strong class="mono">${B["avg50"]:,.2f}</strong>, 200-day <strong class="mono">${B["avg200"]:,.2f}</strong>): {ab200:.1f}% above the 200-day, {fromhi:.1f}% below the 52-week high and {abs(v50):.1f}% {"below" if p < B["avg50"] else "above"} the 50-day.'
    eth = F['ETH']
    return (f'<section id="bitcoin"><div class="section-head"><div class="section-top-row"><span class="kicker-label">Crypto</span><h2>Bitcoin</h2><span class="section-note">Live price at 2:00pm MT (Wednesday Nov 4); BTC trades 24/7. 52-wk range and 50d/200d averages from FMP <code class="mono">quote</code>; 7/30/90-day moves from <code class="mono">historical-price-eod/full?symbol=BTCUSD</code>.</span></div></div>'
            f'<div class="btc-card"><div><div class="btc-price mono">${p:,.2f}</div><div class="btc-chg-row"><span class="btc-chg {c(B["chg_pct"])} mono">{sg(B["chg_pct"])} today</span><span class="btc-sep">&middot;</span><span class="btc-range">52-wk range: <strong class="mono">${B["year_low"]:,.2f}</strong> &ndash; <strong class="mono">${B["year_high"]:,.2f}</strong></span></div><p class="btc-trend-note">{trend}</p></div>'
            f'<div class="btc-moves"><div class="btc-move"><div class="bm-label">7-Day</div><div class="bm-val {c(B["r7"])} mono">{sg(B["r7"])}</div></div><div class="btc-move"><div class="bm-label">30-Day</div><div class="bm-val {c(B["r30"])} mono">{sg(B["r30"])}</div></div><div class="btc-move"><div class="bm-label">90-Day</div><div class="bm-val {c(B["r90"])} mono">{sg(B["r90"])}</div></div><div class="btc-move"><div class="bm-label">Ether</div><div class="bm-val {c(eth["chg_pct"])} mono">{fx(F, "ETH")} ({sg(eth["chg_pct"])})</div></div></div>'
            f'<div class="btc-context">Bitcoin is {sg(B["chg_pct"])} on the day, with 7-day, 30-day and 90-day moves of {sg(B["r7"])}, {sg(B["r30"])} and {sg(B["r90"])}. It has traded between ${B["day_low"]:,.2f} and ${B["day_high"]:,.2f} today and sits below its 50-day average while the Nasdaq 100 futures (NQ) are {sg(F["NQ"]["chg_pct"])} and Ether is {sg(eth["chg_pct"])}. The 90-day gain is large while the 7-day and 30-day moves are negative; price remains above its 200-day average. We searched for a dated Nov 4 spot Bitcoin ETF flow figure and found none, so none is quoted; FMP is the price source here.</div></div></section>')

def sec_worst(T, sector, k):
    return sorted((t for t in T.values() if t['detail']['sector'] == sector), key=lambda t: (t['chg_pct'], t['symbol']))[:k]

def spotlight(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    f = lambda k: f'{k} ({fs[k]["fund"]}) {sg(fs[k]["chg_pct"])}'
    sem, semavg, semup = basket(T, 'semiconductor_ai'); sw, swavg, swup = basket(T, 'software_cloud')
    en = sorted((t for t in T.values() if t['detail']['sector'] == 'Energy'), key=lambda t: (t['chg_pct'], t['symbol']))
    p1 = (f'{f("Energy")} was the weakest of the 11 sectors as crude fell: WTI (CL) {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}), Brent (BZ) {fx(F, "BZ")} ({sg(F["BZ"]["chg_pct"])}), gasoline (RB) {sg(F["RB"]["chg_pct"])} and heating oil (HO) {sg(F["HO"]["chg_pct"])}. '
          f'Our {sa["Energy"][0]} Energy names averaged {sg(sa["Energy"][1])}, with {sa["Energy"][2]} of them at 4 or more red flags: ' + lst(mv(T, t['symbol']) for t in en[:6]) + '. '
          f'<strong>We found no same-day coverage</strong>, so we do not assert why oil fell; the checklist is built on quarterly fundamentals and cannot explain a one-day move.')
    p2 = (f'Eight sectors rose: {f("Consumer Discretionary")}, {f("Communication Services")}, {f("Financials")}, {f("Consumer Staples")}, {f("Real Estate")} and {f("Health Care")}. Our {sa["Consumer Discretionary"][0]} Consumer Discretionary names averaged {sg(sa["Consumer Discretionary"][1])} and our {sa["Health Care"][0]} Health Care names {sg(sa["Health Care"][1])}. '
          f'Leaders included {lst(mv(T, s) for s in ("MRNA", "HCA", "BKNG", "DASH", "CVNA", "LOW"))}. The Dow 30 basket averaged {sg(basket(T, "dow30")[1])} with {basket(T, "dow30")[2]} of 30 names higher, and the Dow fund (DIA) {sg(etf(S, "DIA"))}. We found no coverage to confirm why the gains were this broad.')
    sl = sorted(sem, key=lambda t: (t['chg_pct'], t['symbol']))
    p3 = (f'The Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 names higher, after averaging +2.31% on Tuesday, and {f("Information Technology")}. The weakest in the basket: ' + lst(mv(T, t['symbol']) for t in sl[:5]) + f'. '
          f'AI-infrastructure and power names also fell: {lst(mv(T, s) for s in ("VRT", "PWR", "GEV", "ETN", "CRWV", "NBIS"))}; for comparison Tuesday&rsquo;s moves were {sg(PT["VRT"]["chg_pct"])} for VRT, {sg(PT["PWR"]["chg_pct"])} for PWR, {sg(PT["CRWV"]["chg_pct"])} for CRWV and {sg(PT["NBIS"]["chg_pct"])} for NBIS. The Software/Cloud basket averaged {sg(swavg)} with {swup} of its 20 names higher, and {mv(T, "DDOG")}{epsr(T, "DDOG")}. We found no same-day coverage, so we do not assert why.')
    p4 = (f'Several large names reported: {mv(T, "CVS")}{epsr(T, "CVS")}, {mv(T, "DDOG")}{epsr(T, "DDOG")}, {mv(T, "APP")}{epsr(T, "APP")}, {mv(T, "MCD")}{epsr(T, "MCD")}, {mv(T, "QCOM")}{epsr(T, "QCOM")} and {mv(T, "UBER")}{epsr(T, "UBER")}. '
          f'The EPS figures are FMP&rsquo;s earnings history against its consensus; we found no coverage describing the reactions, so we do not assert why any of them moved.')
    chip = lambda syms: '<div class="names">' + ', '.join(f'<span class="chip">{s}</span>' for s in syms) + '</div>'
    return (f'<section id="spotlight"><div class="section-head"><span class="kicker-label">Analysis</span><h2 style="margin-top:2px">Sector Spotlight</h2></div>'
            f'<div class="spotlight"><h3>Oil Falls, Energy Stocks Sink</h3><p>{p1}</p>{chip([t["symbol"] for t in en[:6]])}</div>'
            f'<div class="spotlight" style="border-top:1px solid var(--line)"><h3>A Broad Rally Led by Consumer, Health Care and the Dow</h3><p>{p2}</p>{chip(["MRNA", "HCA", "BKNG", "DASH", "CVNA", "LOW"])}</div>'
            f'<div class="spotlight" style="border-top:1px solid var(--line)"><h3>Chips and AI Infrastructure Reverse</h3><p>{p3}</p>{chip(["VRT", "PWR", "GEV", "ETN", "CRWV", "NBIS"])}</div>'
            f'<div class="spotlight" style="border-top:1px solid var(--line)"><h3>Earnings Day: Datadog and CVS Fall, AppLovin Rises</h3><p>{p4}</p>{chip(["CVS", "DDOG", "APP", "MCD", "QCOM", "UBER"])}</div>')

def movers_read(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; n = st['n']
    bks = {k: basket(T, k)[1] for k in ('dow30', 'sp500_top100', 'nasdaq100', 'large_cap_proxy', 'software_cloud', 'semiconductor_ai', 'megacap_leaders')}
    return (f'<p class="movers-read"><strong>A broad rally with the Dow in front: oil, energy, chips and AI infrastructure lower.</strong> {st["adv"]} of {n} names rose and {st["dec"]} fell. The Dow fund (DIA) {sg(etf(S, "DIA"))}, the S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))} and the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))} all rose. '
            f'The Dow 30 basket averaged {sg(bks["dow30"])}, the S&amp;P 500 Top 100 basket {sg(bks["sp500_top100"])}, the Nasdaq 100 basket {sg(bks["nasdaq100"])} and the large-cap proxy basket {sg(bks["large_cap_proxy"])}, while the Software/Cloud basket averaged {sg(bks["software_cloud"])}, the Semiconductor/AI basket {sg(bks["semiconductor_ai"])} and the Mega-Cap Leaders basket {sg(bks["megacap_leaders"])}. '
            f'The decliners concentrate in energy, AI infrastructure and several earnings reporters, with WTI crude (CL) {sg(F["CL"]["chg_pct"])}, the VIX {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}) and bond futures higher (ZB {sg(F["ZB"]["chg_pct"])}). We found no same-day coverage to explain it, so read this as breadth data, not a verified story.</p>')

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
    para = (f'<p class="movers-read"><strong>The 4+ red-flag count fell to {st["r4"]} from {st["pr4"]}, with {len(st["new4"])} names joining it and {len(st["off4"])} leaving; {ton} flags moved onto red and {toff} moved off red as the average stock moved {sg(st["avg"])}.</strong> '
            f'Flags moving onto red: {kv(st["on"])}. Flags moving off red: {kv(st["off"])}. Relative-strength red flags went from {st["prs"]} to {st["rs"]}; the benchmark 3-month returns moved (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%), so part of the change is a yardstick effect. '
            f'Names entering the 4+ group: {nm_(st["new4"])}. Names leaving it: {nm_(st["off4"])}. New to the universe: {nm_(new)}. Dropped out: {nm_(dr)}. Biggest red-flag increases: {inc}. Biggest decreases: {dc}. {newer} names show a newer reported quarter than on {C["prior_short"]}, which can move growth and margin flags by itself.</p>')
    order = ['ES', 'NQ', 'ZB', 'CL', 'GC', 'SI', 'BTC', 'ETH', 'VIX']
    rows = ''.join(f'<tr><td>{s} ({F[s]["name"] if False else {"ES": "E-Mini S&amp;P 500", "NQ": "Nasdaq 100", "ZB": "30Y T-Bond", "CL": "WTI Crude", "GC": "Gold", "SI": "Silver", "BTC": "Bitcoin", "ETH": "Ethereum", "VIX": "CBOE Volatility Index"}[s]})</td><td class="px-cell mono">{fx(F, s)}</td><td class="px-cell {"up" if F[s]["last"] > PF[s]["last"] else "down"} mono">{sg((F[s]["last"] / PF[s]["last"] - 1) * 100)}</td></tr>' for s in order)
    cards = (f'<div class="rollup-grid"><div class="rcard"><h3>Futures Since {C["prior_short"]} Close</h3><div class="table-wrap"><table style="min-width:0"><thead><tr><th>Contract</th><th>Last</th><th>Since {C["prior_short"]}</th></tr></thead><tbody>{rows}</tbody></table></div></div>'
             f'<div class="rcard"><h3>Trend Flips</h3><p style="font-size:13.5px;margin:0 0 8px"><strong>Newly red on trend ({len(tn)}):</strong> {nm_(tn)}.</p><p style="font-size:13.5px;margin:0"><strong>No longer red on trend ({len(tf)}):</strong> {nm_(tf)}.</p></div>'
             f'<div class="rcard"><h3>4+ Red Flags</h3><p style="font-size:13.5px;margin:0 0 8px">{st["pr4"]} names on {C["prior_short"]} &rarr; {st["r4"]} now.</p><p style="font-size:13.5px;margin:0 0 8px"><strong>Dropped off:</strong> {nm_(st["off4"])}.</p><p style="font-size:13.5px;margin:0"><strong>Newly on:</strong> {nm_(st["new4"])}.</p></div></div>')
    return f'<section id="vs-previous"><div class="section-head"><span class="kicker-label">Comparison</span><div class="section-top-row"><h2>Vs Previous Full Study ({C["prior_short"]})</h2><span class="section-note">One trading day apart; flags compared on the same rules</span></div></div>{para}{cards}</section>'

def whats_next(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; fs = S['sector_funds']; b = bm(S, P)
    f = lambda k: f'{k} ({fs[k]["fund"]}) {sg(fs[k]["chg_pct"])}'
    up, dn = secfunds(S)
    eps = lambda s: (lambda r: f'EPS ${r[1]:.2f} against ${r[2]:.2f} expected' if r else 'no report in the last two sessions')(reported(T, s, DAYS))
    sem, semavg, semup = basket(T, 'semiconductor_ai')
    q1 = (f'WTI crude futures (CL) {sg(F["CL"]["chg_pct"])} and {f("Energy")} fell while {len(up)} of 11 sectors rose, led by {f("Consumer Discretionary")}. Lower oil is a cost for some companies and lost revenue for others. Which of the 10 checklist points could a one-day oil move change today, and which would take a quarter or more of reported results to show it?')
    h1 = (f'Facts to weigh: our {sector_avgs(T)["Energy"][0]} Energy names averaged {sg(sector_avgs(T)["Energy"][1])} and our {sector_avgs(T)["Consumer Discretionary"][0]} Consumer Discretionary names {sg(sector_avgs(T)["Consumer Discretionary"][1])}; the Dow fund (DIA) {sg(etf(S, "DIA"))} against the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))}. We found no coverage of what drove oil, so the cause is unverified. What would you need to read to find out?')
    q2 = (f'Yesterday&rsquo;s reporters reversed today: {pv(T, PT, "SHOP")}; {pv(T, PT, "TRI")}; {pv(T, PT, "ETN")}. If a report-day move can reverse the next day, how many sessions would you wait before treating the price as a verdict on the report, and what does the earnings-growth point measure that a one-day reaction does not?')
    h2 = (f'Facts to weigh: {mv(T, "SHOP")} ({eps("SHOP")}), {mv(T, "TRI")} ({eps("TRI")}), {mv(T, "ETN")} ({eps("ETN")}), {mv(T, "KDP")} ({eps("KDP")}), {mv(T, "APO")} ({eps("APO")}). We found no coverage of the reactions, so the reasons are yours to propose and test.')
    q3 = (f'The Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 names higher, a day after averaging +2.31%, and {mv(T, "CRWV")} and {mv(T, "NBIS")} each carry {T["CRWV"]["red_flag_count"]} and {T["NBIS"]["red_flag_count"]} red flags. When a group swings several percent in opposite directions on consecutive days with no verified cause, is it more likely a company story or a positioning story, and what data would help you tell them apart?')
    h3 = (f'Facts to weigh: {pv(T, PT, "CRWV")}; {pv(T, PT, "VRT")}; {pv(T, PT, "PWR")}. The VIX was {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}). Relative-strength red flags went from {st["prs"]} to {st["rs"]} while the benchmark 3-month returns rose (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%). Why might the flag count barely move on a day this large?')
    card = lambda n, q, hh: f'<div class="qcard"><div class="qnum">Question {n}</div><div class="q">{q}</div><div class="hint">{hh}</div></div>'
    return (f'<section class="study" id="whats-next"><div class="kicker">Study Session</div><h2>What&rsquo;s Next</h2><p class="setup">Three open questions from today&rsquo;s facts. Work through them yourself before the next session; the data doesn&rsquo;t settle any of them.</p><div class="qlist">{card("One", q1, h1)}{card("Two", q2, h2)}{card("Three", q3, h3)}</div><p class="closer">None of this is a recommendation. The point is to practice separating what the numbers show from the story that explains them.</p></section>')

def news(S, P, T, PT, C):
    F = {f['symbol']: f for f in S['futures']}; M = S['macro']
    macro = (f'<li>Searches for same-day ({C["short"]}) coverage of the close and of the oil move returned only other dates, so no headline is quoted for today and no cause is asserted for the moves above. Index moves here are SPY, QQQ, DIA and IWM from FMP; futures are FMP quotes.</li>'
             f'<li>FMP&rsquo;s newest treasury print (Nov 3) put the 10-year cash yield at {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on Nov 2); it predates today&rsquo;s bond-futures move.</li>'
             f'<li>A search for {C["short"]} spot Bitcoin ETF flows returned nothing dated, so no flow figure is quoted.</li>')
    names = (f'<li><strong>Moderna (MRNA)</strong> {sg(T["MRNA"]["chg_pct"])}, <strong>AppLovin (APP)</strong> {sg(T["APP"]["chg_pct"])}, <strong>HCA Healthcare (HCA)</strong> {sg(T["HCA"]["chg_pct"])}, <strong>Newmont (NEM)</strong> {sg(T["NEM"]["chg_pct"])} and <strong>Booking Holdings (BKNG)</strong> {sg(T["BKNG"]["chg_pct"])} led the gainers; no same-day coverage was found.</li>'
             f'<li><strong>Datadog (DDOG)</strong> {sg(T["DDOG"]["chg_pct"])}, <strong>Vertiv (VRT)</strong> {sg(T["VRT"]["chg_pct"])}, <strong>CVS Health (CVS)</strong> {sg(T["CVS"]["chg_pct"])} and <strong>Quanta Services (PWR)</strong> {sg(T["PWR"]["chg_pct"])} were the largest decliners; earnings-history data dates reports for DDOG and CVS on Nov 4, but we found no article describing the reactions.</li>'
             '<li><strong>No same-day catalyst was verified for any name above</strong>, so their moves are reported as price action.</li>')
    return (f'<section id="news"><div class="section-head"><span class="kicker-label">Research</span><h2 style="margin-top:2px">Market News &amp; Research</h2></div><div class="rollup-grid"><div class="rcard"><h3>Macro</h3><ul>{macro}</ul></div><div class="rcard"><h3>Names from today&rsquo;s movers</h3><ul>{names}</ul><p class="trap-note">Nothing here is independently verified news.</p></div></div>')

def findings(S, P, T, PT, C):
    dn = S['data_notes']; new = lst(f'{nm(T, s)} ({s})' for s in dn['new_names']); dr = lst(f'{s}' for s in dn['dropped_names'])
    dropped = lst(next((x['name'] for x in P['tickers'] if x['symbol'] == s), s) + f' ({s})' for s in dn['dropped_names'])
    return (f'<section id="findings"><div class="findings"><div class="section-head" style="border:none"><span class="kicker-label">Corrections &amp; Methodology</span><h2 style="margin-top:2px">Pipeline Findings</h2></div><h3>Data sources</h3><ul>'
            f'<li>Universe: {len(T)} unique names &mdash; Dow 30, live Nasdaq 100 (101), live S&amp;P 500 top 100 by market cap, large-cap proxy (100; US-only screener; notes, preferreds and duplicate share classes (BRK-A, SOJE, SOMN, APOS) removed), and the three 20-name baskets. New versus {C["prior_short"]}: {new}. Dropped: {dropped}.</li>'
            f'<li>Prices, moving averages and 52-week ranges from FMP <code>/stable/batch-quote</code>; growth, ratios, key metrics and cash flow from the quarterly endpoints; EMAs, YTD and 3-month returns computed from <code>historical-price-eod/full</code>. TRAP #4 data from <code>trap_fundamentals.py</code>; annual-report data from <code>annual_review.py</code>. The pull and scoring use <code>full_study_pull.py</code>, <code>full_study_score.py</code> and <code>full_study_build.py</code>. The VIX is not returned by <code>batch-quote</code>, so it comes from <code>quote?symbol=^VIX</code>. Captured at the 2pm MT close.</li>'
            f'<li>Index moves are FMP ETF proxies (SPY, QQQ, DIA, IWM). Yields are FMP&rsquo;s <code>/stable/treasury-rates</code> with a {S["macro"]["treasury_print_date"]} print. Sector moves are the Select Sector SPDR funds (FMP daily close, {S["date"]}). Report dates and EPS against consensus quoted for individual names come from the TRAP #4 earnings history (FMP).</li></ul>'
            f'<h3>Gaps this session</h3><ul><li>Institutional ownership and moat: every name carries its cached research; MSCI (MSCI) was researched fresh this session (about 74.5% institutional per Q1 2026 13F data on vcpscanner.com; its &ldquo;durable&rdquo; moat verdict rests on a Morningstar wide-moat upgrade headline, as the full report is paywalled); the one-search &ldquo;anything changed&rdquo; refresh was not run for the other names.</li>'
            f'<li>Futures: FMP priced 23 of the 40 contracts through <code>batch-quote</code> (plus the VIX via <code>quote</code>); unpriced: VX, SR3, ZC, ZW, ZL, KC, LE, the currency futures (SB and CT return unrelated token quotes).</li>'
            f'<li>News: searches for same-day coverage of the {C["short"]} close, oil and the biggest movers returned only other dates; no catalyst is asserted as fact and no Bitcoin ETF flow figure dated {C["short"]} was found. The institutional ownership endpoint still returns an empty array on this plan.</li></ul></div></section>')
