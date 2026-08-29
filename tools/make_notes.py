#!/usr/bin/env python3
"""制作ノート（/notes/）のページを生成する。apply_chrome の共通パーツを再利用する。"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_chrome import masthead, crumbs, footer, SCRIPT, NOTES, ROOT

VER = '20260829c'

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


def build(path, title, desc, body, section, trail, postnav=''):
    html = PAGE.format(
        title=title, desc=desc, ver=VER,
        head=masthead(path, section) + '\n\n' + crumbs(trail),
        body=body.strip(), postnav=postnav, foot=footer(), script=SCRIPT,
    )
    return html


def postnav_for(idx):
    """前後の記事リンク。NOTES の並び順を使う。

    片側しか無いときも枠は出す（grid の桁を保つため、無い側は空の span で埋める）。
    リンクが1本も無いとき（記事が1本しかないとき）だけ、まるごと出さない。
    """
    prev = next_ = None
    if idx > 0:
        h, t = NOTES[idx - 1]
        prev = f'  <a class="prev" href="{h}"><span class="lbl">前の記事</span>{t}</a>'
    if idx < len(NOTES) - 1:
        h, t = NOTES[idx + 1]
        next_ = f'  <a class="next" href="{h}"><span class="lbl">次の記事</span>{t}</a>'
    if prev is None and next_ is None:
        return ''
    parts = [prev or '  <span></span>', next_ or '  <span></span>']
    return '\n<nav class="postnav" aria-label="前後の記事">\n' + '\n'.join(parts) + '\n</nav>\n'
