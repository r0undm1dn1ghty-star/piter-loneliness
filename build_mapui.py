# -*- coding: utf-8 -*-
# v5: карта = интерфейс. Клик район → панель района (округа+цифры+фото). Кубик выбирает район.
import os, re, json, io

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, 'v4', 'index.html')
h = io.open(P, encoding='utf-8').read()

# 2. удалить старую простыню-секцию mossec (если есть)
h = re.sub(r'<section class="mossec">[\s\S]*?</section>\s*', '', h)
mo = json.load(io.open(os.path.join(BASE, 'data', 'mo.json'), encoding='utf-8'))
mf = json.load(io.open(os.path.join(BASE, 'scenes_mo', 'manifest.json'), encoding='utf-8'))
slug_of = {}
for slug, m in mf.items():
    slug_of.setdefault(m['name'], slug)

by_d = {}
for it in mo:
    by_d.setdefault(it['district'], []).append(it)

data = {}
for d, mos in by_d.items():
    data[d] = []
    for m_ in sorted(mos, key=lambda x: -x['density']):
        data[d].append({'n': m_['name'], 'd': m_['density'], 's': slug_of.get(m_['name'], '')})

DATA_JS = json.dumps(data, ensure_ascii=False)

# 2. удалить старую простыню-секцию mossec (если есть)
h = re.sub(r'<section class="mossec">[\s\S]*?</section>\s*', '', h)

# 3. слой района: панель справа (fixed), вызывается кликом по path района или кубиком
ui_css = '''<style>
  #dpanel{position:fixed;top:0;right:0;bottom:0;width:min(440px,94vw);z-index:80;
    background:linear-gradient(180deg,#241536,#160a26);border-left:1px solid rgba(181,126,220,.3);
    transform:translateX(102%);transition:transform .45s cubic-bezier(.3,.8,.3,1);
    overflow-y:auto;padding:28px 24px 40px}
  #dpanel.on{transform:none}
  #dp-close{position:absolute;top:14px;right:14px;background:none;border:none;color:#9c8bbd;
    font-size:22px;cursor:pointer}
  #dp-name{font-size:30px;font-weight:600;color:#efe9f6;margin:6px 0 2px}
  #dp-sub{color:#9c8bbd;font-size:13px;margin-bottom:22px}
  #dp-dens{font-size:46px;font-weight:700;color:var(--lav,#b57edc);font-variant-numeric:tabular-nums}
  #dp-dens small{font-size:13px;font-weight:400;color:#9c8bbd;display:block;letter-spacing:.14em;margin-top:2px}
  #dp-q{font-family:Georgia,serif;font-style:italic;font-size:17px;color:#cfc2e2;line-height:1.55;margin:22px 0 26px}
  .dp-h{font-size:11px;letter-spacing:.2em;color:#9c8bbd;text-transform:uppercase;margin:22px 0 10px}
  .mol{display:flex;justify-content:space-between;gap:14px;padding:10px 2px;cursor:pointer;
    border-bottom:1px solid rgba(181,126,220,.14);transition:background .15s}
  .mol:hover{background:rgba(181,126,220,.08)}
  .mol .n{color:#efe9f6;font-size:14.5px}
  .mol .d{color:#b57edc;font-variant-numeric:tabular-nums;font-size:14px}
  .mol img{width:100%;max-height:220px;object-fit:cover;border-radius:3px;margin:10px 0;
    filter:saturate(.75) contrast(1.04);display:none}
  .mol.open img{display:block}
  .mol.open{padding-bottom:14px}
  .mol .q{display:none;font-family:Georgia,serif;font-style:italic;font-size:14.5px;
    color:#cfc2e2;line-height:1.5;margin:8px 0 0}
  .mol.open .q{display:block}
  #dp-hint{font-size:12px;color:#8d7ab0;margin-top:24px;line-height:1.6}
</style>'''
h = h.replace('</head>', ui_css + '\n</head>', 1)

# панель + JS: вставить в конец (после всего)
ui_js = '''<div id="dpanel">
  <button id="dp-close">×</button>
  <div class="dp-h">район</div>
  <div id="dp-name"></div>
  <div id="dp-sub"></div>
  <div id="dp-dens"><small>плотность населения</small></div>
  <p id="dp-q"></p>
  <div class="dp-h">округа района · клик — фото и вопрос</div>
  <div id="dp-mos"></div>
  <div id="dp-hint">кликни округ — откроется снимок и вопрос про вечер, который ты здесь провёл.</div>
</div>
<script>
(function(){
  var DATA = __DATA__;
  var panel = document.getElementById('dpanel');
  var openD = null;
  function openDistrict(d){
    var mos = DATA[d];
    if (!mos) return;
    openD = d;
    document.getElementById('dp-name').textContent = d + ' район';
    document.getElementById('dp-sub').textContent = mos.length + ' внутригородских округов · население: Росстат 01.01.2025';
    var dens = Math.max.apply(null, mos.map(function(m){ return m.d; }));
    document.getElementById('dp-dens').innerHTML = dens.toLocaleString('ru-RU') + '<small>чел/км² — самый плотный округ района</small>';
    var center = { 'Центральный': 44.4, 'Пушкинский': 39.3 };
    var q = 'вспомни вечер в этом районе: какое окно горело, когда ты возвращался? что в нём было только твоим?';
    document.getElementById('dp-q').textContent = q;
    var box = document.getElementById('dp-mos');
    box.innerHTML = '';
    mos.forEach(function(m){
      var el = document.createElement('div');
      el.className = 'mol';
      el.innerHTML = '<span class="n">' + m.n + '</span><span class="d">' + m.d.toLocaleString('ru-RU') + ' чел/км²</span>';
      var body = document.createElement('div');
      var slug = m.s;
      if (slug){
        var img = document.createElement('img');
        img.loading = 'lazy'; img.src = 'mo/' + slug + '.jpg'; img.alt = m.n;
        body.appendChild(img);
      }
      var qq = document.createElement('p');
      qq.className = 'q';
      qq.textContent = 'вспомни вечер в этом округе: какое окно горело, когда ты возвращался? что в нём было только твоим?';
      body.appendChild(qq);
      el.appendChild(body);
      el.addEventListener('click', function(){ el.classList.toggle('open'); });
      box.appendChild(el);
    });
    panel.classList.add('on');
    if (navigator.vibrate) navigator.vibrate(12);
  }
  window.openDistrict = openDistrict;
  function close(){ panel.classList.remove('on'); openD = null; }
  document.getElementById('dp-close').addEventListener('click', close);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') close(); });

  // клик по району на SVG-карте → панель
  document.querySelectorAll('#shapes .dist').forEach(function(p){
    p.addEventListener('click', function(){
      var short = p.dataset.name; // name_short
      var d = null;
      Object.keys(DATA).forEach(function(k){ if (k.indexOf(short) === 0) d = k; });
      if (d) openDistrict(d);
    });
  });
})();
</script>'''
ui_js = ui_js.replace('__DATA__', DATA_JS)
h = h.replace('</body>', ui_js + '\n</body>', 1)

# 4. подсказка на hero: карта интерактивна
h = h.replace('<div class="src">',
    '<div class="src" style="color:#b57edc;opacity:1">кликни район на карте ниже — откроются его округа, цифры и вопрос про твой вечер</div>\n    <div class="src">', 1)

# 5. кубик: связать с районами (бросок открывает панель района), переместить сразу после карты
cube_link = '''<script>
(function(){
  var btn = document.getElementById('roll');
  if (!btn) return;
  var btnText = btn.textContent;
  btn.textContent = 'бросить кубик — он выберет район →';
  var DISTS = Object.keys(window.openDistrict ? {} : {});
  var NAMES = ['Колпинский','Пушкинский','Московский','Красносельский','Петродворцовый','Кронштадтский','Курортный','Приморский','Невский','Фрунзенский','Центральный','Адмиралтейский','Петроградский','Василеостровский','Выборгский','Калининский','Красногвардейский'];
  btn.addEventListener('click', function(){
    var d = NAMES[Math.floor(Math.random() * NAMES.length)];
    setTimeout(function(){ if (window.openDistrict) window.openDistrict(d); }, 900);
  });
})();
</script>'''
# кубик-секция уже есть; добавить связку после неё (перед закрытием body не годится — панель должна существовать; вешаем на window load)
h = h.replace('</body>', cube_link + '\n</body>', 1)

out = os.path.join(BASE, 'v4', 'index.html')
io.open(out, 'w', encoding='utf-8').write(h)
print('v5 карта-интерфейс собрана:', os.path.getsize(out), 'байт')
print('панель района:', h.count('dpanel') > 0, '| простыня-аккордеон удалена:', 'mossec' not in h)
