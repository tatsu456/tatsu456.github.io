#!/usr/bin/env python3
"""暮らしの手引き（/guides/）のページを生成する。apply_chrome の共通パーツを再利用する。"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_chrome import masthead, crumbs, footer, SCRIPT, GUIDES, ROOT

from apply_chrome import CSS_VERSION as VER

PAGE = '''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}｜tatsu456</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="/assets/style.css?v={ver}">
</head>
<body>

{head}

{body}
{postnav}
{foot}

{script}

</body>
</html>
'''


def postnav_for(idx):
    """前後の記事リンク。GUIDES の並び順を使う。片側だけのときは空の span で桁を保つ。"""
    prev = next_ = None
    if idx > 0:
        h, t = GUIDES[idx - 1]
        prev = f'  <a class="prev" href="{h}"><span class="lbl">前の記事</span>{t}</a>'
    if idx < len(GUIDES) - 1:
        h, t = GUIDES[idx + 1]
        next_ = f'  <a class="next" href="{h}"><span class="lbl">次の記事</span>{t}</a>'
    if prev is None and next_ is None:
        return ''
    return ('\n<nav class="postnav" aria-label="前後の記事">\n'
            + '\n'.join([prev or '  <span></span>', next_ or '  <span></span>'])
            + '\n</nav>\n')


def build(path, title, desc, body, postnav=''):
    return PAGE.format(
        title=title, desc=desc, ver=VER,
        head=masthead(path, 'guides') + '\n\n' + crumbs([('/guides/', '暮らしの手引き'), (None, title)]),
        body=body.strip(), postnav=postnav, foot=footer(), script=SCRIPT,
    )
