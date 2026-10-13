"""Merge raw pull + cache + prior snapshot -> scored snapshot (no trap yet) and analyzer_data.json.
Usage: python3 full_study_build.py RAW.json PRIOR.json TODAY(YYYY-MM-DD) OUT_SNAPSHOT.json OUT_ANALYZER.json"""
import json,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from full_study_score import score
raw,prior,today,out,outa=sys.argv[1:6]
R=json.load(open(raw)); P=json.load(open(prior)); C=json.load(open(os.path.join(os.path.dirname(__file__),'..','reports','moat-ownership-cache.json')))
PD={t['symbol']:t['detail'] for t in P['tickers']}
INH=['inst_own_pct','inst_own_trend','inst_own_summary','inst_own_source','moat_verdict','moat_summary','moat_source']
tick=[]
for t in sorted(R['tickers'],key=lambda x:x['symbol']):
    d=t['detail']; s=t['symbol']
    src=C.get(s) or {k:PD.get(s,{}).get(k) for k in INH}
    for k in INH: d[k]=src.get(k)
    bm=R['bm'][d['benchmark_used']]; d['benchmark_3m_pct']=bm
    dd=dict(d); dd['_price']=t['price']
    fl=score(dd,bm)
    notes=''
    t.update(flags=fl,red_flag_count=sum(1 for v in fl.values() if v=='red'),notes=notes)
    tick.append(t)
json.dump({'tickers':tick},open(out,'w'))
A={}
for t in tick:
    e=dict(t['detail']); e.update(symbol=t['symbol'],name=t['name'],lists=t['lists'],chg_pct=t['chg_pct'],price=t['price'],flags=t['flags'],red_flag_count=t['red_flag_count'],notes=t['notes'])
    A[t['symbol']]=e
json.dump(A,open(outa,'w'))
print(len(tick),'names')
