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






OV.update({'ANT': 'Anthropic', 'NBIS': 'Nebius Group', 'CRWV': 'CoreWeave', 'PANW': 'Palo Alto Networks', 'WDC': 'Western Digital', 'FANG': 'Diamondback Energy', 'SNDK': 'SanDisk', 'ALAB': 'Astera Labs', 'ARM': 'Arm Holdings', 'MU': 'Micron Technology', 'AMD': 'AMD', 'AVGO': 'Broadcom', 'MRVL': 'Marvell Technology', 'MPWR': 'Monolithic Power Systems', 'ANET': 'Arista Networks', 'GLW': 'Corning', 'AMAT': 'Applied Materials',
           'HUM': 'Humana', 'UNH': 'UnitedHealth', 'ELV': 'Elevance Health', 'T': 'AT&amp;T', 'TMUS': 'T-Mobile US', 'VZ': 'Verizon', 'CL': 'Colgate-Palmolive', 'AMT': 'American Tower', 'INTU': 'Intuit', 'TSLA': 'Tesla', 'DE': 'Deere', 'TDG': 'TransDigm',
           'HPE': 'Hewlett Packard Enterprise', 'ZS': 'Zscaler', 'CRWD': 'CrowdStrike', 'INTC': 'Intel', 'KLAC': 'KLA', 'LRCX': 'Lam Research', 'ORCL': 'Oracle', 'KEYS': 'Keysight Technologies', 'F': 'Ford Motor', 'BE': 'Bloom Energy', 'MNST': 'Monster Beverage', 'OXY': 'Occidental Petroleum', 'VLO': 'Valero Energy', 'MSTR': 'Strategy', 'BMY': 'Bristol-Myers Squibb', 'CVS': 'CVS Health', 'DVN': 'Devon Energy', 'MRK': 'Merck', 'NVDA': 'NVIDIA', 'MSFT': 'Microsoft', 'AAPL': 'Apple',
           'ADI': 'Analog Devices', 'TXN': 'Texas Instruments', 'MRNA': 'Moderna', 'NKE': 'Nike', 'AMGN': 'Amgen', 'ALNY': 'Alnylam Pharmaceuticals', 'REGN': 'Regeneron Pharmaceuticals', 'VRTX': 'Vertex Pharmaceuticals', 'LLY': 'Eli Lilly', 'JNJ': 'Johnson &amp; Johnson', 'ABBV': 'AbbVie', 'PFE': 'Pfizer', 'SWKS': 'Skyworks Solutions', 'TRI': 'Thomson Reuters', 'TGT': 'Target', 'PH': 'Parker-Hannifin', 'CMG': 'Chipotle Mexican Grill', 'FITB': 'Fifth Third Bancorp', 'APO': 'Apollo Global Management', 'ADBE': 'Adobe', 'BSX': 'Boston Scientific', 'ON': 'ON Semiconductor', 'MCHP': 'Microchip Technology', 'TER': 'Teradyne', 'ADSK': 'Autodesk', 'WDAY': 'Workday', 'MDT': 'Medtronic', 'APH': 'Amphenol', 'CSCO': 'Cisco Systems'})
OV.update({'AXON': 'Axon Enterprise', 'SCCO': 'Southern Copper', 'SLB': 'SLB', 'CEG': 'Constellation Energy', 'DASH': 'DoorDash', 'PAYX': 'Paychex', 'FCX': 'Freeport-McMoRan', 'LIN': 'Linde', 'IBM': 'IBM', 'ACN': 'Accenture', 'NXPI': 'NXP Semiconductors', 'WDC': 'Western Digital', 'ROST': 'Ross Stores', 'CRM': 'Salesforce', 'KKR': 'KKR &amp; Co.', 'TFC': 'Truist Financial', 'PYPL': 'PayPal'})
OV.update({'RKLB': 'Rocket Lab', 'SHOP': 'Shopify', 'DELL': 'Dell Technologies', 'LITE': 'Lumentum', 'STX': 'Seagate Technology', 'HUBS': 'HubSpot', 'TRGP': 'Targa Resources', 'EBAY': 'eBay', 'TJX': 'TJX Companies', 'EW': 'Edwards Lifesciences', 'TMO': 'Thermo Fisher Scientific', 'RSG': 'Republic Services', 'ORLY': "O'Reilly Automotive", 'KDP': 'Keurig Dr Pepper', 'BDX': 'Becton Dickinson', 'ALL': 'Allstate', 'NEM': 'Newmont', 'SPCX': 'Space Exploration Technologies', 'COST': 'Costco', 'WMT': 'Walmart', 'HD': 'Home Depot', 'XOM': 'Exxon Mobil', 'CVX': 'Chevron', 'HWM': 'Howmet Aerospace', 'AXP': 'American Express'})
DAYS = ('2026-11-26', '2026-11-27')
def epsr(T, s):
    r = reported(T, s, DAYS); m = lambda v: ('-' if v < 0 else '') + f'${abs(v):.2f}'; return f' (FMP dates its report {r[0][5:].replace("-", "/")}, EPS {m(r[1])} against {m(r[2])} expected)' if r else ''

def pv(T, PT, s): return f'{mv(T, s)} (Wednesday: {sg(PT[s]["chg_pct"])})'
def pm(PT, s): return f'{nm(PT, s)} ({s}) {sg(PT[s]["chg_pct"])}'
SRC = '<a href="https://finance.yahoo.com/markets/live/stock-market-today-firday-november-27-dow-sp-500-nasdaq-black-friday-holiday-091152065.html" target="_blank" rel="noopener">Yahoo Finance &#8599;</a>'
SRC2 = '<a href="https://www.washingtonpost.com/business/2026/11/27/wall-street-stocks-dow-nasdaq/d71517d6-ea92-11f1-8db0-6f1e3c389e7c_story.html" target="_blank" rel="noopener">AP via the Washington Post &#8599;</a>'
CAUSE = ('Beyond the easing AI-profitability worries, the GDP revision and the Black Friday spending forecasts described in the linked coverage, we found no dated coverage explaining individual moves, so no cause is stated for them.')
def worst(T, k, key=None):
    v = [t for t in T.values() if key is None or key(t)]
    return sorted(v, key=lambda t: (t['chg_pct'], t['symbol']))[:k]
def names_or_none(T, ss): return lst(f'{nm(T, s)} ({s})' for s in ss) or 'none'
def nxt(T, s):
    d = T[s]['detail'].get('next_earnings_date'); return d[5:].replace('-', '/') if d else 'not dated by FMP'
MEM = ("SNDK", "MU", "STX", "WDC", "LITE", "ALAB", "MRVL", "ARM")
EQUIP = ("LRCX", "AMAT", "KLAC", "INTC", "AMD", "TSM", "NVDA")
AIS = ("ANT", "DELL", "ANET", "SHOP", "ORCL", "DDOG", "AMZN", "TSLA", "META")
DEF = ("VRTX", "ALNY", "ABBV", "BDX", "BMY", "MDT", "TJX", "EBAY")
def lead(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; st = stats(S, P, T, PT); n = st['n']; B = S['bitcoin']; M = S['macro']; b = bm(S, P)
    up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    sem, semavg, semup = basket(T, 'semiconductor_ai'); sw, swavg, swup = basket(T, 'software_cloud'); mg, mgavg, mgup = basket(T, 'megacap_leaders')
    allsec = sorted(up + dn, reverse=True)
    nup = len([1 for c, k, f in allsec if c > 0])
    p1 = (f'<p class="intro"><strong>A broad Black Friday rally in a half-day session: the chip stocks that led Wednesday&rsquo;s losses led the rebound, every sector fund rose, and the VIX fell back.</strong> The S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))}, the Dow fund (DIA) {sg(etf(S, "DIA"))} and the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))}. '
          f'{st["adv"]} of {n} names rose and {st["dec"]} fell, and <strong>the average move across our names was {sg(st["avg"])}</strong>, against {sg(st["pavg"])} on Wednesday. '
          f'S&amp;P 500 futures (ES) {fx(F, "ES")} ({sg(F["ES"]["chg_pct"])}), Nasdaq 100 futures (NQ) {fx(F, "NQ")} ({sg(F["NQ"]["chg_pct"])}), Mini Dow (YM) {fx(F, "YM")} ({sg(F["YM"]["chg_pct"])}) and Russell 2000 (RTY) {fx(F, "RTY")} ({sg(F["RTY"]["chg_pct"])}), all still below their 50-day and 200-day averages. '
          f'Stocks closed early at 1pm ET after Thanksgiving. Coverage said chip stocks bounced as worries about AI profitability eased, and tied higher Treasury yields to the upward revision of third-quarter GDP to 4.3% ({SRC}); all three major indexes closed higher ({SRC2}). '
          f'<strong>The VIX was {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}).</strong> '
          f'Bonds sold off: 30-year bond futures (ZB) {fx(F, "ZB")} ({sg(F["ZB"]["chg_pct"])}) and 10-year note futures (ZN) {fx(F, "ZN")} ({sg(F["ZN"]["chg_pct"])}), and FMP&rsquo;s cash 10-year print for today is {M["ust10y"]:.2f}%, against {M["ust10y_prev"]:.2f}% on Wednesday. The dollar index (DX) was {fx(F, "DX")} ({sg(F["DX"]["chg_pct"])}). '
          f'Precious metals surged: silver (SI) {fx(F, "SI")} ({sg(F["SI"]["chg_pct"])}), platinum (PL) {fx(F, "PL")} ({sg(F["PL"]["chg_pct"])}), gold (GC) {fx(F, "GC")} ({sg(F["GC"]["chg_pct"])}) and copper (HG) {fx(F, "HG")} ({sg(F["HG"]["chg_pct"])}); WTI crude (CL) {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}) and Brent (BZ) {fx(F, "BZ")} ({sg(F["BZ"]["chg_pct"])}). '
          f'<strong>Bitcoin is ${B["price"]:,.2f} ({sg(B["chg_pct"])})</strong>, {sg(B["r7"])} over seven days, and Ether {fx(F, "ETH")} ({sg(F["ETH"]["chg_pct"])}).</p>')
    wk = worst(T, 8); ld = sorted(T.values(), key=lambda t: (-t['chg_pct'], t['symbol']))[:8]
    p2 = (f'<p class="intro"><strong>{nup} of 11 S&amp;P 500 sectors rose: {allsec[0][1]} ({allsec[0][2]}) {sg(allsec[0][0])} led, and Utilities (XLU) {sg(fs["Utilities"]["chg_pct"])} and Health Care (XLV) {sg(fs["Health Care"]["chg_pct"])} were the weakest.</strong> By sector, <strong>' + lst(f'{k} ({f}) {sg(c)}' for c, k, f in allsec) + '</strong>. '
          f'Our {sa["Information Technology"][0]} Information Technology names averaged {sg(sa["Information Technology"][1])}, our {sa["Materials"][0]} Materials names {sg(sa["Materials"][1])} and our {sa["Health Care"][0]} Health Care names {sg(sa["Health Care"][1])}. '
          f'<strong>The Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 names up</strong>, after {sg(basket(PT, "semiconductor_ai")[1])} on Wednesday; the Software/Cloud basket averaged {sg(swavg)} with {swup} of 20 up, and the Mega-Cap Leaders basket {sg(mgavg)} with {mgup} of 20 up. The Nasdaq 100 basket averaged {sg(basket(T, "nasdaq100")[1])} and the Dow 30 basket {sg(basket(T, "dow30")[1])} ({basket(T, "dow30")[2]} of 30 names rose). '
          f'The market leaders: {lst(mv(T, s) for s in ("NVDA", "MSFT", "AAPL", "GOOGL", "META", "AMZN", "AVGO", "TSLA"))}. '
          f'<strong>The biggest gainers were memory, storage and AI hardware</strong>: ' + lst(mv(T, t['symbol']) for t in ld) + '. '
          f'<strong>The few losers were mostly health care and retail</strong>: ' + lst(mv(T, t['symbol']) for t in wk) + '.</p>')
    of = names_or_none(T, st['off4']); nw = names_or_none(T, st['new4'])
    inc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['inc'][:4]) or 'none'
    dc = '; '.join(f'{nm(T, s)} ({s}) ({PT[s]["red_flag_count"]} &rarr; {T[s]["red_flag_count"]})' for d, s in st['dec_'][:4]) or 'none'
    tr = sum(t['flags']['trend'] == 'red' for t in T.values()); ptr = sum(t['flags']['trend'] == 'red' for t in PT.values())
    p3 = (f'<p class="intro">On the checklist, <strong>{st["r4"]} of {n} names carry 4 or more red flags, against {st["pr4"]} on Wednesday</strong> ({st["z"]} names are clean, against {st["pz"]}). Trend red flags went from {ptr} to {tr} and relative-strength red flags from {st["prs"]} to {st["rs"]}, as the benchmarks&rsquo; three-month returns improved (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%). Names moving onto the 4+ list: {nw}. Names leaving it: {of}. '
          f'The biggest increases: {inc}. The biggest decreases: {dc}. {mv(T, "BE")}, on your watchlist, is back in the large-cap proxy with {T["BE"]["red_flag_count"]} red flags, and Keysight Technologies (KEYS) re-entered too; Chipotle Mexican Grill (CMG) and Fifth Third Bancorp (FITB) dropped out. '
          f'Bitcoin was ${B["price"]:,.2f} ({sg(B["chg_pct"])}) at the close, {abs((B["price"] / B["avg200"] - 1) * 100):.1f}% {"below" if B["price"] < B["avg200"] else "above"} its 200-day average and {abs((B["price"] / B["avg50"] - 1) * 100):.1f}% {"below" if B["price"] < B["avg50"] else "above"} its 50-day.</p>')
    pulls = [(sg(fs["Information Technology"]["chg_pct"]), 'Information Technology (XLK), the Leading Sector'), ('11 / 11', 'Sector Funds That Rose'), (f'{st["adv"]} / {n}', 'Names That Rose'), (f'{st["r4"]} / {n}', 'Names With 4+ Red Flags')]
    pr = '<div class="pull-row">' + ''.join(f'<div class="pull"><div class="pn mono">{a}</div><div class="pl">{b_}</div></div>' for a, b_ in pulls) + '</div>'
    return p1 + p2 + p3 + pr

def macro(S, P, F, C):
    M = S['macro']; B = S['bitcoin']; ff = lambda s: f'{fx(F, s)} ({sg(F[s]["chg_pct"])})'; T = S_T(S)
    return (f'<section><div class="section-head"><div class="section-top-row"><span class="kicker-label">Setup</span></div><h2 style="margin-top:2px">Macro Backdrop</h2><span class="section-note">2:00pm MT, {C["long_label"]} (after the 1pm ET early close). FMP futures quotes; daily % versus Wednesday&rsquo;s settle. Yields are FMP&rsquo;s treasury print for {M["treasury_print_date"]}.</span></div><div class="macro-grid">'
            f'<div class="mcard"><h3>Rates &amp; the Fed</h3><p class="big">10-year {M["ust10y"]:.2f}%</p><p>Cash Treasury yields (FMP, {M["treasury_print_date"]} print): 2-year {M["ust2y"]:.2f}%, 10-year {M["ust10y"]:.2f}% ({M["ust10y_prev"]:.2f}% on {M["ust10y_prev_date"][5:].replace("-", "/")}), 30-year {M["ust30y"]:.2f}%. Futures: 30-year bond futures (ZB) {ff("ZB")}, 10-year note futures (ZN) {ff("ZN")}, 5-year (ZF) {ff("ZF")}, 2-year (ZT) {ff("ZT")}. Coverage tied the rise in yields to the upward revision of third-quarter GDP to 4.3% from 3.4% ({SRC}). The Fed meets Dec. 8-9; next week brings fresh jobs data. Bond trading closed at 2pm ET.</p></div>'
            f'<div class="mcard"><h3>Equities</h3><p class="big">Broad half-day rally</p><p>S&amp;P 500 futures (ES) {ff("ES")}, Nasdaq 100 futures (NQ) {ff("NQ")}, Mini Dow (YM) {ff("YM")}, Russell 2000 (RTY) {ff("RTY")}; all four are still below their 50-day and 200-day averages. The VIX is {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}), still above its 50-day average. Coverage said chips bounced as AI-profitability worries eased ({SRC}): {mv(T, "MU")}, {mv(T, "SNDK")} and {mv(T, "NVDA")}. On the retail side, Adobe projected holiday online spending 6.7% above last year and the National Retail Federation forecast holiday sales above $1 trillion ({SRC}); {mv(T, "WMT")}, {mv(T, "AMZN")}, {mv(T, "TGT")}.</p></div>'
            f'<div class="mcard"><h3>Oil &amp; Energy</h3><p class="big">Crude pares gains</p><p>WTI (CL) {ff("CL")}, Brent (BZ) {ff("BZ")}, RBOB gasoline (RB) {ff("RB")}, heating oil (HO) {ff("HO")}, natural gas (NG) {ff("NG")}. Coverage said oil pared gains despite stepped-up Houthi attacks on Saudi energy infrastructure, with US crude inventories up a third straight week and OPEC meeting Nov. 29 ({SRC}). Brent&rsquo;s January contract expires Nov. 30, so FMP&rsquo;s continuous Brent quote may be rolling. The Energy sector fund (XLE) was {sg(S["sector_funds"]["Energy"]["chg_pct"])}.</p></div>'
            f'<div class="mcard"><h3>Metals, Dollar &amp; Crypto</h3><p class="big">Silver {sg(F["SI"]["chg_pct"])}</p><p>Gold (GC) {ff("GC")}, silver (SI) {ff("SI")}, platinum (PL) {ff("PL")}, palladium (PA) {ff("PA")}, copper (HG) {ff("HG")}; all five are still below their 50-day and 200-day averages. Soybean meal (ZM) {ff("ZM")}; cocoa (CC) {ff("CC")}; dollar index (DX) {ff("DX")}. Bitcoin (BTC) {ff("BTC")}, Ether (ETH) {ff("ETH")}. The dollar and the index futures both rose, so the dollar rule did not hold today.</p></div></div></section>')

def bitcoin(S, F, C):
    B = S['bitcoin']; p = B['price']; v200 = (p / B['avg200'] - 1) * 100; v50 = (p / B['avg50'] - 1) * 100; fromhi = (1 - p / B['year_high']) * 100
    c = lambda x: 'up' if x > 0 else 'down'
    assert p < B['avg200'] and p < B['avg50']
    trend = f'Price is below both its 50-day and 200-day averages (50-day <strong class="mono">${B["avg50"]:,.2f}</strong>, 200-day <strong class="mono">${B["avg200"]:,.2f}</strong>): {abs(v200):.1f}% below the 200-day, {abs(v50):.1f}% below the 50-day and {fromhi:.1f}% below the 52-week high.'
    eth = F['ETH']; T = S_T(S); lo = (p / B['year_low'] - 1) * 100
    return (f'<section id="bitcoin"><div class="section-head"><div class="section-top-row"><span class="kicker-label">Crypto</span><h2>Bitcoin</h2><span class="section-note">Live price at 2:00pm MT ({C["today_label"]}); BTC trades 24/7, so later prices will differ. 52-wk range and 50d/200d averages from FMP <code class="mono">quote</code>; 7/30/90-day moves from <code class="mono">historical-price-eod/full?symbol=BTCUSD</code>.</span></div></div>'
            f'<div class="btc-card"><div><div class="btc-price mono">${p:,.2f}</div><div class="btc-chg-row"><span class="btc-chg {c(B["chg_pct"])} mono">{sg(B["chg_pct"])} today</span><span class="btc-sep">&middot;</span><span class="btc-range">52-wk range: <strong class="mono">${B["year_low"]:,.2f}</strong> &ndash; <strong class="mono">${B["year_high"]:,.2f}</strong></span></div><p class="btc-trend-note">{trend}</p></div>'
            f'<div class="btc-moves"><div class="btc-move"><div class="bm-label">7-Day</div><div class="bm-val {c(B["r7"])} mono">{sg(B["r7"])}</div></div><div class="btc-move"><div class="bm-label">30-Day</div><div class="bm-val {c(B["r30"])} mono">{sg(B["r30"])}</div></div><div class="btc-move"><div class="bm-label">90-Day</div><div class="bm-val {c(B["r90"])} mono">{sg(B["r90"])}</div></div><div class="btc-move"><div class="bm-label">Ether</div><div class="bm-val {c(eth["chg_pct"])} mono">{fx(F, "ETH")} ({sg(eth["chg_pct"])})</div></div></div>'
            f'<div class="btc-context">Bitcoin is {sg(B["chg_pct"])} on the day while stocks rallied, with 7-day, 30-day and 90-day moves of {sg(B["r7"])}, {sg(B["r30"])} and {sg(B["r90"])}. It traded between ${B["day_low"]:,.2f} and ${B["day_high"]:,.2f} today and sits {lo:.1f}% above its 52-week low of ${B["year_low"]:,.2f}. The stocks tied to it rose anyway: Strategy (MSTR) {sg(T["MSTR"]["chg_pct"])} and Robinhood Markets (HOOD) {sg(T["HOOD"]["chg_pct"])}. We found no spot ETF flow figure dated today, so none is quoted. FMP is the price source here.</div></div></section>')
def S_T(S): return {t['symbol']: t for t in S['tickers']}


def spotlight(S, P, T, PT):
    F = {f['symbol']: f for f in S['futures']}; up, dn = secfunds(S); sa = sector_avgs(T); fs = S['sector_funds']
    f = lambda k: f'{k} ({fs[k]["fund"]}) {sg(fs[k]["chg_pct"])}'
    sw, swavg, swup = basket(T, 'software_cloud'); sem, semavg, semup = basket(T, 'semiconductor_ai')
    p1 = (f'Wednesday&rsquo;s losers led the rebound. Memory and storage turned hardest: {lst(pv(T, PT, s) for s in MEM[:2])}, and {lst(mv(T, s) for s in MEM[2:])}. Chip equipment and the big chip makers followed: {lst(mv(T, s) for s in EQUIP)}. '
          f'All 20 Semiconductor/AI names rose and the basket averaged {sg(semavg)}; {f("Information Technology")} led all 11 sector funds, and our {sa["Information Technology"][0]} Information Technology names averaged {sg(sa["Information Technology"][1])}. Coverage said chips bounced as worries about AI profitability eased ({SRC}).')
    p2 = (f'The AI trade reached past the chips: {lst(mv(T, s) for s in AIS)}. The Software/Cloud basket averaged {sg(swavg)} with {swup} of 20 up. '
          f'NVIDIA lagged its own group at {mv(T, "NVDA")}; coverage tied its swings this week to CEO Jensen Huang&rsquo;s return and his congressional hearings next week ({SRC}). {f("Consumer Discretionary")} and {f("Communication Services")} were the next-best sector funds.')
    p3 = (f'Every sector fund rose, but the defensive ones lagged: {f("Utilities")}, {f("Health Care")} and {f("Consumer Staples")}. Our {sa["Health Care"][0]} Health Care names averaged {sg(sa["Health Care"][1])}, and most of the day&rsquo;s few losers came from that sector or from retail: {lst(mv(T, s) for s in DEF)}. '
          f'We found no dated coverage explaining the Vertex Pharmaceuticals drop, so no cause is given.')
    chip = lambda syms: '<div class="names">' + ', '.join(f'<span class="chip">{s}</span>' for s in syms) + '</div>'
    bt = ' style="border-top:1px solid var(--line)"'
    sec = lambda t, body, names, first=False: f'<div class="spotlight"{"" if first else bt}><h3>{t}</h3><p>{body}</p>{chip(names)}</div>'
    return (f'<section id="spotlight"><div class="section-head"><span class="kicker-label">Analysis</span><h2 style="margin-top:2px">Sector Spotlight</h2></div>'
            + sec('Memory and Storage Lead the Chip Rebound', p1, list(MEM) + list(EQUIP), True)
            + sec('The AI Trade Broadens', p2, list(AIS))
            + sec('Defensives Lag, Health Care Trails', p3, list(DEF)))

def movers_read(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; n = st['n']
    bks = {k: basket(T, k)[1] for k in ('dow30', 'sp500_top100', 'nasdaq100', 'large_cap_proxy', 'software_cloud', 'semiconductor_ai', 'megacap_leaders')}
    srt = sorted(T.values(), key=lambda t: (-t['chg_pct'], t['symbol'])); g10 = srt[:10]; l10 = sorted(T.values(), key=lambda t: (t['chg_pct'], t['symbol']))[:10]
    itg = sum(t['detail']['sector'] == 'Information Technology' for t in g10); hcl = sum(t['detail']['sector'] == 'Health Care' for t in l10)
    return (f'<p class="movers-read"><strong>A broad up day: nearly nine in ten names rose, led by the chip stocks that fell hardest on Wednesday.</strong> {st["adv"]} of {n} names rose and {st["dec"]} fell, and the average move was {sg(st["avg"])}. The S&amp;P 500 fund (SPY) {sg(etf(S, "SPY"))}, the Nasdaq 100 fund (QQQ) {sg(etf(S, "QQQ"))}, the Dow fund (DIA) {sg(etf(S, "DIA"))} and the Russell 2000 fund (IWM) {sg(etf(S, "IWM"))}. '
            f'The Dow 30 basket averaged {sg(bks["dow30"])}, the S&amp;P 500 Top 100 basket {sg(bks["sp500_top100"])}, the Nasdaq 100 basket {sg(bks["nasdaq100"])} and the large-cap proxy basket {sg(bks["large_cap_proxy"])}, while the Software/Cloud basket averaged {sg(bks["software_cloud"])}, the Semiconductor/AI basket {sg(bks["semiconductor_ai"])} and the Mega-Cap Leaders basket {sg(bks["megacap_leaders"])}. '
            f'{itg} of the top 10 gainers are Information Technology names, and {hcl} of the 10 weakest are Health Care names. WTI crude (CL) was {fx(F, "CL")} ({sg(F["CL"]["chg_pct"])}) and the VIX {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}). It was a half-day session after a holiday, when volume is usually thin. {CAUSE}</p>')

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
        wl = s in R['watchlist'][:19]
        tag = ' &middot; &#9733; on your watchlist' if wl else (' &middot; newly at 4+ red' if s in newly else ' &middot; new to the universe' + (' at 4+ red' if T[s]['red_flag_count'] >= 4 else ''))
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
            f'Flags moving onto red: {kv(st["on"]) or "none"}. Flags moving off red: {kv(st["off"]) or "none"}. Relative-strength red flags went from {st["prs"]} to {st["rs"]}; the benchmark 3-month returns moved (SPY {b["psp"]:+.2f}% &rarr; {b["sp"]:+.2f}%, QQQ {b["pqq"]:+.2f}% &rarr; {b["qq"]:+.2f}%), so a stock that rose less than its benchmark can pick up a relative-strength flag on an up day. '
            f'Names entering the 4+ group: {nm_(st["new4"])}. Names leaving it: {nm_(st["off4"])}. New in the universe: {nm_(new)}. Dropped out: {nm_(dr)}. Biggest red-flag increases: {inc}. Biggest decreases: {dc}. {newer} names show a newer reported quarter than on {C["prior_short"]}, which can move growth and margin flags by itself.</p>')
    order = ['ES', 'NQ', 'ZB', 'CL', 'GC', 'SI', 'BTC', 'ETH', 'VIX']
    rows = ''.join(f'<tr><td>{s} ({ {"ES": "E-Mini S&amp;P 500", "NQ": "Nasdaq 100", "ZB": "30Y T-Bond", "CL": "WTI Crude", "GC": "Gold", "SI": "Silver", "BTC": "Bitcoin", "ETH": "Ethereum", "VIX": "CBOE Volatility Index"}[s]})</td><td class="px-cell mono">{fx(F, s)}</td><td class="px-cell {"up" if F[s]["last"] > PF[s]["last"] else "down"} mono">{sg((F[s]["last"] / PF[s]["last"] - 1) * 100)}</td></tr>' for s in order)
    cards = (f'<div class="rollup-grid"><div class="rcard"><h3>Futures Since {C["prior_short"]} Close</h3><div class="table-wrap"><table style="min-width:0"><thead><tr><th>Contract</th><th>Last</th><th>Since {C["prior_short"]}</th></tr></thead><tbody>{rows}</tbody></table></div></div>'
             f'<div class="rcard"><h3>Trend Flips</h3><p style="font-size:13.5px;margin:0 0 8px"><strong>Newly red on trend ({len(tn)}):</strong> {nm_(tn)}.</p><p style="font-size:13.5px;margin:0"><strong>No longer red on trend ({len(tf)}):</strong> {nm_(tf)}.</p></div>'
             f'<div class="rcard"><h3>4+ Red Flags</h3><p style="font-size:13.5px;margin:0 0 8px">{st["pr4"]} names on {C["prior_short"]} &rarr; {st["r4"]} now.</p><p style="font-size:13.5px;margin:0 0 8px"><strong>Dropped off:</strong> {nm_(st["off4"])}.</p><p style="font-size:13.5px;margin:0"><strong>Newly on:</strong> {nm_(st["new4"])}.</p></div></div>')
    return f'<section id="vs-previous"><div class="section-head"><span class="kicker-label">Comparison</span><div class="section-top-row"><h2>Vs Previous Full Study ({C["prior_short"]})</h2><span class="section-note">One trading day apart (markets were closed for Thanksgiving); flags compared on the same rules</span></div></div>{para}{cards}</section>'


def whats_next(S, P, T, PT):
    st = stats(S, P, T, PT); F = {f['symbol']: f for f in S['futures']}; M = S['macro']; B = S['bitcoin']; b = bm(S, P); fs = S['sector_funds']
    sem, semavg, semup = basket(T, 'semiconductor_ai')
    q1 = (f'The names that led Wednesday&rsquo;s losses led Friday&rsquo;s gains: {pv(T, PT, "SNDK")} and {pv(T, PT, "MU")}. How much weight would you give a move made in a half-day session after a holiday?')
    h1 = (f'Facts to weigh: stocks closed at 1pm ET and post-holiday volume is usually thin; the Semiconductor/AI basket averaged {sg(semavg)} with {semup} of 20 up; the VIX was {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}) but is still above its 50-day average; all four index futures are still below their 50-day and 200-day averages. Open SanDisk (SNDK) and Micron Technology (MU) in the 10-Point Analyzer and look at the trend detail. What would you want to see on Monday, with a full session, before treating this as more than a bounce?')
    q2 = (f'The dollar index (DX) {sg(F["DX"]["chg_pct"])}, the 10-year yield went from {M["ust10y_prev"]:.2f}% to {M["ust10y"]:.2f}%, and S&amp;P 500 futures (ES) {sg(F["ES"]["chg_pct"])} anyway. At the same time silver (SI) {sg(F["SI"]["chg_pct"])} and gold (GC) {sg(F["GC"]["chg_pct"])}. What story fits all four moves at once?')
    h2 = (f'Facts to weigh: your rule says a stronger dollar is a headwind for stocks, and today it did not hold; coverage tied higher yields to the GDP revision to 4.3% ({SRC}); gold, silver and copper are all still below their 50-day and 200-day averages. Is a rally in stocks, yields and precious metals together a sign of growth, of inflation worry, or of thin holiday trading moving everything at once? Which of those would you expect to show up again next week, when the jobs data arrives?')
    q3 = (f'Every sector fund rose, yet {st["r4"]} names still carry 4 or more red flags and trend red flags only went from {sum(t["flags"]["trend"] == "red" for t in PT.values())} to {sum(t["flags"]["trend"] == "red" for t in T.values())}. Health Care (XLV) {sg(fs["Health Care"]["chg_pct"])} lagged, and {mv(T, "VRTX")}. Does one strong day change the checklist picture?')
    h3 = (f'Facts to weigh: the checklist&rsquo;s trend point compares price with the 50-day and 200-day averages, which move slowly; relative-strength red flags went from {st["prs"]} to {st["rs"]} even on an up day, because the benchmarks&rsquo; three-month returns improved. Use the Analyzer&rsquo;s Sector filter on Health Care and sort by Most red flags. Which flags would you expect to change first if this rally lasted a week, and which would barely move?')
    card = lambda n_, q, hh: f'<div class="qcard"><div class="qnum">Question {n_}</div><div class="q">{q}</div><div class="hint">{hh}</div></div>'
    return (f'<section class="study" id="whats-next"><div class="kicker">Study Session</div><h2>What&rsquo;s Next</h2><p class="setup">Three open questions from today&rsquo;s facts. Work through them yourself; the data doesn&rsquo;t settle any of them.</p><div class="qlist">{card("One", q1, h1)}{card("Two", q2, h2)}{card("Three", q3, h3)}</div><p class="closer">None of this is a recommendation. The point is to practice separating what the numbers show from the story that explains them.</p></section>')

def news(S, P, T, PT, C):
    F = {f['symbol']: f for f in S['futures']}; M = S['macro']
    macro = (f'<li>Stocks closed higher across the board in a shortened Black Friday session that ended at 1pm ET ({SRC2}). The VIX closed at {fx(F, "VIX")} ({sg(F["VIX"]["chg_pct"])}).</li>'
             f'<li>Chip stocks bounced as worries about AI profitability eased; Treasury yields rose after third-quarter GDP was revised up to 4.3%; next week brings jobs data ({SRC}).</li>'
             f'<li>Oil pared gains despite stepped-up Houthi attacks on Saudi energy infrastructure; US crude inventories rose for a third straight week, and OPEC meets Nov. 29 ({SRC}).</li>'
             f'<li>Holiday spending: Adobe expects online spending from Nov. 1 to Dec. 31 to run 6.7% above a year earlier, and the National Retail Federation forecasts holiday sales above $1 trillion, 4.2% more than last year ({SRC}).</li>')
    names = (f'<li><strong>NVIDIA (NVDA)</strong> {sg(T["NVDA"]["chg_pct"])}: coverage tied this week&rsquo;s swings to CEO Jensen Huang&rsquo;s return and noted his congressional hearings next week ({SRC}).</li>'
             f'<li><strong>Micron Technology (MU)</strong> {sg(T["MU"]["chg_pct"])} and <strong>SanDisk (SNDK)</strong> {sg(T["SNDK"]["chg_pct"])}: part of the chip rebound described in the coverage ({SRC}).</li>'
             f'<li><strong>Space Exploration Technologies (SPCX)</strong> {sg(T["SPCX"]["chg_pct"])}: coverage tied the move to Elon Musk&rsquo;s pledge of annual share giveaways to children through Trump Accounts ({SRC}).</li>'
             f'<li><strong>Allstate (ALL)</strong> {sg(T["ALL"]["chg_pct"])}: a multiday technology outage since Nov. 23 disrupted its website, app and roadside assistance; the company said customers will not lose coverage or pay late fees ({SRC}).</li>'
             f'<li><strong>Vertex Pharmaceuticals (VRTX)</strong> {sg(T["VRTX"]["chg_pct"])}: we found no dated coverage giving the cause.</li>'
             f'<li>Next reports per FMP: Broadcom (AVGO) {nxt(T, "AVGO")}, Oracle (ORCL) {nxt(T, "ORCL")}, Accenture (ACN) {nxt(T, "ACN")}, Micron Technology (MU) {nxt(T, "MU")}, Nike (NKE) {nxt(T, "NKE")}.</li>')
    return (f'<section id="news"><div class="section-head"><span class="kicker-label">Research</span><h2 style="margin-top:2px">Market News &amp; Research</h2></div><div class="rollup-grid"><div class="rcard"><h3>Macro</h3><ul>{macro}</ul></div><div class="rcard"><h3>Names from today&rsquo;s movers</h3><ul>{names}</ul><p class="trap-note">Headlines are from the linked coverage; check them against the companies&rsquo; own filings.</p></div></div>')


def findings(S, P, T, PT, C):
    dn = S['data_notes']; new = lst(f'{nm(T, s)} ({s})' for s in dn['new_names']) or 'none'
    dropped = lst(nm(PT, s) + f' ({s})' for s in dn['dropped_names']) or 'none'
    return (f'<section id="findings"><div class="findings"><div class="section-head" style="border:none"><span class="kicker-label">Corrections &amp; Methodology</span><h2 style="margin-top:2px">Pipeline Findings</h2></div><h3>Data sources</h3><ul>'
            f'<li>Universe: {len(T)} unique names &mdash; Dow 30, live Nasdaq 100 (101), live S&amp;P 500 top 100 by market cap, large-cap proxy (100; US-only screener; notes, preferreds, collateral-trust bonds and duplicate share classes (BRK-A, SOJE, SOMN, APOS) removed), and the three 20-name baskets. New versus {C["prior_short"]}: {new}. Dropped: {dropped}.</li>'
            f'<li>Prices, moving averages and 52-week ranges from FMP <code>/stable/batch-quote</code>; growth, ratios, key metrics and cash flow from the quarterly endpoints; EMAs, YTD and 3-month returns computed from <code>historical-price-eod/full</code>. TRAP #4 data from <code>trap_fundamentals.py</code>; annual-report data from <code>annual_review.py</code>. The pull and scoring use <code>full_study_pull.py</code>, <code>full_study_score.py</code> and <code>full_study_build.py</code>. The VIX is not returned by <code>batch-quote</code>, so it comes from <code>quote?symbol=^VIX</code>. Captured at 2pm MT, after the 1pm ET early close.</li>'
            f'<li>Index moves are FMP ETF proxies (SPY, QQQ, DIA, IWM). Yields are FMP&rsquo;s <code>/stable/treasury-rates</code> print for {S["macro"]["treasury_print_date"]}, compared with {S["macro"]["ust10y_prev_date"]}. Sector moves are the Select Sector SPDR funds ({S["date"]}). Report dates and EPS against consensus quoted for individual names come from the TRAP #4 earnings history (FMP). This study is compared with Wednesday&rsquo;s; there was no session Thursday.</li></ul>'
            f'<h3>Gaps this session</h3><ul><li>Watchlist: Bloom Energy (BE), on your watchlist, re-entered the large-cap proxy and is back on both pages. The watchlist stores on the dashboard and the Analyzer already matched, so no sync write was needed.</li>'
            f'<li>Institutional ownership and moat: both names new to today&rsquo;s universe (BE, KEYS) already had cache entries, so no name needed fresh research, and the one-search &ldquo;anything changed&rdquo; refresh was not run for existing entries. The full pull completed with no missing tickers.</li>'
            f'<li>Futures: FMP priced 23 of the 40 contracts through <code>batch-quote</code> (plus the VIX via <code>quote</code>); unpriced: VX, SR3, ZC, ZW, ZL, KC, LE, the currency futures (SB and CT return unrelated token quotes).</li>'
            f'<li>News: headlines come from coverage dated today, linked above; that coverage quoted index levels and moves that differ from the 2pm MT figures here, so only FMP numbers are used. No Bitcoin ETF flow figure dated {C["short"]} was found, and no cause was found for the Vertex Pharmaceuticals (VRTX) drop. The institutional ownership endpoint still returns an empty array on this plan.</li></ul></div></section>')
