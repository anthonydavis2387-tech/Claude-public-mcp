"""Assemble the full-study snapshot from the pulled/scored pieces.
Usage: python3 full_study_snapshot.py RAW.json TICK.json TRAP.json VIX.json PRIOR.json TODAY OUT_SNAPSHOT.json OUT_ANALYZER.json ANALYZER_IN.json WATCH.json
Merges `trap` into each ticker's detail, adds futures/bitcoin/macro/etf_proxies/rollup/data_notes. sector_funds is added later by sector_table.py."""
import json, sys, datetime
raw, tick, trap, vix, prior, today, out, outa, ana, watch = sys.argv[1:11]
R = json.load(open(raw)); T = json.load(open(tick))['tickers']; TR = json.load(open(trap)); V = json.load(open(vix))[0]
P = json.load(open(prior)); A = json.load(open(ana)); W = json.load(open(watch))
Q = R['quotes']
FUT = [('ES','ESUSD'),('NQ','NQUSD'),('YM','YMUSD'),('RTY','RTYUSD'),('ZB','ZBUSD'),('ZN','ZNUSD'),('ZF','ZFUSD'),('ZT','ZTUSD'),('CL','CLUSD'),('BZ','BZUSD'),('NG','NGUSD'),('RB','RBUSD'),('HO','HOUSD'),('GC','GCUSD'),('SI','SIUSD'),('HG','HGUSD'),('PL','PLUSD'),('PA','PAUSD'),('ZM','ZMUSD'),('CC','CCUSD'),('DX','DXUSD'),('BTC','BTCUSD'),('ETH','ETHUSD')]
def flag(p, a50, a200):
    if p > a50 and p > a200: return 'green'
    if p < a50 and p < a200: return 'red'
    return 'neutral'
fut = []
for s, k in FUT + [('VIX', None)]:
    q = V if k is None else Q[k]
    fut.append(dict(symbol=s, name=q['name'], last=q['price'], chg_pct=round(q['changePercentage'], 2), trend_flag=flag(q['price'], q['priceAvg50'], q['priceAvg200']), source='fmp', prev_last=q['previousClose'], avg50=q['priceAvg50'], avg200=q['priceAvg200']))
b = Q['BTCUSD']; bc = R['btc_closes']; p = b['price']
r = lambda n: round((p / bc[-1 - n] - 1) * 100, 2)
bitcoin = dict(price=p, chg_pct=round(b['changePercentage'], 2), year_high=b['yearHigh'], year_low=b['yearLow'], avg50=b['priceAvg50'], avg200=b['priceAvg200'], r7=r(7), r30=r(30), r90=r(90), day_low=b['dayLow'], day_high=b['dayHigh'])
etf = {s: dict(price=Q[s]['price'], chg=Q[s]['changePercentage'], a50=Q[s]['priceAvg50'], a200=Q[s]['priceAvg200']) for s in ('SPY','QQQ','DIA','IWM','TLT','IEF')}
tr = R['treasury']
macro = dict(ust10y=tr[0]['year10'], ust30y=tr[0]['year30'], ust2y=tr[0]['year2'], treasury_print_date=tr[0]['date'], vix=V['price'], ust10y_prev=tr[1]['year10'], ust10y_prev_date=tr[1]['date'])
for t in T:
    s = t['symbol']; a = A[s]; d = t['detail']
    t['detail'] = d
    tp = TR.get(s)
    if tp:
        d['trap'] = tp; d['next_earnings_date'] = tp.get('next_date')
        a['trap'] = tp; a['next_earnings_date'] = tp.get('next_date')
    a['inst_own_pct'] = d.get('inst_own_pct')
# prior comparisons
PT = {t['symbol']: t for t in P['tickers']}
wl = sorted(k for k, v in W['tickers'].items() if v)
by = sorted(T, key=lambda t: (-t['red_flag_count'], t['symbol']))
multi = [t['symbol'] for t in by if t['red_flag_count'] >= 4]
movers = [t['symbol'] for t in sorted(T, key=lambda t: -abs(t['chg_pct']))[:10]]
dec = sorted(((PT[t['symbol']]['red_flag_count'] - t['red_flag_count'], t['symbol']) for t in T if t['symbol'] in PT and t['red_flag_count'] < PT[t['symbol']]['red_flag_count']), key=lambda x: (-x[0], x[1]))
improving = [s for _, s in dec[:8]]
pm = {t['symbol'] for t in P['tickers'] if t['red_flag_count'] >= 4}
newly = [s for s in multi if s not in pm]
new = sorted(set(R['new'])); dropped = sorted(R['dropped'])
watchlist = wl + [s for s in newly if s not in wl] + [s for s in new if s not in wl and s not in newly]
cnt = {}
for t in T:
    for l in t['lists']: cnt[l] = cnt.get(l, 0) + 1
cnt['unique'] = len(T)
now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:00Z')
snap = dict(date=today, session='full-study', generated_at=now, futures=fut, bitcoin=bitcoin, etf_proxies=etf, macro=macro, tickers=T,
    universe_counts=cnt,
    rollup=dict(movers=movers, multi_red_flag=multi, improving=improving, watchlist=watchlist),
    data_notes=dict(new_names=new, dropped_names=dropped, unpriced_futures=P['data_notes']['unpriced_futures'], comparison_base=f"{P['date']} full study snapshot", scoring=P['data_notes']['scoring'],
        sources=P['data_notes']['sources'].split(' institutional ownership and moat')[0] + ' institutional ownership and moat from reports/moat-ownership-cache.json (' + ', '.join(x for x in new if x) + ' researched fresh this session if not already cached; no existing entry was quick-rechecked this session). BRK-A is excluded from the large-cap proxy as a second share class of BRK-B.'))
json.dump(snap, open(out, 'w'))
json.dump(A, open(outa, 'w'))
print('ok', len(T), 'multi', len(multi), 'newly', newly, 'new', new, 'dropped', dropped)
