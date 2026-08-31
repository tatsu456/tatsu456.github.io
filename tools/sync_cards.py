#!/usr/bin/env python3
"""分野ページ（/guides/freezing/ など）の紹介文を、各記事の description に合わせる。

紹介文が2か所（記事の <meta> と分野ページのカード）にあって食い違っていたため、
記事側を正として流し込む。使い方: python3 tools/sync_cards.py
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from apply_chrome import GUIDES

desc = {}
for h, _ in GUIDES:
    s = open(os.path.join(ROOT, h.lstrip('/'))).read()
    desc[h] = re.search(r'<meta name="description" content="([^"]*)"', s).group(1)

changed = 0
for d in ('freezing', 'nukadoko', 'hiking', 'living'):
    p = os.path.join(ROOT, 'guides', d, 'index.html')
    s = open(p).read()
    orig = s

    def fix(m):
        global changed
        href, head, body = m.group(1), m.group(2), m.group(3)
        if href not in desc or body == desc[href]:
            return m.group(0)
        changed += 1
        print(f'  {d}/ {href}')
        return head + desc[href] + '</p>'

    s = re.sub(r'(?s)(?:<h3><a href="(/guides/[a-z-]+\.html)">.*?</a></h3>\s*)(<p>)(.*?)</p>',
               lambda m: (lambda href, body: m.group(0) if href not in desc or body == desc[href]
                          else m.group(0).replace('<p>' + body + '</p>', '<p>' + desc[href] + '</p>'))(m.group(1), m.group(3)),
               s)
    if s != orig:
        open(p, 'w').write(s)
        print(f'{d}/index.html を更新')

print('完了')
