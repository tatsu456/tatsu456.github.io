#!/usr/bin/env python3
"""tatsu456.github.io の全ページに、共通ヘッダー（プルダウン）・パンくず・フッターを流し込む。

ユーザーサイト（ルート配信）なので、リンクは絶対パスで統一する。
どのページでもナビのHTMLが完全に同一になり、増減の管理が1か所で済む。
"""
import os, re, sys

ROOT = '/Users/taka/tatsu456.github.io'

# スタイルシートの版。CSSを変えたらここを上げる（全ページのリンクに付く）
CSS_VERSION = '20260831q'

APPS = [
    ('/yamajitaku/',     '山じたく',             '登山の持ち物チェックリスト'),
    ('/kondate/',        '献立メーカー_EX',      '晩ごはんの献立'),
    ('/reitou/',         '冷凍図鑑',             '切り方から解凍まで'),
    ('/nukadoko-diary/', 'ぬか床日記',           '混ぜたか覚えておかなくていい'),
    ('/splitbill/',      'SplitBill_EX',       '多通貨の割り勘'),
    ('/counter1234/',    'Counter1234',        'カウンターと記録'),
]

# 手引きは分野ごとにまとめる。本数が増えるとプルダウンが読めなくなるため。
GUIDE_GROUPS = [
    ('冷凍保存', [
        ('/guides/freezing-basics.html',     '冷凍に向く食材・向かない食材の分かれ目'),
        ('/guides/freezing-vegetables.html', '野菜の冷凍・解凍 早見表'),
        ('/guides/freezing-meat.html',       '肉の冷凍と解凍'),
        ('/guides/freezing-seafood.html',    '魚介の冷凍と解凍'),
        ('/guides/freezing-staples.html',    'ごはん・パン・麺の冷凍'),
        ('/guides/freezing-dishes.html',     '作りおきと料理の冷凍'),
        ('/guides/freezer-care.html',        '冷凍焼けを防ぐ、冷凍庫の使い方'),
    ]),
    ('ぬか床', [
        ('/guides/nukadoko-troubleshooting.html', 'ぬか床の症状別・原因と手当て'),
        ('/guides/nukazuke-timing.html',          'ぬか漬けの漬け時間は、野菜と季節で変わる'),
        ('/guides/ferment-intervals.html',        '発酵食品ごとに、世話の間隔はこれだけ違う'),
        ('/guides/ferment-storage.html',          '発酵食品を常温・冷暗所・冷蔵庫のどこに置くか'),
    ]),
    ('登山', [
        ('/guides/hiking-gear-by-altitude.html', '標高と季節で変わる登山の持ち物'),
        ('/guides/pack-weight.html',             'ザックの重さは体重の何％まで'),
        ('/guides/hiking-water.html',            '登山に水をどれだけ持つか'),
        ('/guides/hiking-advisories.html',       '山で先に知っておきたい注意は、条件で変わる'),
    ]),
    ('くらしの段取り', [
        ('/guides/meal-planning.html',           '献立が決まらないときに、何から決めるか'),
        ('/guides/shopping-list.html',           '買い物リストは、売り場の順に並べると速い'),
        ('/guides/food-cost.html',               '献立の材料費は、何で決まるか'),
        ('/guides/splitting-bills.html',         '割り勘の計算は、足す順序で金額が変わる'),
        ('/guides/currency-rates.html',          '旅行の割り勘で、為替レートをいつ確定させるか'),
        ('/guides/lending-excluding.html',       '割り勘から外すもの、立て替えたもの'),
        ('/guides/counting-situations.html',     '数え間違いが起きる場面と、その防ぎ方'),
        ('/guides/counting-record.html',         '数えたあとに、記録をどう残すか'),
        ('/guides/counting-inventory.html',      '棚卸しの段取り'),
    ]),
]

# 分野ごとの一覧ページ。パンくずの中間階層になる
GUIDE_CATEGORIES = {
    '冷凍保存':       ('/guides/freezing/', '冷凍保存'),
    'ぬか床':         ('/guides/nukadoko/', 'ぬか床と発酵'),
    '登山':           ('/guides/hiking/',   '登山'),
    'くらしの段取り': ('/guides/living/',   'くらしの段取り'),
}

# 平坦なリスト（フッターやページ定義で使う）
GUIDES = [row for _, rows in GUIDE_GROUPS for row in rows]

# 記事 → 所属カテゴリ（パンくずに使う）
GUIDE_OF = {href: label for label, rows in GUIDE_GROUPS for href, _ in rows}

# アプリの並びに合わせる
POLICIES = [
    ('/yamajitaku/privacy.html',      '山じたく'),
    ('/privacy-policy.html',          '献立メーカー_EX'),
    ('/reitou/privacy.html',          '冷凍図鑑'),
    ('/nukadoko-diary/privacy.html',  'ぬか床日記'),
    ('/splitbill/privacy.html',       'SplitBill_EX'),
    ('/counter1234/privacy.html',     'Counter1234'),
]


def cur(href, page):
    return ' aria-current="page"' if href == page else ''


def masthead(page, section):
    def items(rows, withsub=True):
        out = []
        for row in rows:
            href, name = row[0], row[1]
            sub = row[2] if withsub and len(row) > 2 else None
            inner = name + (f'<small>{sub}</small>' if sub else '')
            out.append(f'      <a href="{href}"{cur(href, page)}>{inner}</a>')
        return '\n'.join(out)

    def openattr(sec):
        return ' data-current' if section == sec else ''

    def grouped_guides(page):
        """分野を折りたたみにして、既定では分野名だけが並ぶようにする。

        24本を平らに並べると縦に長くなりすぎるため、分野ごとの <details> に畳む。
        いま開いているページを含む分野だけは開いた状態で出す。
        """
        out = []
        for label, rows in GUIDE_GROUPS:
            url, title = GUIDE_CATEGORIES[label]
            here = page == url or any(page == h for h, _ in rows)
            out.append(f'        <details class="submenu"{" open" if here else ""}>')
            out.append(f'          <summary>{title}<small>{len(rows)}本</small></summary>')
            out.append(f'          <div class="sub-items">')
            out.append(f'            <a class="sub-index" href="{url}"{cur(url, page)}>'
                       f'{title}の記事一覧</a>')
            for href, name in rows:
                out.append(f'            <a href="{href}"{cur(href, page)}>{name}</a>')
            out.append('          </div>')
            out.append('        </details>')
        return '\n'.join(out)

    return f'''<header class="masthead">
<div class="masthead-inner">
  <a class="brand" href="/">tatsu456</a>
  <nav class="mainnav" aria-label="サイト内メニュー">
    <a href="/"{cur('/', page)}>ホーム</a>
    <details class="menu"{openattr('apps')}>
      <summary>アプリ</summary>
      <div class="menu-panel">
{items(APPS)}
      </div>
    </details>
    <details class="menu"{openattr('guides')}>
      <summary>暮らしの手引き</summary>
      <div class="menu-panel">
        <a href="/guides/"{cur('/guides/', page)}>記事の一覧</a>
{grouped_guides(page)}
      </div>
    </details>
    <details class="menu"{openattr('support')}>
      <summary>サポート</summary>
      <div class="menu-panel">
        <a href="/#contact">お問い合わせ</a>
        <hr>
        <p class="grp">プライバシーポリシー</p>
{items(POLICIES)}
        <hr>
        <a href="/reitou/terms.html"{cur('/reitou/terms.html', page)}>利用規約（冷凍図鑑）</a>
      </div>
    </details>
  </nav>
</div>
</header>'''


def crumbs(trail):
    """trail: [(href|None, label), ...] 末尾は現在地"""
    if not trail:
        return ''
    parts = ['<nav class="crumbs" aria-label="現在の位置">', '  <a href="/">ホーム</a>']
    for href, label in trail:
        parts.append('  <span class="sep">›</span>')
        if href:
            parts.append(f'  <a href="{href}">{label}</a>')
        else:
            parts.append(f'  <span aria-current="page">{label}</span>')
    parts.append('</nav>')
    return '\n'.join(parts)


def footer():
    def lis(rows, withsub=False):
        return '\n'.join(f'      <li><a href="{r[0]}">{r[1]}</a></li>' for r in rows)
    return f'''<footer class="sitefooter">
<div class="sitefooter-inner">
  <div>
    <h2>アプリ</h2>
    <ul>
{lis(APPS)}
    </ul>
  </div>
  <div>
    <h2>暮らしの手引き</h2>
    <ul>
      <li><a href="/guides/">記事の一覧</a></li>
{lis(GUIDES)}
    </ul>
  </div>
  <div>
    <h2>サポート</h2>
    <ul>
      <li><a href="/#contact">お問い合わせ</a></li>
      <li><a href="/privacy-policy.html">プライバシーポリシー</a></li>
      <li><a href="/reitou/terms.html">利用規約（冷凍図鑑）</a></li>
    </ul>
  </div>
  <div class="copy">© 2026 tatsu456　iOSアプリを作っています。</div>
</div>
</footer>'''


SCRIPT = '''<script>
(function () {
  var menus = Array.prototype.slice.call(document.querySelectorAll('.masthead .menu'));
  menus.forEach(function (m) {
    m.addEventListener('toggle', function () {
      if (m.open) menus.forEach(function (o) { if (o !== m) o.open = false; });
    });
  });

  // 分野の折りたたみ。広い画面では右に張り出すので、同時に開くと重なる。
  var subs = Array.prototype.slice.call(document.querySelectorAll('.masthead .submenu'));
  subs.forEach(function (s) {
    s.addEventListener('toggle', function () {
      if (s.open) subs.forEach(function (o) { if (o !== s) o.open = false; });
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.masthead .menu')) menus.forEach(function (m) { m.open = false; });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') menus.forEach(function (m) { m.open = false; });
  });
})();
</script>'''


# ページ定義: 相対パス -> (現在地の絶対パス, セクション, パンくずtrail)
PAGES = {
    'index.html': ('/', 'home', []),

    'guides/index.html': ('/guides/', 'guides', [(None, '暮らしの手引き')]),
    'guides/freezing-basics.html': ('/guides/freezing-basics.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '冷凍に向く食材・向かない食材の分かれ目')]),
    'guides/freezing-vegetables.html': ('/guides/freezing-vegetables.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '野菜の冷凍・解凍 早見表')]),
    'guides/nukadoko-troubleshooting.html': ('/guides/nukadoko-troubleshooting.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, 'ぬか床の症状別・原因と手当て')]),
    'guides/hiking-gear-by-altitude.html': ('/guides/hiking-gear-by-altitude.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '標高と季節で変わる登山の持ち物')]),
    'guides/freezing-meat.html': ('/guides/freezing-meat.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '肉の冷凍と解凍')]),
    'guides/freezing-seafood.html': ('/guides/freezing-seafood.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '魚介の冷凍と解凍')]),
    'guides/freezing-staples.html': ('/guides/freezing-staples.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, 'ごはん・パン・麺の冷凍')]),
    'guides/freezing-dishes.html': ('/guides/freezing-dishes.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '作りおきと料理の冷凍')]),
    'guides/freezer-care.html': ('/guides/freezer-care.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '冷凍焼けを防ぐ、冷凍庫の使い方')]),
    'guides/pack-weight.html': ('/guides/pack-weight.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, 'ザックの重さは体重の何％まで')]),
    'guides/nukazuke-timing.html': ('/guides/nukazuke-timing.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, 'ぬか漬けの漬け時間は、野菜と季節で変わる')]),
    'guides/meal-planning.html': ('/guides/meal-planning.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '献立が決まらないときに、何から決めるか')]),
    'guides/splitting-bills.html': ('/guides/splitting-bills.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '割り勘の計算は、足す順序で金額が変わる')]),
    'guides/counting-situations.html': ('/guides/counting-situations.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '数え間違いが起きる場面と、その防ぎ方')]),
    'guides/ferment-intervals.html': ('/guides/ferment-intervals.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '発酵食品ごとに、世話の間隔はこれだけ違う')]),
    'guides/ferment-storage.html': ('/guides/ferment-storage.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '発酵食品を常温・冷暗所・冷蔵庫のどこに置くか')]),
    'guides/hiking-water.html': ('/guides/hiking-water.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '登山に水をどれだけ持つか')]),
    'guides/hiking-advisories.html': ('/guides/hiking-advisories.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '山で先に知っておきたい注意は、条件で変わる')]),
    'guides/counting-record.html': ('/guides/counting-record.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '数えたあとに、記録をどう残すか')]),
    'guides/counting-inventory.html': ('/guides/counting-inventory.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '棚卸しの段取り')]),
    'guides/shopping-list.html': ('/guides/shopping-list.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '買い物リストは、売り場の順に並べると速い')]),
    'guides/food-cost.html': ('/guides/food-cost.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '献立の材料費は、何で決まるか')]),
    'guides/currency-rates.html': ('/guides/currency-rates.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '旅行の割り勘で、為替レートをいつ確定させるか')]),
    'guides/lending-excluding.html': ('/guides/lending-excluding.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '割り勘から外すもの、立て替えたもの')]),

    'counter1234/index.html': ('/counter1234/', 'apps', [(None, 'Counter1234')]),
    'counter1234/privacy.html': ('/counter1234/privacy.html', 'support',
        [('/counter1234/', 'Counter1234'), (None, 'プライバシーポリシー')]),
    'kondate/index.html': ('/kondate/', 'apps', [(None, '献立メーカー_EX')]),
    'splitbill/index.html': ('/splitbill/', 'apps', [(None, 'SplitBill_EX')]),
    'splitbill/privacy.html': ('/splitbill/privacy.html', 'support',
        [('/splitbill/', 'SplitBill_EX'), (None, 'プライバシーポリシー')]),
    'yamajitaku/index.html': ('/yamajitaku/', 'apps', [(None, '山じたく')]),
    'yamajitaku/privacy.html': ('/yamajitaku/privacy.html', 'support',
        [('/yamajitaku/', '山じたく'), (None, 'プライバシーポリシー')]),
    'reitou/index.html': ('/reitou/', 'apps', [(None, '冷凍図鑑')]),
    'reitou/privacy.html': ('/reitou/privacy.html', 'support',
        [('/reitou/', '冷凍図鑑'), (None, 'プライバシーポリシー')]),
    'reitou/terms.html': ('/reitou/terms.html', 'support',
        [('/reitou/', '冷凍図鑑'), (None, '利用規約')]),

    'privacy-policy.html': ('/privacy-policy.html', 'support', [(None, 'プライバシーポリシー')]),
}


def apply(rel, page, section, trail):
    path = os.path.join(ROOT, rel)
    s = open(path, encoding='utf-8').read()
    before = s

    block = masthead(page, section)
    c = crumbs(trail)
    if c:
        block += '\n\n' + c

    # 既存のヘッダーとパンくずを「すべて」取り除いてから入れ直す。
    # 属性違い（aria-label など）で取り逃すと、再実行のたびに二重に積まれるため、
    # 置換ではなく全削除＋挿入にして冪等にしている。
    if 'class="sitenav"' in s:
        s = re.sub(r'<nav class="sitenav">.*?</nav>', '', s, flags=re.S)
    s = re.sub(r'<header class="masthead">.*?</header>', '', s, flags=re.S)
    s = re.sub(r'<nav class="crumbs"[^>]*>.*?</nav>', '', s, flags=re.S)
    s = s.replace('<body>', '<body>\n\n' + block, 1)

    # パンくずと重複する戻りリンクを外す
    s = re.sub(r'\n?<p class="note"><a href="\.\./">← アプリ一覧</a></p>\n?', '\n', s)

    # 旧フッターを共通フッターへ
    s = re.sub(r'<footer>.*?</footer>', '', s, flags=re.S)
    s = re.sub(r'<footer class="sitefooter">.*?</footer>', '', s, flags=re.S)
    s = re.sub(r'<script>\s*\(function \(\) \{\s*var menus.*?</script>', '', s, flags=re.S)
    s = s.replace('</body>', footer() + '\n\n' + SCRIPT + '\n\n</body>')

    # スタイルシートの版を、生成のたびに現在の値へそろえる
    s = re.sub(r'(/assets/style\.css\?v=)[0-9a-z]+', r'\g<1>' + CSS_VERSION, s)

    # 列の多い表がページごと横に流れないよう、表を横スクロールの包みに入れる。
    # 何度流しても同じ結果になるよう、いったん全部ほどいてから包み直す。
    while '<div class="tablewrap">' in s:
        s2 = re.sub(r'\n?<div class="tablewrap">\s*(<table class="data">.*?</table>)\s*</div>',
                    lambda m: '\n' + m.group(1), s, flags=re.S)
        s2 = re.sub(r'\n?<div class="tablewrap">\s*(<div class="tablewrap">)', r'\n\1', s2)
        s2 = re.sub(r'(</table>)\s*</div>\s*</div>', r'\1\n</div>', s2)
        if s2 == s:
            break
        s = s2
    s = re.sub(r'\n?(<table class="data">.*?</table>)',
               lambda m: '\n<div class="tablewrap">\n' + m.group(1) + '\n</div>',
               s, flags=re.S)

    # 余分な空行を整理
    s = re.sub(r'\n{4,}', '\n\n\n', s)

    if s != before:
        open(path, 'w', encoding='utf-8').write(s)
        return True
    return False


def guide_trail(page):
    """手引きの記事は、分野の一覧ページを挟んだ4階層にする。"""
    label = GUIDE_OF.get(page)
    if label is None:
        return None
    cat_url, cat_title = GUIDE_CATEGORIES[label]
    title = dict(GUIDES)[page]
    return [('/guides/', '暮らしの手引き'), (cat_url, cat_title), (None, title)]


if __name__ == '__main__':
    n = 0
    for rel, (page, section, trail) in PAGES.items():
        trail = guide_trail(page) or trail
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f'  skip (未作成): {rel}')
            continue
        if apply(rel, page, section, trail):
            n += 1
            print(f'  ✓ {rel}')
    print(f'\n{n} ページ更新')
