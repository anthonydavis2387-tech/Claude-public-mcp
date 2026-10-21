"""Split the "Why" column of the dashboard's "Names Flashing Multiple Red Flags" table into Red / Green / Moat columns.

Usage: python3 install_flag_split.py page.html out.html

The 2pm run writes each row's Why cell as one sentence run:
  "Red on: Trend, Debt. Green on: Revenue Growth. Moat (stable): <note>"
This turns it into three columns the user can scan (asked for on 2026-10-21): the red checklist items as red chips,
the green ones as green chips, and the moat note. It also checks that each row's red-chip count equals its Red
column and stops if not. Safe to run again on a page already split (it leaves those rows as they are).
"""
import html, re, sys

CSS = """<style id="flag-split-css">
  /* Flagged-names table: red and green checklist items in their own columns */
  #flagged .fl-list { display: flex; flex-wrap: wrap; gap: 4px; }
  #flagged .fl { display: inline-block; font-family: 'Source Sans 3', sans-serif; font-size: 11.5px; font-weight: 600; line-height: 1.3;
    padding: 2px 7px; border-radius: 3px; white-space: nowrap; }
  #flagged .fl.r { background: var(--red-bg); color: var(--red); }
  #flagged .fl.g { background: var(--green-bg); color: var(--green); }
  #flagged .fl-none { color: var(--ink-faint); font-size: 12px; font-style: italic; }
  #flagged th.th-red { color: var(--red); } #flagged th.th-green { color: var(--green); }
  #flagged td.red-cell { min-width: 150px; } #flagged td.green-cell { min-width: 120px; }
  #flagged .moat-k { display: block; font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .05em; color: var(--ink-faint); margin-bottom: 2px; }
  #flagged .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  /* Phones: each name becomes a card (ticker, company and red count on top, then price, red, green and moat stacked) */
  @media (max-width: 640px) {
    #flagged table { min-width: 0; }
    #flagged thead { display: none; }
    #flagged tbody tr { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 6px 10px; padding: 12px 2px; border-bottom: 1px solid var(--line); }
    #flagged tbody td { border: 0; padding: 0; min-width: 0; }
    #flagged tbody td.px-cell, #flagged tbody td.red-cell, #flagged tbody td.green-cell, #flagged tbody td.note-cell { grid-column: 1 / -1; }
    #flagged tbody td.redcount::after { content: " red"; font-weight: 400; color: var(--ink-faint); font-size: 11px; }
    #flagged tbody td.red-cell::before, #flagged tbody td.green-cell::before { display: block; font-family: 'Source Sans 3', sans-serif; font-size: 10px;
      font-weight: 700; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 3px; }
    #flagged tbody td.red-cell::before { content: "Red on"; color: var(--red); }
    #flagged tbody td.green-cell::before { content: "Green on"; color: var(--green); }
    #flagged .moat-k::before { content: "Moat \\00b7  "; }
  }
</style>"""
HEAD_OLD = '<th>Price / Chg</th><th>Why</th>'
HEAD_NEW = '<th>Price / Chg</th><th class="th-red">Red on</th><th class="th-green">Green on</th><th>Moat</th>'
ROW = re.compile(r'(<tr data-search="[^"]*" data-lists="[^"]*" data-red="(\d+)">(?:(?!</tr>).)*?)<td class="note-cell">(.*?)</td></tr>', re.S)
PART = re.compile(r'(Red on|Green on|Moat(?: \([a-z ]+\))?):\s*(.*?)(?=\s*(?:Red on|Green on|Moat(?: \([a-z ]+\))?):|$)', re.S)


def chips(items, cls):
    if not items:
        return '<span class="fl-none">none</span>'
    # the hidden commas make the Listen player say "Trend, Debt" instead of running the items together
    return '<span class="fl-list">' + '<span class="sr">, </span>'.join(f'<span class="fl {cls}">{x}</span>' for x in items) + '</span>'


def split_cell(note):
    parts = {k: v.strip() for k, v in PART.findall(note)}
    items = lambda k: [x.strip() for x in parts.get(k, '').rstrip('.').split(',') if x.strip()]
    moat_k = next((k for k in parts if k.startswith('Moat')), None)
    return items('Red on'), items('Green on'), moat_k, parts.get(moat_k, '') if moat_k else ''


def main(src, out):
    s = open(src).read()
    i = s.find('id="flagBody"')
    if i < 0:
        raise SystemExit('no flagged table (id="flagBody") on the page')
    j = s.find('</tbody>', i)
    errors = []

    def row(m):
        if 'class="red-cell"' in m.group(0):   # already split on an earlier run
            return m.group(0)
        red, green, moat_k, moat = split_cell(m.group(3))
        tk = re.search(r'<span class="tk">([^<]+)</span>', m.group(1))
        if len(red) != int(m.group(2)):
            errors.append(f'{tk.group(1) if tk else "?"}: Red column says {m.group(2)}, the Why text lists {len(red)} red items')
        moat_cell = (f'<span class="moat-k">{html.escape(moat_k.replace("Moat ", "").strip("()"))}</span>{moat}' if moat_k
                     else '<span class="fl-none">no note</span>')
        return (f'{m.group(1)}<td class="red-cell">{chips(red, "r")}</td><td class="green-cell">{chips(green, "g")}</td>'
                f'<td class="note-cell">{moat_cell}</td></tr>')

    body, n = ROW.subn(row, s[i:j])
    if errors:
        raise SystemExit('red counts do not match the Why text:\n  ' + '\n  '.join(errors))
    s = s[:i] + body + s[j:]
    if HEAD_OLD in s[:i][-3000:]:
        k = s.rfind(HEAD_OLD, 0, i)
        s = s[:k] + HEAD_NEW + s[k + len(HEAD_OLD):]
    s = re.sub(r'<style id="flag-split-css">.*?</style>', '', s, flags=re.S)
    k = s.find('id="flagged"')
    k = s.rfind('<section', 0, k)
    s = s[:k] + CSS + s[k:]
    open(out, 'w').write(s)
    print(f'split {n} rows')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
