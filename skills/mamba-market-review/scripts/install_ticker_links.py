"""Install (or update) the shared ticker linker from assets/ticker-links.html on any Mamba page.

Usage: python3 install_ticker_links.py page.html out.html
  Every ticker symbol on the page becomes a link: dashboard-universe stocks open the 10-Point Analyzer (#t-SYM),
  the 100 ETF Explorer funds open the ETF Explorer (#e-SYM), futures open TradingView, and any other real ticker
  (from the ETF holdings files) opens TradingView. Replaces an earlier copy (including the dashboard's old
  stocks-only <script id="ticker-links">), otherwise inserts it before the Listen player. links_block() is used by
  the page builders (etf_explorer.py, world_watch.py, weekly_recap.py).
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
FUTURES = {'ES': 'CME_MINI:ES1!', 'NQ': 'CME_MINI:NQ1!', 'YM': 'CBOT_MINI:YM1!', 'RTY': 'CME_MINI:RTY1!',
           'ZB': 'CBOT:ZB1!', 'ZN': 'CBOT:ZN1!', 'ZF': 'CBOT:ZF1!', 'ZT': 'CBOT:ZT1!', 'CL': 'NYMEX:CL1!',
           'BZ': 'NYMEX:BB1!', 'NG': 'NYMEX:NG1!', 'RB': 'NYMEX:RB1!', 'HO': 'NYMEX:HO1!', 'GC': 'COMEX:GC1!',
           'SI': 'COMEX:SI1!', 'HG': 'COMEX:HG1!', 'PL': 'NYMEX:PL1!', 'PA': 'NYMEX:PA1!', 'ZM': 'CBOT:ZM1!',
           'CC': 'ICEUS:CC1!', 'DX': 'ICEUS:DX1!', 'BTC': 'BITSTAMP:BTCUSD', 'ETH': 'BITSTAMP:ETHUSD', 'VIX': 'TVC:VIX'}
OLD = re.compile(r'(?:<style id="ticker-links-css">.*?</style>\s*)?<script id="ticker-links">.*?</script>', re.S)


def url(name):
    p = os.path.join(ROOT, 'reports', name)
    return open(p).read().strip() if os.path.exists(p) else ''


def link_data():
    snaps = sorted(glob.glob(os.path.join(ROOT, 'reports', '20*', 'full-study.json')))
    stocks = sorted({t['symbol'] for t in json.load(open(snaps[-1]))['tickers']}) if snaps else []
    etfs = sorted({f['s'] for f in json.load(open(os.path.join(ROOT, 'etf', 'etf_list.json')))})
    other = set()
    for f in glob.glob(os.path.join(ROOT, 'etf', 'holdings', '*.json')):
        for r in json.load(open(f)).get('rows', []):
            if r.get('tk') and re.fullmatch(r'[A-Z]{1,5}(?:[.\-][A-Z]{1,2})?', r['tk']):
                other.add(r['tk'])
    other -= set(stocks) | set(etfs)
    return {'analyzerUrl': url('.analyzer-url.txt'), 'etfUrl': url('.etf-url.txt'), 'stocks': stocks, 'etfs': etfs,
            'other': sorted(other), 'futures': FUTURES}


def links_block():
    tpl = open(os.path.join(ROOT, 'assets', 'ticker-links.html')).read().strip()
    return tpl.replace('__LINKDATA__', json.dumps(link_data(), separators=(',', ':')).replace('</', '<\\/'))


def install(s):
    block = links_block()
    if OLD.search(s):
        return OLD.sub(lambda _: block, s, count=1)
    i = s.find('<style id="listen-css">')
    return (s[:i] + block + '\n' + s[i:]) if i >= 0 else (s.rstrip() + '\n' + block + '\n')


def main(src, out):
    s = open(src).read()
    if '<body>' in s[:3000]:
        s = s.split('<body>', 1)[1]
    s = re.sub(r'</body>\s*</html>\s*$', '', s)
    open(out, 'w').write(install(s))
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
