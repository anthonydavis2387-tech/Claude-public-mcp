"""Build the World Watch page for the 5pm MT check.

Usage: python3 world_watch.py notes.json out.html
  notes.json holds the run's hand-written regional notes (see references/world-watch.md).
  Prices come from one FMP batch-quote call (FMP_API_KEY env var).
Prints the phone-reminder text on stdout.
"""
import html, json, os, sys, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

FUT = [('ESUSD', 'S&P 500 fut', True), ('NQUSD', 'Nasdaq 100 fut', True), ('CLUSD', 'WTI crude', True),
       ('GCUSD', 'Gold', True), ('BTCUSD', 'Bitcoin', True), ('DXUSD', 'Dollar index', False)]
REGIONS = [
    ('asia', 'Asia-Pacific', [('EWJ', 'Japan'), ('EWY', 'South Korea'), ('EWT', 'Taiwan'), ('INDA', 'India')]),
    ('china', 'China & Hong Kong', [('FXI', 'China large-cap')]),
    ('europe', 'Europe', [('EZU', 'Eurozone'), ('EWG', 'Germany'), ('EWU', 'United Kingdom')]),
    ('latam', 'Latin America', [('EWZ', 'Brazil'), ('EWW', 'Mexico')]),
    ('mideast', 'Middle East & Oil', []),
]
e = lambda s: html.escape(str(s), quote=True)


def quotes(syms):
    url = f"https://financialmodelingprep.com/stable/batch-quote?symbols={','.join(syms)}&apikey={os.environ['FMP_API_KEY']}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return {q['symbol']: q for q in json.loads(r.read())}


def pct(x):
    return '&mdash;' if x is None else f"{'+' if x >= 0 else '&minus;'}{abs(x):.2f}%"


def cls(x):
    return 'up' if (x or 0) > 0.05 else 'down' if (x or 0) < -0.05 else 'flat'


def main(notes_path, out_path):
    notes = json.load(open(notes_path))
    syms = [s for s, _, _ in FUT] + [s for _, _, etfs in REGIONS for s, _ in etfs]
    Q = quotes(syms)
    now = datetime.now(timezone.utc).astimezone(ZoneInfo('America/Denver'))
    stamp = now.strftime('%a %b %-d, %Y · %-I:%M %p MT')

    fut_cells, top5 = [], []
    for s, label, dollar in FUT:
        q = Q.get(s)
        if not q: continue
        px, ch = q['price'], q.get('changePercentage')
        pxs = (f"${px:,.2f}" if px < 1000 else f"${px:,.0f}") if dollar else f"{px:,.2f}"
        fut_cells.append(f'<div class="tick"><span class="tl">{e(label)}</span><span class="tp">{pxs}</span><span class="tc {cls(ch)}">{pct(ch)}</span></div>')
        if s in ('ESUSD', 'NQUSD', 'CLUSD', 'GCUSD', 'BTCUSD'):
            top5.append(f"{label.replace(' fut', '')} {'+' if (ch or 0) >= 0 else '-'}{abs(ch or 0):.1f}%")

    cards = []
    for key, name, etfs in REGIONS:
        n = notes.get('regions', {}).get(key, {})
        rows = ''.join(
            f'<li><span>{e(lbl)} <em>{s}</em></span><span class="tc {cls(Q[s].get("changePercentage"))}">{pct(Q[s].get("changePercentage"))}</span></li>'
            for s, lbl in etfs if s in Q)
        if key == 'mideast':
            rows = ''.join(f'<li><span>{lbl}</span><span class="tc {cls(Q[s].get("changePercentage"))}">${Q[s]["price"]:,.2f} · {pct(Q[s].get("changePercentage"))}</span></li>'
                           for s, lbl in (('CLUSD', 'WTI crude'),) if s in Q)  # FMP's BZUSD shows contract-roll jumps; Brent comes from the notes
        src = ''.join(f'<a href="{e(l["url"])}" target="_blank" rel="noopener">{e(l["name"])} &#8599;</a>' for l in n.get('sources', []))
        cards.append(f'''<article class="region" id="{key}">
  <header><h2>{e(name)}</h2><span class="status" data-region="{key}"></span></header>
  <p class="head">{e(n.get("headline", "No update this session."))}</p>
  <p class="body">{e(n.get("detail", ""))}</p>
  {f'<ul class="funds">{rows}</ul>' if rows else ''}
  <div class="src">{src}</div>
</article>''')

    watch = ''.join(f'<li>{e(w)}</li>' for w in notes.get('on_notice', []))
    page = TEMPLATE.replace('{{STAMP}}', e(stamp)).replace('{{TICKS}}', '\n'.join(fut_cells)) \
        .replace('{{CARDS}}', '\n'.join(cards)).replace('{{WATCH}}', watch) \
        .replace('{{GENERATED}}', now.isoformat())
    open(out_path, 'w').write(page)
    heads = notes.get('push_headlines', [])[:3]
    print(f"Time to review the futures. {', '.join(top5)}. " + ' '.join(f'• {h}' for h in heads))


TEMPLATE = r'''<title>World Watch</title>
<style>
  /* Layout: a single column of region briefs under a live "who's open" clock strip; shares the Mamba Review palette. */
  :root {
    --bg: #f5f1e6; --surface: #fbf9f2; --line: #c9bfa0; --ink: #1a1712; --ink-soft: #4a4438; --ink-faint: #7d7561;
    --accent: #1f2f45; --accent-soft: #e4e8ee; --green: #1e5c34; --red: #8c2a2a; --amber: #8a6a1f;
    --display: 'Playfair Display', Georgia, serif; --body: 'PT Serif', Georgia, serif;
    --ui: 'Source Sans 3', -apple-system, sans-serif; --mono: 'IBM Plex Mono', ui-monospace, monospace;
  }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
    --bg: #16140f; --surface: #1e1b14; --line: #40392b; --ink: #ece5d2; --ink-soft: #beb49a; --ink-faint: #8c8267;
    --accent: #9fb3cc; --accent-soft: #232c38; --green: #7fb894; --red: #cf8a83; --amber: #cbab5e; color-scheme: dark; } }
  :root[data-theme="dark"] {
    --bg: #16140f; --surface: #1e1b14; --line: #40392b; --ink: #ece5d2; --ink-soft: #beb49a; --ink-faint: #8c8267;
    --accent: #9fb3cc; --accent-soft: #232c38; --green: #7fb894; --red: #cf8a83; --amber: #cbab5e; color-scheme: dark; }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--ink); font-family: var(--body); max-width: 760px; margin: 0 auto; padding-inline: 18px; padding-block: 22px 48px; font-size: 15.5px; }
  h1, h2 { font-family: var(--display); margin: 0; text-wrap: balance; }
  a { color: var(--accent); }
  .top { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 6px 16px; border-bottom: 2px solid var(--ink); padding-bottom: 10px; }
  .top h1 { font-size: 30px; font-weight: 800; }
  .stamp { font-family: var(--ui); font-size: 12.5px; color: var(--ink-faint); }
  .lede { color: var(--ink-soft); font-size: 14.5px; line-height: 1.6; margin: 12px 0 18px; max-width: 62ch; }
  .label { font-family: var(--ui); font-size: 10.5px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-faint); margin: 22px 0 8px; }
  .clock { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
  .mkt { background: var(--surface); border: 1px solid var(--line); border-radius: 4px; padding: 8px 10px; font-family: var(--ui); display: grid; gap: 2px; }
  .mkt b { font-size: 13px; } .mkt small { font-size: 11.5px; color: var(--ink-faint); }
  .mkt .st { font-size: 11.5px; font-weight: 700; }
  .st.open { color: var(--green); } .st.soon { color: var(--amber); } .st.closed { color: var(--ink-faint); }
  .ticks { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 0; border-top: 1px solid var(--line); border-left: 1px solid var(--line); }
  .tick { border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 9px 11px; display: grid; gap: 1px; }
  .tl { font-family: var(--ui); font-size: 11px; color: var(--ink-faint); }
  .tp { font-family: var(--mono); font-size: 15px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .tc { font-family: var(--mono); font-size: 12.5px; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .up { color: var(--green); } .down { color: var(--red); } .flat { color: var(--ink-faint); }
  .regions { display: grid; gap: 0; }
  .region { border-bottom: 1px solid var(--line); padding: 16px 0; display: grid; gap: 6px; }
  .region header { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
  .region h2 { font-size: 20px; font-weight: 700; }
  .status { font-family: var(--ui); font-size: 11.5px; font-weight: 700; }
  .head { margin: 0; font-weight: 700; font-size: 15.5px; line-height: 1.45; }
  .body { margin: 0; color: var(--ink-soft); line-height: 1.6; max-width: 64ch; }
  .funds { list-style: none; margin: 4px 0 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 4px 18px; font-family: var(--ui); font-size: 13px; }
  .funds li { display: flex; justify-content: space-between; gap: 8px; border-bottom: 1px dotted var(--line); padding: 2px 0; }
  .funds em { font-style: normal; color: var(--ink-faint); font-size: 11.5px; }
  .src { display: flex; flex-wrap: wrap; gap: 4px 14px; font-family: var(--ui); font-size: 12.5px; }
  .notice { background: var(--accent-soft); border-left: 3px solid var(--accent); padding: 12px 16px; }
  .notice ul { margin: 0; padding-left: 18px; line-height: 1.6; }
  .links { display: flex; flex-wrap: wrap; gap: 8px 18px; font-family: var(--ui); font-size: 13.5px; }
  footer { margin-top: 28px; font-family: var(--ui); font-size: 11.5px; color: var(--ink-faint); line-height: 1.5; }
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=PT+Serif:wght@400;700&family=Source+Sans+3:wght@400;700&family=IBM+Plex+Mono:wght@500;600&display=swap">

<div class="top"><h1>World Watch</h1><span class="stamp">{{STAMP}}</span></div>
<p class="lede">A five-minute look past the US market before tonight&rsquo;s futures session. Asia opens first, so its card matters most at this hour. For the full picture of US stocks, see <a href="https://claude.ai/artifact/CjZFMqQ5r2b8qgBR2bVkav">The Mamba Market Review</a>.</p>

<div class="label">Who&rsquo;s trading now</div>
<div class="clock" id="clock"></div>

<div class="label">Futures to review</div>
<div class="ticks">
{{TICKS}}
</div>

<div class="label">On notice</div>
<div class="notice"><ul>{{WATCH}}</ul></div>

<div class="label">Regions</div>
<div class="regions">
{{CARDS}}
</div>

<div class="label">Go look yourself</div>
<div class="links">
  <a href="https://www.tradingview.com/markets/world-indices/" target="_blank" rel="noopener">&#8599; World indices (TradingView)</a>
  <a href="https://www.tradingview.com/markets/futures/quotes-all/" target="_blank" rel="noopener">&#8599; All futures (TradingView)</a>
  <a href="https://www.investing.com/indices/major-indices" target="_blank" rel="noopener">&#8599; Major indices (Investing.com)</a>
  <a href="https://www.riotimesonline.com/" target="_blank" rel="noopener">&#8599; Latin America (Rio Times)</a>
  <a href="https://tradingeconomics.com/calendar" target="_blank" rel="noopener">&#8599; Economic calendar</a>
</div>
<footer>Country moves are US-listed iShares country funds from today&rsquo;s US session, a same-day proxy for how each market is priced; local index closes are in the text. Oil and futures are live at generation time. Built {{GENERATED}}.</footer>

<script>
(function(){
  try {
    // Local trading hours (weekdays). Clock shows each market's state right now, in the viewer's browser.
    var M = [
      ['Tokyo','Asia/Tokyo',540,930,'asia'], ['Hong Kong','Asia/Hong_Kong',570,960,'china'], ['Shanghai','Asia/Shanghai',570,900,'china'],
      ['Mumbai','Asia/Kolkata',555,930,'asia'], ['Frankfurt','Europe/Berlin',540,1050,'europe'], ['London','Europe/London',480,990,'europe'],
      ['São Paulo','America/Sao_Paulo',600,1020,'latam'], ['New York','America/New_York',570,960,null]
    ];
    function local(tz){
      var p = new Intl.DateTimeFormat('en-US',{timeZone:tz,hour12:false,weekday:'short',hour:'2-digit',minute:'2-digit'}).formatToParts(new Date());
      var o = {}; p.forEach(function(x){ o[x.type]=x.value; });
      return { day:o.weekday, min:(parseInt(o.hour,10)%24)*60+parseInt(o.minute,10), time:o.hour+':'+o.minute };
    }
    function fmt(m){ var h=Math.floor(m/60), mm=m%60; return (h? h+'h ':'')+mm+'m'; }
    function render(){
      var el = document.getElementById('clock'); if (!el) return;
      var html = '', byRegion = {};
      M.forEach(function(m){
        var l = local(m[1]), wk = ['Sat','Sun'].indexOf(l.day) === -1, st, cls;
        if (wk && l.min >= m[2] && l.min < m[3]) { st = 'Open · closes in ' + fmt(m[3]-l.min); cls='open'; }
        else if (wk && l.min < m[2] && m[2]-l.min <= 240) { st = 'Opens in ' + fmt(m[2]-l.min); cls='soon'; }
        else { st = 'Closed'; cls='closed'; }
        html += '<div class="mkt"><b>'+m[0]+'</b><small>'+l.day+' '+l.time+' local</small><span class="st '+cls+'">'+st+'</span></div>';
        if (m[4] && (!byRegion[m[4]] || cls==='open' || (cls==='soon' && byRegion[m[4]].cls==='closed'))) byRegion[m[4]] = {st:m[0]+': '+st, cls:cls};
      });
      el.innerHTML = html;
      Object.keys(byRegion).forEach(function(k){
        var s = document.querySelector('.status[data-region="'+k+'"]');
        if (s) { s.textContent = byRegion[k].st; s.className = 'status st ' + byRegion[k].cls; }
      });
    }
    render(); setInterval(render, 60000);
  } catch (e) {}
})();
</script>
'''

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
