#!/usr/bin/env python3
"""tatsu456.github.io の全ページに、共通ヘッダー（プルダウン）・パンくず・フッターを流し込む。

ユーザーサイト（ルート配信）なので、リンクは絶対パスで統一する。
どのページでもナビのHTMLが完全に同一になり、増減の管理が1か所で済む。
"""
import os, re, sys

ROOT = '/Users/taka/tatsu456.github.io'

# スタイルシートの版。CSSを変えたらここを上げる（全ページのリンクに付く）
CSS_VERSION = '20261002a'

# Google アナリティクス（GA4）の測定ID。tatsu456.github.io 用のウェブストリーム。
GA_ID = 'G-MMGJW4XELK'

GA_SNIPPET = f'''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{ dataLayer.push(arguments); }}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>'''

APPS = [
    ('/yamajitaku/',     '山じたく',             '登山の持ち物チェックリスト'),
    ('/albumdiet/',      'アルバムダイエット',   '写真と動画を小さくして容量確保'),
    ('/ablooplay/',      'ABループレイ',         'ABリピートとゆっくり再生'),
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
        ('/guides/iphone-storage.html',          'iPhone の容量がいっぱいになったら、何から片付けるか'),
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
    ('/albumdiet/privacy.html',       'アルバムダイエット'),
    ('/ablooplay/privacy.html',       'ABループレイ'),
    ('/privacy-policy.html',          '献立メーカー_EX'),
    ('/reitou/privacy.html',          '冷凍図鑑'),
    ('/nukadoko-diary/privacy.html',  'ぬか床日記'),
    ('/splitbill/privacy.html',       'SplitBill_EX'),
    ('/counter1234/privacy.html',     'Counter1234'),
]


# 英語ページ。ヘッダーとフッターも英語にする。
# 山じたく・献立・冷凍図鑑はアプリが日本語だけなので、副題でそう断る
APPS_EN = [
    ('/yamajitaku/en/',     'Yamajitaku',        'Hiking packing list (Japanese only)'),
    ('/albumdiet/en/',      'Album Diet',        'Shrink photos and videos, free up space'),
    ('/ablooplay/en/',      'ABLooplay',         'A-B repeat and slow playback'),
    ('/kondate/en/',        'Kondate Maker_EX',  'Dinner menu planner (Japanese only)'),
    ('/reitou/en/',         'Reitou Zukan',      'How to freeze 181 foods (Japanese only)'),
    ('/nukadoko-diary/en/', 'Nuka Diary',        'Care log for your nuka pot'),
    ('/splitbill/en/',      'SplitBill_EX',      'Multi-currency bill splitting'),
    ('/counter1234/en/',    'Counter1234',       'Count without looking'),
]

POLICIES_EN = [
    ('/yamajitaku/en/privacy.html',      'Yamajitaku'),
    ('/albumdiet/en/privacy.html',       'Album Diet'),
    ('/ablooplay/en/privacy.html',       'ABLooplay'),
    ('/kondate/en/privacy.html',         'Kondate Maker_EX'),
    ('/reitou/en/privacy.html',          'Reitou Zukan'),
    ('/nukadoko-diary/en/privacy.html',  'Nuka Diary'),
    ('/splitbill/en/privacy.html',       'SplitBill_EX'),
    ('/counter1234/en/privacy.html',     'Counter1234'),
]

# 日本語ページ → 英語ページ。右上の言語の切り替えと hreflang に使う。
# 対になる英語ページが無いページ（手引きなど）では、切り替えは英語のトップへ向ける
EN_OF = {
    '/': '/en/',
    '/privacy-policy.html': '/kondate/en/privacy.html',
    '/reitou/terms.html': '/reitou/en/terms.html',
}
for _href, _name, _sub in APPS:
    EN_OF[_href] = _href + 'en/'
for _href, _name in POLICIES:
    if _href != '/privacy-policy.html':
        EN_OF[_href] = _href.replace('/privacy.html', '/en/privacy.html')
JA_OF = {en: ja for ja, en in EN_OF.items()}


def lang_selector(page, lang):
    """右上の言語の切り替え。いま見ている言語は押せない印にする。"""
    if lang == 'en':
        ja, en = JA_OF.get(page, '/'), page
    else:
        ja, en = page, EN_OF.get(page, '/en/')
    def item(code, label, href):
        if code == lang:
            return f'<span lang="{code}" aria-current="true">{label}</span>'
        return f'<a href="{href}" lang="{code}" hreflang="{code}">{label}</a>'
    return ('  <div class="langsel" role="group" aria-label="言語 / Language">'
            + item('ja', '日本語', ja) + item('en', 'English', en) + '</div>')


def cur(href, page):
    return ' aria-current="page"' if href == page else ''


def masthead(page, section, lang='ja'):
    if lang == 'en':
        return masthead_en(page, section)

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
{lang_selector(page, 'ja')}
</div>
</header>'''


def masthead_en(page, section):
    """英語ページのヘッダー。手引きの記事は日本語だけなので、メニューには出さない。"""
    def items(rows):
        out = []
        for row in rows:
            href, name = row[0], row[1]
            sub = f'<small>{row[2]}</small>' if len(row) > 2 else ''
            out.append(f'      <a href="{href}"{cur(href, page)}>{name}{sub}</a>')
        return '\n'.join(out)

    def openattr(sec):
        return ' data-current' if section == sec else ''

    return f'''<header class="masthead">
<div class="masthead-inner">
  <a class="brand" href="/en/">tatsu456</a>
  <nav class="mainnav" aria-label="Site menu">
    <a href="/en/"{cur('/en/', page)}>Home</a>
    <details class="menu"{openattr('apps')}>
      <summary>Apps</summary>
      <div class="menu-panel">
{items(APPS_EN)}
      </div>
    </details>
    <details class="menu"{openattr('support')}>
      <summary>Support</summary>
      <div class="menu-panel">
        <a href="/en/#contact">Contact</a>
        <hr>
        <p class="grp">Privacy policies</p>
{items(POLICIES_EN)}
        <hr>
        <a href="/reitou/en/terms.html"{cur('/reitou/en/terms.html', page)}>Terms of Use (Reitou Zukan)</a>
      </div>
    </details>
  </nav>
{lang_selector(page, 'en')}
</div>
</header>'''


def crumbs(trail, lang='ja'):
    """trail: [(href|None, label), ...] 末尾は現在地。lang='en' で英語ページ用の見出しにする"""
    if not trail:
        return ''
    aria, home, top = (('Breadcrumb', 'Home', '/en/') if lang == 'en'
                       else ('現在の位置', 'ホーム', '/'))
    parts = [f'<nav class="crumbs" aria-label="{aria}">', f'  <a href="{top}">{home}</a>']
    for href, label in trail:
        parts.append('  <span class="sep">›</span>')
        if href:
            parts.append(f'  <a href="{href}">{label}</a>')
        else:
            parts.append(f'  <span aria-current="page">{label}</span>')
    parts.append('</nav>')
    return '\n'.join(parts)


def footer(lang='ja'):
    if lang == 'en':
        return footer_en()

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
  <div class="copy">© 2026 tatsu456　アプリを作っています。</div>
</div>
</footer>'''


def footer_en():
    def lis(rows):
        return '\n'.join(f'      <li><a href="{r[0]}">{r[1]}</a></li>' for r in rows)
    return f'''<footer class="sitefooter">
<div class="sitefooter-inner">
  <div>
    <h2>Apps</h2>
    <ul>
{lis(APPS_EN)}
    </ul>
  </div>
  <div>
    <h2>Privacy policies</h2>
    <ul>
{lis(POLICIES_EN)}
    </ul>
  </div>
  <div>
    <h2>Support</h2>
    <ul>
      <li><a href="/en/#contact">Contact</a></li>
      <li><a href="/reitou/en/terms.html">Terms of Use (Reitou Zukan)</a></li>
      <li><a href="/guides/" hreflang="ja">Guides (in Japanese)</a></li>
    </ul>
  </div>
  <div class="copy">© 2026 tatsu456 — I make small apps.</div>
</div>
</footer>'''


SCRIPT = '''<!-- ここから下は tools/apply_chrome.py が入れ直す -->
<script>
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
</script>

<script>
(function () {
  // スクリーンショットは、ページを離れずに大きく見られるようにする。
  // リンクのままだと画像のURLへ飛ぶので、ブラウザの戻るでしか帰れず、
  // 隣の画面と見比べることもできない。閉じるボタンと前後の送りを出す。
  // ここが動かないときは、これまでどおりリンクとして開く。
  var groups = Array.prototype.slice.call(document.querySelectorAll('.shots'));
  if (!groups.length || !document.body) return;
  var en = document.documentElement.lang === 'en';
  var words = en
    ? { dialog: 'Screenshot', close: 'Close', prev: 'Previous screen', next: 'Next screen' }
    : { dialog: '画面を大きく見る', close: '閉じる', prev: '前の画面', next: '次の画面' };

  var links = [];     // いま開いている並び。ページに複数あっても混ざらない
  var at = 0;
  var opener = null;  // 閉じたときに、押した絵へ戻す

  var box = document.createElement('div');
  box.className = 'lightbox';
  box.hidden = true;
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.setAttribute('aria-label', words.dialog);
  box.innerHTML =
    '<button type="button" class="lightbox-btn lightbox-close" aria-label="' + words.close + '">\u00d7</button>' +
    '<img class="lightbox-image" alt="">' +
    '<button type="button" class="lightbox-btn lightbox-prev" aria-label="' + words.prev + '">\u2039</button>' +
    '<button type="button" class="lightbox-btn lightbox-next" aria-label="' + words.next + '">\u203a</button>' +
    '<p class="lightbox-bar"><span class="lightbox-caption"></span>' +
    '<span class="lightbox-count"></span></p>';
  document.body.appendChild(box);

  var image = box.querySelector('.lightbox-image');
  var caption = box.querySelector('.lightbox-caption');
  var count = box.querySelector('.lightbox-count');
  var btnClose = box.querySelector('.lightbox-close');
  var btnPrev = box.querySelector('.lightbox-prev');
  var btnNext = box.querySelector('.lightbox-next');

  function show(n) {
    at = (n + links.length) % links.length;
    var link = links[at];
    var thumb = link.querySelector('img');
    var text = thumb ? (thumb.getAttribute('alt') || '') : '';
    image.src = link.getAttribute('href');
    image.alt = text;
    caption.textContent = text;
    var many = links.length > 1;
    count.textContent = many ? (at + 1) + ' / ' + links.length : '';
    btnPrev.hidden = !many;
    btnNext.hidden = !many;
    // 隣のぶんを先に読ませる。送るたびに白くなるのを避ける。
    if (many) {
      [1, -1].forEach(function (d) {
        var ahead = new Image();
        ahead.src = links[(at + d + links.length) % links.length].getAttribute('href');
      });
    }
  }

  function open(group, n, from) {
    links = Array.prototype.slice.call(group.querySelectorAll('a'));
    opener = from || null;
    box.hidden = false;
    document.body.classList.add('lightbox-open');
    show(n);
    btnClose.focus();
  }

  function shut() {
    box.hidden = true;
    image.removeAttribute('src');
    document.body.classList.remove('lightbox-open');
    if (opener) { opener.focus(); opener = null; }
  }

  groups.forEach(function (group) {
    Array.prototype.slice.call(group.querySelectorAll('a')).forEach(function (link, n) {
      link.addEventListener('click', function (e) {
        // 新しいタブで開きたい人の邪魔はしない
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        open(group, n, link);
      });
    });
  });

  btnClose.addEventListener('click', shut);
  btnPrev.addEventListener('click', function () { show(at - 1); });
  btnNext.addEventListener('click', function () { show(at + 1); });

  // 画像やボタン以外を押したら閉じる
  box.addEventListener('click', function (e) {
    if (e.target === image || e.target.closest('.lightbox-btn')) return;
    shut();
  });

  document.addEventListener('keydown', function (e) {
    if (box.hidden) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      shut();
    } else if (e.key === 'ArrowLeft' && links.length > 1) {
      e.preventDefault();
      show(at - 1);
    } else if (e.key === 'ArrowRight' && links.length > 1) {
      e.preventDefault();
      show(at + 1);
    } else if (e.key === 'Tab') {
      // 開いているあいだは、閉じる・前へ・次へ の中だけを回す
      var stops = [btnClose, btnPrev, btnNext].filter(function (b) { return !b.hidden; });
      var i = stops.indexOf(document.activeElement);
      e.preventDefault();
      stops[(i + (e.shiftKey ? -1 : 1) + stops.length) % stops.length].focus();
    }
  });

  // 指で左右になぞっても送れる。狭い画面では矢印より先にこちらを使う。
  var fromX = null;
  var fromY = null;
  box.addEventListener('touchstart', function (e) {
    if (e.touches.length !== 1) { fromX = null; return; }
    fromX = e.touches[0].clientX;
    fromY = e.touches[0].clientY;
  }, { passive: true });
  box.addEventListener('touchend', function (e) {
    if (fromX === null || links.length < 2) { fromX = null; return; }
    var end = e.changedTouches[0];
    var dx = end.clientX - fromX;
    var dy = end.clientY - fromY;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) show(at + (dx < 0 ? 1 : -1));
    fromX = null;
  }, { passive: true });
})();
</script>
<!-- ここまで -->'''


# ページ定義: 相対パス -> (現在地の絶対パス, セクション, パンくずtrail)
PAGES = {
    'index.html': ('/', 'home', []),

    'guides/index.html': ('/guides/', 'guides', [(None, '暮らしの手引き')]),

    # 英語ページ（ヘッダー・パンくず・フッターも英語）。下の EN_PAGES から足す

    # 分野ページ。ここが対象から漏れていて、CSSの版もアプリの並びも古いままだった
    'guides/freezing/index.html': ('/guides/freezing/', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '冷凍保存')]),
    'guides/nukadoko/index.html': ('/guides/nukadoko/', 'guides',
        [('/guides/', '暮らしの手引き'), (None, 'ぬか床と発酵')]),
    'guides/hiking/index.html': ('/guides/hiking/', 'guides',
        [('/guides/', '暮らしの手引き'), (None, '登山')]),
    'guides/living/index.html': ('/guides/living/', 'guides',
        [('/guides/', '暮らしの手引き'), (None, 'くらしの段取り')]),
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
    'guides/iphone-storage.html': ('/guides/iphone-storage.html', 'guides',
        [('/guides/', '暮らしの手引き'), (None, 'iPhone の容量がいっぱいになったら、何から片付けるか')]),

    'counter1234/index.html': ('/counter1234/', 'apps', [(None, 'Counter1234')]),
    'counter1234/privacy.html': ('/counter1234/privacy.html', 'support',
        [('/counter1234/', 'Counter1234'), (None, 'プライバシーポリシー')]),
    'kondate/index.html': ('/kondate/', 'apps', [(None, '献立メーカー_EX')]),
    'splitbill/index.html': ('/splitbill/', 'apps', [(None, 'SplitBill_EX')]),
    'splitbill/privacy.html': ('/splitbill/privacy.html', 'support',
        [('/splitbill/', 'SplitBill_EX'), (None, 'プライバシーポリシー')]),
    'albumdiet/index.html': ('/albumdiet/', 'apps', [(None, 'アルバムダイエット')]),
    'albumdiet/privacy.html': ('/albumdiet/privacy.html', 'support',
        [('/albumdiet/', 'アルバムダイエット'), (None, 'プライバシーポリシー')]),
    'ablooplay/index.html': ('/ablooplay/', 'apps', [(None, 'ABループレイ')]),
    'ablooplay/privacy.html': ('/ablooplay/privacy.html', 'support',
        [('/ablooplay/', 'ABループレイ'), (None, 'プライバシーポリシー')]),
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


SITE = 'https://tatsu456.github.io'


def hreflang_links(page, lang):
    """日本語と英語の対があるページにだけ、互いを指す hreflang を付ける。"""
    ja = page if lang == 'ja' else JA_OF.get(page)
    en = EN_OF.get(page) if lang == 'ja' else page
    if not ja or not en:
        return ''
    # 対の相手がまだ無い（英語版を作っていない）ときは付けない
    if not (os.path.exists(local_file(ja)) and os.path.exists(local_file(en))):
        return ''
    return (f'<link rel="alternate" hreflang="ja" href="{SITE}{ja}">\n'
            f'<link rel="alternate" hreflang="en" href="{SITE}{en}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}{ja}">')


def local_file(href):
    """公開パスから手元のファイルへ。/nukadoko-diary/ は別リポジトリ。"""
    rel = href.lstrip('/')
    if rel.endswith('/') or rel == '':
        rel += 'index.html'
    if rel.startswith('nukadoko-diary/'):
        return os.path.join(NUKADOKO_ROOT, rel[len('nukadoko-diary/'):])
    return os.path.join(ROOT, rel)


# /nukadoko-diary/ を配信している別リポジトリ（tatsu456/nukadoko-diary）の手元
NUKADOKO_ROOT = os.path.expanduser('~/nukadoko-diary')


def apply(rel, page, section, trail, lang='ja', root=ROOT):
    path = os.path.join(root, rel)
    s = open(path, encoding='utf-8').read()
    before = s

    block = masthead(page, section, lang)
    c = crumbs(trail, lang)
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

    # 言語の切り替えはヘッダーの右上に移した。本文に置いていた分は外す
    s = re.sub(r'\n?<p class="langswitch">.*?</p>\n?', '\n', s, flags=re.S)

    # ページの言語と、対になるページへの hreflang
    s = re.sub(r'<html lang="[a-z-]+">', f'<html lang="{lang}">', s, count=1)
    s = re.sub(r'<link rel="alternate" hreflang="[^"]+" href="[^"]*">\n?', '', s)
    links = hreflang_links(page, lang)
    if links:
        s = re.sub(r'(\n<link rel="stylesheet")', '\n' + links + r'\1', s, count=1)

    # パンくずと重複する戻りリンクを外す
    s = re.sub(r'\n?<p class="note"><a href="\.\./">← アプリ一覧</a></p>\n?', '\n', s)

    # 旧フッターを共通フッターへ
    s = re.sub(r'<footer>.*?</footer>', '', s, flags=re.S)
    s = re.sub(r'<footer class="sitefooter">.*?</footer>', '', s, flags=re.S)
    s = re.sub(r'<!-- ここから下は tools/apply_chrome\.py が入れ直す -->.*?<!-- ここまで -->',
               '', s, flags=re.S)
    # 目印を付ける前に入れたぶん（スクリプトが1つだけの形）
    s = re.sub(r'<script>\s*\(function \(\) \{\s*var menus.*?</script>', '', s, flags=re.S)
    s = s.replace('</body>', footer(lang) + '\n\n' + SCRIPT + '\n\n</body>')

    # スタイルシートの版を、生成のたびに現在の値へそろえる
    s = re.sub(r'(/assets/style\.css\?v=)[0-9a-z]+', r'\g<1>' + CSS_VERSION, s)

    # Google アナリティクスのタグを <head> の先頭（charset の直後）へ。
    # 既存の分は消してから入れ直すので、IDを変えても二重に積まれない。
    # 2つの <script> にまたがる。コメント付きの組と、はぐれた分の
    # どちらも消えるまで繰り返す（壊れた状態からでも収束するように）
    while True:
        s2 = re.sub(
            r'<!-- Google tag \(gtag\.js\) -->\s*'
            r'<script[^>]*></script>\s*'
            r'<script>.*?</script>\n*',
            '', s, flags=re.S)
        s2 = re.sub(
            r'<script>\s*window\.dataLayer.*?gtag\(\'config\'.*?</script>\n*',
            '', s2, flags=re.S)
        if s2 == s:
            break
        s = s2
    s = s.replace('<meta charset="utf-8">',
                  '<meta charset="utf-8">\n' + GA_SNIPPET, 1)

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


def en_pages():
    """英語ページの定義。アプリごとに説明とプライバシーポリシー、冷凍図鑑は利用規約も。"""
    pages = {'en/index.html': ('/en/', 'home', [], 'en')}
    for href, name, _ in APPS_EN:
        if href.startswith('/nukadoko-diary/'):
            continue  # 別リポジトリ。NUKADOKO_PAGES で扱う
        rel = href.lstrip('/') + 'index.html'
        pages[rel] = (href, 'apps', [(None, name)], 'en')
        pol = href + 'privacy.html'
        pages[pol.lstrip('/')] = (pol, 'support', [(href, name), (None, 'Privacy Policy')], 'en')
    pages['reitou/en/terms.html'] = ('/reitou/en/terms.html', 'support',
        [('/reitou/en/', 'Reitou Zukan'), (None, 'Terms of Use')], 'en')
    return pages


PAGES.update(en_pages())

# 別リポジトリ（/nukadoko-diary/）のページ。NUKADOKO_ROOT からの相対パス
NUKADOKO_PAGES = {
    'index.html': ('/nukadoko-diary/', 'apps', [(None, 'ぬか床日記')], 'ja'),
    'privacy.html': ('/nukadoko-diary/privacy.html', 'support',
        [('/nukadoko-diary/', 'ぬか床日記'), (None, 'プライバシーポリシー')], 'ja'),
    'en/index.html': ('/nukadoko-diary/en/', 'apps', [(None, 'Nuka Diary')], 'en'),
    'en/privacy.html': ('/nukadoko-diary/en/privacy.html', 'support',
        [('/nukadoko-diary/en/', 'Nuka Diary'), (None, 'Privacy Policy')], 'en'),
}


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
    for rel, entry in PAGES.items():
        page, section, trail = entry[0], entry[1], entry[2]
        lang = entry[3] if len(entry) > 3 else 'ja'
        trail = guide_trail(page) or trail
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f'  skip (未作成): {rel}')
            continue
        if apply(rel, page, section, trail, lang):
            n += 1
            print(f'  ✓ {rel}')
    # 別リポジトリのぬか床日記。--nukadoko を付けたときだけ書き換える
    if '--nukadoko' in sys.argv:
        for rel, (page, section, trail, lang) in NUKADOKO_PAGES.items():
            if not os.path.exists(os.path.join(NUKADOKO_ROOT, rel)):
                print(f'  skip (未作成): nukadoko-diary/{rel}')
                continue
            if apply(rel, page, section, trail, lang, root=NUKADOKO_ROOT):
                n += 1
                print(f'  ✓ nukadoko-diary/{rel}')
    print(f'\n{n} ページ更新')
