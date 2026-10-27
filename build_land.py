# -*- coding: utf-8 -*-
# Сборка лендинга v3 «петербургское одиночество»: палитра blue~purple, секция МО с фото, кубик 3D, честность v2
import os, re, json, io, shutil, html

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, 'v2', 'index.html')
OUTDIR = os.path.join(BASE, 'v3')
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(os.path.join(OUTDIR, 'mo'), exist_ok=True)

# 1. фото → v3/mo/
n_img = 0
for f in os.listdir(os.path.join(BASE, 'scenes_mo_final')):
    shutil.copy(os.path.join(BASE, 'scenes_mo_final', f), os.path.join(OUTDIR, 'mo', f))
    n_img += 1
print('фото скопировано:', n_img)

# манифест: slug → {name, district, density}
mf = json.load(io.open(os.path.join(BASE, 'scenes_mo', 'manifest.json'), encoding='utf-8'))
slug_by_name = {}
for slug, m in mf.items():
    slug_by_name.setdefault(m['name'], slug)

h = io.open(SRC, encoding='utf-8').read()

# 2. палитра: розово-фиолетовый → сине-фиолетовый blue~purple, розовый акцент — светлее и реже
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

# 3. hero-текст v2 (голос Виктора, источники+даты)
old_lead = '<p>столько домохозяйств петербурга состоит из одного человека. не метафора, не ощущение — перепись.</p>'
new_lead = ('<p>я проверил цифры: 49% домохозяйств Петербурга — из одного человека. '
            'в 2002-м таких была примерно четверть. город вырос до рекорда — '
            'но рост остановлен минимум до 2036 года, и про одиночество официальные цифры молчат. '
            'поэтому я считаю сам — по переписи и по муниципальным округам.</p>')
h = h.replace(old_lead, new_lead)

h = h.replace('источник: росстат, всероссийская перепись населения; петростат. москва — 52%, санкт-петербург — 49%. в начале 2000-х было около четверти.',
              'источник: росстат, перепись 2021; петростат на 01.01.2025. москва — 52%, санкт-петербург — 49%. в 2002-м — около четверти.')

# 4. честность v2
old_h = re.search(r'<div class="honest">[\s\S]*?</div>', h)
if old_h:
    new_h = ('<div class="honest"><b>что здесь честно, а что — модель.</b> '
             '49% и состав домохозяйств — перепись 2021. численность округов — Росстат на 01.01.2025. '
             'плотность — расчёт по площадям из открытых источников. '
             'районной статистики одиночества не существует: карта показывает условия, '
             'в которых одному живётся теснее или просторнее. '
             'РБК отдельно писал, что перепись могла завысить долю одиночек процедурой — '
             'я оставляю цифру с этой оговоркой. '
             'фото округов — атмосферные снимки по характеру застройки, не документальные.</div>')
    h = h.replace(old_h.group(0), new_h)

# 5. секция МО с фото: аккордеон по районам (перед кубиком)
mo = json.load(io.open(os.path.join(BASE, 'data', 'mo.json'), encoding='utf-8'))
slug_by_name = {}
mf = json.load(io.open(os.path.join(BASE, 'scenes_mo', 'manifest.json'), encoding='utf-8'))
for slug, m in mf.items():
    slug_by_name.setdefault(m['name'], slug)

def fmt(n): return format(n, ',').replace(',', ' ')

by_district = {}
for it in mo:
    by_district.setdefault(it['district'], []).append(it)

rows = []
for d in sorted(by_district):
    mos = sorted(by_district[d], key=lambda x: -x['density'])
    lines = []
    for m_ in mos:
        slug = slug_by_name.get(m_['name'])
        img = ('<img loading="lazy" src="mo/%s.jpg" alt="">' % slug) if slug else ''
        lines.append(
            '<div class="mol" data-name="%s"><div class="molhead"><span class="mo">%s</span>'
            '<span class="den">%s чел/км²</span><span class="chev">▸</span></div>'
            '<div class="molbody">%s<p class="moq">вспомни вечер в этом округе: какое окно горело, '
            'когда ты возвращался?</p></div></div>'
            % (html.escape(m_['name']), html.escape(m_['name']), fmt(m_['density']), img))
    rows.append('<div class="rrow" data-d="%s"><button class="rcap"><span class="rn">%s</span>'
                '<span class="rm">%d округа · от %s до %s чел/км²</span><span class="chev">▸</span></button>'
                '<div class="rbody">%s</div></div>'
                % (html.escape(d), html.escape(d), len(mos), fmt(mos[-1]['density']), fmt(mos[0]['density']),
                   '\n'.join(lines)))

mos_sec = ('<section class="mossec"><div class="maphead"><h2>одиночество измеряется не районом — округом</h2>'
           '<span>111 внутригородских округов · население: Росстат 01.01.2025 · кликни округ — фото и цифра</span></div>'
           '%s</section>\n  ' % '\n'.join(rows))

# вставить секцию МО перед кубиком
anchor = h.find('<section class="cubesect">')
h = h[:anchor] + mos_sec + h[anchor:]

# 6. кубик 3D: заменить старую секцию барабана на новый куб
c_start = h.find('<section class="cubesect">')
c_end = h.find('</section>', c_start) + len('</section>')
cube3d = io.open(os.path.join(BASE, 'design', 'cube3d.html'), encoding='utf-8').read()
m_body = re.search(r'<body>([\s\S]*?)</body>', cube3d)
m_css = re.search(r'<style>([\s\S]*?)</style>', cube3d)
m_js = re.search(r'<script>([\s\S]*?)</script>', cube3d)

new_cube = ('<section class="cubesect">'
            '<div class="maphead"><h2>брось кубик — вспомни вечер</h2>'
            '<span>6 питерских сцен · одна выпадет · привяжи к своему округу</span></div>'
            + m_body.group(1).replace('background:#111', '') + '</section>')

h = h[:c_start] + new_cube + h[c_end:]
h = h.replace('</style>', m_css.group(1) + '\n</style>', 1)
h = h.replace('</body>', m_js.group(1) + '\n</body>', 1)

io.open(os.path.join(OUTDIR, 'index.html'), 'w', encoding='utf-8').write(h)
print('собран v3/index.html:', os.path.getsize(os.path.join(OUTDIR, 'index.html')), 'байт')
print('фото mo/:', len(os.listdir(os.path.join(OUTDIR, 'mo'))))
