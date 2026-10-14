"""Annual-report check for every name in the 10-Point Analyzer.

Usage: python3 annual_review.py analyzer_data.json out.json [--max-age-days 7]
  For each symbol in the Analyzer's data island, pulls the last three fiscal years from FMP (FMP_API_KEY): income
  statement, balance sheet, cash flow and the dividend history, plus the latest 10-K (or 20-F / 40-F) link from SEC
  EDGAR. Writes {SYMBOL: annual} to out.json, to merge into each ticker's detail as `annual`.
  Results are cached in reports/annual-cache.json; a name is re-pulled only when its cache entry is older than
  --max-age-days (annual numbers change once a year, so the daily run stays cheap).
  The written research (shareholder letter, innovation pipeline, management's own reason for any debt) lives in
  reports/annual-research-cache.json and is merged in as `annual.research` when present.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, '..', 'reports')
CACHE = os.path.join(REPORTS, 'annual-cache.json')
RESEARCH = os.path.join(REPORTS, 'annual-research-cache.json')
SEC_UA = os.environ.get('SEC_USER_AGENT', 'Mamba Market Review anthonydavis2387@gmail.com')
_last = [0.0]


def fmp(path, **kw):
    kw['apikey'] = os.environ['FMP_API_KEY']
    url = 'https://financialmodelingprep.com/stable/' + path + '?' + urllib.parse.urlencode(kw)
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


def sec_json(url):
    for attempt in range(4):
        wait = 0.15 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': SEC_UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):
                time.sleep(10 * (attempt + 1)); continue
            return None
        except Exception:
            time.sleep(3)
    return None


def pct(a, b):
    if a is None or b in (None, 0):
        return None
    return round((a - b) / abs(b) * 100, 1)


def annual_report_link(cik):
    if not cik:
        return None
    d = sec_json(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json')
    if not d:
        return None
    r = d.get('filings', {}).get('recent', {})
    for form, acc, doc, fdate, rdate in zip(r.get('form', []), r.get('accessionNumber', []), r.get('primaryDocument', []),
                                           r.get('filingDate', []), r.get('reportDate', [])):
        if form in ('10-K', '20-F', '40-F', '10-K405'):
            return {'form': form, 'filed': fdate, 'period': rdate,
                    'url': f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}/{doc}'}
    return None


def dividend_change(divs):
    """Trailing-12-month dividends per share versus the 12 months before."""
    if not divs:
        return {'pays': False}
    today = date.today()
    y1, y2 = today - timedelta(days=365), today - timedelta(days=730)
    def total(lo, hi):
        return round(sum(d.get('adjDividend') or d.get('dividend') or 0 for d in divs if lo < date.fromisoformat(d['date']) <= hi), 4)
    last, prev = total(y1, today), total(y2, y1)
    if last == 0 and prev == 0:
        return {'pays': False}
    freq = divs[0].get('frequency')
    ch = pct(last, prev)
    trend = 'started' if prev == 0 else 'stopped' if last == 0 else 'increased' if ch > 1 else 'decreased' if ch < -1 else 'held steady'
    # consecutive per-payment raises/cuts give a cleaner signal than yearly totals when payment counts shift
    recent = [d.get('adjDividend') or d.get('dividend') for d in divs[:8] if d.get('adjDividend') or d.get('dividend')]
    raises = sum(1 for a, b in zip(recent, recent[1:]) if a > b * 1.001)
    cuts = sum(1 for a, b in zip(recent, recent[1:]) if a < b * 0.999)
    return {'pays': True, 'ttm': last, 'prior_ttm': prev, 'change_pct': ch, 'trend': trend, 'frequency': freq,
            'latest': recent[0] if recent else None, 'raises_last_8': raises, 'cuts_last_8': cuts}


def debt_story(bs, cf):
    """How debt moved over the last fiscal year and, if it rose, where the cash went (inferred from the cash flow statement)."""
    if len(bs) < 2 or not cf:
        return None
    now, before = bs[0].get('totalDebt'), bs[1].get('totalDebt')
    c = cf[0]
    issued = c.get('netDebtIssuance') or 0
    capex = abs(c.get('capitalExpenditure') or 0)
    acq = -(c.get('acquisitionsNet') or 0) if (c.get('acquisitionsNet') or 0) < 0 else 0
    buyback = abs(c.get('commonStockRepurchased') or 0)
    divs = abs(c.get('commonDividendsPaid') or c.get('netDividendsPaid') or 0)
    ocf = c.get('operatingCashFlow') or 0
    fcf = c.get('freeCashFlow') or (ocf - capex)
    prev_capex = abs(cf[1].get('capitalExpenditure') or 0) if len(cf) > 1 else None
    out = {'total_debt': now, 'prior_total_debt': before, 'change_pct': pct(now, before), 'net_issued': issued,
           'uses': {'capex': capex, 'acquisitions': acq, 'buybacks': buyback, 'dividends': divs}, 'ocf': ocf, 'fcf': fcf,
           'capex_change_pct': pct(capex, prev_capex)}
    rising = (now or 0) > (before or 0) * 1.03 or issued > 0.03 * max(now or 1, 1)
    if not rising:
        out['direction'] = 'down' if (now or 0) < (before or 0) * 0.97 else 'flat'
        out['purpose'] = None
        return out
    out['direction'] = 'up'
    added = max(issued, (now or 0) - (before or 0), 0)
    payout = buyback + divs
    if acq >= 0.5 * added and acq > 0:
        out['purpose'], out['purpose_kind'] = 'Funded acquisitions', 'growth'
    elif payout > max(fcf, 0) and payout >= 0.5 * added:
        out['purpose'], out['purpose_kind'] = 'Funded buybacks and dividends beyond free cash flow', 'shareholder returns'
    elif capex > 0 and (fcf < 0 or (out['capex_change_pct'] or 0) > 15):
        out['purpose'], out['purpose_kind'] = 'Funded heavier investment (capital spending up %s%%)' % (round(out['capex_change_pct']) if out['capex_change_pct'] is not None else '?'), 'growth'
    else:
        out['purpose'], out['purpose_kind'] = 'Refinancing or general purposes (no clear single use in the cash flow statement)', 'other'
    return out


SENSITIVITY = {'Basic Materials': 'Cyclical', 'Consumer Cyclical': 'Cyclical', 'Financial Services': 'Cyclical', 'Real Estate': 'Cyclical',
               'Communication Services': 'Sensitive', 'Energy': 'Sensitive', 'Industrials': 'Sensitive', 'Technology': 'Sensitive',
               'Consumer Defensive': 'Defensive', 'Healthcare': 'Defensive', 'Utilities': 'Defensive'}
SKIP_SEG = re.compile(r'elimination|corporate|intersegment|reconcil|adjustment', re.I)


REGION_NAMES = {'TAIWAN, PROVINCE OF CHINA': 'Taiwan', 'KOREA, REPUBLIC OF': 'South Korea', 'Geographic Distribution, Domestic': 'United States (domestic)',
                'UNITED STATES': 'United States', 'Non-US': 'Outside the US', 'CHINA': 'China'}


def seg_key(name):
    return re.sub(r'[^a-z0-9]', '', re.sub(r'\(.*?\)', '', name.lower()).replace('segment', '')).rstrip('s')


def seg_name(name, geo):
    n = re.sub(r'\s+Segment$', '', name).strip()
    n = REGION_NAMES.get(n, n)
    return n.title() if geo and n.isupper() and len(n) > 3 else n


def segments(rows, revenue=None, geo=False):
    """Latest year's segment split (accounting lines dropped), with growth where the same line appears the year before."""
    if not isinstance(rows, list) or not rows or not rows[0].get('data'):
        return None
    ok = lambda v: isinstance(v, (int, float)) and v > 0
    cur = {k: v for k, v in rows[0]['data'].items() if ok(v) and not SKIP_SEG.search(k)}
    prev = {seg_key(k): v for k, v in ((rows[1].get('data') or {}) if len(rows) > 1 else {}).items() if ok(v)}
    if not cur:
        return None
    total = sum(cur.values())
    base = revenue if geo and revenue else total
    order = sorted(cur.items(), key=lambda x: (bool(re.match(r'(all )?other', x[0], re.I)), -x[1]))   # "Other" lines last
    lines = [{'name': seg_name(k, geo), 'rev': v, 'share': round(v / base * 100, 1) if base else None,
              'growth': pct(v, prev.get(seg_key(k)))} for k, v in order]
    out = {'year': rows[0].get('fiscalYear'), 'lines': lines}
    if geo and revenue and total > revenue * 1.1:
        out['overlap'] = True   # the company reports overlapping regions (e.g. "Domestic" plus continents)
    return out


def life_stage(inc, debt):
    """Where the business sits: hyper growth, operating leverage, capital return, or decline."""
    def om(x):
        return round(x['operatingIncome'] / x['revenue'] * 100, 1) if x.get('revenue') and x.get('operatingIncome') is not None else None
    margins = [om(x) for x in inc[:3]]
    g1 = pct(inc[0].get('revenue'), inc[1].get('revenue')) if len(inc) > 1 else None
    g0 = pct(inc[1].get('revenue'), inc[2].get('revenue')) if len(inc) > 2 else None
    dm = round(margins[0] - margins[1], 1) if len(margins) > 1 and None not in margins[:2] else None
    payout = None
    if debt and (debt.get('fcf') or 0) > 0:
        payout = round((debt['uses']['buybacks'] + debt['uses']['dividends']) / debt['fcf'] * 100)
    ev = {'revenue_growth': g1, 'revenue_growth_prior': g0, 'op_margins': margins, 'op_margin_change': dm, 'payout_pct_fcf': payout}
    if g1 is None:
        return {'stage': None, **ev}
    if g1 < 0 and ((g0 is not None and g0 < 0) or (dm is not None and dm < -1)):
        st, why = 'Decline', 'Revenue is shrinking' + (' for a second year' if g0 is not None and g0 < 0 else ' and operating margin is falling')
    elif g1 >= 25 or (g0 is not None and g1 >= 20 and g0 >= 25):
        st, why = 'Hyper growth', 'Revenue is growing 25% or more a year'
    elif g1 >= 5 and dm is not None and dm >= 1:
        st, why = 'Operating leverage', 'Revenue is growing and operating margin is widening, so profit grows faster than sales'
    elif payout is not None and payout >= 50 and g1 < 15:
        st, why = 'Capital return', 'Growth is modest and the company pays out most of its free cash flow in buybacks and dividends'
    elif g1 < 0:
        st, why = 'Between capital return and decline', 'Revenue dipped this year but margins held; watch whether it recovers'
    elif g1 >= 10:
        st, why = 'Between hyper growth and operating leverage', 'Growing at a double-digit rate without margins widening yet'
    else:
        st, why = 'Between operating leverage and capital return', 'Single-digit growth with steady margins and payouts below half of free cash flow'
    if dm is not None and dm <= -2:
        why += f'. Note: operating margin fell {abs(dm):.1f} points this year'
    return {'stage': st, 'why': why, **ev}


def review(sym):
    try:
        return _review(sym)
    except Exception as e:   # one company's odd filing must not stop the run; it is retried on the next run
        return sym, {'error': f'{type(e).__name__}: {e}'}


def _review(sym):
    inc = fmp('income-statement', symbol=sym, period='annual', limit=3) or []
    bs = fmp('balance-sheet-statement', symbol=sym, period='annual', limit=2) or []
    cf = fmp('cash-flow-statement', symbol=sym, period='annual', limit=2) or []
    divs = fmp('dividends', symbol=sym, limit=16) or []
    prof = (fmp('profile', symbol=sym) or [{}])
    prof = prof[0] if isinstance(prof, list) and prof else {}
    prod = fmp('revenue-product-segmentation', symbol=sym, period='annual')
    geo = fmp('revenue-geographic-segmentation', symbol=sym, period='annual')
    if not isinstance(inc, list) or not inc:
        return sym, {'error': 'no annual statements'}
    a, b = inc[0], inc[1] if len(inc) > 1 else {}
    c = inc[2] if len(inc) > 2 else {}
    def margin(x):
        return round(x['netIncome'] / x['revenue'] * 100, 1) if x.get('revenue') and x.get('netIncome') is not None else None
    out = {
        'fiscal_year': a.get('fiscalYear'), 'period_end': a.get('date'), 'filed': (a.get('filingDate') or '')[:10],
        'currency': a.get('reportedCurrency'),
        'revenue': a.get('revenue'), 'revenue_growth': pct(a.get('revenue'), b.get('revenue')),
        'revenue_growth_prior': pct(b.get('revenue'), c.get('revenue')),
        'net_income': a.get('netIncome'), 'net_income_growth': pct(a.get('netIncome'), b.get('netIncome')),
        'net_income_growth_prior': pct(b.get('netIncome'), c.get('netIncome')),
        'eps': a.get('epsDiluted') or a.get('eps'), 'eps_growth': pct(a.get('epsDiluted') or a.get('eps'), b.get('epsDiluted') or b.get('eps')),
        'net_margin': margin(a), 'net_margin_prior': margin(b),
        'rnd': a.get('researchAndDevelopmentExpenses'), 'rnd_growth': pct(a.get('researchAndDevelopmentExpenses'), b.get('researchAndDevelopmentExpenses')),
        'debt': debt_story(bs, cf) if isinstance(bs, list) and isinstance(cf, list) else None,
        'dividend': dividend_change(divs if isinstance(divs, list) else []),
        'report': annual_report_link(a.get('cik')),
        'profile': {'country': prof.get('country'), 'sector': prof.get('sector'), 'industry': prof.get('industry'),
                    'exchange': prof.get('exchange'), 'adr': prof.get('isAdr'), 'sensitivity': SENSITIVITY.get(prof.get('sector'))},
        'products': segments(prod),
        'regions': segments(geo, a.get('revenue'), geo=True),
        'checked': datetime.now(timezone.utc).date().isoformat(),
    }
    out['stage'] = life_stage(inc, out['debt'])
    return sym, out


def main(src, out_path, max_age=7):
    data = json.load(open(src))
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    research = json.load(open(RESEARCH)) if os.path.exists(RESEARCH) else {}
    today = date.today()
    stale = [s for s in sorted(data) if s not in cache or 'error' in cache[s]
             or (today - date.fromisoformat(cache[s].get('checked', '2000-01-01'))).days >= max_age]
    with ThreadPoolExecutor(6) as ex:
        for sym, res in ex.map(review, stale):
            cache[sym] = res
    json.dump(cache, open(CACHE, 'w'), separators=(',', ':'), sort_keys=True)
    out = {}
    for s in data:
        a = dict(cache.get(s) or {})
        if s in research:
            a['research'] = research[s]
        out[s] = a
    json.dump(out, open(out_path, 'w'), separators=(',', ':'))
    print(f'{len(stale)} names refreshed, {len(out)} written, {sum(1 for s in out if "research" in out[s])} with written research')


if __name__ == '__main__':
    age = int(sys.argv[sys.argv.index('--max-age-days') + 1]) if '--max-age-days' in sys.argv else 7
    main(sys.argv[1], sys.argv[2], age)
