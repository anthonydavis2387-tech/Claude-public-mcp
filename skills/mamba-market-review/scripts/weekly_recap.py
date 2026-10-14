"""Build the STOP THE CAP weekly recap page (Saturday morning MT).

Usage:
  python3 weekly_recap.py build WEEK_END notes.json   # WEEK_END = the Friday, YYYY-MM-DD
      Pulls the week's prices from FMP (FMP_API_KEY env var), reads the week's saved daily snapshots,
      merges in the hand-written notes (see references/weekly-recap.md) and writes
      reports/weekly/WEEK_END.json.
  python3 weekly_recap.py render out.html [--prior published.html]
      With --prior, weeks found on the live page that have no local file are kept too.
      Renders every reports/weekly/*.json into one page (newest week shown, older weeks in the
      archive picker). Prints the phone-reminder text on stdout.
"""
import glob, html, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, '..', 'reports')
WEEKLY = os.path.join(REPORTS, 'weekly')
MT = ZoneInfo('America/Denver')
B = 'https://financialmodelingprep.com/stable/'

INDEXES = [('SPY', 'S&P 500'), ('QQQ', 'Nasdaq 100'), ('DIA', 'Dow 30'), ('IWM', 'Russell 2000'), ('RSP', 'S&P 500 equal-weight')]
SECTORS = [('XLK', 'Technology'), ('XLF', 'Financial Services'), ('XLV', 'Healthcare'), ('XLE', 'Energy'),
           ('XLI', 'Industrials'), ('XLY', 'Consumer Cyclical'), ('XLP', 'Consumer Defensive'), ('XLU', 'Utilities'),
           ('XLB', 'Basic Materials'), ('XLRE', 'Real Estate'), ('XLC', 'Communication Services')]
MACRO = [('^VIX', 'VIX (fear gauge)'), ('TLT', '20+ yr Treasuries'), ('UUP', 'US dollar'), ('USO', 'WTI crude oil'),
         ('GLD', 'Gold'), ('BTCUSD', 'Bitcoin')]
ECON_KEEP = ('FOMC', 'Fed Interest Rate', 'Fed Chair', 'Beige Book', 'Nonfarm', 'Unemployment Rate', 'Inflation Rate',
             'Core Inflation', 'PCE', 'Producer Price', 'Retail Sales MoM', 'GDP', 'Initial Jobless', 'ISM',
             'Michigan Consumer Sentiment', 'Existing Home Sales', 'New Home Sales', 'Industrial Production',
             'Durable Goods', 'JOLTs')


def get(path, **kw):
    kw['apikey'] = os.environ['FMP_API_KEY']
    url = B + path + '?' + urllib.parse.urlencode(kw, safe=',^')
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 * (attempt + 1)); continue
            return None
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def closes(sym, start, end):
    d = get('historical-price-eod/light', symbol=sym, **{'from': start, 'to': end})
    return sym, sorted([(x['date'], x['price']) for x in d], key=lambda x: x[0]) if isinstance(d, list) else []


def latest_snapshot(week_end):
    for f in sorted(glob.glob(os.path.join(REPORTS, '20*', 'full-study.json')), reverse=True):
        if os.path.basename(os.path.dirname(f)) <= week_end:
            return json.load(open(f))
    raise SystemExit('no full-study snapshot found')


def build(week_end, notes_path):
    notes = json.load(open(notes_path))
    fri = date.fromisoformat(week_end)
    mon = fri - timedelta(days=4)
    days = [(mon + timedelta(days=i)).isoformat() for i in range(5)]
    start = (mon - timedelta(days=10)).isoformat()
    snap = latest_snapshot(week_end)
    uni = {t['symbol']: t for t in snap['tickers']}
    watch = [s for s in notes.get('watchlist', [])]
    syms = [s for s, _ in INDEXES + SECTORS + MACRO] + sorted(set(uni) | set(watch))
    with ThreadPoolExecutor(6) as ex:
        hist = dict(ex.map(lambda s: closes(s, start, week_end), syms))

    def series(sym):
        h = hist.get(sym) or []
        prior_fri = (mon - timedelta(days=3)).isoformat()
        base = [x for x in h if x[0] <= prior_fri]  # Friday-to-Friday, also for 7-day markets like Bitcoin
        wk = [x for x in h if x[0] in days]
        if not base or not wk:
            return None
        pts = [base[-1]] + wk
        return {'base_date': base[-1][0], 'points': [[d, round(p, 4)] for d, p in pts],
                'week_pct': round((wk[-1][1] / base[-1][1] - 1) * 100, 2)}

    def block(pairs):
        out = []
        for s, label in pairs:
            se = series(s)
            if se:
                out.append({'s': s, 'label': label, **se})
        return out

    moves = []
    for s, t in uni.items():
        se = series(s)
        if se:
            moves.append({'s': s, 'name': t.get('name'), 'sector': (t.get('detail') or {}).get('sector') or t.get('sector'),
                          'week_pct': se['week_pct'], 'points': se['points']})
    moves.sort(key=lambda m: m['week_pct'])
    up = sum(1 for m in moves if m['week_pct'] > 0)

    # The dashboard's own daily readings, from the snapshots the 8am/2pm runs saved.
    daily = []
    for d in days:
        row = {'date': d}
        fp = os.path.join(REPORTS, d, 'full-study.json')
        if os.path.exists(fp):
            f = json.load(open(fp))
            ch = sorted([(x['chg_pct'], x['symbol']) for x in f['tickers'] if x.get('chg_pct') is not None])
            row.update(saved=True, advancers=sum(1 for c, _ in ch if c > 0), names=len(ch),
                       vix=(f.get('macro') or {}).get('vix'), ust10y=(f.get('macro') or {}).get('ust10y'),
                       best=[[s, c] for c, s in ch[-3:][::-1]], worst=[[s, c] for c, s in ch[:3]])
        else:
            row['saved'] = False
        spy = dict((series('SPY') or {}).get('points', []))
        prev = [p for dd, p in sorted(spy.items()) if dd < d]
        if d in spy and prev:
            row['spy_pct'] = round((spy[d] / prev[-1] - 1) * 100, 2)
        daily.append(row)

    nxt_mon = fri + timedelta(days=3)
    nxt_fri = nxt_mon + timedelta(days=4)
    earn = get('earnings-calendar', **{'from': nxt_mon.isoformat(), 'to': nxt_fri.isoformat()}) or []
    earnings = sorted([{'s': e['symbol'], 'name': uni[e['symbol']].get('name'), 'date': e['date'],
                        'eps_est': e.get('epsEstimated')} for e in earn if e.get('symbol') in uni],
                      key=lambda e: (e['date'], e['s']))
    econ = get('economic-calendar', **{'from': nxt_mon.isoformat(), 'to': nxt_fri.isoformat()}) or []
    events, seen = [], set()
    for e in sorted(econ, key=lambda e: e['date']):
        if e.get('country') != 'US' or not any(k.lower() in e['event'].lower() for k in ECON_KEEP):
            continue
        if e.get('impact') not in ('High', 'Medium') or e['event'] in seen:
            continue
        if any(k in e['event'] for k in ('Inflation Rate (', 'Existing Home Sales (', 'New Home Sales (')):
            continue  # index-level or unit duplicates of the MoM/YoY lines
        seen.add(e['event'])
        when = datetime.fromisoformat(e['date']).replace(tzinfo=timezone.utc).astimezone(MT)
        events.append({'when': when.strftime('%a %b %-d, %-I:%M %p MT'), 'day': when.date().isoformat(),
                       'event': e['event'], 'estimate': e.get('estimate'), 'previous': e.get('previous'),
                       'impact': e.get('impact')})

    out = {'week_end': week_end, 'week_start': days[0], 'days': days, 'built_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'indexes': block(INDEXES), 'sectors': block(SECTORS), 'macro': block(MACRO),
           'breadth': {'up': up, 'total': len(moves)}, 'best': moves[-10:][::-1], 'worst': moves[:10],
           'watchlist': [{'s': s, 'name': (uni.get(s) or {}).get('name'), **(series(s) or {})} for s in watch],
           'daily': daily, 'next_earnings': earnings, 'next_events': events, 'notes': notes}
    os.makedirs(WEEKLY, exist_ok=True)
    path = os.path.join(WEEKLY, f'{week_end}.json')
    json.dump(out, open(path, 'w'), indent=1)
    print(f'wrote {path}: {len(moves)} names, {up} up; {len(earnings)} earnings, {len(events)} events next week')


def prior_weeks(published_path):
    """Weeks already on the live page (its recap-data island), so the archive survives even when a run can't save to GitHub."""
    import re
    try:
        html = open(published_path).read()
        m = re.search(r'<script id="recap-data" type="application/json">(.*?)</script>', html, re.S)
        return json.loads(m.group(1).replace('<\\/', '</'))['weeks'] if m else []
    except Exception:
        return []


def render(out_path, prior=None):
    weeks = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(WEEKLY, '*.json')), reverse=True)]
    have = {w['week_end'] for w in weeks}
    if prior:
        weeks += [w for w in prior_weeks(prior) if w.get('week_end') not in have]
        weeks.sort(key=lambda w: w['week_end'], reverse=True)
    if not weeks:
        raise SystemExit('no weekly files')
    urls = {}
    for k, f in (('dashboard', '.dashboard-url.txt'), ('analyzer', '.analyzer-url.txt'), ('etf', '.etf-url.txt'),
                 ('worldwatch', '.worldwatch-url.txt'), ('affirmations', '.affirmations-url.txt')):
        p = os.path.join(REPORTS, f)
        urls[k] = open(p).read().strip() if os.path.exists(p) else ''
    tpl = open(os.path.join(HERE, 'weekly_recap_template.html')).read()
    data = json.dumps({'weeks': weeks, 'urls': urls}, separators=(',', ':')).replace('</', '<\\/')
    sys.path.insert(0, HERE)
    from install_listen_player import player_block
    from install_ticker_links import links_block
    open(out_path, 'w').write(tpl.replace('__DATA__', data) + '\n' + links_block() + '\n' + player_block() + '\n')
    w = weeks[0]
    spy = next((i for i in w['indexes'] if i['s'] == 'SPY'), None)
    lead = w['notes'].get('push') or w['notes'].get('headline', '')
    print(f"STOP THE CAP: your weekly recap is ready. S&P 500 {spy['week_pct']:+.2f}% this week. {lead}".strip() if spy else
          f"STOP THE CAP: your weekly recap is ready. {lead}".strip())


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'build':
        build(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 3 and sys.argv[1] == 'render':
        render(sys.argv[2], sys.argv[4] if len(sys.argv) >= 5 and sys.argv[3] == '--prior' else None)
    else:
        print(__doc__); sys.exit(1)
