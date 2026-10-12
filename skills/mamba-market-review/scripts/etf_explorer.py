"""Build the ETF Explorer page from the 100-fund list, FMP fund stats and the SEC holdings files.

Usage: python3 etf_explorer.py out.html
  Reads etf/etf_list.json and etf/holdings/*.json (from etf_holdings.py); pulls fund stats and returns from FMP
  (FMP_API_KEY): etf/info, stock-price-change and batch-quote. Writes etf/stats.json and the page to out.html.
"""
import json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')


def fmp(path, **kw):
    kw['apikey'] = os.environ['FMP_API_KEY']
    url = 'https://financialmodelingprep.com/stable/' + path + '?' + urllib.parse.urlencode(kw, safe=',')
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def overlap(a, b):
    """Share of weight two funds hold in common (sum of the smaller weight per shared name)."""
    wa = {r['tk'] or r['name']: r['pct'] for r in a}
    wb = {r['tk'] or r['name']: r['pct'] for r in b}
    return sum(min(wa[k], wb[k]) for k in wa.keys() & wb.keys())


def main(out_path):
    etfs = json.load(open(os.path.join(ROOT, 'etf', 'etf_list.json')))
    syms = [e['s'] for e in etfs]
    with ThreadPoolExecutor(8) as ex:
        infos = dict(ex.map(lambda s: (s, (fmp('etf/info', symbol=s) or [None])[0]), syms))
    chg, quote = {}, {}
    for i in range(0, len(syms), 50):
        for r in fmp('stock-price-change', symbol=','.join(syms[i:i + 50])) or []:
            chg[r['symbol']] = r
    for r in fmp('batch-quote', symbols=','.join(syms)) or []:
        quote[r['symbol']] = r
    funds = []
    for e in etfs:
        s = e['s']
        i = infos.get(s) or {}
        c = chg.get(s, {})
        hp = os.path.join(ROOT, 'etf', 'holdings', f'{s}.json')
        h = json.load(open(hp)) if os.path.exists(hp) else {'kind': 'missing'}
        sectors = sorted([[x['industry'], round(x['exposure'], 1)] for x in (i.get('sectorsList') or []) if x.get('exposure')],
                         key=lambda x: -x[1])
        funds.append({**e, 'name': i.get('name') or quote.get(s, {}).get('name'), 'issuer': i.get('etfCompany'),
                      'aum': i.get('assetsUnderManagement'), 'er': i.get('expenseRatio'), 'inc': i.get('inceptionDate'),
                      'cls': i.get('assetClass'), 'price': quote.get(s, {}).get('price'),
                      'd1': quote.get(s, {}).get('changePercentage'), 'd5': c.get('5D'), 'm1': c.get('1M'),
                      'ytd': c.get('ytd'), 'y1': c.get('1Y'), 'sectors': sectors[:11], 'h': h})
    # Most similar funds by holdings overlap.
    held = [f for f in funds if f['h'].get('rows')]
    for f in held:
        sims = sorted(((round(overlap(f['h']['rows'], g['h']['rows']), 1), g['s']) for g in held if g is not f), reverse=True)
        f['similar'] = [[s, o] for o, s in sims[:3] if o >= 5]
    stats = {f['s']: {k: f[k] for k in ('aum', 'er', 'inc', 'price', 'd5', 'm1', 'ytd', 'y1')} for f in funds}
    json.dump(stats, open(os.path.join(ROOT, 'etf', 'stats.json'), 'w'), indent=0)
    idx_p = os.path.join(ROOT, 'etf', 'holdings-index.json')
    index = json.load(open(idx_p)) if os.path.exists(idx_p) else {}
    urls = {}
    for k, fn in (('dashboard', '.dashboard-url.txt'), ('analyzer', '.analyzer-url.txt'), ('weekly', '.weekly-url.txt'),
                  ('worldwatch', '.worldwatch-url.txt')):
        p = os.path.join(ROOT, 'reports', fn)
        urls[k] = open(p).read().strip() if os.path.exists(p) else ''
    data = {'funds': funds, 'index': index, 'urls': urls,
            'built_at': datetime.now(timezone.utc).isoformat(timespec='minutes')}
    tpl = open(os.path.join(HERE, 'etf_explorer_template.html')).read()
    open(out_path, 'w').write(tpl.replace('__DATA__', json.dumps(data, separators=(',', ':')).replace('</', '<\\/')))
    kinds = {}
    for f in funds:
        kinds[f['h'].get('kind')] = kinds.get(f['h'].get('kind'), 0) + 1
    print('built', out_path, kinds, os.path.getsize(out_path) // 1024, 'KB')


if __name__ == '__main__':
    main(sys.argv[1])
