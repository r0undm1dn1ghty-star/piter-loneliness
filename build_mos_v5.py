# -*- coding: utf-8 -*-
# v5: аккордеон-простыню → компактная навигация; фото округов — РЕАЛЬНЫЙ ПАРСИНГ Wikimedia Commons в браузере
import io, re, json, os, html

BASE = r"C:\Users\Victor\Desktop\hermes_work\питер-одиночество"
P = os.path.join(BASE, 'v4', 'index.html')
h = io.open(P, encoding='utf-8').read()

# 1. вырезать старую простыню mossec
m = re.search(r'<section class="mossec">[\s\S]*?</section>', h)
if not m:
    print('mossec не найдена'); raise SystemExit(1)
old = m.group(0)

# 2. вытащить данные районов из старой секции
districts = []
for rr in re.findall(r'<div class="rrow" data-d="([^"]+)">', old):
    if rr not in districts:
        districts.append(rr)
mos_by_d = {}
for rr_m in re.finditer(r'<div class="rrow" data-d="([^"]+)">([\s\S]*?)(?=<div class="rrow"|$)', old):
    d = rr_m.group(1)
    mos = []
    for mm in re.finditer(r'<span class="mo">([^<]+)</span><span class="den">([^<]+)</span>', rr_m.group(2)):
        mos.append({'name': mm.group(1), 'den': mm.group(2)})
    mos_by_d[d] = mos
print('районов:', len(districts), '| МО всего:', sum(len(v) for v in mos_by_d.values()))

# 3. новая компактная секция
DATA = json.dumps(mos_by_d, ensure_ascii=False)

sec = """<section class="mossec">
  <div class="maphead"><h2>одиночество измеряется не районом — округом</h2>
  <span>111 округов · население: Росстат 01.01.2025 · клик по округу — реальные фото места из свободного архива</span></div>
  <div class="dgrid" id="dgrid">__DBTN__</div>
  <div class="mopanel" id="mopanel" style="display:none">
    <div class="mop-head"><span id="mop-d"></span><button id="mop-back">← к районам</button></div>
    <div class="mop-list" id="mop-list"></div>
  </div>
  <div class="mocard" id="mocard" style="display:none">
    <button id="mc-back" class="mc-back">← назад</button>
    <div id="mc-img" class="mc-img"><span class="mc-load">ищу настоящие фото места…</span></div>
    <div class="mc-info">
      <div id="mc-name" class="mc-name"></div>
      <div id="mc-den" class="mc-den"></div>
      <p class="mc-q">вспомни вечер в этом округе: какое окно горело, когда ты возвращался? что в нём было только твоим?</p>
      <div class="mc-src">фото: Wikimedia Commons, свободные лицензии · парсинг в браузере</div>
    </div>
  </div>
</section>
<style>
.mossec{padding:11vh 6vw;background:linear-gradient(180deg,#160a26,var(--deep,#1a0b2e))}
.mossec .cap,.mossec .maphead{margin-bottom:4vh}
.mossec h2{font-size:clamp(26px,4.6vw,46px);margin:0 0 10px;color:#efe9f6;font-weight:600}
.mossec h2 em,.mossec .maphead span{color:#b57edc}
.mossec .maphead span{display:block;font-size:13px;margin-top:8px}
.dgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}
.dbtn{background:none;border:1px solid rgba(181,126,220,.24);color:#efe9f6;font:inherit;font-size:15px;
  padding:16px 14px;border-radius:3px;cursor:pointer;text-align:left;transition:border-color .2s,background .2s}
.dbtn:hover,.dbtn.on{border-color:#b57edc;background:rgba(181,126,220,.08)}
.dbtn small{display:block;color:#9c8bbd;font-size:12px;margin-top:4px}
.mopanel,.mocard{max-width:760px;margin:4vh auto 0;border:1px solid rgba(181,126,220,.24);border-radius:4px;
  background:rgba(20,10,36,.7);padding:20px 22px}
.mop-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px}
.mop-head span{font-size:20px;font-weight:600;color:#efe9f6}
#mop-back,.mc-back{background:none;border:none;color:#b57edc;font:inherit;font-size:13px;cursor:pointer;padding:0}
.moline{display:flex;justify-content:space-between;gap:16px;padding:11px 2px;cursor:pointer;
  border-bottom:1px solid rgba(181,126,220,.14);transition:background .15s}
.moline:hover{background:rgba(181,126,220,.07)}
.moline .n{color:#efe9f6}
.moline .d{color:#b57edc;font-variant-numeric:tabular-nums}
.mc-img{position:relative;height:380px;background:#160a26;margin-bottom:18px;overflow:hidden;border-radius:3px}
.mc-img img{width:100%;height:100%;object-fit:cover;filter:saturate(.75) contrast(1.04)}
.mc-load{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#9c8bbd;font-size:14px}
.mc-name{font-size:26px;font-weight:600;color:#efe9f6}
.mc-den{color:#b57edc;font-size:16px;margin:6px 0 14px}
.mc-q{font-family:Georgia,serif;font-style:italic;font-size:17px;line-height:1.55;color:#cfc2e2;margin:0 0 14px}
.mc-src{font-size:11.5px;color:#8d7ab0}
</style>
<script>
(function(){
  var DATA = __DATA__;
  var API = 'https://commons.wikimedia.org/w/api.php?action=query&format=json&origin=*' +
            '&generator=search&gsrnamespace=6&gsrlimit=8&prop=imageinfo&iiprop=url&iiurlwidth=900';
  var cache = {};
  var grid = document.getElementById('dgrid');
  var panel = document.getElementById('mopanel');
  var card = document.getElementById('mocard');
  var list = document.getElementById('mop-list');
  var curD = null;

  Object.keys(DATA).forEach(function(d){
    var b = document.createElement('button');
    b.className = 'dbtn';
    b.innerHTML = d + '<small>' + DATA[d].length + ' округа</small>';
    b.addEventListener('click', function(){ openDistrict(d, b); });
    grid.appendChild(b);
  });

  function openDistrict(d, btn){
    document.querySelectorAll('.dbtn').forEach(function(b){ b.classList.remove('on'); });
    if (btn) btn.classList.add('on');
    curD = d;
    document.getElementById('mop-d').textContent = d + ' район';
    list.innerHTML = '';
    DATA[d].forEach(function(mo){
      var el = document.createElement('div');
      el.className = 'moline';
      el.innerHTML = '<span class="n">' + mo.name + '</span><span class="d">' + mo.den + '</span>';
      el.addEventListener('click', function(){ openMo(mo, el); });
      list.appendChild(el);
    });
    panel.style.display = 'block';
    card.style.display = 'none';
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function openMo(mo, el){
    document.getElementById('mc-name').textContent = mo.name;
    document.getElementById('mc-den').textContent = mo.den + ' человек на квадратный километр';
    var imgBox = document.getElementById('mc-img');
    imgBox.innerHTML = '<span class="mc-load">ищу настоящие фото места…</span>';
    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    var key = mo.name;
    if (cache[key]) { render(cache[key]); return; }
    var q = key.replace(/^Муниципальный округ\\s*/i, '').replace(/^(г|п)\\s+/i, '').trim();
    fetch(API + '&gsrsearch=' + encodeURIComponent(q + ' Санкт-Петербург'))
      .then(function(r){ return r.json(); })
      .then(function(d){
        var pages = d && d.query && d.query.pages || {};
        var imgs = [];
        Object.keys(pages).forEach(function(pid){
          var inf = pages[pid].imageinfo && pages[pid].imageinfo[0];
          if (inf && inf.thumburl && !/\\.svg|\\.map|\\.pdf/i.test(inf.thumburl))
            imgs.push({ url: inf.thumburl, cap: pages[pid].title.replace(/^Файл:/, '') });
        });
        cache[key] = imgs;
        render(imgs);
      })
      .catch(function(){ render([]); });

    function render(imgs){
      imgBox.innerHTML = '';
      if (!imgs.length){
        imgBox.innerHTML = '<span class="mc-load" style="padding:40px;text-align:center;display:block">'
          + 'свободных фото этого округа в архиве не нашлось — цифра остаётся, фото добавим точечным парсингом</span>';
        return;
      }
      var first = imgs[0];
      var im = document.createElement('img');
      im.src = first.url; im.alt = first.cap; im.loading = 'lazy';
      im.onload = function(){ document.title = document.title; };
      imgBox.appendChild(im);
      if (imgs[1]) {
        var im2 = document.createElement('img');
        im2.src = imgs[1].url; im2.alt = imgs[1].cap; im2.loading = 'lazy';
        im2.style.marginTop = '4px'; im2.style.maxHeight = '160px';
        imgBox.appendChild(im2);
      }
      var cap = document.createElement('div');
      cap.className = 'mc-src'; cap.style.padding = '8px 12px';
      cap.textContent = first.cap;
      imgBox.appendChild(cap);
    }
  }
})();
</script>
"""
sec = sec.replace('__DBTN__', '\n'.join(
    '<button class="dbtn" data-d="%s">%s<small>%d округа</small></button>' % (d, d, len(mos_by_d[d]))
    for d in districts))
sec = sec.replace('__DATA__', DATA)

# 4. вставить новую секцию вместо старой
h = h.replace(old, sec)

# 5. убрать дубль заголовка кубика (cap/h2/sub внутри вставки кубика) — они уже в maphead
h = re.sub(r'<div class="cap">петербургское одиночество · механика</div>\s*<h2>брось кубик — вспомни вечер</h2>\s*<p class="sub">шесть питерских сцен\. одна выпадет — и вытянется воспоминание, которое ты давно не крутил\.</p>', '', h)

out = os.path.join(BASE, 'v4', 'index.html')
io.open(out, 'w', encoding='utf-8').write(h)
print('v5 собран:', os.path.getsize(out), 'байт')
print('старая простыня удалена, секция: 18 районов-кнопок → панель округа → карточка с реальными фото (Wikimedia)')
