"""Fact-check a Mamba page against the session's own data before it is published.

Usage:
  python3 fact_check.py PAGE.html --snapshot reports/DATE/full-study.json [--prior reports/PRIOR/full-study.json]
  python3 fact_check.py PAGE.html --snapshot reports/LAST_FULL/full-study.json --morning reports/DATE/morning-macro.json
      # the 8am run: futures and Bitcoin from this morning, stocks from the last full study
  python3 fact_check.py PAGE.html --style-only        # pages whose numbers come from elsewhere (World Watch, Stop the Cap)

Exit code 1 if any ERROR is found; the page must not be published until it is clean. Rules (house style, see
references/style-and-accuracy.md):
  * Every daily move written after a ticker in parentheses is signed and matches the data:
    "KKR & Co. (KKR) -4.72%", never "KKR & Co. (KKR) 4.72%" and never "(KKR) fell 4.72%".
  * No direction word in front of a signed number ("fell -0.3%", "rose +1%").
  * Dollar sign: stock, ETF, crypto and commodity prices always carry "$"; index levels, index futures
    (ES, NQ, YM, RTY), Treasury futures (ZB, ZN, ZF, ZT), the dollar index (DX) and the VIX are points and never do.
  * Futures cards, Bitcoin figures, Treasury yields, sector averages, breadth tiles, red-flag counts, the movers
    tables and every row of the data islands must match the snapshot.
"""
import html as H, json, re, sys
from collections import defaultdict

POINTS = {'ES', 'NQ', 'YM', 'RTY', 'ZB', 'ZN', 'ZF', 'ZT', 'DX', 'VIX'}
DIR_WORDS = r'(?:fell|rose|lost|gained|slipped|jumped|dropped|climbed|added|declined|advanced|eased|edged up|edged down|sank|surged|slid|rallied|was up|was down|is up|is down|up|down)'
NUM = r'(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)'
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from sectors import GICS_SECTORS, FMP_TO_GICS
SECTORS = sorted(GICS_SECTORS, key=len, reverse=True)
FMP_ONLY = re.compile(r'\b(Consumer Cyclical|Consumer Defensive|Financial Services|Basic Materials|(?<!HCA )Healthcare)\b(?=\s*\(|\s*[+\-]\d|\s+sector|\s+names|\s*$)'
                      r'|(?<!Information )\b(Technology)\b(?=\s+sector|\s*\(?[+\-]\d)')   # bare "Technology" only as a sector, not "Micron Technology (MU)"
POINTS_UNIT = {'ES', 'NQ', 'YM', 'RTY', 'ZB', 'ZN', 'ZF', 'ZT', 'DX'}   # quoted in points: written "7,793.50 pts" (the VIX stays a plain level)
# words right after a percentage that mean it is not the day's move
NOT_DAY = re.compile(r'^\s*(?:above|below|from|off|since|this (?:year|week|month)|year[- ]to[- ]date|YTD|over|in the (?:past|last)|on the (?:week|month|year)|for the (?:week|month|year)|week|month|of |owned|stake|share|institutional|weight|margin|yield|annual|a year)', re.I)


def num(s):
    return float(s.replace(',', '').replace('−', '-'))


def decimals(s):
    return len(s.split('.')[1]) if '.' in s else 0


def visible_text(page):
    s = re.sub(r'<script\b.*?</script>', ' ', page, flags=re.S)
    s = re.sub(r'<style\b.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'</?(?:p|li|div|h\d|tr|td|th|section|br|ul|ol|table|thead|tbody|header|footer|nav|blockquote|figure)\b[^>]*>', '\n', s)
    t = H.unescape(re.sub(r'<[^>]+>', '', s)).replace('−', '-')
    t = re.sub(r'[ \t ]+', ' ', t)
    return [ln.strip() for ln in t.split('\n') if ln.strip()]


def island_prose(page):
    """Hand-written text kept in a JSON island and drawn by the page's script (Stop the Cap's weekly notes)."""
    out = []
    m = re.search(r'<script id="recap-data" type="application/json">(.*?)</script>', page, re.S)
    if not m:
        return out
    def walk(x):
        if isinstance(x, str):
            if len(x) > 30 and ' ' in x:
                out.append(x.replace('\u2212', '-'))
        elif isinstance(x, list):
            for v in x: walk(v)
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in ('url', 'sources', 'name'): walk(v)
    for w in json.loads(m.group(1).replace('<\\/', '</')).get('weeks', []):
        walk(w.get('notes') or {})
    return out


class Report:
    def __init__(self):
        self.items = []

    def err(self, rule, msg, ctx=''):
        self.items.append(('ERROR', rule, msg, ctx))

    def warn(self, rule, msg, ctx=''):
        self.items.append(('WARN', rule, msg, ctx))


def clip(line, a, b, pad=60):
    return ('...' if a > pad else '') + line[max(0, a - pad):b + pad] + ('...' if b + pad < len(line) else '')


def load_snapshot(path):
    d = json.load(open(path))
    stocks = {t['symbol']: t for t in d['tickers']}
    fut = {f['symbol']: f for f in d.get('futures') or []}
    etf = {s: {'price': v['price'], 'chg_pct': round(v['chg'], 2)} for s, v in (d.get('etf_proxies') or {}).items()}
    return d, stocks, fut, etf


def check_style(lines, R):
    for ln in lines:
        # direction word followed by a signed number: "fell -0.3%", "rose +1.2%"
        for m in re.finditer(DIR_WORDS + r'\s+(?:by\s+)?([+\-])' + NUM + '%', ln):
            R.err('double-sign', 'a direction word in front of a signed number reads twice ("fell minus ..."); keep only the sign', clip(ln, m.start(), m.end()))
        # ticker followed by an unsigned percentage, with or without a verb in between
        for m in re.finditer(r'\(([A-Z][A-Z0-9.\-]{0,5})\)((?:,[^,.;()]{1,45},)?)\s+(' + DIR_WORDS + r'\s+(?:by\s+)?)?(?:at\s+)?' + NUM + '%', ln):
            if NOT_DAY.match(ln[m.end():m.end() + 30]):
                continue
            R.err('unsigned-move', f'{m.group(1)}: write the move with its sign right after the ticker, e.g. "({m.group(1)}) -1.23%"', clip(ln, m.start(), m.end()))
        for m in re.finditer(r'\(([A-Z][A-Z0-9.\-]{0,5})\)\s+(?:closed\s+|ended\s+|finished\s+)?' + NUM + r'%\s+(?:lower|higher)', ln):
            R.err('unsigned-move', f'{m.group(1)}: write "({m.group(1)}) -0.04%" instead of "x% lower/higher"', clip(ln, m.start(), m.end()))
        for m in re.finditer(r'(?<!\) )\b' + DIR_WORDS + r'\s+(?:about\s+|roughly\s+|by\s+)?' + NUM + '%(?!\s+(?:above|below|from|off|since))', ln):
            if re.match(r'\s*(?:YoY|y/y|year[- ]over[- ]year|a year|annually|in 20\d\d)', ln[m.end():m.end() + 20], re.I) or \
               re.search(r'(?:revenue|sales|deliveries|earnings|EPS|income|margin|shipments|bookings|users|subscribers|market|share)\b[^.;]{0,25}$', ln[:m.start()], re.I):
                continue  # a company's yearly or business figure, not today's price move
            if re.search(r'\([A-Z][A-Z0-9.\-]{0,5}\)(?:,[^,.;()]{1,45},)?\s*$', ln[:m.start()]):
                continue  # already reported as unsigned-move
            R.err('verb-move', 'house style is a signed number ("silver -1.68%"), so the reader and the audio always hear the direction', clip(ln, m.start(), m.end()))


def check_values(lines, R, stocks, fut, etf, d, prior, alt_fut=None):
    known = {**{s: ('stock', t['price'], t['chg_pct']) for s, t in stocks.items()},
             **{s: ('etf', v['price'], v['chg_pct']) for s, v in etf.items()},
             **{s: ('fut', f['last'], f['chg_pct']) for s, f in fut.items()},
             **{v['fund']: ('etf', v['close'], v['chg_pct']) for v in (d.get('sector_funds') or {}).values()}}
    alt = {s: (f['last'], f['chg_pct']) for s, f in (alt_fut or {}).items()}   # 8am: prose may still quote the 2pm close
    for ln in lines:
        # (TICK) +1.23%  -- signed moves right after a ticker, optionally after a short aside
        for m in re.finditer(r'\(([A-Z][A-Z0-9.\-]{0,5})\)((?:,[^,.;()]{1,45},)?)\s+(?:was flat at\s+)?([+\-])' + NUM + '%', ln):
            sym, sign, val = m.group(1), m.group(3), m.group(4)
            if sym not in known or NOT_DAY.match(ln[m.end():m.end() + 30]):
                continue
            want = known[sym][2]
            got = num(sign + val)
            ok = lambda w: w is not None and abs(got - round(w, decimals(val))) <= 0.5 * 10 ** -decimals(val) + 1e-9
            if not ok(want) and not (sym in alt and ok(alt[sym][1])):
                R.err('wrong-move', f'{sym}: page says {sign}{val}%, data says {want:+.2f}%', clip(ln, m.start(), m.end()))
        for m in re.finditer(r'\(([A-Z][A-Z0-9.\-]{0,5})\)(?:\s+(?:settled|closed|was|at|to))*\s+\$?' + NUM + r'(?:\s*pts)?\s+\(([+\-]?)' + NUM + r'%\)', ln):
            sym, sign, val = m.group(1), m.group(3), m.group(4)
            if sym not in known:
                continue
            if not sign and num(val) != 0:
                R.err('unsigned-move', f'{sym}: move {val}% needs a sign', clip(ln, m.start(), m.end()))
            elif all(abs(num(sign + val) - round(w, decimals(val))) > 0.5 * 10 ** -decimals(val) + 1e-9
                     for w in [known[sym][2]] + ([alt[sym][1]] if sym in alt else []) if w is not None):
                R.err('wrong-move', f'{sym}: page says {sign}{val}%, data says {known[sym][2]:+.2f}%', clip(ln, m.start(), m.end()))
        # prices next to a ticker: "(ES) $7,854.75", "(CL) $94.77", "(VIX) 15.25", "(SYM) ... at $12.34"
        for m in re.finditer(r'\(([A-Z][A-Z0-9.\-]{0,5})\)(?:[^;()]{0,40}?\b(?:at|to)\s+)?\s*(\$?)' + NUM + r'(?!\s*%|\d|\s*(?:bp|x|to \d))', ln):
            sym, dollar, val = m.group(1), m.group(2), m.group(3)
            if sym not in known or '.' not in val and ',' not in val:
                continue
            kind, price, _ = known[sym]
            if price is None:
                continue
            if abs(num(val) - price) > max(0.006, 10 ** -decimals(val) * 0.6) and abs(num(val) - price) / max(price, 1e-9) > 0.0015:
                continue  # some other number (a level, a target); not this price
            points = sym in POINTS
            if points and dollar:
                R.err('dollar-sign', f'{sym} is quoted in points, not dollars: drop the "$" and write "pts"', clip(ln, m.start(), m.end()))
            elif sym in POINTS_UNIT and not ln[m.end():m.end() + 5].lstrip().startswith('pts'):
                R.err('points-label', f'{sym} price needs its unit: "{val} pts"', clip(ln, m.start(), m.end()))
            if not points and not dollar:
                R.err('dollar-sign', f'{sym} price needs a "$"', clip(ln, m.start(), m.end()))
        # bare prices of a named stock without "$" anywhere in the same line
        for sym in set(re.findall(r'\(([A-Z][A-Z0-9.\-]{0,5})\)', ln)):
            if sym not in stocks or sym in POINTS or not stocks[sym].get('price'):
                continue
            p = stocks[sym]['price']
            for m in re.finditer(r'(?<![\d$.,])' + re.escape(f'{p:,.2f}') + r'(?!\d|%)', ln):
                R.err('dollar-sign', f'{sym} price {p:,.2f} needs a "$"', clip(ln, m.start(), m.end()))
    # Treasury yields named in prose
    mac = d.get('macro') or {}
    for key, label in (('ust10y', '10-year'), ('ust2y', '2-year'), ('ust30y', '30-year')):
        if mac.get(key) is None:
            continue
        for ln in lines:
            for m in re.finditer(label + r'(?: Treasury)?(?: yield)?(?: fell| rose| eased| climbed| was| at)?(?: to)?\s+' + NUM + '%', ln):
                if abs(num(m.group(1)) - mac[key]) > 0.0051:
                    R.err('wrong-yield', f'{label} yield: page says {m.group(1)}%, data says {mac[key]:.2f}%', clip(ln, m.start(), m.end()))


def sector_stats(stocks):
    by = defaultdict(list)
    for t in stocks.values():
        sec = (t.get('detail') or {}).get('sector') or t.get('sector')
        if sec and t.get('chg_pct') is not None:
            by[sec].append(t)
    return {s: {'n': len(v), 'avg': round(sum(x['chg_pct'] for x in v) / len(v), 2),
                'red4': sum(1 for x in v if (x.get('red_flag_count') or 0) >= 4)} for s, v in by.items()}


def check_aggregates(page, lines, R, stocks, d, prior):
    chg = [t['chg_pct'] for t in stocks.values() if t.get('chg_pct') is not None]
    adv, dec = sum(1 for c in chg if c > 0), sum(1 for c in chg if c < 0)
    avg = round(sum(chg) / len(chg), 2) if chg else None
    red4 = sum(1 for t in stocks.values() if (t.get('red_flag_count') or 0) >= 4)
    zero = sum(1 for t in stocks.values() if (t.get('red_flag_count') or 0) == 0)
    n = len(stocks)
    tiles = dict((H.unescape(re.sub('<[^>]+>', '', l)).split('·')[0].strip().lower(), H.unescape(v).replace('−', '-'))
                 for v, l in re.findall(r'<div class="n[^"]*">([^<]+)</div>\s*<div class="l">(.*?)</div>', page))
    expect = {'unique names scanned': str(n), 'zero red flags': str(zero), '4+ red flags': str(red4),
              'average move, full universe': f'{avg:+.2f}%', 'advancing': str(adv), 'declining': str(dec),
              'unchanged': str(n - adv - dec)}
    for k, v in tiles.items():
        if k in expect and v != expect[k]:
            R.err('wrong-tile', f'tile "{k}": page says {v}, data says {expect[k]}')
    secs = sector_stats(stocks)
    funds = d.get('sector_funds') or {}
    rows = re.findall(r'#sector-[^"]*">([^<]+)</a></td><td[^>]*>([A-Z]{2,5})</td><td[^>]*>\$([\d,.]+)</td><td[^>]*>([+\-]?[\d.]+)%</td><td[^>]*>(\d+)</td><td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td><td[^>]*>(\d+)</td>', page)
    if 'id="directory-detail-data"' in page:   # the dashboard carries the sector table; other pages do not
        if sorted(H.unescape(r[0]) for r in rows) != sorted(GICS_SECTORS):
            R.err('sector-table', f'the sector table must list the 11 GICS sectors once each; it lists {sorted(H.unescape(r[0]) for r in rows)}')
    for name, fund, close, day, cnt, a, _, r4 in rows:
        name = H.unescape(name); f = funds.get(name); st = secs.get(name, {'n': 0, 'avg': None, 'red4': 0})
        if not f:
            R.err('sector-table', f'{name}: no official sector-fund data in the snapshot (run scripts/sector_table.py)'); continue
        if fund != f['fund'] or abs(num(close) - f['close']) > 0.006 or abs(num(day) - f['chg_pct']) > 0.0051:
            R.err('sector-table', f'{name}: page {fund} ${close} {day}%, data {f["fund"]} ${f["close"]} {f["chg_pct"]:+.2f}%')
        if int(cnt) != st['n'] or int(r4) != st['red4'] or (st['avg'] is not None and abs(num(H.unescape(a).rstrip('%')) - st['avg']) > 0.0051):
            R.err('sector-table', f'{name}: dashboard names {cnt} / {a} / {r4} with 4+, data {st["n"]} / {st["avg"]} / {st["red4"]}')
    for ln in lines:
        for m in FMP_ONLY.finditer(ln):
            w = m.group(1) or m.group(2)
            R.err('sector-name', f'"{w}" is FMP\'s label; use the GICS name "{FMP_TO_GICS[w]}"', clip(ln, m.start(), m.end()))
        for sec in SECTORS:
            for m in re.finditer(r'(?<![A-Za-z])' + re.escape(sec) + r'(?:\s*\(([A-Z]{2,5})\))?(?: sector)?(?: fund)?(?: \(([A-Z]{2,5})\))?(?: names)?(?: that)?(?: averaged| led the sectors at| led at| was| were| at)?\s*(?:<[^>]+>)?\(?([+\-])' + NUM + r'%', ln):
                if m.group(2) and not m.group(1):
                    m_fund = m.group(2)
                else:
                    m_fund = m.group(1)
                fund_tk = {v['fund'] for v in funds.values()} | {'XLK', 'XLF', 'XLV', 'XLY', 'XLC', 'XLI', 'XLP', 'XLE', 'XLU', 'XLRE', 'XLB'}
                if m_fund and m_fund not in fund_tk:
                    continue   # a company name ending in a sector word, e.g. "Applied Materials (AMAT)"
                got = num(m.group(3) + m.group(4)); before = ln[max(0, m.start() - 45):m.start()].lower()
                # "Health Care (XLV) +1.86%" is the official fund; "our 33 Health Care names averaged +2.25%" is the universe average
                universe = not m_fund and (bool(re.search(r'(our|dashboard) (\d+ )?$', before)) or 'names' in ln[m.start():m.end()])
                want = (secs.get(sec) or {}).get('avg') if universe else (funds.get(sec) or {}).get('chg_pct')
                if want is None and not universe and sec in secs:
                    want = secs[sec]['avg']
                if want is not None and abs(got - want) > 0.0051:
                    R.err('wrong-sector', f'{sec}: page says {m.group(3)}{m.group(4)}%, ' + (f'the official sector fund says {want:+.2f}%' if not universe else f'the dashboard names average {want:+.2f}%') +
                          ('' if universe else ' (write "our N ... names averaged" for the universe average)'), clip(ln, m.start(), m.end()))
        if funds:
            up = sum(1 for v in funds.values() if v['chg_pct'] > 0)
            for m in re.finditer(r'\b(\d+) of (?:the )?11 (?:S&P 500 )?sectors (?:rose|gained|advanced|were higher)', ln):
                if int(m.group(1)) != up:
                    R.err('wrong-count', f'page says {m.group(1)} of 11 sectors rose, the sector funds say {up}', clip(ln, m.start(), m.end()))
        for m in re.finditer(r'\b(\d+) of (\d+) names (?:carry|with|have) 4 or more red flags', ln):
            if int(m.group(1)) != red4 or int(m.group(2)) != n:
                R.err('wrong-count', f'page says {m.group(1)} of {m.group(2)} with 4+ red, data says {red4} of {n}', clip(ln, m.start(), m.end()))
        for m in re.finditer(r'(\d+) advanc\w*', ln):
            if int(m.group(1)) not in (adv,) and 'names' not in ln[m.end():m.end() + 8]:
                R.err('wrong-count', f'advancers: page says {m.group(1)}, data says {adv}', clip(ln, m.start(), m.end()))
        for m in re.finditer(r'(\d+) declin\w*', ln):
            if int(m.group(1)) != dec:
                R.err('wrong-count', f'decliners: page says {m.group(1)}, data says {dec}', clip(ln, m.start(), m.end()))


def check_flag_changes(lines, R, stocks, prior):
    """Red-flag counts quoted as changes, "(C) (2 -> 5)" or "(GS) went from 3 to 6", against both days' data."""
    if not prior:
        return
    before = {t['symbol']: t.get('red_flag_count') for t in prior['tickers']}
    pat = [r'\(([A-Z][A-Z0-9.\-]{0,5})\)\s*\((\d+)\s*\u2192\s*(\d+)\)',
           r'\(([A-Z][A-Z0-9.\-]{0,5})\)(?: rose| went| fell| dropped| moved)? from (\d+) to (\d+)(?! ?%)']
    for ln in lines:
        for p in pat:
            for m in re.finditer(p, ln):
                sym, a, b = m.group(1), int(m.group(2)), int(m.group(3))
                if sym in stocks and sym in before and (a, b) != (before[sym], stocks[sym].get('red_flag_count')):
                    R.err('wrong-flags', f'{sym}: page says {a} -> {b} red flags, data says {before[sym]} -> {stocks[sym].get("red_flag_count")}', clip(ln, m.start(), m.end()))


def check_cards(page, R, fut):
    for name, px, cls, ch in re.findall(r'<div class="sym">([^<(]+?)\s*\([^<]*\)</div>\s*<div class="px[^"]*">([^<]+)</div>\s*<div class="chg (\w+)[^"]*">([^<]+)</div>', page):
        sym = name.strip()
        f = fut.get(sym)
        if not f:
            continue
        px, ch = H.unescape(px).strip(), H.unescape(ch).strip().replace('−', '-')
        unit = px.endswith(' pts'); px = px.replace(' pts', '')
        val = num(px.lstrip('$'))
        if sym in POINTS_UNIT and not unit:
            R.err('points-label', f'futures card {sym}: write "{px} pts"')
        if abs(val - f['last']) > 10 ** -decimals(px) * 0.6 + 1e-9:
            R.err('wrong-card', f'futures card {sym}: page {px}, data {f["last"]}')
        if (sym in POINTS) == px.startswith('$'):
            R.err('dollar-sign', f'futures card {sym}: ' + ('points, drop the "$"' if sym in POINTS else 'needs a "$"'), px)
        if not re.match(r'^[+\-]\d', ch) and num(ch.rstrip('%')) != 0:
            R.err('unsigned-move', f'futures card {sym}: change {ch} has no sign')
        elif abs(num(ch.rstrip('%')) - f['chg_pct']) > 0.0051:
            R.err('wrong-card', f'futures card {sym}: change {ch}, data {f["chg_pct"]:+.2f}%')
        want = 'up' if f['chg_pct'] > 0 else 'down' if f['chg_pct'] < 0 else 'flat'
        if cls != want:
            R.err('wrong-color', f'futures card {sym}: colored "{cls}" but the move is {want}')


def check_more_formats(page, R, stocks, fut, alt_fut=None):
    """Contract tables ("<td>ES (E-Mini S&P 500)</td><td>7,854.75</td>") and chart captions ("90 sessions: $a -> $b")."""
    for sym, px in re.findall(r'<td>([A-Z]{1,4}) \([^<]*\)</td>\s*<td[^>]*>([^<]+)</td>', page):
        if sym not in fut:
            continue
        px = H.unescape(px).strip()
        if sym in POINTS_UNIT and not px.endswith(' pts'):
            R.err('points-label', f'table row {sym}: write "{px} pts"')
        px = px.replace(' pts', '')
        if (sym in POINTS) == px.startswith('$'):
            R.err('dollar-sign', f'table row {sym}: ' + ('points, drop the "$"' if sym in POINTS else 'needs a "$"'), px)
        elif all(abs(num(px.lstrip('$')) - F[sym]['last']) > 10 ** -decimals(px) * 0.6 + 1e-9 for F in (fut, alt_fut or {}) if sym in F):
            R.err('wrong-table', f'table row {sym}: page {px}, data {fut[sym]["last"]}')
    for sym, body in re.findall(r'<h3[^>]*>([A-Z.]{1,6}) &middot;[^<]*</h3>((?:(?!<h3).){0,4000}?\d+ sessions: [^<]+)', page, re.S):
        cap = H.unescape(re.search(r'\d+ sessions: [^<]+', body).group(0))
        m = re.match(r'\d+ sessions: (\$?)([\d.,]+) \u2192 (\$?)([\d.,]+) \(([+\-])([\d.]+)%\)', cap)
        if not m:
            R.err('chart-caption', f'{sym}: caption not in the form "90 sessions: $a \u2192 $b (+x.x%)"', cap); continue
        if sym in stocks and not (m.group(1) and m.group(3)):
            R.err('dollar-sign', f'{sym} chart caption: prices need a "$"', cap)
        a_, b_ = num(m.group(2)), num(m.group(4))
        if abs((b_ / a_ - 1) * 100 - num(m.group(5) + m.group(6))) > 0.051:
            R.err('chart-caption', f'{sym}: {cap} -- the percentage does not match the two prices')
        if sym in stocks and abs(b_ - stocks[sym]['price']) > 0.006:
            R.err('chart-caption', f'{sym}: chart ends at {b_}, today\'s price is {stocks[sym]["price"]}')


def check_tables(page, R, stocks):
    # Movers / flagged tables: <td class="tk">SYM</td> ... <td class="px-cell ...">$PRICE</td><td class="px-cell up|down">+X%</td>
    for sym, row in re.findall(r'<tr[^>]*>\s*<td[^>]*>\s*(?:<[^>]+>\s*)*<span class="tk">([A-Z.\-]+)</span>(.*?)</tr>', page, re.S):
        t = stocks.get(sym)
        if not t:
            continue
        cells = [H.unescape(re.sub('<[^>]+>', '', c)).strip().replace('−', '-') for c in re.findall(r'<td[^>]*class="px-cell[^"]*"[^>]*>(.*?)</td>', row, re.S)]
        for c in cells:
            for p in re.findall(r'(\$?)(\d[\d,]*\.\d{2})(?!%)', c):
                if p[1] and abs(num(p[1]) - (t.get('price') or 0)) < 0.006 and not p[0]:
                    R.err('dollar-sign', f'table row {sym}: price {p[1]} needs a "$"')
                elif p[0] and abs(num(p[1]) - (t.get('price') or 0)) > 0.006:
                    R.err('wrong-table', f'table row {sym}: price {p[0]}{p[1]}, data ${t["price"]:,.2f}')
            for s, v in re.findall(r'(?<![\w.])([+\-]?)(\d+\.\d{2})%', c):
                if not s and float(v) != 0:
                    R.err('unsigned-move', f'table row {sym}: {v}% has no sign')
                elif abs(num(s + v) - t['chg_pct']) > 0.0051:
                    R.err('wrong-table', f'table row {sym}: {s}{v}%, data {t["chg_pct"]:+.2f}%')


def check_islands(page, R, stocks):
    for name in ('directory-detail-data', 'analyzer-data'):
        m = re.search(r'<script id="' + name + r'" type="application/json">(.*?)</script>', page, re.S)
        if not m:
            continue
        data = json.loads(m.group(1).replace('<\\/', '</'))
        rows = data if isinstance(data, dict) else {r.get('symbol'): r for r in data}
        bad = 0
        for sym, r in rows.items():
            t = stocks.get(sym)
            if not isinstance(r, dict):
                continue
            if not t:
                R.err('island', f'{name}: {sym} is not in the snapshot'); bad += 1; continue
            sec = r.get('sector') or (r.get('detail') or {}).get('sector')
            if sec and sec not in GICS_SECTORS:
                R.err('island', f'{name}: {sym} sector "{sec}" is not a GICS name'); bad += 1
            for k in ('price', 'chg_pct', 'red_flag_count'):
                if k in r and r[k] is not None and t.get(k) is not None and abs(r[k] - t[k]) > 1e-6:
                    R.err('island', f'{name}: {sym} {k} {r[k]} vs snapshot {t[k]}'); bad += 1
        missing = set(stocks) - set(rows)
        if missing and name == 'analyzer-data':
            R.err('island', f'{name}: {len(missing)} snapshot names missing, e.g. {sorted(missing)[:5]}')


def check_bitcoin(lines, R, d, alt_b=None):
    b = d.get('bitcoin') or {}
    alt_b = alt_b or {}
    if not b:
        return
    want = {f'{b["price"]:,.2f}'} if b.get('price') else set()
    for ln in lines:
        if 'Bitcoin' not in ln and 'BTC' not in ln:
            continue
        for m in re.finditer(r'Bitcoin(?: \(BTC\))?(?: traded at| at)?\s+(\$?)' + NUM + r'(?:\s*\(([+\-]?)' + NUM + r'%\))?', ln):
            dollar, val, s, ch = m.group(1), m.group(2), m.group(3), m.group(4)
            if '.' not in val and ',' not in val:
                continue
            if not dollar:
                R.err('dollar-sign', 'Bitcoin price needs a "$"', clip(ln, m.start(), m.end()))
            if b.get('price') and abs(num(val) - b['price']) > 0.006 and not (alt_b.get('price') and abs(num(val) - alt_b['price']) <= 0.006):
                R.err('wrong-btc', f'Bitcoin: page {val}, data {b["price"]:,.2f}', clip(ln, m.start(), m.end()))
            if ch is not None:
                if not s:
                    R.err('unsigned-move', 'Bitcoin move needs a sign', clip(ln, m.start(), m.end()))
                elif abs(num(s + ch) - b['chg_pct']) > 0.0051 and not (alt_b.get('chg_pct') is not None and abs(num(s + ch) - alt_b['chg_pct']) <= 0.0051):
                    R.err('wrong-btc', f'Bitcoin move: page {s}{ch}%, data {b["chg_pct"]:+.2f}%', clip(ln, m.start(), m.end()))


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    page = open(a[0]).read()
    R = Report()
    lines = visible_text(page)
    lines += island_prose(page)
    check_style(lines, R)
    if '--snapshot' in a:
        d, stocks, fut, etf = load_snapshot(a[a.index('--snapshot') + 1])
        alt_fut = alt_btc = None
        if '--morning' in a:   # 8am: the futures tape and Bitcoin are this morning's; other tables may still carry 2pm values
            mm = json.load(open(a[a.index('--morning') + 1]))
            alt_fut = fut
            fut = {f['symbol']: f for f in mm.get('futures') or []}
            alt_btc = d.get('bitcoin')
            mmac = {k: v for k, v in (mm.get('macro') or {}).items() if k in ('ust10y', 'ust2y', 'ust30y')}   # newer cash yields
            d = dict(d, bitcoin=mm.get('bitcoin') or d.get('bitcoin'), macro=dict(d.get('macro') or {}, **mmac))
        prior = json.load(open(a[a.index('--prior') + 1])) if '--prior' in a else None
        check_values(lines, R, stocks, fut, etf, d, prior, alt_fut)
        check_aggregates(page, lines, R, stocks, d, prior)
        check_cards(page, R, fut)
        check_tables(page, R, stocks)
        check_more_formats(page, R, stocks, fut, alt_fut)
        check_islands(page, R, stocks)
        check_bitcoin(lines, R, d, alt_btc)
        check_flag_changes(lines, R, stocks, prior)
    seen = set()
    for lvl, rule, msg, ctx in R.items:
        if (rule, msg, ctx) in seen:
            continue
        seen.add((rule, msg, ctx))
        print(f'{lvl} [{rule}] {msg}' + (f'\n      {ctx}' if ctx else ''))
    errs = sum(1 for i in R.items if i[0] == 'ERROR')
    print(f'\n{errs} error(s), {sum(1 for i in R.items if i[0] == "WARN")} warning(s)' + (' -- do not publish' if errs else ' -- clean'))
    sys.exit(1 if errs else 0)


if __name__ == '__main__':
    main()
