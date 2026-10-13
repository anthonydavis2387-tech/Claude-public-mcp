"""Merge the annual-report data into the 10-Point Analyzer and install its "Annual Report & Shareholder Letter" box.

Usage: python3 install_annual_panel.py published.html annual.json out.html
  published.html is the Analyzer as read back (or as just rebuilt); annual.json is annual_review.py's output.
  Sets `annual` on every name in the analyzer-data island, then adds (or replaces) the panel block from
  assets/annual-panel.html. The box renders in the browser from the island, so only the data changes per run.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISLAND = re.compile(r'(<script id="analyzer-data" type="application/json">)(.*?)(</script>)', re.S)
PANEL = re.compile(r'<style id="annual-css">.*?<script id="annual-report">.*?</script>', re.S)


def main(src, annual_path, out):
    s = open(src).read()
    if '<body>' in s[:3000]:
        s = s.split('<body>', 1)[1]
    s = re.sub(r'</body>\s*</html>\s*$', '', s)
    annual = json.load(open(annual_path))
    m = ISLAND.search(s)
    if not m:
        raise SystemExit('no analyzer-data island')
    data = json.loads(m.group(2).replace('<\\/', '</'))
    hit = 0
    for sym, d in data.items():
        if sym in annual:
            d['annual'] = annual[sym]; hit += 1
    blob = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
    s = s[:m.start(2)] + blob + s[m.end(2):]
    panel = open(os.path.join(HERE, '..', 'assets', 'annual-panel.html')).read().strip()
    if PANEL.search(s):
        s = PANEL.sub(lambda _: panel, s, count=1)
    else:
        # before the Listen player so its reader sees the box; else at the end
        i = s.find('<style id="listen-css">')
        s = (s[:i] + panel + '\n' + s[i:]) if i >= 0 else (s.rstrip() + '\n' + panel + '\n')
    open(out, 'w').write(s)
    print(f'wrote {out}: annual data on {hit} of {len(data)} names, '
          f'{sum(1 for x in data.values() if (x.get("annual") or {}).get("research"))} with written research')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
