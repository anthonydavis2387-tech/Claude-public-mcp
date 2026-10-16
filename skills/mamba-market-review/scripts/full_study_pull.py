"""Full-study data pull + scoring. Usage: python3 full_study_pull.py PRIOR_SNAPSHOT.json OUT.json
Builds the universe (Dow30, live Nasdaq100, live S&P500 top100, US large-cap proxy, 3 baskets), pulls FMP data,
scores the 10 flags per reference docs. Moat/inst-own and TRAP data are merged afterwards."""
import json, os, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sectors import gics
B='https://financialmodelingprep.com/stable'; K=os.environ['FMP_API_KEY']
def get(path):
    sep='&' if '?' in path else '?'
    for a in range(5):
        try:
            with urllib.request.urlopen(f"{B}/{path}{sep}apikey={K}",timeout=60) as r: return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(2*(a+1)); continue
            return None
        except Exception: time.sleep(2*(a+1))
DOW="AAPL AMGN AMZN AXP BA CAT CRM CSCO CVX DIS GS HD HON IBM JNJ JPM KO MCD MMM MRK MSFT NKE NVDA PG SHW TRV UNH V VZ WMT".split()
SW="MSFT CRM ADBE NOW INTU ORCL SAP WDAY TEAM SNOW DDOG CRWD PANW FTNT ZS NET MDB HUBS DOCU PLTR".split()
MEGA="AAPL MSFT GOOGL AMZN NVDA META TSLA BRK-B AVGO JPM V WMT UNH XOM MA PG JNJ HD COST LLY".split()
SEMI="NVDA AVGO AMD TSM QCOM TXN INTC AMAT LRCX KLAC MU ADI MRVL NXPI MCHP ON SWKS MPWR ARM ASML".split()
FUT={'ES':'ESUSD','NQ':'NQUSD','YM':'YMUSD','RTY':'RTYUSD','ZB':'ZBUSD','ZN':'ZNUSD','ZF':'ZFUSD','ZT':'ZTUSD','CL':'CLUSD','BZ':'BZUSD','NG':'NGUSD','RB':'RBUSD','HO':'HOUSD','GC':'GCUSD','SI':'SIUSD','HG':'HGUSD','PL':'PLUSD','PA':'PAUSD','ZM':'ZMUSD','CC':'CCUSD','DX':'DXUSD','BTC':'BTCUSD','ETH':'ETHUSD'}
def bq(syms):
    out={}
    syms=list(syms)
    chunks=[syms[i:i+40] for i in range(0,len(syms),40)]
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(lambda c:get('batch-quote?symbols='+urllib.parse.quote(','.join(c))),chunks):
            for q in r or []: out[q['symbol']]=q
    return out
def ema(closes,n):
    k=2/(n+1); e=closes[0]
    for c in closes[1:]: e=c*k+e*(1-k)+0
    return e
def main(prior,out):
    P=json.load(open(prior)); psec={t['symbol']:t['detail'].get('sector') for t in P['tickers']}
    nd=[x['symbol'] for x in get('nasdaq-constituent')]
    sp=[x['symbol'] for x in get('sp500-constituent')]
    spq=bq(sp); sp100=[s for s,_ in sorted(((s,q.get('marketCap') or 0) for s,q in spq.items()),key=lambda x:-x[1])[:100]]
    scr=get('company-screener?exchange=NASDAQ,NYSE&country=US&isEtf=false&isFund=false&isActivelyTrading=true&marketCapMoreThan=20000000000&limit=400') or []
    scr.sort(key=lambda x:-(x.get('marketCap') or 0))
    base=set(DOW)|set(nd)|set(sp100)
    bad=('%','notes','trust','preferred','depositary','capital obligations',' pfd')
    proxy=[];names={}
    for x in scr:
        s=x['symbol']; n=(x.get('companyName') or '')
        if s in base or any(b in n.lower() for b in bad) or '-P' in s: continue
        if s in ('SOJE','SOMN','APOS','BRK-A'): continue  # BRK-A duplicates BRK-B (same company, second share class)
        proxy.append(s); names[s]=x.get('sector')
        if len(proxy)==100: break
    lists={}
    for nm,L in [('dow30',DOW),('nasdaq100',nd),('sp500_top100',sp100),('large_cap_proxy',proxy),('software_cloud',SW),('megacap_leaders',MEGA),('semiconductor_ai',SEMI)]:
        for s in L: lists.setdefault(s,[]).append(nm)
    syms=sorted(lists)
    print('universe',len(syms),'nd',len(nd),flush=True)
    Q=bq(syms+['SPY','QQQ','DIA','IWM','TLT','IEF']+list(FUT.values())+['^VIX'])
    def hist(s):
        h=get(f'historical-price-eod/full?symbol={s}') or []
        h=sorted(h,key=lambda r:r['date']); return h
    def one(s):
        q=Q.get(s)
        if not q: return s,None
        h=hist(s); cl=[r['close'] for r in h]
        d={'avg50':q.get('priceAvg50'),'avg200':q.get('priceAvg200'),'year_high':q.get('yearHigh'),'year_low':q.get('yearLow'),'exchange':q.get('exchange'),'market_cap':q.get('marketCap')}
        p=q['price']; d['momentum_50d_pct']=round((p/q['priceAvg50']-1)*100,2) if q.get('priceAvg50') else None
        d['stock_3m_pct']=round((cl[-1]/cl[-64]-1)*100,2) if len(cl)>64 else None
        d['ticker_3m_pct']=d['stock_3m_pct']
        if len(cl)>=72:
            for n in (72,210,420): d[f'ema{n}']=round(ema(cl,n),2) if len(cl)>=n or n==72 else round(ema(cl,n),2)
            yr=str(date.today().year); prev=[r for r in h if r['date']<yr]
            d['ytd_pct']=round((cl[-1]/prev[-1]['close']-1)*100,2) if prev else None
            d['listed_2026']=not prev
        else: d.update(ema72=None,ema210=None,ema420=None,ytd_pct=None,listed_2026=True)
        g=get(f'financial-growth?symbol={s}&period=quarter&limit=4') or []
        r=get(f'ratios?symbol={s}&period=quarter&limit=8') or []
        km=get(f'key-metrics?symbol={s}&period=quarter&limit=1') or []
        cf=get(f'cash-flow-statement?symbol={s}&period=quarter&limit=4') or []
        pc=lambda v:None if v is None else round(v*100,2)
        if g:
            d['revenue_growth_pct']=pc(g[0].get('revenueGrowth')); d['revenue_growth_prev_pct']=pc(g[1].get('revenueGrowth')) if len(g)>1 else None
            d['eps_growth_pct']=pc(g[0].get('epsgrowth')); d['latest_fiscal_period']=f"{g[0].get('fiscalYear')} {g[0].get('period')}"
        if r:
            d['gross_margin_pct']=pc(r[0].get('grossProfitMargin')); d['op_margin_pct']=pc(r[0].get('operatingProfitMargin')); d['net_margin_pct']=pc(r[0].get('netProfitMargin'))
            if len(r)>=5: d['gross_margin_4q_ago_pct']=pc(r[4].get('grossProfitMargin')); d['op_margin_4q_ago_pct']=pc(r[4].get('operatingProfitMargin'))
            d['debt_to_equity']=r[0].get('debtToEquityRatio'); d['pe_ratio']=r[0].get('priceToEarningsRatio'); d['ps_ratio']=r[0].get('priceToSalesRatio')
        if km: d['net_debt_to_ebitda']=km[0].get('netDebtToEBITDA'); d['ev_to_ebitda']=km[0].get('evToEBITDA')
        d['fcf_last4q']=[c.get('freeCashFlow') for c in cf]
        for k in ('debt_to_equity','pe_ratio','ps_ratio','net_debt_to_ebitda','ev_to_ebitda'):
            if isinstance(d.get(k),(int,float)): d[k]=round(d[k],2)
        sec=psec.get(s) or names.get(s)
        if not sec:
            pr=get(f'profile?symbol={s}') or [{}]; sec=pr[0].get('sector')
        d['sector']=gics(sec)   # standard GICS name (FMP says "Consumer Cyclical" etc.)
        d['benchmark_used']='QQQ' if 'nasdaq100' in lists[s] else 'SPY'
        return s,{'symbol':s,'name':q.get('name'),'lists':sorted(lists[s]),'price':p,'chg_pct':round(q.get('changePercentage') or 0,2),'detail':d}
    with ThreadPoolExecutor(8) as ex: res=dict(ex.map(one,syms))
    # benchmarks 3m
    bm={}
    for b in ('SPY','QQQ'):
        cl=[r['close'] for r in hist(b)]; bm[b]=round((cl[-1]/cl[-64]-1)*100,2)
    btc=sorted(get('historical-price-eod/full?symbol=BTCUSD') or [],key=lambda r:r['date']); bc=[r['close'] for r in btc]
    tr=(get('treasury-rates?from=%s&to=%s'%('2026-09-25',date.today().isoformat())) or [{}])
    json.dump({'tickers':[v for v in res.values() if v],'missing':[s for s,v in res.items() if not v],'bm':bm,'quotes':{k:Q[k] for k in Q if k in FUT.values() or k in('SPY','QQQ','DIA','IWM','TLT','IEF','^VIX','BTCUSD')},'btc_closes':bc[-100:],'btc_dates':[r['date'] for r in btc[-100:]],'treasury':tr[:3],'new':sorted(set(syms)-set(psec)),'dropped':sorted(set(psec)-set(syms))},open(out,'w'))
    print('done',len(res))
main(sys.argv[1],sys.argv[2])
