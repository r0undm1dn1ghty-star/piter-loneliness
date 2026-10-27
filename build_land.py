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
        slug = slug_by_name.get(m_['name'], '')
        nm = html.escape(m_['name']).replace('округ округ', 'округ').replace('N ', '№ ')
        lines.append('<div class="mol" data-slug="%s" data-name="%s" data-den="%s чел/км²">'
                     '<span class="mo">%s</span><span class="den">%s чел/км²</span></div>'
                     % (slug, nm, fmt(m_['density']), nm, fmt(m_['density'])))
    rows.append('<div class="rrow" data-d="%s"><button class="rcap"><span class="rn">%s</span>'
                '<span class="rm">%d округа · от %s до %s чел/км²</span><span class="chev">▸</span></button>'
                '<div class="rbody">%s</div></div>'
                % (html.escape(d), html.escape(d), len(mos), fmt(mos[-1]['density']), fmt(mos[0]['density']),
                   '\n'.join(lines)))

slugs_json = json.dumps({k: v for k, v in slug_by_name.items()}, ensure_ascii=False)

mos_sec = ('<section class="mossec"><div class="maphead"><h2>одиночество измеряется не районом — округом</h2>'
           '<span>111 округов · население: Росстат 01.01.2025 · клик по округу — фото и цифра</span></div>'
           '%s</section>\n  ' % '\n'.join(rows))

# оверлей фото округа: клик по строке → фото + цифра + вопрос
moCSS = '''<style>
  #moover{position:fixed;inset:0;z-index:70;display:none;align-items:center;justify-content:center;
    background:rgba(10,5,20,.88);backdrop-filter:blur(8px);padding:4vh 4vw}
  #moover.on{display:flex}
  .mobox{max-width:640px;width:100%;background:#160a26;border:1px solid rgba(181,126,220,.32);
    border-radius:6px;overflow:hidden;max-height:92vh;overflow-y:auto}
  .mobox img{width:100%;max-height:400px;object-fit:cover;display:block}
  .moinfo{padding:22px 24px 26px}
  #moname{font-size:26px;font-weight:600;color:#efe9f6}
  #moden{color:var(--lav,#b57edc);font-size:16px;margin:6px 0 14px}
  #moq{font-family:Georgia,serif;font-style:italic;font-size:17px;color:#cfc2e2;line-height:1.55;margin:0 0 16px}
  #moclose{background:none;border:1px solid rgba(181,126,220,.4);color:#cfc2e2;font:inherit;
    font-size:13px;padding:8px 16px;border-radius:2px;cursor:pointer}
</style>'''
moJS = '''<script>
(function(){
  var slugs = __SLUGS__;
  var ov = document.createElement('div');
  ov.id = 'moover';
  ov.innerHTML = '<div class="mobox"><img id="moimg" alt=""><div class="moinfo">'
    + '<div id="moname"></div><div id="moden"></div>'
    + '<p id="moq">вспомни вечер в этом округе: какое окно горело, когда ты возвращался? '
    + 'что в нём было только твоим?</p>'
    + '<button id="moclose">закрыть</button></div></div>';
  document.body.appendChild(ov);
  document.querySelectorAll('.mol').forEach(function(el){
    el.style.cursor = 'pointer';
    el.addEventListener('click', function(){
      var slug = el.dataset.slug || '';
      var img = document.getElementById('moimg');
      if (slug){ img.src = 'mo/' + slug + '.jpg'; img.style.display = 'block'; }
      else { img.style.display = 'none'; }
      document.getElementById('moname').textContent = el.dataset.name;
      document.getElementById('moden').textContent = el.dataset.den;
      ov.classList.add('on');
    });
  });
  document.getElementById('moclose').addEventListener('click', function(){ ov.classList.remove('on'); });
  ov.addEventListener('click', function(e){ if (e.target === ov) ov.classList.remove('on'); });
})();
</script>'''
h = h.replace('</head>', moCSS + '\n</head>', 1)
h = h.replace('</body>', moJS.replace('__SLUGS__', slugs_json) + '\n</body>', 1)

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

body_clean = re.sub(r'<div class="cap">[\s\S]*?<div class="scene3d">', '<div class="scene3d">', m_body.group(1))
body_clean = body_clean.replace('background:#111', '')
new_cube = ('<section class="cubesect">'
            '<div class="maphead"><h2>брось кубик — вспомни вечер</h2>'
            '<span>6 питерских сцен · одна выпадет · вопрос на подумать</span></div>'
            + body_clean + '</section>')

h = h[:c_start] + new_cube + h[c_end:]
h = h.replace('</style>', m_css.group(1) + '\n</style>', 1)
h = h.replace('</body>', '<script>' + m_js.group(1) + '\n</script>\n</body>', 1)

io.open(os.path.join(OUTDIR, 'index.html'), 'w', encoding='utf-8').write(h)
print('собран v3/index.html:', os.path.getsize(os.path.join(OUTDIR, 'index.html')), 'байт')
print('фото mo/:', len(os.listdir(os.path.join(OUTDIR, 'mo'))))
