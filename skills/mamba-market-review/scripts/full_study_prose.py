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
OV = {'HONA': 'Honeywell Aerospace', 'BRK-B': 'Berkshire Hathaway', 'SPCX': 'Space Exploration Technologies', 'GEHC': 'GE HealthCare', 'CME': 'CME Group', 'TSM': 'Taiwan Semiconductor', 'ODFL': 'Old Dominion Freight Line', 'AJG': 'Arthur J. Gallagher', 'WM': 'Waste Management', 'HOOD': 'Robinhood Markets', 'ITW': 'Illinois Tool Works', 'META': 'Meta Platforms', 'MDT': 'Medtronic', 'LHX': 'L3Harris', 'AMZN': 'Amazon', 'BDX': 'Becton Dickinson', 'MCO': "Moody's", 'GOOG': 'Alphabet (Class C)', 'GOOGL': 'Alphabet (Class A)', 'FTNT': 'Fortinet', 'NOW': 'ServiceNow', 'ADP': 'Automatic Data Processing', 'COF': 'Capital One', 'SNDK': 'SanDisk', 'VRT': 'Vertiv', 'NET': 'Cloudflare', 'TTWO': 'Take-Two Interactive', 'LITE': 'Lumentum', 'BSX': 'Boston Scientific', 'TER': 'Teradyne', 'ON': 'ON Semiconductor', 'WELL': 'Welltower', 'PWR': 'Quanta Services', 'XOM': 'Exxon Mobil', 'MPC': 'Marathon Petroleum', 'DDOG': 'Datadog', 'MRNA': 'Moderna', 'HCA': 'HCA Healthcare', 'NEM': 'Newmont', 'BKNG': 'Booking Holdings', 'MMM': '3M', 'CVNA': 'Carvana', 'LOW': "Lowe's", 'DELL': 'Dell Technologies', 'GEV': 'GE Vernova', 'STX': 'Seagate Technology', 'EOG': 'EOG Resources', 'COP': 'ConocoPhillips', 'MCD': "McDonald's", 'GWW': 'W.W. Grainger', 'MCK': 'McKesson', 'QCOM': 'Qualcomm', 'UBER': 'Uber Technologies', 'APP': 'AppLovin', 'EPD': 'Enterprise Products Partners'}
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






DAYS = ('2026-11-19', '2026-11-20')
def epsr(T, s):
    r = reported(T, s, DAYS); m = lambda v: ('-' if v < 0 else '') + f'${abs(v):.2f}'; return f' (FMP dates its report {r[0][5:].replace("-", "/")}, EPS {m(r[1])} against {m(r[2])} expected)' if r else ''

def pv(T, PT, s): return f'{mv(T, s)} (Thursday: {sg(PT[s]["chg_pct"])})'
def pm(PT, s): return f'{nm(PT, s)} ({s}) {sg(PT[s]["chg_pct"])}'
OV.update({'ANT': 'Anthropic', 'NBIS': 'Nebius Group', 'CRWV': 'CoreWeave', 'PDD': 'PDD Holdings', 'VTR': 'Ventas', 'PANW': 'Palo Alto Networks', 'WDC': 'Western Digital', 'AXON': 'Axon Enterprise', 'FANG': 'Diamondback Energy', 'RCL': 'Royal Caribbean', 'DASH': 'DoorDash', 'SHOP': 'Shopify',
           'SNDK': 'SanDisk', 'ALAB': 'Astera Labs', 'ARM': 'Arm Holdings', 'MU': 'Micron Technology', 'AMD': 'AMD', 'AVGO': 'Broadcom', 'MRVL': 'Marvell Technology', 'MPWR': 'Monolithic Power Systems', 'ANET': 'Arista Networks', 'GLW': 'Corning', 'RKLB': 'Rocket Lab', 'AMAT': 'Applied Materials',
           'HUM': 'Humana', 'UNH': 'UnitedHealth', 'ELV': 'Elevance Health', 'T': 'AT&amp;T', 'TMUS': 'T-Mobile US', 'VZ': 'Verizon', 'CL': 'Colgate-Palmolive', 'AMT': 'American Tower', 'KDP': 'Keurig Dr Pepper', 'CMG': 'Chipotle Mexican Grill', 'WCN': 'Waste Connections', 'INTU': 'Intuit', 'TSLA': 'Tesla', 'DE': 'Deere', 'TDG': 'TransDigm'})
SRC = '<a href="https://finance.biggo.com/news/b30cb73c-880a-4d83-a70a-39e03bb6b924" target="_blank" rel="noopener">BigGo Finance &#8599;</a>'
SRC2 = '<a href="https://fool.com/investing/2026/11/20/why-nvidia-stock-is-down-today" target="_blank" rel="noopener">Motley Fool &#8599;</a>'
SRC3 = '<a href="https://www.forbes.com/sites/siladityaray/2026/11/20/nvidia-rival-amd-shares-slump-again-after-short-seller-says-it-has-its-own-china-problem/" target="_blank" rel="noopener">Forbes &#8599;</a>'
SRC4 = '<a href="https://cnbc.com/2026/11/19/amd-falls-on-short-seller-report-of-alleged-china-exposure.html" target="_blank" rel="noopener">CNBC &#8599;</a>'
SRC5 = '<a href="https://finance.yahoo.com/markets/stocks/articles/wall-street-ends-sharply-lower-213427908.html" target="_blank" rel="noopener">Yahoo Finance &#8599;</a>'
CAUSE = ('Outside the Anthropic, NVIDIA, AMD and Humana stories linked here, we found no dated coverage explaining individual moves, so no cause is stated for them.')
def worst(T, k, key=None):
    v = [t for t in T.values() if key is None or key(t)]
    return sorted(v, key=lambda t: (t['chg_pct'], t['symbol']))[:k]
def names_or_none(T, ss): return lst(f'{nm(T, s)} ({s})' for s in ss) or 'none'
def nxt(T, s):
    d = T[s]['detail'].get('next_earnings_date'); return d[5:].replace('-', '/') if d else 'not dated by FMP'
CHIPS = ("NVDA", "AMD", "MU", "AVGO", "ARM", "ALAB", "MRVL", "MPWR", "AMAT")
STORE = ("SNDK", "STX", "WDC", "LITE", "ANET", "DELL", "GLW")
DEF = ("HCA", "UNH", "HUM", "ELV", "JNJ")
TEL = ("T", "TMUS", "VZ", "AMT")
STAP = ("CL", "WMT", "KDP", "PEP")
def ipo(T): return T['ANT']['price'] / 83.0
def lead(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; st = stats(S, P, T, PT); n = st['n']; B = S['bitcoin']; M = S['macro']; b = bm(S, P)
    up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    sem, semavg, semup = basket(T, 'semiconductor_ai'); sw, swavg, swup = basket(T, 'software_cloud'); mg, mgavg, mgup = basket(T, 'megacap_leaders')
    allsec = sorted(up + dn, reverse=True)
    nup = len([1 for c, k, f in allsec if c > 0])
    p1 = (f'<p class="intro"><strong>The AI selloff turned into a rout: the chip names fell hardest, the VIX closed at {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}) and {st["dec"]} of {n} names fell.</strong> The S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))}, the Dow fund (DIA) {sg(etf(S, "DIA"))} and the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))}. '
          f'<strong>{st["adv"]} of {n} names advanced ({st["adv"] / n * 100:.1f}%)</strong>, and the average move was {sg(st["avg"])}, against {sg(st["pavg"])} on Thursday. '
          f'S&amp;P 500 futures (ES) {fx(F, "ES")} ({sg(F["ES"]["chg_pct"])}), Nasdaq 100 futures (NQ) {fx(F, "NQ")} ({sg(F["NQ"]["chg_pct"])}), Mini Dow (YM) {fx(F, "YM")} ({sg(F["YM"]["chg_pct"])}) and Russell 2000 (RTY) {fx(F, "RTY")} ({sg(F["RTY"]["chg_pct"])}). '
          f'Coverage said the Nasdaq Composite erased its 2026 gain and the S&amp;P 500 closed out the week in correction territory, with Anthropic&rsquo;s second-day slide, Fed officials signaling further rate increases and NVIDIA&rsquo;s leadership turmoil all cited ({SRC}; {SRC5}). '
          f'<strong>{mv(T, "ANT")}, closing at ${T["ANT"]["price"]:,.2f}, {(ipo(T) - 1) * 100:.2f}% above its $83.00 IPO price.</strong> '
          f'<strong>Bonds rallied</strong>: FMP&rsquo;s cash Treasury print for today has the 10-year at {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on {M["ust10y_prev_date"][5:].replace("-", "/")}), the 2-year at {M["ust2y"]:.2f}% and the 30-year at {M["ust30y"]:.2f}%, and 30-year bond futures (ZB) were {fx(F, "ZB")} ({sg(F["ZB"]["chg_pct"])}). The dollar index (DX) was {fx(F, "DX")} ({sg(F["DX"]["chg_pct"])}). '
          f'Crude rose while metals sold off again: WTI crude (CL) {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}), Brent (BZ) {fx(F, "BZ")} ({sg(F["BZ"]["chg_pct"])}), gold (GC) {fx(F, "GC")} ({sg(F["GC"]["chg_pct"])}) and silver (SI) {fx(F, "SI")} ({sg(F["SI"]["chg_pct"])}). '
          f'<strong>Bitcoin is ${B["price"]:,.2f} ({sg(B["chg_pct"])})</strong>, {sg(B["r7"])} over seven days, and Ether {fx(F, "ETH")} ({sg(F["ETH"]["chg_pct"])}).</p>')
    wk = worst(T, 8); ld = sorted(T.values(), key=lambda t: (-t['chg_pct'], t['symbol']))[:8]
    p2 = (f'<p class="intro"><strong>{nup} of 11 S&amp;P 500 sectors rose: {allsec[0][1]} ({allsec[0][2]}) {sg(allsec[0][0])} was the only gainer, and {allsec[-1][1]} ({allsec[-1][2]}) {sg(allsec[-1][0])} was the weakest by far.</strong> By sector, <strong>' + lst(f'{k} ({f}) {sg(c)}' for c, k, f in allsec) + '</strong>. '
          f'Our {sa["Information Technology"][0]} Information Technology names averaged {sg(sa["Information Technology"][1])}, our {sa["Health Care"][0]} Health Care names {sg(sa["Health Care"][1])} and our {sa["Consumer Staples"][0]} Consumer Staples names {sg(sa["Consumer Staples"][1])}. '
          f'<strong>The Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 names up</strong>; the Software/Cloud basket averaged {sg(swavg)} with {swup} of 20 up, and the Mega-Cap Leaders basket {sg(mgavg)} with {mgup} of 20 up. The Nasdaq 100 basket averaged {sg(basket(T, "nasdaq100")[1])} and the Dow 30 basket {sg(basket(T, "dow30")[1])} ({basket(T, "dow30")[2]} of 30 names rose). '
          f'The market leaders: {lst(mv(T, s) for s in ("NVDA", "MSFT", "AAPL", "GOOGL", "META", "AMZN", "AVGO", "TSLA"))}. '
          f'<strong>The gainers were defensive</strong>: ' + lst(mv(T, t['symbol']) for t in ld) + '. '
          f'<strong>The weakest names</strong>: ' + lst(mv(T, t['symbol']) for t in wk) + '.</p>')
    of = names_or_none(T, st['off4']); nw = names_or_none(T, st['new4'])
    inc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['inc'][:4])
    dc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['dec_'][:4]) or 'none'
    tr = sum(t['flags']['trend'] == 'red' for t in T.values()); ptr = sum(t['flags']['trend'] == 'red' for t in PT.values())
    new = S['data_notes']['new_names']; dr = S['data_notes']['dropped_names']
    drn = lst(next((x['name'] for x in P['tickers'] if x['symbol'] == s), s).replace(', Inc.', '').replace(' Inc.', '') + f' ({s})' for s in dr) or 'none'
    p3 = (f'<p class="intro">On the checklist, <strong>{st["r4"]} of {n} names carry 4 or more red flags, against {st["pr4"]} on Thursday</strong> ({st["z"]} names are clean, against {st["pz"]}). Trend red flags went from {ptr} to {tr}, while relative-strength red flags fell from {st["prs"]} to {st["rs"]} because the benchmarks themselves fell (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}% over three months). Names moving onto the 4+ list: {nw}. Names leaving it: {of}. '
          f'The biggest increases: {inc}. The biggest decreases: {dc}. New to the universe: {names_or_none(T, new)}; dropped out: {drn}. '
          f'Bitcoin was ${B["price"]:,.2f} ({sg(B["chg_pct"])}) at the close, {abs((B["price"] / B["avg200"] - 1) * 100):.1f}% {"below" if B["price"] < B["avg200"] else "above"} its 200-day average and {abs((B["price"] / B["avg50"] - 1) * 100):.1f}% {"below" if B["price"] < B["avg50"] else "above"} its 50-day.</p>')
    pulls = [(f'${T["ANT"]["price"]:,.2f}', 'Anthropic (ANT) Second-Day Close'), (f'{st["adv"]} / {n}', 'Names Advancing'), (fx(F, "VIX"), 'VIX at the Close'), (f'{st["r4"]} / {n}', 'Names With 4+ Red Flags')]
    pr = '<div class="pull-row">' + ''.join(f'<div class="pull"><div class="pn mono">{a}</div><div class="pl">{b_}</div></div>' for a, b_ in pulls) + '</div>'
    return p1 + p2 + p3 + pr

def macro(S, P, F, C):
    M = S['macro']; B = S['bitcoin']; ff = lambda s: f'{fx(F, s)} ({sg(F[s]["chg_pct"])})'; T = S_T(S)
    return (f'<section><div class="section-head"><div class="section-top-row"><span class="kicker-label">Setup</span></div><h2 style="margin-top:2px">Macro Backdrop</h2><span class="section-note">2:00pm MT, {C["long_label"]} (close). FMP futures quotes; daily % versus the prior settle. Yields are FMP&rsquo;s treasury print for {M["treasury_print_date"]}.</span></div><div class="macro-grid">'
            f'<div class="mcard"><h3>Rates &amp; the Fed</h3><p class="big">A flight to bonds</p><p>Cash Treasury yields (FMP, {M["treasury_print_date"]} print): 2-year {M["ust2y"]:.2f}%, 10-year {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on {M["ust10y_prev_date"][5:].replace("-", "/")}), 30-year {M["ust30y"]:.2f}%. Futures: 30-year bond futures (ZB) {ff("ZB")}, 10-year note futures (ZN) {ff("ZN")}, 5-year (ZF) {ff("ZF")}, 2-year (ZT) {ff("ZT")}. Coverage said Fed officials signaled further rate increases ({SRC}), yet yields fell on the day as money moved into bonds.</p></div>'
            f'<div class="mcard"><h3>Equities</h3><p class="big red">Correction territory</p><p>S&amp;P 500 futures (ES) {ff("ES")}, Nasdaq 100 futures (NQ) {ff("NQ")}, Mini Dow (YM) {ff("YM")}, Russell 2000 (RTY) {ff("RTY")}. The VIX is {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}). {mv(T, "ANT")} on its second day ({SRC}); {mv(T, "NVDA")} amid its leadership turmoil ({SRC2}); {mv(T, "AMD")} as the short-seller dispute continued ({SRC3}).</p></div>'
            f'<div class="mcard"><h3>Oil &amp; Energy</h3><p class="big">Crude up, energy held</p><p>WTI (CL) {ff("CL")}, Brent (BZ) {ff("BZ")}, RBOB gasoline (RB) {ff("RB")}, heating oil (HO) {ff("HO")}, natural gas (NG) {ff("NG")}. The Energy sector fund (XLE) {sg(S["sector_funds"]["Energy"]["chg_pct"])} lost less than the S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}.</p></div>'
            f'<div class="mcard"><h3>Metals, Dollar &amp; Crypto</h3><p class="big red">Metals and crypto hit hard</p><p>Gold (GC) {ff("GC")}, silver (SI) {ff("SI")}, platinum (PL) {ff("PL")}, palladium (PA) {ff("PA")}, copper (HG) {ff("HG")}; soybean meal (ZM) {ff("ZM")}; cocoa (CC) {ff("CC")}; dollar index (DX) {ff("DX")}. Bitcoin (BTC) {ff("BTC")}, Ether (ETH) {ff("ETH")}.</p></div></div></section>')

def bitcoin(S, F, C):
    B = S['bitcoin']; p = B['price']; v200 = (p / B['avg200'] - 1) * 100; v50 = (p / B['avg50'] - 1) * 100; fromhi = (1 - p / B['year_high']) * 100
    c = lambda x: 'up' if x > 0 else 'down'
    assert p < B['avg200'] and p < B['avg50']
    trend = f'Price is below both its 50-day and 200-day averages (50-day <strong class="mono">${B["avg50"]:,.2f}</strong>, 200-day <strong class="mono">${B["avg200"]:,.2f}</strong>): {abs(v200):.1f}% below the 200-day, {abs(v50):.1f}% below the 50-day and {fromhi:.1f}% below the 52-week high.'
    eth = F['ETH']; T = S_T(S); lo = (p / B['year_low'] - 1) * 100
    return (f'<section id="bitcoin"><div class="section-head"><div class="section-top-row"><span class="kicker-label">Crypto</span><h2>Bitcoin</h2><span class="section-note">Live price at 2:00pm MT ({C["today_label"]}); BTC trades 24/7, so later prices will differ. 52-wk range and 50d/200d averages from FMP <code class="mono">quote</code>; 7/30/90-day moves from <code class="mono">historical-price-eod/full?symbol=BTCUSD</code>.</span></div></div>'
            f'<div class="btc-card"><div><div class="btc-price mono">${p:,.2f}</div><div class="btc-chg-row"><span class="btc-chg {c(B["chg_pct"])} mono">{sg(B["chg_pct"])} today</span><span class="btc-sep">&middot;</span><span class="btc-range">52-wk range: <strong class="mono">${B["year_low"]:,.2f}</strong> &ndash; <strong class="mono">${B["year_high"]:,.2f}</strong></span></div><p class="btc-trend-note">{trend}</p></div>'
            f'<div class="btc-moves"><div class="btc-move"><div class="bm-label">7-Day</div><div class="bm-val {c(B["r7"])} mono">{sg(B["r7"])}</div></div><div class="btc-move"><div class="bm-label">30-Day</div><div class="bm-val {c(B["r30"])} mono">{sg(B["r30"])}</div></div><div class="btc-move"><div class="bm-label">90-Day</div><div class="bm-val {c(B["r90"])} mono">{sg(B["r90"])}</div></div><div class="btc-move"><div class="bm-label">Ether</div><div class="bm-val {c(eth["chg_pct"])} mono">{fx(F, "ETH")} ({sg(eth["chg_pct"])})</div></div></div>'
            f'<div class="btc-context">Bitcoin is {sg(B["chg_pct"])} on the day, with 7-day, 30-day and 90-day moves of {sg(B["r7"])}, {sg(B["r30"])} and {sg(B["r90"])}. It traded between ${B["day_low"]:,.2f} and ${B["day_high"]:,.2f} today and sits only {lo:.1f}% above its 52-week low of ${B["year_low"]:,.2f}. The stocks tied to it: Strategy (MSTR) {sg(T["MSTR"]["chg_pct"])} and Robinhood Markets (HOOD) {sg(T["HOOD"]["chg_pct"])}. It fell with the stock market rather than acting as a refuge, while bonds rallied. We found no dated spot Bitcoin ETF flow figure for today, so none is quoted; FMP is the price source here.</div></div></section>')
def S_T(S): return {t['symbol']: t for t in S['tickers']}


def spotlight(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    f = lambda k: f'{k} ({fs[k]["fund"]}) {sg(fs[k]["chg_pct"])}'
    sw, swavg, swup = basket(T, 'software_cloud'); sem, semavg, semup = basket(T, 'semiconductor_ai')
    a = T['ANT']; d = a['detail']
    p1 = (f'{f("Information Technology")} was the worst sector fund by a wide margin. The chipmakers led: {lst(mv(T, s) for s in CHIPS)}. The Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 names up, and our {sa["Information Technology"][0]} Information Technology names averaged {sg(sa["Information Technology"][1])}. '
          f'NVIDIA is down seven sessions running, and coverage tied today&rsquo;s drop to the leadership turmoil since its CEO resigned on Nov. 12 and to Anthropic&rsquo;s IPO failing to restore faith in the AI trade ({SRC2}). AMD extended Thursday&rsquo;s fall after the Hunterbrook short report alleging China ties, which AMD disputes ({SRC4}; {SRC3}). {pv(T, PT, "AMD")}.')
    p2 = (f'Storage, networking and optical names fell nearly as hard: {lst(mv(T, s) for s in STORE)}, along with the AI cloud names {mv(T, "NBIS")} and {mv(T, "CRWV")}. '
          f'{mv(T, "ANT")} on its second day; it closed at ${a["price"]:,.2f}, still {(ipo(T) - 1) * 100:.2f}% above its $83.00 IPO price but well below Thursday&rsquo;s high of ${d["year_high"]:,.2f} ({SRC}). '
          f'Software fell too: the Software/Cloud basket averaged {sg(swavg)}, and {mv(T, "INTU")}{epsr(T, "INTU")}; we found no dated coverage of the reaction to its report.')
    p3 = (f'The money that stayed in stocks went to defensive names. Health care insurers and hospitals led: {lst(mv(T, s) for s in DEF)}, against {f("Health Care")}; our {sa["Health Care"][0]} Health Care names averaged {sg(sa["Health Care"][1])}. Coverage tied Humana&rsquo;s gain to proposed Medicare Advantage changes ({SRC}). '
          f'Telecom and towers rose: {lst(mv(T, s) for s in TEL)}. Consumer staples held up: {lst(mv(T, s) for s in STAP)}, with {f("Consumer Staples")} the only sector fund up; Walmart reported Thursday{epsr(T, "WMT")}.')
    chip = lambda syms: '<div class="names">' + ', '.join(f'<span class="chip">{s}</span>' for s in syms) + '</div>'
    bt = ' style="border-top:1px solid var(--line)"'
    sec = lambda t, body, names, first=False: f'<div class="spotlight"{"" if first else bt}><h3>{t}</h3><p>{body}</p>{chip(names)}</div>'
    return (f'<section id="spotlight"><div class="section-head"><span class="kicker-label">Analysis</span><h2 style="margin-top:2px">Sector Spotlight</h2></div>'
            + sec('Chipmakers Lead the AI Rout', p1, list(CHIPS), True)
            + sec('Storage, Networking, AI Cloud and Anthropic', p2, list(STORE) + ["NBIS", "CRWV", "ANT", "INTU"])
            + sec('Defensives Take the Money', p3, list(DEF) + list(TEL) + list(STAP)))

def movers_read(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; n = st['n']
    bks = {k: basket(T, k)[1] for k in ('dow30', 'sp500_top100', 'nasdaq100', 'large_cap_proxy', 'software_cloud', 'semiconductor_ai', 'megacap_leaders')}
    return (f'<p class="movers-read"><strong>A one-way day for AI hardware, and a rotation into defensives.</strong> {st["adv"]} of {n} names rose and {st["dec"]} fell, and the average move was {sg(st["avg"])}. The S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))}, the Dow fund (DIA) {sg(etf(S, "DIA"))} and the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))}. '
            f'The Dow 30 basket averaged {sg(bks["dow30"])}, the S&amp;P 500 Top 100 basket {sg(bks["sp500_top100"])}, the Nasdaq 100 basket {sg(bks["nasdaq100"])} and the large-cap proxy basket {sg(bks["large_cap_proxy"])}, while the Software/Cloud basket averaged {sg(bks["software_cloud"])}, the Semiconductor/AI basket {sg(bks["semiconductor_ai"])} and the Mega-Cap Leaders basket {sg(bks["megacap_leaders"])}. '
            f'Every one of the top 10 losers is a chip, storage, networking or AI cloud name; the top 10 gainers are health care, telecom, towers and consumer staples. The VIX was {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}). {CAUSE}</p>')

def rollup(S, P, T, PT, C):
    R = S['rollup']
    li = lambda s, extra='': f'<li><strong>{e(s)}</strong> &middot; {e(T[s]["name"])} {sg(T[s]["chg_pct"])} ({T[s]["red_flag_count"]} red){extra}</li>'
    mv_ = ''.join(li(s) for s in R['movers']); mr = ''.join(li(s) for s in R['multi_red_flag'][:8])
    imp = ''.join(f'<li><strong>{e(s)}</strong> &middot; {e(T[s]["name"])} ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]} of 10 red)</li>' for s in R['improving']) or '<li>No name lost a red flag since the last study.</li>'
    new = set(S['data_notes']['new_names']); newly = {s for s in T if T[s]['red_flag_count'] >= 4 and s in PT and PT[s]['red_flag_count'] < 4}
    w = ''
    for s in R['watchlist']:
        if s not in T:
            w += f'<li><strong>{e(s)}</strong> &middot; &#9733; on your watchlist, but not in today&rsquo;s scanned universe</li>'; continue
        tag = ' &middot; &#9733; on your watchlist' if s not in newly and s not in new else (' &middot; newly at 4+ red' if s in newly else ' &middot; new to the universe')
        if s in new and s not in newly: tag = ' &middot; new to the universe'
        w += li(s, tag)
    return (f'<section id="rollup"><div class="section-head"><span class="kicker-label">Digest</span><h2 style="margin-top:2px">Roll-Up</h2></div><div class="rollup-grid"><div class="rcard"><h3>Notable Movers (|% chg|)</h3><ul>{mv_}</ul></div>'
            f'<div class="rcard"><h3>Multiple Red Flags (top 8 shown; {len(R["multi_red_flag"])} at 4+)</h3><ul>{mr}</ul></div><div class="rcard"><h3>Improving vs {C["prior_short"]}</h3><ul>{imp}</ul></div><div class="rcard watch"><h3>Watchlist for Next Session</h3><ul>{w}</ul></div></div></section>')

def vs_previous(S, P, T, PT, F, PF, C):
    st = stats(S, P, T, PT); b = bm(S, P)
    nm_ = lambda ss: lst(f'{nm(T if s in T else {s: next(x for x in P["tickers"] if x["symbol"] == s)}, s)} ({s})' for s in ss) or 'none'
    inc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['inc']) or 'none'
    dc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['dec_']) or 'none'
    new = S['data_notes']['new_names']; dr = S['data_notes']['dropped_names']
    newer = sum(1 for s in T if s in PT and T[s]['detail'].get('latest_fiscal_period') != PT[s]['detail'].get('latest_fiscal_period'))
    ton = sum(st['on'].values()); toff = sum(st['off'].values())
    tn = sorted(s for s in T if s in PT and PT[s]['flags']['trend'] != 'red' and T[s]['flags']['trend'] == 'red'); tf = sorted(s for s in T if s in PT and PT[s]['flags']['trend'] == 'red' and T[s]['flags']['trend'] != 'red')
    para = (f'<p class="movers-read"><strong>The 4+ red-flag count {"rose" if st["r4"]>st["pr4"] else "fell" if st["r4"]<st["pr4"] else "held"} to {st["r4"]} from {st["pr4"]}, with {len(st["new4"])} names joining it and {len(st["off4"])} leaving; {ton} flags moved onto red and {toff} moved off red as the average stock moved {sg(st["avg"])}.</strong> '
            f'Flags moving onto red: {kv(st["on"]) or "none"}. Flags moving off red: {kv(st["off"]) or "none"}. Relative-strength red flags went from {st["prs"]} to {st["rs"]}; the benchmark 3-month returns moved (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%), so a stock that held up better than a falling benchmark loses its red flag without rising. '
            f'Names entering the 4+ group: {nm_(st["new4"])}. Names leaving it: {nm_(st["off4"])}. New in the universe: {nm_(new)}. Dropped out: {nm_(dr)}. Biggest red-flag increases: {inc}. Biggest decreases: {dc}. {newer} names show a newer reported quarter than on {C["prior_short"]}, which can move growth and margin flags by itself.</p>')
    order = ['ES', 'NQ', 'ZB', 'CL', 'GC', 'SI', 'BTC', 'ETH', 'VIX']
    rows = ''.join(f'<tr><td>{s} ({ {"ES": "E-Mini S&amp;P 500", "NQ": "Nasdaq 100", "ZB": "30Y T-Bond", "CL": "WTI Crude", "GC": "Gold", "SI": "Silver", "BTC": "Bitcoin", "ETH": "Ethereum", "VIX": "CBOE Volatility Index"}[s]})</td><td class="px-cell mono">{fx(F, s)}</td><td class="px-cell {"up" if F[s]["last"] > PF[s]["last"] else "down"} mono">{sg((F[s]["last"] / PF[s]["last"] - 1) * 100)}</td></tr>' for s in order)
    cards = (f'<div class="rollup-grid"><div class="rcard"><h3>Futures Since {C["prior_short"]} Close</h3><div class="table-wrap"><table style="min-width:0"><thead><tr><th>Contract</th><th>Last</th><th>Since {C["prior_short"]}</th></tr></thead><tbody>{rows}</tbody></table></div></div>'
             f'<div class="rcard"><h3>Trend Flips</h3><p style="font-size:13.5px;margin:0 0 8px"><strong>Newly red on trend ({len(tn)}):</strong> {nm_(tn)}.</p><p style="font-size:13.5px;margin:0"><strong>No longer red on trend ({len(tf)}):</strong> {nm_(tf)}.</p></div>'
             f'<div class="rcard"><h3>4+ Red Flags</h3><p style="font-size:13.5px;margin:0 0 8px">{st["pr4"]} names on {C["prior_short"]} &rarr; {st["r4"]} now.</p><p style="font-size:13.5px;margin:0 0 8px"><strong>Dropped off:</strong> {nm_(st["off4"])}.</p><p style="font-size:13.5px;margin:0"><strong>Newly on:</strong> {nm_(st["new4"])}.</p></div></div>')
    return f'<section id="vs-previous"><div class="section-head"><span class="kicker-label">Comparison</span><div class="section-top-row"><h2>Vs Previous Full Study ({C["prior_short"]})</h2><span class="section-note">One trading day apart; flags compared on the same rules</span></div></div>{para}{cards}</section>'



def whats_next(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; M = S['macro']; B = S['bitcoin']; b = bm(S, P)
    sw, swavg, swup = basket(T, 'software_cloud'); sem, semavg, semup = basket(T, 'semiconductor_ai')
    q1 = (f'Relative-strength red flags fell from {st["prs"]} to {st["rs"]} on a day when {st["dec"]} of {st["n"]} names fell. How can a checklist look healthier on one of the worst days of the year?')
    h1 = (f'Facts to weigh: relative strength compares each stock&rsquo;s 3-month return with SPY or QQQ, and those benchmarks moved from {b["psp"]:+.2f}% to {b["sp"]:+.2f}% and from {b["pqq"]:+.2f}% to {b["qq"]:+.2f}%. A defensive name that sat still now beats a falling yardstick. Ask which of the 10 points measure a company and which measure the market around it, and how you would weigh each on a day like this.')
    q2 = (f'The Semiconductor/AI basket averaged {sg(semavg)} and {mv(T, "NVDA")}, while health care insurers and staples rose. Is this the market repricing AI earnings, or selling what it owns the most of to raise cash?')
    h2 = (f'Facts to weigh: open {nm(T, "NVDA")} (NVDA) and {nm(T, "MU")} (MU) in the 10-Point Analyzer and compare revenue growth, margins and the TRAP #4 earnings history with today&rsquo;s price. Then compare the gainers list with the losers list: did anything change in the gainers&rsquo; businesses today? If the fundamentals didn&rsquo;t move, what does that say about the cause?')
    q3 = (f'Bonds rallied (the 10-year fell to {M["ust10y"]:.2f}%), gold (GC) {sg(F["GC"]["chg_pct"])} and Bitcoin {sg(B["chg_pct"])}. Your dollar rule didn&rsquo;t get a real test: the dollar index (DX) {sg(F["DX"]["chg_pct"])} against Nasdaq 100 futures (NQ) {sg(F["NQ"]["chg_pct"])}. Which assets acted as a refuge today, and which were sold alongside stocks?')
    h3 = (f'Facts to weigh: in a fast selloff, investors sometimes sell what has gains or what they can sell quickly, even assets usually seen as safe. Compare the Futures Since {"Thursday"} table with the sector table, and ask whether gold and Bitcoin behaved like refuges or like risk assets this week.')
    card = lambda n_, q, hh: f'<div class="qcard"><div class="qnum">Question {n_}</div><div class="q">{q}</div><div class="hint">{hh}</div></div>'
    return (f'<section class="study" id="whats-next"><div class="kicker">Study Session</div><h2>What&rsquo;s Next</h2><p class="setup">Three open questions from today&rsquo;s facts. Work through them yourself; the data doesn&rsquo;t settle any of them.</p><div class="qlist">{card("One", q1, h1)}{card("Two", q2, h2)}{card("Three", q3, h3)}</div><p class="closer">None of this is a recommendation. The point is to practice separating what the numbers show from the story that explains them.</p></section>')

def news(S, P, T, PT, C):
    F = {f['symbol']: f for f in S['futures']}; M = S['macro']
    macro = (f'<li>Coverage said the Nasdaq Composite erased its 2026 gain and the S&amp;P 500 entered correction territory, with Anthropic&rsquo;s post-IPO slide, Fed officials signaling further rate increases, NVIDIA&rsquo;s leadership turmoil and doubts about AI spending all cited ({SRC}; {SRC5}).</li>'
             f'<li>FMP&rsquo;s treasury print for {M["treasury_print_date"]} has the 10-year at {M["ust10y"]:.2f}% and the 30-year at {M["ust30y"]:.2f}%. The VIX closed at {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}).</li>')
    names = (f'<li><strong>Anthropic (ANT)</strong> {sg(T["ANT"]["chg_pct"])} on its second day of trading, closing at ${T["ANT"]["price"]:,.2f} against the $83.00 IPO price ({SRC}).</li>'
             f'<li><strong>NVIDIA (NVDA)</strong> {sg(T["NVDA"]["chg_pct"])}: coverage cited the fallout from its CEO&rsquo;s Nov. 12 resignation and Anthropic&rsquo;s IPO failing to lift the AI trade ({SRC2}).</li>'
             f'<li><strong>AMD (AMD)</strong> {sg(T["AMD"]["chg_pct"])} as the Hunterbrook short report on alleged China ties weighed for a second day; AMD disputes the claims ({SRC3}; {SRC4}).</li>'
             f'<li><strong>Humana (HUM)</strong> {sg(T["HUM"]["chg_pct"])}: coverage tied the gain to proposed Medicare Advantage changes ({SRC}).</li>'
             f'<li>Next reports per FMP: Agilent (A) {nxt(T, "A")}, Analog Devices (ADI) {nxt(T, "ADI")}, Dell Technologies (DELL) {nxt(T, "DELL")}, Deere (DE) {nxt(T, "DE")}, CrowdStrike (CRWD) {nxt(T, "CRWD")}, Marvell Technology (MRVL) {nxt(T, "MRVL")}.</li>')
    return (f'<section id="news"><div class="section-head"><span class="kicker-label">Research</span><h2 style="margin-top:2px">Market News &amp; Research</h2></div><div class="rollup-grid"><div class="rcard"><h3>Macro</h3><ul>{macro}</ul></div><div class="rcard"><h3>Names from today&rsquo;s movers</h3><ul>{names}</ul><p class="trap-note">Headlines are from the linked coverage; check them against the companies&rsquo; own filings.</p></div></div>')


def findings(S, P, T, PT, C):
    dn = S['data_notes']; new = lst(f'{nm(T, s)} ({s})' for s in dn['new_names']) or 'none'
    dropped = lst(next((x['name'] for x in P['tickers'] if x['symbol'] == s), s) + f' ({s})' for s in dn['dropped_names']) or 'none'
    return (f'<section id="findings"><div class="findings"><div class="section-head" style="border:none"><span class="kicker-label">Corrections &amp; Methodology</span><h2 style="margin-top:2px">Pipeline Findings</h2></div><h3>Data sources</h3><ul>'
            f'<li>Universe: {len(T)} unique names &mdash; Dow 30, live Nasdaq 100 (101), live S&amp;P 500 top 100 by market cap, large-cap proxy (100; US-only screener; notes, preferreds, collateral-trust bonds and duplicate share classes (BRK-A, SOJE, SOMN, APOS) removed), and the three 20-name baskets. New versus {C["prior_short"]}: {new}. Dropped: {dropped}. The market-cap ranks shift when prices move this much, which is why names rotate in and out of the S&amp;P 500 Top 100 and the large-cap proxy.</li>'
            f'<li>Prices, moving averages and 52-week ranges from FMP <code>/stable/batch-quote</code>; growth, ratios, key metrics and cash flow from the quarterly endpoints; EMAs, YTD and 3-month returns computed from <code>historical-price-eod/full</code>. TRAP #4 data from <code>trap_fundamentals.py</code>; annual-report data from <code>annual_review.py</code>. The pull and scoring use <code>full_study_pull.py</code>, <code>full_study_score.py</code> and <code>full_study_build.py</code>. The VIX is not returned by <code>batch-quote</code>, so it comes from <code>quote?symbol=^VIX</code>. Captured at the 2pm MT close.</li>'
            f'<li>Index moves are FMP ETF proxies (SPY, QQQ, DIA, IWM). Yields are FMP&rsquo;s <code>/stable/treasury-rates</code> with a {S["macro"]["treasury_print_date"]} print. Sector moves are the Select Sector SPDR funds ({S["date"]}). Report dates and EPS against consensus quoted for individual names come from the TRAP #4 earnings history (FMP).</li></ul>'
            f'<h3>Gaps this session</h3><ul><li>Watchlist: Bloom Energy (BE), on your watchlist, dropped out of the large-cap proxy today, so it has no row on either page this session; it stays on the watchlist and returns when it re-enters a scanned list.</li>'
            f'<li>Institutional ownership and moat: Chipotle Mexican Grill (CMG) was researched fresh and cached; Humana (HUM), Vylor (VYLR) and Waste Connections (WCN) returned with their existing cache entries. The one-search &ldquo;anything changed&rdquo; refresh was not run for existing entries. The full pull completed with no missing tickers.</li>'
            f'<li>Futures: FMP priced 23 of the 40 contracts through <code>batch-quote</code> (plus the VIX via <code>quote</code>); unpriced: VX, SR3, ZC, ZW, ZL, KC, LE, the currency futures (SB and CT return unrelated token quotes).</li>'
            f'<li>News: headlines come from coverage dated today, linked above; several sources quoted intraday moves that differ from the 2pm MT figures here, so only FMP numbers are used. No Bitcoin ETF flow figure dated {C["short"]} was found. The institutional ownership endpoint still returns an empty array on this plan.</li></ul></div></section>')
