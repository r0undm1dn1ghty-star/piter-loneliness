# -*- coding: utf-8 -*-
# v4: БЕЗ генеративных фото. Атмосфера — фото Виктора (референс). Секция МО — типографика + вопрос.
import os, re, json, io, shutil, html

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, 'v2', 'index.html')
OUTDIR = os.path.join(BASE, 'v4')
os.makedirs(OUTDIR, exist_ok=True)

h = io.open(SRC, encoding='utf-8').read()

# 1. палитра blue~purple
PAIRS = [
    ('#170b1e', '#1a0b2e'),
    ('#2a1030', '#2e1a47'),
    ('#1f0f29', '#241536'),
    ('#a33f74', '#b57edc'),
    ('#f3d9e8', '#d9c7ef'),
    ('#e85da8', '#c77dff'),
]
for a, b in PAIRS:
    h = h.replace(a, b).replace(a.upper(), b)

# 2. фон-атмосфера: собственное фото Виктора (референс) как фиксированный слой под всем
h = h.replace('</head>',
    '<style>'
    '.victorfoto{position:fixed;inset:0;z-index:0;pointer-events:none;'
    'background:url("depression.jpg") center/cover no-repeat;opacity:.14;filter:blur(2px) saturate(.8)}'
    '.victorfoto::after{content:"";position:absolute;inset:0;'
    'background:linear-gradient(180deg,rgba(26,11,46,.86),rgba(26,11,46,.94))}'
    'body>*:not(.victorfoto){position:relative;z-index:1}'
    '</style>\n</head>')
h = h.replace('<body>', '<body><div class="victorfoto"></div>')

# 3. hero: убираем антитезу, оставляем голос + источники
h = h.replace(
    '<p>столько домохозяйств петербурга состоит из одного человека. не метафора, не ощущение — перепись.</p>',
    '<p>я проверил цифры: 49% домохозяйств Петербурга — из одного человека. '
    'в 2002-м таких была примерно четверть. город вырос до рекорда — '
    'но рост остановлен минимум до 2036 года, и про одиночество официальные цифры молчат. '
    'поэтому я считаю сам — по переписи и по муниципальным округам.</p>')
h = h.replace('источник: росстат, всероссийская перепись населения; петростат. москва — 52%, санкт-петербург — 49%. в начале 2000-х было около четверти.',
              'источник: росстат, перепись 2021; петростат на 01.01.2025. москва — 52%, санкт-петербург — 49%. в 2002-м — около четверти.')

# 4. честность v2 (с оговоркой РБК + про фото больше нет)
old_h = re.search(r'<div class="honest">[\s\S]*?</div>', h)
if old_h:
    new_h = ('<div class="honest"><b>что здесь честно, а что — модель.</b> '
             '49% и состав домохозяйств — перепись 2021. численность округов — Росстат на 01.01.2025. '
             'плотность — расчёт по площадям из открытых источников. '
             'районной статистики одиночества не существует: карта показывает условия, '
             'в которых одному живётся теснее или просторнее. '
             'РБК отдельно писал, что перепись могла завысить долю одиночек процедурой — '
             'я оставляю цифру с этой оговоркой. фон — моя фотография, не сток.</div>')
    h = h.replace(old_h.group(0), new_h)

# 5. секция МО: типографика + личный вопрос, БЕЗ фото
mo = json.load(io.open(os.path.join(BASE, 'data', 'mo.json'), encoding='utf-8'))

def fmt(n): return format(n, ',').replace(',', ' ')

by_district = {}
for it in mo:
    by_district.setdefault(it['district'], []).append(it)

rows = []
for d in sorted(by_district):
    mos = sorted(by_district[d], key=lambda x: -x['density'])
    lines = []
    for m_ in mos:
        lines.append(
            '<div class="mol"><span class="mo">%s</span><span class="den">%s чел/км²</span></div>'
            % (html.escape(m_['name']), fmt(m_['density'])))
    rows.append('<div class="rrow" data-d="%s"><button class="rcap"><span class="rn">%s</span>'
                '<span class="rm">%d округа · от %s до %s чел/км²</span><span class="chev">▸</span></button>'
                '<div class="rbody"><p class="rq">вспомни вечер в этом районе: какое окно горело, '
                'когда ты возвращался?</p>%s</div></div>'
                % (html.escape(d), html.escape(d), len(mos), fmt(mos[-1]['density']), fmt(mos[0]['density']),
                   '\n'.join(lines)))

mos_sec = ('<section class="mossec"><div class="maphead"><h2>одиночество измеряется не районом — округом</h2>'
           '<span>111 внутригородских округов · население: Росстат 01.01.2025 · кликни район — свои округа</span></div>'
           '%s</section>\n  ' % '\n'.join(rows))

anchor = h.find('<section class="cubesect">')
h = h[:anchor] + mos_sec + h[anchor:]

# 6. кубик 3D вместо барабана (сцены текстом, без фото)
c_start = h.find('<section class="cubesect">')
c_end = h.find('</section>', c_start) + len('</section>')
cube3d = io.open(os.path.join(BASE, 'design', 'cube3d.html'), encoding='utf-8').read()
m_body = re.search(r'<body>([\s\S]*?)</body>', cube3d)
m_css = re.search(r'<style>([\s\S]*?)</style>', cube3d)
m_js = re.search(r'<script>([\s\S]*?)</script>', cube3d)

new_cube = ('<section class="cubesect">'
            '<div class="maphead"><h2>брось кубик — вспомни вечер</h2>'
            '<span>6 питерских сцен · одна выпадет · вопрос на подумать</span></div>'
            + m_body.group(1).replace('background:#111', '') + '</section>')

h = h[:c_start] + new_cube + h[c_end:]
h = h.replace('</style>', m_css.group(1) + '\n</style>', 1)
h = h.replace('</body>', m_js.group(1) + '\n</body>', 1)

io.open(os.path.join(OUTDIR, 'index.html'), 'w', encoding='utf-8').write(h)
print('v4 собран:', os.path.getsize(os.path.join(OUTDIR, 'index.html')), 'байт')
print('генеративных фото: 0 | victorfoto (референс):', h.count('victorfoto'))
print('кубик 3D:', h.count('scene3d') > 0, '| секция МО:', h.count('mossec') > 0)
