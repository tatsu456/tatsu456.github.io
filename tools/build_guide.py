#!/usr/bin/env python3
"""書き直した記事の本文と図を組み合わせて、ページを作る。

  本文  work/new/<slug>.body.html   … <!--FIG:1--> の印で図の場所を示す
  図    work/new/<slug>.figs.py     … FIGS = [svg文字列, ...] を定義する

印と図の数が合わなければ止める。組み立てたあと checkfig で点検する。
使い方:  python3 tools/build_guide.py <slug> [<slug> ...]
        python3 tools/build_guide.py --check <slug>   … 書き出さずに点検だけ
"""
import os, re, sys, json, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
WORK = os.environ.get('GUIDE_WORK') or os.path.join(ROOT, '.work')

import make_guides as M
from apply_chrome import GUIDES
import checkfig


def load_figs(slug):
    p = os.path.join(WORK, 'new', f'{slug}.figs.py')
    if not os.path.exists(p):
        return []
    spec = importlib.util.spec_from_file_location(f'figs_{slug.replace("-","_")}', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.FIGS)


def assemble(slug):
    body = open(os.path.join(WORK, 'new', f'{slug}.body.html')).read()
    figs = load_figs(slug)
    marks = re.findall(r'<!--FIG:(\d+)-->', body)
    if sorted(int(m) for m in marks) != list(range(1, len(figs) + 1)):
        raise SystemExit(f'{slug}: 印 {marks} と図 {len(figs)} 枚が対応しない')
    for i, sv in enumerate(figs, 1):
        body = body.replace(f'<!--FIG:{i}-->', sv)
    return body


def build(slug, write=True):
    meta = json.load(open(os.path.join(WORK, 'meta.json')))[slug]
    body = assemble(slug)
    issues = []
    for i, sv in enumerate(re.findall(r'<svg\b.*?</svg>', body, flags=re.S), 1):
        issues += checkfig.check(sv, f'{slug} 図{i}')
    for m in issues:
        print(m)
    if write:
        order = [h for h, _ in GUIDES]
        idx = order.index(meta['path'])
        html = M.build(meta['path'], meta['title'], meta['desc'], body, M.postnav_for(idx))
        open(os.path.join(ROOT, meta['path'].lstrip('/')), 'w').write(html)
        print(f'  ✓ {meta["path"]}  本文{len(re.sub(r"[ \t\n]+","",re.sub(r"<[^>]+>","",body)))}字')
    return len(issues)


if __name__ == '__main__':
    args = sys.argv[1:]
    write = True
    if args and args[0] == '--check':
        write, args = False, args[1:]
    bad = sum(build(s, write) for s in args)
    sys.exit(1 if bad else 0)
