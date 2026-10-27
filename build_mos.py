# -*- coding: utf-8 -*-
# Секция лендинга: 18 районов → их МО с плотностью. Фрагмент с инлайн-стилями для превью.
import json, io, os, html

BASE = os.path.dirname(os.path.abspath(__file__))
items = json.load(io.open(os.path.join(BASE, 'data', 'mo.json'), encoding='utf-8'))

by_district = {}
for it in items:
    by_district.setdefault(it['district'], []).append(it)

def fmt(n): return format(n, ',').replace(',', ' ')

ORDER = list(dict.fromkeys(['Центральный','Петроградский','Адмиралтейский','Василеостровский','Выборгский',
         'Калининский','Кировский','Красногвардейский','Красносельский','Московский',
         'Невский','Фрунзенский','Приморский','Колпинский',
         'Кронштадтский','Курортный','Пушкинский','Петродворцовый']))

rows = []
for d in ORDER:
    mos = by_district.get(d)
    if not mos: continue
    mos = sorted(mos, key=lambda x: -x['density'])
    top = mos[0]; low = mos[-1]
    rows.append('''
  <div class="rrow" data-d="%s">
    <button class="rcap"><span class="rname">%s район</span>
      <span class="rmeta">%d МО · от %s до %s чел/км²</span><span class="chev">▸</span></button>
    <div class="rbody">
      <div class="moline"><span class="mo-name">%s</span><span class="mo-den">%s чел/км²</span></div>
      %s
      <p class="rnote">самый просторный — <b>%s</b>: %s чел/км². разница внутри одного района — в %s раз.</p>
    </div>
  </div>''' % (
      html.escape(d), html.escape(d), len(mos), fmt(low['density']), fmt(top['density']),
      html.escape(top['name']), fmt(top['density']),
      '\n      '.join('<div class="moline"><span class="mo-name">%s</span><span class="mo-den">%s</span></div>'
                      % (html.escape(m['name']), fmt(m['density'])) for m in mos[1:]),
      html.escape(low['name']), fmt(low['density']),
      '%.1f' % (top['density'] / max(1, low['density']))
  ))

frag = '''<!-- секция: район → МО -->
<section class="mossec">
  <div class="cap">детализация · внутригородские округа</div>
  <h2>одиночество измеряется не районом — <em>округом</em></h2>
  <p class="sub">внутри одного района плотность гуляет в разы. раскрой свой район — найди свой округ и его цифру. 111 округов · население на 01.01.2025 · площади по Википедии</p>
  <div class="rlist">__ROWS__
  </div>
</section>
<style>
.mossec{background:linear-gradient(180deg,#160a26,var(--deep, #1a0b2e));padding:11vh 7vw}
.mossec .cap{font-size:11px;letter-spacing:.3em;color:var(--lav,#b57edc);text-transform:uppercase;margin-bottom:12px}
.mossec h2{font-size:clamp(26px,4.6vw,46px);margin:0 0 10px;font-weight:600;color:#efe9f6}
.mossec h2 em{font-style:normal;color:var(--lav,#b57edc)}
.mossec .sub{color:#9c8bbd;font-size:14.5px;line-height:1.6;max-width:62ch;margin:0 0 5vh}
.rlist{border-top:1px solid rgba(181,126,220,.18)}
.rrow{border-bottom:1px solid rgba(181,126,220,.18)}
.rcap{width:100%;display:flex;align-items:baseline;gap:16px;background:none;border:none;color:#efe9f6;
  font:inherit;font-size:17px;padding:20px 4px;cursor:pointer;text-align:left}
.rname{font-weight:600}
.rmeta{margin-left:auto;color:#9c8bbd;font-size:12.5px}
.chev{color:var(--lav,#b57edc);transition:transform .25s}
.rbody{display:none;padding:2px 4px 24px}
.rrow.open .rbody{display:block}
.rrow.open .chev{transform:rotate(90deg)}
.moline{display:flex;justify-content:space-between;gap:18px;padding:7px 0;border-bottom:1px dashed rgba(181,126,220,.14);font-size:14.5px}
.mo-name{color:#cfc2e2}
.mo-den{color:var(--lav,#b57edc);font-variant-numeric:tabular-nums}
.rnote{font-size:13px;color:#9c8bbd;margin:14px 0 0;line-height:1.6}
.rnote b{color:#efe9f6}
</style>
<script>
document.querySelectorAll('.rrow .rcap').forEach(function(c){
  c.addEventListener('click', function(){
    var row = c.parentNode, was = row.classList.contains('open');
    document.querySelectorAll('.rrow.open').forEach(function(r){ r.classList.remove('open'); });
    if (!was) row.classList.add('open');
  });
});
</script>
'''

frag = frag.replace('__ROWS__', '\n'.join(rows))

io.open(os.path.join(BASE, 'design', 'mos_section.html'), 'w', encoding='utf-8').write(frag)

# превью-страница
prev = '''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>превью секции МО</title>
<style>body{margin:0;background:var(--deep,#1a0b2e);--deep:#1a0b2e;--lav:#b57edc;font-family:-apple-system,'Segoe UI',Roboto,sans-serif}</style>
</head><body>%s</body></html>''' % frag
io.open(os.path.join(BASE, 'design', 'mos_preview.html'), 'w', encoding='utf-8').write(prev)
print('фрагмент собран: районов', len(ORDER) if rows else len(rows), '| МО в фрагменте:', sum(len(v) for v in by_district.values()))
