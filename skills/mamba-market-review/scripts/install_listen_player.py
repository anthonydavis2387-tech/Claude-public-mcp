"""Install (or update) the Listen player from assets/listen-player.html on any Mamba page.

Usage: python3 install_listen_player.py published.html out.html
  published.html is the page as read back from its artifact (dashboard, 10-Point Analyzer, ...). Replaces an earlier
  copy of the player or the dashboard's old voice bar, otherwise appends it; strips the publish skeleton so the
  output can be republished.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(src, out):
    s = open(src).read()
    if '<body>' in s[:3000]:
        s = s.split('<body>', 1)[1]
    s = re.sub(r'</body>\s*</html>\s*$', '', s)
    player = open(os.path.join(HERE, '..', 'assets', 'listen-player.html')).read()
    player = re.sub(r'<!-- LISTEN-PLAYER:\w+ -->\n', '', player)
    # Old voice-bar CSS (the block between its comment and the next mobile rule).
    s = re.sub(r'  /\* Voice bar \*/.*?(?=  @media \(max-width: 640px\) \{\s*\.stats)', '', s, flags=re.S)
    # Old markup + script, or a previous install of the player.
    old = re.compile(r'<div class="voice-spacer"></div>.*?<script id="voice-scripts">.*?</script>', re.S)
    new = re.compile(r'<style id="listen-css">.*?<script id="listen-player">.*?</script>', re.S)
    if new.search(s):
        s = new.sub(lambda m: player.strip(), s, count=1)
    elif old.search(s):
        s = old.sub(lambda m: player.strip(), s, count=1)
    else:
        s = s.rstrip() + '\n' + player.strip() + '\n'   # pages that never had a read-aloud bar
    if 'id="voice-scripts"' in s or 'vMic' in s:
        raise SystemExit('old voice command code still present')
    open(out, 'w').write(s)
    print('wrote', out, len(s))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])


def player_block():
    """The player markup for page builders (etf_explorer.py, world_watch.py) to append."""
    return re.sub(r'<!-- LISTEN-PLAYER:\w+ -->\n', '', open(os.path.join(HERE, '..', 'assets', 'listen-player.html')).read()).strip()
