"""Install (or refresh) the "Food for thought" dollar-vs-indices card at the top of the dashboard's Futures Tape.

Usage: python3 install_futures_note.py dashboard.html out.html
  The user's reminder: "What's good for the US currency is bad for the indices, and vice versa." The card shows it with
  a tighter wording, why it works, when it breaks, its track record (recomputed here from FMP daily closes of the dollar
  fund UUP and the S&P 500 fund SPY; FMP's plan does not include daily futures history), and a live check of today's
  tape read from the page's own DX / ES / NQ futures cards. Replaces an earlier copy, otherwise inserts it before the
  first futures-row. Needs FMP_API_KEY.
"""
import json, os, re, sys, urllib.request
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = re.compile(r'<style id="futures-note-css">.*?<script id="futures-note-js">.*?</script>\s*', re.S)


def closes(sym):
    start = (date.today() - timedelta(days=400)).isoformat()
    url = f"https://financialmodelingprep.com/stable/historical-price-eod/light?symbol={sym}&from={start}&apikey={os.environ['FMP_API_KEY']}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return {x['date']: x['price'] for x in json.loads(r.read()) if x.get('price')}


def stats():
    dx, sp = closes('UUP'), closes('SPY')
    days = sorted(set(dx) & set(sp))[-261:]
    pairs = [((dx[d] / dx[p] - 1) * 100, (sp[d] / sp[p] - 1) * 100) for p, d in zip(days, days[1:])]

    def share(ps):
        opp = sum(1 for a, b in ps if a * b < 0)
        return opp, len(ps)
    o12, n12 = share(pairs)
    o60, n60 = share(pairs[-60:])
    big = [p for p in pairs if abs(p[0]) >= 0.4]
    ob, nb = share(big)
    return (f"Over the last 12 months ({n12} trading days) they moved in opposite directions on {o12 / n12:.0%} of days, "
            f"and {o60 / n60:.0%} over the last 60. On the {nb} days the dollar moved 0.4% or more, the rule held "
            f"{ob} times ({ob / nb:.0%}). Updated {days[-1]}.")


def main(src, out):
    s = open(src).read()
    if '<body>' in s[:3000]:
        s = s.split('<body>', 1)[1]
    s = re.sub(r'</body>\s*</html>\s*$', '', s)
    block = open(os.path.join(HERE, '..', 'assets', 'futures-note.html')).read().strip().replace('__STATS__', stats()) + '\n'
    if OLD.search(s):
        s = OLD.sub(lambda _: block, s, count=1)
    else:
        i = s.find('<div class="futures-row">')
        if i < 0:
            raise SystemExit('no futures-row on this page')
        s = s[:i] + block + s[i:]
    open(out, 'w').write(s)
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
