#!/usr/bin/env python3
"""記事の図（インラインSVG）を、ブラウザを開かずに点検する。

見るのは3つ。
  1. 部品が viewBox からはみ出していないか
  2. 文字どうしが重なっていないか
  3. 使っているクラスが style.css の .fig 以下に定義されているか

文字の幅はフォントの実測ではなく字種からの見積もり（全角は文字サイズぶん、
半角はその0.55倍）。多めに見積もるので、ここで出た指摘が実際には
問題ないことはあるが、逆に見落とすことは少ない。最後はブラウザで確かめる。
"""
import re, sys, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- style.css から .fig 以下のクラスと文字サイズを読む ----------

def load_css():
    s = open(os.path.join(ROOT, 'assets', 'style.css')).read()
    classes, sizes = set(), {}
    for m in re.finditer(r'\.fig\s+\.([a-z0-9-]+)[^{]*\{([^}]*)\}', s):
        classes.add(m.group(1))
        fs = re.search(r'font-size:\s*([0-9.]+)px', m.group(2))
        if fs:
            sizes[m.group(1)] = float(fs.group(1))
    return classes, sizes


CLASSES, SIZES = load_css()
DEFAULT_SIZE = 15.0


def font_size(el_class, style, attr):
    m = re.search(r'font-size:\s*([0-9.]+)px', style or '')
    if m:
        return float(m.group(1))
    for c in (el_class or '').split():
        if c in SIZES:
            return SIZES[c]
    if attr:
        try:
            return float(re.sub(r'[^0-9.]', '', attr))
        except ValueError:
            pass
    return DEFAULT_SIZE


def char_w(ch, size):
    o = ord(ch)
    # CJK・かな・全角記号・矢印などは全角として数える
    if o >= 0x2000 and not (0x2000 <= o <= 0x200F):
        return size
    return size * 0.55


def text_w(t, size):
    return sum(char_w(c, size) for c in t)


# ---------- SVG を読む ----------

TAG = re.compile(r'<(rect|circle|ellipse|line|polygon|polyline|path|text)\b([^>]*)>(?:(.*?)</\1>)?', re.S)
ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')


def num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def path_points(d):
    """パスの通る点をだいたい拾う。制御点も含めるので広めに出る。"""
    pts, x, y = [], 0.0, 0.0
    for cmd, args in re.findall(r'([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)', d):
        vals = [float(v) for v in re.findall(r'-?[0-9]*\.?[0-9]+(?:e-?[0-9]+)?', args)]
        rel = cmd.islower()
        c = cmd.upper()
        i = 0
        if c == 'Z':
            continue
        while i < len(vals):
            if c == 'H':
                x = (x + vals[i]) if rel else vals[i]; i += 1
            elif c == 'V':
                y = (y + vals[i]) if rel else vals[i]; i += 1
            elif c in 'MLT':
                nx, ny = vals[i], vals[i + 1]; i += 2
                x, y = (x + nx, y + ny) if rel else (nx, ny)
            elif c in 'QS':
                for k in (0, 2):
                    px, py = vals[i + k], vals[i + k + 1]
                    pts.append((x + px, y + py) if rel else (px, py))
                nx, ny = vals[i + 2], vals[i + 3]; i += 4
                x, y = (x + nx, y + ny) if rel else (nx, ny)
            elif c == 'C':
                for k in (0, 2):
                    px, py = vals[i + k], vals[i + k + 1]
                    pts.append((x + px, y + py) if rel else (px, py))
                nx, ny = vals[i + 4], vals[i + 5]; i += 6
                x, y = (x + nx, y + ny) if rel else (nx, ny)
            elif c == 'A':
                nx, ny = vals[i + 5], vals[i + 6]; i += 7
                x, y = (x + nx, y + ny) if rel else (nx, ny)
            else:
                break
            pts.append((x, y))
    return pts


def body_of(svg):
    return re.sub(r'<defs>.*?</defs>', '', svg, flags=re.S)


def boxes(svg):
    """(種類, 説明, x0, y0, x1, y1) の一覧を返す。"""
    out = []
    body = svg
    # defs の中（グラデーションやマーカー）は座標系が別なので外す
    body = re.sub(r'<defs>.*?</defs>', '', body, flags=re.S)
    for m in TAG.finditer(body):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        a = dict(ATTR.findall(attrs))
        cls = a.get('class', '')
        if tag == 'rect':
            x, y = num(a.get('x')), num(a.get('y'))
            out.append(('rect', cls or 'rect', x, y, x + num(a.get('width')), y + num(a.get('height'))))
        elif tag in ('circle', 'ellipse'):
            cx, cy = num(a.get('cx')), num(a.get('cy'))
            rx = num(a.get('r'), num(a.get('rx')))
            ry = num(a.get('r'), num(a.get('ry')))
            out.append((tag, cls or tag, cx - rx, cy - ry, cx + rx, cy + ry))
        elif tag == 'line':
            x1, y1, x2, y2 = (num(a.get(k)) for k in ('x1', 'y1', 'x2', 'y2'))
            out.append(('line', cls or 'line', min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        elif tag in ('polygon', 'polyline'):
            v = [float(t) for t in re.findall(r'-?[0-9.]+', a.get('points', ''))]
            xs, ys = v[0::2], v[1::2]
            out.append((tag, cls or tag, min(xs), min(ys), max(xs), max(ys)))
        elif tag == 'path':
            pts = path_points(a.get('d', ''))
            if not pts:
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            out.append(('path', cls or 'path', min(xs), min(ys), max(xs), max(ys)))
        elif tag == 'text':
            t = re.sub(r'<[^>]+>', '', inner or '')
            size = font_size(cls, a.get('style'), a.get('font-size'))
            w = text_w(t, size)
            x, y = num(a.get('x')), num(a.get('y'))
            anc = a.get('text-anchor', 'start')
            x0 = x - w / 2 if anc == 'middle' else (x - w if anc == 'end' else x)
            # ブラウザの getBBox は字面より広く返す。実測に合わせて上0.95・下0.25で見る
            out.append(('text', t, x0, y - size * 0.95, x0 + w, y + size * 0.25))
    return out


def text_metrics(svg):
    """<text> の (中身, 左, 右, baseline, 文字サイズ) を集める。"""
    out = []
    for m in re.finditer(r'<text\b([^>]*)>(.*?)</text>', body_of(svg), re.S):
        a = dict(ATTR.findall(m.group(1)))
        t = re.sub(r'<[^>]+>', '', m.group(2))
        size = font_size(a.get('class', ''), a.get('style'), a.get('font-size'))
        w = text_w(t, size)
        x, y = num(a.get('x')), num(a.get('y'))
        anc = a.get('text-anchor', 'start')
        x0 = x - w / 2 if anc == 'middle' else (x - w if anc == 'end' else x)
        out.append((t, x0, x0 + w, y, size))
    return out


def classes_used(svg):
    return {c for attr in re.findall(r'class="([^"]*)"', svg) for c in attr.split()}


def check(svg, label=''):
    issues = []
    vb = re.search(r'viewBox="\s*(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)\s+([\d.]+)', svg)
    if not vb:
        return [f'{label}: viewBox がない']
    vx, vy, vw, vh = (float(vb.group(i)) for i in range(1, 5))
    bs = boxes(svg)

    for kind, name, x0, y0, x1, y1 in bs:
        over = []
        if x0 < vx - 0.5: over.append(f'左に{vx-x0:.1f}')
        if y0 < vy - 0.5: over.append(f'上に{vy-y0:.1f}')
        if x1 > vx + vw + 0.5: over.append(f'右に{x1-(vx+vw):.1f}')
        if y1 > vy + vh + 0.5: over.append(f'下に{y1-(vy+vh):.1f}')
        if over:
            issues.append(f'{label}: はみ出し [{kind} "{name[:20]}"] ' + '／'.join(over))

    # 文字どうしの重なり。行送りの詰まり具合は字面だけでは判定できない
    # （13pxが2行続く普通の並びと、15pxの見出しの下に13pxを置いた窮屈な並びの差が
    #  1px も出ない）ので見ない。代わりに、実際に困る「帯の縁への張り付き」を見る。
    ts = text_metrics(svg)
    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            (n1, ax0, ax1, ab, asz) = ts[i]
            (n2, bx0, bx1, bb, bsz) = ts[j]
            if min(ax1, bx1) - max(ax0, bx0) <= 1.5:
                continue
            top, bot = (ts[i], ts[j]) if ab <= bb else (ts[j], ts[i])
            if bot[3] - top[3] < top[4] * 0.25 + bot[4] * 0.95:
                issues.append(f'{label}: 文字が重なる "{n1[:16]}" × "{n2[:16]}"')

    # 帯や箱の縁に文字が張り付いていないか（内側に3px以上の余白がほしい）
    panels = [b for b in bs if b[0] == 'rect' and any(
        c in b[1].split() for c in ('panel', 'panel-bad', 'panel-good', 'box', 'box-hi',
                                    'cell', 'cell-broken'))]
    for t, tx0, tx1, tb, tsz in ts:
        ty0, ty1 = tb - tsz * 0.95, tb + tsz * 0.25
        for _, pname, px0, py0, px1, py1 in panels:
            inside_x = px0 - 2 <= tx0 and tx1 <= px1 + 2
            overlaps_y = py0 - 2 < ty1 and ty0 < py1 + 2
            if not (inside_x and overlaps_y):
                continue
            for edge, d in (('上', ty0 - py0), ('下', py1 - ty1)):
                # 2px。字の高さを多めに見積もっているので、これを割ると実際に接する
                if -1.0 < d < 2.0:
                    issues.append(f'{label}: 文字が帯の縁に近い "{t[:16]}" '
                                  f'({pname} の{edge}の内側 {d:.1f}px／2px以上あける)')

    unknown = classes_used(svg) - CLASSES - {'fig'}
    if unknown:
        issues.append(f'{label}: style.css にないクラス: {", ".join(sorted(unknown))}')
    return issues


def main(paths):
    total = 0
    for p in paths:
        s = open(p).read()
        svgs = re.findall(r'<svg\b.*?</svg>', s, flags=re.S)
        if not svgs:
            print(f'{p}: 図なし')
            continue
        for i, sv in enumerate(svgs, 1):
            for msg in check(sv, f'{os.path.basename(p)} 図{i}'):
                print(msg); total += 1
    print(f'\n指摘 {total} 件')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
