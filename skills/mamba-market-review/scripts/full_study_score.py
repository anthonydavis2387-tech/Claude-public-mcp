"""Scoring rules (see data_notes.scoring in snapshots). score(detail, price) -> flags dict."""
FIN=('Financials','Financial Services')   # GICS name, and FMP's label in older snapshots
def score(d, bench3m):
    f={}
    p=d.get('_price'); a50,a200=d.get('avg50'),d.get('avg200')
    if p is None or a50 is None or a200 is None: f['trend']='na'
    elif p>a50 and p>a200: f['trend']='green'
    elif p<a50 and p<a200: f['trend']='red'
    else: f['trend']='neutral'
    s3=d.get('stock_3m_pct')
    if s3 is None or bench3m is None: f['relative_strength']='na'
    elif s3>bench3m: f['relative_strength']='green'
    elif s3<bench3m-5: f['relative_strength']='red'
    else: f['relative_strength']='neutral'
    r=d.get('revenue_growth_pct')
    f['revenue_growth']='na' if r is None else 'red' if r<0 else 'green' if r>=8 else 'neutral'
    o,o4=d.get('op_margin_pct'),d.get('op_margin_4q_ago_pct')
    f['margin_trend']='na' if o is None or o4 is None else 'green' if o-o4>=1 else 'red' if o-o4<=-1 else 'neutral'
    e=d.get('eps_growth_pct')
    f['earnings_growth']='na' if e is None else 'red' if e<-10 else 'green' if e>=5 else 'neutral'
    q=[x for x in (d.get('fcf_last4q') or []) if x is not None]
    f['free_cash_flow']='na' if not q else 'green' if len(q)==4 and all(x>0 for x in q) else 'red' if sum(q)<0 else 'neutral'
    de,nd=d.get('debt_to_equity'),d.get('net_debt_to_ebitda'); fin=d.get('sector') in FIN
    if de is None and nd is None: f['debt']='na'
    elif fin: f['debt']='neutral'
    elif (de is not None and de>2.5) or (nd is not None and nd>14): f['debt']='red'
    elif de is not None and de<1: f['debt']='green'
    else: f['debt']='neutral'
    pe,ps=d.get('pe_ratio'),d.get('ps_ratio')
    if pe is None and ps is None: f['valuation']='na'
    elif (pe is not None and pe>50) or (ps is not None and ps>15): f['valuation']='red'
    elif pe is not None and ps is not None and 0<pe<20 and ps<5: f['valuation']='green'
    else: f['valuation']='neutral'
    t=d.get('inst_own_trend') or ''
    f['institutional_ownership']='green' if t.startswith('rising') else 'red' if t.startswith('declin') else 'neutral'
    m=d.get('moat_verdict')
    f['moat']='green' if m=='durable' else 'red' if m=='eroding' else 'neutral'
    return f
