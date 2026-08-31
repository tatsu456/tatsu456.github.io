#!/usr/bin/env python3
"""記事の図だけを並べた確認用ページを .claude/ に作る（gitには入らない）。

図を1枚ずつ見るために使う。記事ページごと開くとスクロールが要り、
プレビュー枠の再描画が追いつかず真っ白なスクリーンショットになることがある。
使い方: python3 tools/figpage.py <slug> [<slug> ...]  →  /.claude/fig-<slug>.html
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from apply_chrome import CSS_VERSION

TPL = '''<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/assets/style.css?v={ver}">
<style>body{{margin:0;padding:12px;background:var(--bg)}}
.fig{{margin:0 0 26px}} .fig svg{{max-width:100%!important;width:520px}}
.lbl{{font:600 13px system-ui;color:var(--muted);margin:0 0 4px}}</style>
</head><body>
{figs}
</body></html>
'''

os.makedirs(os.path.join(ROOT, '.claude'), exist_ok=True)
for slug in sys.argv[1:]:
    s = open(os.path.join(ROOT, 'guides', f'{slug}.html')).read()
    svgs = re.findall(r'<svg\b.*?</svg>', s, flags=re.S)
    figs = '\n'.join(f'<p class="lbl">図{i}</p><figure class="fig">{sv}</figure>'
                     for i, sv in enumerate(svgs, 1))
    p = os.path.join(ROOT, '.claude', f'fig-{slug}.html')
    open(p, 'w').write(TPL.format(ver=CSS_VERSION, figs=figs))
    print(f'{p}  図{len(svgs)}枚')
