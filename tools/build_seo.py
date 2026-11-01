#!/usr/bin/env python3
"""Regenerates the per-game landing pages (play/<id>.html), sitemap.xml and robots.txt
from the `games` array in index.html. Run from anywhere: python3 tools/build_seo.py"""
import json, os, subprocess, tempfile, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://liav-melamud.github.io/arcade-zone/'

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
i = src.index('  const games = [')
j = src.index('\n  ];', i) + 5
js = src[i:j].replace('const games =', 'var games =') + \
    "\nconsole.log(JSON.stringify(games.map(g=>({id:g.id,icon:g.icon,audience:g.audience||'kids',title:g.title,desc:g.desc}))));"
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
    f.write(js)
games = json.loads(subprocess.run(['node', f.name], capture_output=True, text=True, check=True).stdout)
os.unlink(f.name)

def pick(v, lang):
    return v if isinstance(v, str) else (v.get(lang) or v.get('en') or v.get('he'))

e = html.escape

PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - Play Free Online | Arcade Zone</title>
<meta name="description" content="{desc_en} Play {title} free in your browser - no download, no sign-up.">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title} - Play Free Online | Arcade Zone">
<meta property="og:description" content="{desc_en}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{base}icon-512.png">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#1a0b2e">
<link rel="icon" type="image/png" href="../icon-192.png">
<script type="application/ld+json">{ld}</script>
<style>
  :root{{ color-scheme: dark; }}
  *{{ box-sizing:border-box; }}
  body{{ margin:0; min-height:100vh; font-family:'Segoe UI',system-ui,-apple-system,sans-serif; color:#fffffe;
    background:linear-gradient(160deg,#1a0b2e,#2b1055 55%,#0f3460); display:flex; justify-content:center; padding:24px 16px; }}
  main{{ width:100%; max-width:560px; text-align:center; }}
  .icon{{ font-size:64px; line-height:1; margin-top:12px; }}
  h1{{ font-size:30px; margin:10px 0 6px; }}
  p{{ line-height:1.55; opacity:.92; margin:8px 0; }}
  .he{{ direction:rtl; }}
  .play{{ display:inline-block; margin:18px 0 8px; padding:15px 36px; border-radius:16px; font-weight:900; font-size:18px;
    text-decoration:none; color:#1a0b2e; background:linear-gradient(135deg,#ffd803,#ff9a3c); }}
  ul{{ list-style:none; padding:0; margin:18px 0; display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }}
  li{{ font-size:13px; padding:6px 12px; border-radius:99px; background:rgba(255,255,255,.1); }}
  h2{{ font-size:15px; margin:26px 0 10px; opacity:.8; }}
  nav a{{ display:inline-block; margin:4px 6px; color:#c9b8ff; text-decoration:none; font-size:14px; }}
  nav a:hover{{ text-decoration:underline; }}
</style>
</head>
<body>
<main>
  <div class="icon">{icon}</div>
  <h1>{title}</h1>
  <p>{desc_en}</p>
  <p class="he">{desc_he}</p>
  <a class="play" href="../index.html#{id}">▶ Play now / שחקו עכשיו</a>
  <ul>
    <li>Free</li><li>No sign-up</li><li>Works on phone &amp; desktop</li><li>Scores saved automatically</li><li>Earn coins &amp; unlock items</li>
  </ul>
  <h2>More games on Arcade Zone</h2>
  <nav>{links}</nav>
  <p style="margin-top:26px;font-size:13px"><a style="color:#c9b8ff" href="../index.html">🎮 All games / כל המשחקים</a></p>
</main>
</body>
</html>
'''

os.makedirs(os.path.join(ROOT, 'play'), exist_ok=True)
links_all = ''.join('<a href="{}.html">{}</a>'.format(g['id'], e(pick(g['title'], 'en'))) for g in games)
urls = [BASE]
for g in games:
    title = pick(g['title'], 'en')
    url = BASE + 'play/' + g['id'] + '.html'
    urls.append(url)
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'VideoGame', 'name': title,
        'description': pick(g['desc'], 'en'), 'url': url, 'applicationCategory': 'Game',
        'operatingSystem': 'Any (web browser)', 'inLanguage': ['en', 'he'],
        'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
    }, ensure_ascii=False)
    page = PAGE.format(title=e(title), desc_en=e(pick(g['desc'], 'en')), desc_he=e(pick(g['desc'], 'he')),
                       url=url, base=BASE, icon=g['icon'], id=g['id'], ld=ld, links=links_all)
    open(os.path.join(ROOT, 'play', g['id'] + '.html'), 'w', encoding='utf-8').write(page)

sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sm += ['  <url><loc>{}</loc></url>'.format(u) for u in urls] + ['</urlset>', '']
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm))
open(os.path.join(ROOT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: ' + BASE + 'sitemap.xml\n')

# crawlable links from the home page (the cards themselves are JS-rendered, hash-routed buttons)
nav = '<nav class="seoLinks" aria-label="All games">' + ''.join(
    '<a href="play/{}.html">{}</a>'.format(g['id'], e(pick(g['title'], 'en'))) for g in games) + '</nav>'
idx_path = os.path.join(ROOT, 'index.html')
idx = open(idx_path, encoding='utf-8').read()
import re
idx = re.sub(r'<nav class="seoLinks".*?</nav>', '', idx, flags=re.S)
marker = '</footer>'
k = idx.index(marker)
idx = idx[:k + len(marker)] + '\n    ' + nav + idx[k + len(marker):]
if 'rel="canonical"' not in idx:
    idx = idx.replace('<meta name="theme-color"', '<link rel="canonical" href="' + BASE + '">\n<meta name="theme-color"', 1)
if '.seoLinks{' not in idx:
    css = '  .seoLinks{ max-width:700px; margin:0 auto 28px; padding:0 16px; text-align:center; opacity:.55; font-size:12px; }\n  .seoLinks a{ color:inherit; margin:0 7px; text-decoration:none; display:inline-block; line-height:2; }\n'
    idx = idx.replace('  .dcsCard{ max-width:600px;', css + '  .dcsCard{ max-width:600px;', 1)
open(idx_path, 'w', encoding='utf-8').write(idx)
print('pages:', len(games))
