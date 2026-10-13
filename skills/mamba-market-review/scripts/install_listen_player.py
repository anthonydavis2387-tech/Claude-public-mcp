"""Swap the dashboard's read-aloud bar for the Listen player in assets/listen-player.html.

Usage: python3 install_listen_player.py published.html out.html
  published.html is the dashboard as read back from its artifact. Replaces the old voice bar (CSS, markup and
  script) or an earlier copy of the Listen player, and strips the publish skeleton so the output can be republished.
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
        raise SystemExit('no voice bar or listen player found')
    if 'id="voice-scripts"' in s or 'vMic' in s:
        raise SystemExit('old voice command code still present')
    open(out, 'w').write(s)
    print('wrote', out, len(s))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
