#!/usr/bin/env python3
"""記事に入れる図を組み立てる。

座標を手で書くとずれるので、部品を関数にして計算で置く。
色は CSS 側の変数（.fig 以下）を参照するので、ダーク／ライトに追従する。
"""
import math


# ---------- 部品 ----------

def snowflake(cx, cy, r, cls='ice', arms=6, branch=True):
    """雪の結晶。arms 本の腕を放射状に引き、各腕に小枝を付ける。"""
    d = []
    for i in range(arms // 2):
        a = math.pi * i / (arms // 2)
        dx, dy = math.cos(a) * r, math.sin(a) * r
        d.append(f'M{cx-dx:.1f} {cy-dy:.1f} L{cx+dx:.1f} {cy+dy:.1f}')
    if branch:
        for i in range(arms):
            a = 2 * math.pi * i / arms
            # 腕の 55% と 80% の位置に、±35度の小枝
            for at, bl in ((0.55, 0.30), (0.80, 0.20)):
                bx, by = cx + math.cos(a) * r * at, cy + math.sin(a) * r * at
                for s in (+1, -1):
                    a2 = a + s * math.radians(38)
                    d.append(f'M{bx:.1f} {by:.1f} '
                             f'L{bx+math.cos(a2)*r*bl:.1f} {by+math.sin(a2)*r*bl:.1f}')
    return f'<path class="{cls}" d="{" ".join(d)}"/>'


def droplet(cx, cy, r=5):
    """しずく。上がとがった水滴の形。"""
    return (f'<path class="drop" d="M{cx:.1f} {cy-r*1.6:.1f} '
            f'C{cx+r:.1f} {cy-r*0.2:.1f} {cx+r:.1f} {cy+r:.1f} {cx:.1f} {cy+r:.1f} '
            f'C{cx-r:.1f} {cy+r:.1f} {cx-r:.1f} {cy-r*0.2:.1f} {cx:.1f} {cy-r*1.6:.1f} Z"/>')


def pill(x, y, w, h, text, hi=False, size=14):
    """角丸のラベル。hi=True で塗りつぶし。

    size が効くのは hi=True のときだけ。hi=False の文字は .t-sm クラスが付き、
    CSS の font-size(13px) が属性より強いので、size を渡しても 13px で描かれる。
    幅を見積もるときは 13px として数えること。
    """
    c = 'pill-hi' if hi else 'pill'
    if hi:
        return (f'<rect class="{c}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2:.0f}"/>'
                f'<text class="t-on" x="{x+w/2:.0f}" y="{y+h/2+size*0.36:.0f}" '
                f'text-anchor="middle" font-size="{size}">{text}</text>')
    return (f'<rect class="{c}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2:.0f}"/>'
            f'<text class="t-sm" x="{x+w/2:.0f}" y="{y+h/2+4.6:.0f}" text-anchor="middle">{text}</text>')


def diamond(cx, cy, w, h):
    """判断の菱形。"""
    return (f'<path class="dia" d="M{cx:.0f} {cy-h/2:.0f} L{cx+w/2:.0f} {cy:.0f} '
            f'L{cx:.0f} {cy+h/2:.0f} L{cx-w/2:.0f} {cy:.0f} Z"/>')


def elbow(x1, y1, x2, y2, r=10, marker='arw'):
    """角を丸めた直角の接続線。縦→横の順に曲がる。"""
    if abs(y2 - y1) < 1:
        d = f'M{x1} {y1} L{x2} {y2}'
    else:
        sx = 1 if x2 > x1 else -1
        sy = 1 if y2 > y1 else -1
        d = (f'M{x1} {y1} V{y2 - sy*r} '
             f'Q{x1} {y2} {x1 + sx*r} {y2} H{x2}')
    return f'<path class="arrow" d="{d}" marker-end="url(#{marker})"/>'


ARROW_DEFS = (
    '<defs>'
    '<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
    'orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" opacity=".5"/></marker>'
    '</defs>'
)


def svg(view_w, view_h, body, label, pad_top=4):
    """図の外枠。上に少し余白を取るのは、いちばん上の見出しの文字の
    上端が baseline より上に出て、viewBox からはみ出すため。"""
    return (f'<svg viewBox="0 {-pad_top} {view_w} {view_h + pad_top}" role="img" '
            f'aria-label="{label}">\n{ARROW_DEFS}\n{body}\n</svg>')


def lines(x, y, rows, cls='t-sm', anchor='middle', lh=17):
    """複数行のテキスト。rows は (文字列, クラス上書き or None) か文字列。"""
    out = []
    for i, row in enumerate(rows):
        txt, c = (row, cls) if isinstance(row, str) else row
        out.append(f'<text class="{c}" x="{x}" y="{y + i*lh}" text-anchor="{anchor}">{txt}</text>')
    return '\n'.join(out)
