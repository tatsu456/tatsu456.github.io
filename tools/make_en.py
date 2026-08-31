#!/usr/bin/env python3
"""英語版アプリページを生成する。日本語版と同じ共通パーツを使う。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_chrome import masthead, crumbs, footer, SCRIPT, ROOT

VER = '20260831c'

PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="alternate" hreflang="ja" href="https://tatsu456.github.io{ja}">
<link rel="alternate" hreflang="en" href="https://tatsu456.github.io{en}">
<link rel="alternate" hreflang="x-default" href="https://tatsu456.github.io{ja}">
<link rel="stylesheet" href="/assets/style.css?v={ver}">
</head>
<body>

{head}

<p class="langswitch">
  <a href="{ja}">日本語</a>
  <span aria-current="true">English</span>
</p>

{body}
{foot}

{script}

</body>
</html>
'''


def lang_switch_ja(en_path):
    """日本語ページ側に差し込む切り替え。"""
    return ('<p class="langswitch">\n'
            '  <span aria-current="true">日本語</span>\n'
            f'  <a href="{en_path}">English</a>\n'
            '</p>')


def en_crumbs(ja_path, crumb_label):
    """英語ページのパンくず。ラベルも英語にする。"""
    return ('<nav class="crumbs" aria-label="Breadcrumb">\n'
            '  <a href="/">Home</a>\n'
            '  <span class="sep">\u203a</span>\n'
            f'  <a href="{ja_path}">{crumb_label}</a>\n'
            '  <span class="sep">\u203a</span>\n'
            '  <span aria-current="page">English</span>\n'
            '</nav>')


def build(en_path, ja_path, title, desc, body, crumb_label):
    return PAGE.format(
        title=title, desc=desc, ver=VER, ja=ja_path, en=en_path,
        head=masthead(ja_path, 'apps') + '\n\n' + en_crumbs(ja_path, crumb_label),
        body=body.strip(), foot=footer(), script=SCRIPT,
    )
