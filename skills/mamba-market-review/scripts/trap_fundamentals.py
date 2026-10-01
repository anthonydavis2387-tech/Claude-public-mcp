"""TRAP Criteria #4 (Fundamentals - Company): best-candidate check for every scanned name.

Usage: python3 trap_fundamentals.py analyzer_data.json out.json
  analyzer_data.json = the 10-Point Analyzer's data island ({SYMBOL: detail, ...}); it supplies the
  symbols plus the debt flag, moat verdict and sector used by the caution checks.
  Writes {SYMBOL: trap} to out.json, to be merged into each ticker's detail as `trap`.

Three FMP calls per name (FMP_API_KEY): key-metrics-ttm (ROIC, current ratio, capex/revenue),
ratios-ttm (net margin), earnings (last reported EPS vs estimate, next report date).
"""
import json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date

B = 'https://financialmodelingprep.com/stable'
K = os.environ['FMP_API_KEY']


def get(path):
    url = f"{B}/{path}&apikey={K}"
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


def first(x):
    return x[0] if isinstance(x, list) and x else {}


def pct(v):
    return None if v is None else round(v * 100, 1)


def margin_tier(nm):
    if nm is None: return None
    if nm > 20: return 'best'
    if nm > 10: return 'very_solid'
    if nm >= 7: return 'acceptable'
    return 'look_elsewhere'


def check(sym, d):
    km = first(get(f'key-metrics-ttm?symbol={sym}'))
    ra = first(get(f'ratios-ttm?symbol={sym}'))
    er = get(f'earnings?symbol={sym}&limit=10') or []
    today = date.today().isoformat()
    reported = [e for e in er if e.get('epsActual') is not None][:4]
    upcoming = sorted([e for e in er if e.get('epsActual') is None and (e.get('date') or '') >= today], key=lambda e: e['date'])
    nxt = upcoming[0] if upcoming else None
    beats = sum(1 for e in reported if e.get('epsEstimated') is not None and e['epsActual'] >= e['epsEstimated'])
    misses = sum(1 for e in reported if e.get('epsEstimated') is not None and e['epsActual'] < e['epsEstimated'])
    acts = [e['epsActual'] for e in reported]
    eps_growing = len(acts) >= 3 and acts[0] > acts[-1]
    ests = [e.get('epsEstimated') for e in reported if e.get('epsEstimated') is not None]
    est_growing = None
    if nxt and nxt.get('epsEstimated') is not None and ests:
        est_growing = nxt['epsEstimated'] > ests[0]
    elif len(ests) >= 3:
        est_growing = ests[0] > ests[-1]
    roic = pct(km.get('returnOnInvestedCapitalTTM'))
    nm = pct(ra.get('netProfitMarginTTM'))
    cr = km.get('currentRatioTTM') or ra.get('currentRatioTTM')
    capex = pct(km.get('capexToRevenueTTM'))
    if capex is not None: capex = abs(capex)
    fin = d.get('sector') == 'Financial Services'
    cautions = []
    if (d.get('flags') or {}).get('debt') == 'red': cautions.append('Heavy debt')
    if misses >= 2: cautions.append(f'Missed {misses} of last {len(reported)} earnings')
    if d.get('moat_verdict') == 'eroding': cautions.append('Eroding moat/industry position')
    if roic is not None and roic < 5 and not fin: cautions.append('Low or negative ROIC')
    if capex is not None and capex > 15: cautions.append('Capital intensive')
    if cr is not None and cr < 0.8 and not fin: cautions.append('Low liquidity (current ratio below 0.8)')
    passes = sum([bool(eps_growing and beats >= 3), bool(roic is not None and roic > 10 and not fin),
                  margin_tier(nm) in ('best', 'very_solid')])
    return sym, {
        'eps_hist': [{'date': e['date'], 'actual': e['epsActual'], 'est': e.get('epsEstimated')} for e in reported],
        'eps_growing': eps_growing, 'beats': beats, 'misses': misses, 'est_growing': est_growing,
        'next_date': nxt['date'] if nxt else None, 'next_est': nxt.get('epsEstimated') if nxt else None,
        'roic_pct': roic, 'net_margin_ttm_pct': nm, 'margin_tier': margin_tier(nm),
        'current_ratio': round(cr, 2) if cr is not None else None, 'capex_to_rev_pct': capex,
        'financial': fin, 'cautions': cautions, 'passes': passes,
    }


def main(src, out):
    data = json.load(open(src))
    with ThreadPoolExecutor(8) as ex:
        res = dict(ex.map(lambda s: check(s, data[s]), sorted(data)))
    json.dump(res, open(out, 'w'))
    print(len(res), 'names;', sum(1 for v in res.values() if v['passes'] == 3), 'pass all three checks')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
