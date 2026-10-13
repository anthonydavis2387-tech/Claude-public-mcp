"""Pull full ETF holdings from the SEC's free N-PORT filings for the ETF Explorer.

Usage: python3 etf_holdings.py [SYMBOL ...]   (no symbols = all 100 funds)
  Reads etf/etf_list.json (the 100 funds) and writes:
    etf/holdings/{SYMBOL}.json  - the fund's latest reported holdings (top 250 by weight, plus totals)
    etf/holdings-index.json     - reverse map: dashboard ticker -> [[ETF, weight %], ...] across all 100 funds
  Needs network access to www.sec.gov and data.sec.gov. SEC asks for <= 10 requests/second and a contact in the
  User-Agent (SEC_USER_AGENT env var overrides the default below). Uses FMP (FMP_API_KEY) only to read the CUSIPs of
  the dashboard's names so holdings can link to the 10-Point Analyzer.

Funds are matched to SEC series through company_tickers_mf.json. Unit-investment-trust ETFs (SPY, QQQ) do not
file N-PORT, so they borrow the holdings of a fund tracking the same index (PROXY); DIA's price-weighted Dow
weights are computed from the 30 share prices. Commodity and crypto trusts hold
the asset itself and have no N-PORT; they are marked `direct`.
"""
import glob, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'etf', 'holdings')
UA = os.environ.get('SEC_USER_AGENT', 'Mamba Market Review anthonydavis2387@gmail.com')  # SEC requires a real contact
PROXY = {'SPY': 'IVV', 'QQQ': 'QQQM', 'MDY': 'IJH'}  # same index, open-end fund that files N-PORT
DOW30 = ('AAPL AMGN AMZN AXP BA CAT CRM CSCO CVX DIS GS HD HON IBM JNJ JPM KO MCD MMM MRK MSFT NKE NVDA PG SHW '
         'TRV UNH V VZ WMT').split()
DIRECT = {'GLD': 'Physical gold bullion', 'SLV': 'Physical silver bullion', 'IBIT': 'Bitcoin', 'ETHA': 'Ether',
          'USO': 'WTI crude oil futures', 'UNG': 'Natural gas futures', 'CPER': 'Copper futures',
          'DBC': 'A basket of commodity futures', 'DBA': 'Agricultural commodity futures',
          'UUP': 'US dollar index futures'}
KEEP = 250
_last = [0.0]


def sec(url, as_json=False):
    for attempt in range(5):
        wait = 0.15 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'identity'})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            return json.loads(body) if as_json else body
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):
                time.sleep(15 * (attempt + 1)); continue
            if e.code == 404:
                return None
            raise
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f'SEC request kept failing: {url}')


def fmp(path, **kw):
    kw['apikey'] = os.environ['FMP_API_KEY']
    url = 'https://financialmodelingprep.com/stable/' + path + '?' + urllib.parse.urlencode(kw)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def latest_nport(cik, series):
    """Newest NPORT-P filing for this series: (accession, report date) or None."""
    feed = sec('https://www.sec.gov/cgi-bin/browse-edgar?' + urllib.parse.urlencode(
        {'action': 'getcompany', 'CIK': series, 'type': 'NPORT-P', 'dateb': '', 'owner': 'include', 'count': '10', 'output': 'atom'}))
    if not feed:
        return None
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(feed)
    for entry in root.findall('a:entry', ns):
        content = entry.find('a:content', ns)
        acc = content.findtext('a:accession-number', default='', namespaces=ns) if content is not None else ''
        if not acc:
            m = re.search(r'(\d{10}-\d{2}-\d{6})', ET.tostring(entry, encoding='unicode'))
            acc = m.group(1) if m else ''
        if acc:
            return acc
    return None


def find_by_name(fund_name):
    """For funds too new for company_tickers_mf.json: full-text search N-PORT filings for the fund's name and keep
    the newest filing whose own series name matches. Returns (cik, accession, xml) or None."""
    r = sec('https://efts.sec.gov/LATEST/search-index?' + urllib.parse.urlencode({'q': f'"{fund_name}"', 'forms': 'NPORT-P'}), as_json=True)
    hits = sorted((r or {}).get('hits', {}).get('hits', []), key=lambda h: h['_source'].get('period_ending') or '', reverse=True)
    for h in hits[:6]:
        acc, cik = h['_id'].split(':')[0], int(h['_source']['ciks'][0])
        xml = sec(f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-", "")}/primary_doc.xml')
        if xml and norm(parse_nport(xml, header_only=True)) == norm(fund_name):
            return cik, acc, xml
    return None


def parse_nport(xml_bytes, header_only=False):
    root = ET.fromstring(xml_bytes)
    strip = lambda t: t.split('}', 1)[-1]
    for el in root.iter():
        el.tag = strip(el.tag)
    gen = root.find('.//genInfo')
    if header_only:
        return gen.findtext('seriesName') if gen is not None else ''
    fund = root.find('.//fundInfo')
    rows = []
    for inv in root.iter('invstOrSec'):
        ids = inv.find('identifiers')
        isin = ids.find('isin').get('value') if ids is not None and ids.find('isin') is not None else None
        tick = ids.find('ticker').get('value') if ids is not None and ids.find('ticker') is not None else None
        cusip = (inv.findtext('cusip') or '').strip()
        if (not cusip or cusip in ('N/A', '000000000')) and isin and isin.startswith('US'):
            cusip = isin[2:11]
        try:
            pct = float(inv.findtext('pctVal') or 0)
        except ValueError:
            pct = 0.0
        rows.append({'name': (inv.findtext('name') or inv.findtext('title') or '').strip(),
                     'title': (inv.findtext('title') or '').strip(), 'cusip': cusip or None, 'ticker': tick,
                     'pct': round(pct, 4), 'value': float(inv.findtext('valUSD') or 0),
                     'cat': inv.findtext('assetCat') or (inv.find('assetConditional').get('assetCat') if inv.find('assetConditional') is not None else None),
                     'country': inv.findtext('invCountry')})
    rows.sort(key=lambda r: -r['pct'])
    return {'as_of': gen.findtext('repPdDate') if gen is not None else None,
            'series_name': gen.findtext('seriesName') if gen is not None else None,
            'net_assets': float(fund.findtext('netAssets') or 0) if fund is not None else None,
            'count': len(rows), 'rows': rows}


NORM_DROP = re.compile(r'\b(inc|incorporated|corp|corporation|co|company|ltd|limited|plc|holdings?|group|the|class [a-c]|cl [a-c]|sa|nv|ag|se|lp|llc|new|com|common|stock|shares|ordinary|adr|ads)\b')


def norm(n):
    n = re.sub(r'[^a-z0-9 ]', ' ', (n or '').lower())
    return re.sub(r'\s+', ' ', NORM_DROP.sub(' ', n)).strip()


def key(n):
    # 'ExxonMobil' vs 'Exxon Mobil Corp', 'D.R. Horton' vs 'DR Horton Inc'
    return norm(n).replace(' ', '')


NAME_FIX = {'IDEF': 'iShares Defense Industrials Active ETF'}  # FMP truncates this fund's name


def main():
    os.makedirs(OUT, exist_ok=True)
    etfs = json.load(open(os.path.join(ROOT, 'etf', 'etf_list.json')))
    only = set(a.upper() for a in sys.argv[1:])
    if only:
        etfs = [e for e in etfs if e['s'] in only]
    mf = sec('https://www.sec.gov/files/company_tickers_mf.json', as_json=True)
    series_of = {r[mf['fields'].index('symbol')]: (r[mf['fields'].index('cik')], r[mf['fields'].index('seriesId')]) for r in mf['data']}
    ct = sec('https://www.sec.gov/files/company_tickers.json', as_json=True)
    name_to_tk = {}
    for v in ct.values():
        name_to_tk.setdefault(key(v['title']), v['ticker'])

    # Dashboard names: CUSIP -> ticker, so holdings can link to the Analyzer.
    snaps = sorted(glob.glob(os.path.join(ROOT, 'reports', '20*', 'full-study.json')))
    uni = {t['symbol']: t.get('name') for t in json.load(open(snaps[-1]))['tickers']} if snaps else {}
    cache_p = os.path.join(ROOT, 'etf', 'cusips.json')
    cus = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    for s in uni:
        if s not in cus:
            p = fmp('profile', symbol=s)
            cus[s] = (p[0].get('cusip') if isinstance(p, list) and p else None)
    json.dump(cus, open(cache_p, 'w'), indent=0, sort_keys=True)
    cusip_to_tk = {c: s for s, c in cus.items() if c}
    uni_norm = {key(n): s for s, n in uni.items() if n}

    def ticker_for(r):
        if r['cusip'] and r['cusip'] in cusip_to_tk:
            return cusip_to_tk[r['cusip']], True
        n = key(r['name']) or key(r['title'])
        if n in uni_norm:
            return uni_norm[n], True
        if r['ticker'] and re.fullmatch(r'[A-Z.\-]{1,6}', r['ticker']):
            return r['ticker'], r['ticker'] in uni
        tk = name_to_tk.get(n)
        return tk, tk in uni

    index, report = {}, []
    for e in etfs:
        sym = e['s']
        out = {'s': sym, 'fetched_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
        if sym in DIRECT:
            out.update(kind='direct', holds=DIRECT[sym])
        elif sym == 'DIA' and sym not in series_of:
            # The Dow is price-weighted, so its exact weights follow from the 30 share prices.
            q = fmp('batch-quote', symbols=','.join(DOW30)) or []
            tot = sum(x['price'] for x in q)
            rows = sorted([{'name': x.get('name'), 'tk': x['symbol'], 'in_uni': x['symbol'] in uni,
                            'pct': round(x['price'] / tot * 100, 4), 'cat': 'EC', 'country': 'US'} for x in q],
                          key=lambda r: -r['pct'])
            out.update(kind='computed', note='Dow 30 weights computed from share prices (price-weighted index)',
                       as_of=datetime.now(timezone.utc).date().isoformat(), count=len(rows),
                       top10_pct=round(sum(r['pct'] for r in rows[:10]), 2), rows=rows,
                       dash=[[r['tk'], r['pct']] for r in rows if r['in_uni']])
            for r in rows:
                index.setdefault(r['tk'], {})[sym] = r['pct']
        else:
            src = sym if sym in series_of else PROXY.get(sym)
            if sym in PROXY and sym not in series_of:
                src = PROXY[sym]
            found = None
            if not src or src not in series_of:
                info = fmp('etf/info', symbol=sym)
                fname = NAME_FIX.get(sym) or (info[0].get('name') if isinstance(info, list) and info else None)
                found = find_by_name(fname) if fname else None
                if not found:
                    out.update(kind='missing', note='No SEC holdings filing found for this fund yet')
            if found:
                cik, acc, xml = found
                d = parse_nport(xml)
                for r in d['rows']:
                    r['tk'], r['in_uni'] = ticker_for(r)
                out.update(kind='nport', source=sym, series=None, cik=cik, accession=acc,
                           filing_url=f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-", "")}/',
                           as_of=d['as_of'], series_name=d['series_name'], net_assets=d['net_assets'],
                           count=d['count'], top10_pct=round(sum(r['pct'] for r in d['rows'][:10]), 2),
                           rows=[{k: r[k] for k in ('name', 'tk', 'in_uni', 'pct', 'cat', 'country')} for r in d['rows'][:KEEP]],
                           dash=[[r['tk'], r['pct']] for r in d['rows'] if r['in_uni'] and r['tk'] and r['pct'] > 0])
                for r in d['rows']:
                    if r['in_uni'] and r['tk'] and r['pct'] > 0:
                        index.setdefault(r['tk'], {})
                        index[r['tk']][sym] = round(index[r['tk']].get(sym, 0) + r['pct'], 4)
            elif src and src in series_of:
                cik, series = series_of[src]
                acc = latest_nport(cik, series)
                if not acc:
                    out.update(kind='missing', note=f'No N-PORT filing found for series {series}')
                else:
                    xml = sec(f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-", "")}/primary_doc.xml')
                    if not xml:
                        out.update(kind='missing', note=f'Filing {acc} has no primary_doc.xml')
                    else:
                        d = parse_nport(xml)
                        for r in d['rows']:
                            r['tk'], r['in_uni'] = ticker_for(r)
                        out.update(kind='nport', source=src, series=series, cik=cik, accession=acc,
                                   filing_url=f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-", "")}/',
                                   as_of=d['as_of'], series_name=d['series_name'], net_assets=d['net_assets'],
                                   count=d['count'], top10_pct=round(sum(r['pct'] for r in d['rows'][:10]), 2),
                                   rows=[{k: r[k] for k in ('name', 'tk', 'in_uni', 'pct', 'cat', 'country')} for r in d['rows'][:KEEP]],
                           dash=[[r['tk'], r['pct']] for r in d['rows'] if r['in_uni'] and r['tk'] and r['pct'] > 0])
                        for r in d['rows']:
                            if r['in_uni'] and r['tk'] and r['pct'] > 0:
                                index.setdefault(r['tk'], {})
                                index[r['tk']][sym] = round(index[r['tk']].get(sym, 0) + r['pct'], 4)
        json.dump(out, open(os.path.join(OUT, f'{sym}.json'), 'w'), separators=(',', ':'))
        report.append((sym, out['kind'], out.get('as_of'), out.get('count'), out.get('source')))
        print(sym, out['kind'], out.get('source', ''), out.get('as_of', ''), out.get('count', ''), flush=True)
    index = {}
    for f in sorted(glob.glob(os.path.join(OUT, '*.json'))):
        h = json.load(open(f))
        for tk, p in h.get('dash', []):
            index.setdefault(tk, {})
            index[tk][h['s']] = index[tk].get(h['s'], 0) + p
    idx = {tk: sorted([[e, round(p, 3)] for e, p in m.items()], key=lambda x: -x[1]) for tk, m in sorted(index.items())}
    json.dump(idx, open(os.path.join(ROOT, 'etf', 'holdings-index.json'), 'w'), separators=(',', ':'))
    kinds = {}
    for _, k, *_ in report:
        kinds[k] = kinds.get(k, 0) + 1
    print('done', kinds, len(idx), 'dashboard names held by at least one fund')


if __name__ == '__main__':
    main()
