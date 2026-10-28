# -*- coding: utf-8 -*-
# v6: панель района — клик по округу → РЕАЛЬНЫЕ фото места (Wikimedia Commons, парсинг в браузере).
# Сгенерированные mo/*.jpg из карточек округов убраны: они не являются фото этих мест.
import os, io, json, re
import json as j

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, 'v4', 'index.html')
def mo_by_d_json():
    mo = j.load(io.open(os.path.join(BASE, 'data', 'mo.json'), encoding='utf-8'))
    by_d = {}
    for it in mo:
        by_d.setdefault(it['district'], []).append({'n': it['name'], 'd': it['density'], 'dist': it['district']})
    return by_d

BASE2 = BASE
h = io.open(P, encoding='utf-8').read()

old_js = h[h.find('<div id="dp-hint">'):h.find('</div>\n</script>') + len('</div>\n</script>')]
# заменить весь UI-JS панели: клик по округу → Commons
start = h.find('<script>\n(function(){\n  var DATA =')
end = h.find('</script>', start) + len('</script>')
new_js = '''<script>
(function(){
  var DATA = __DATA__;
  var panel = document.getElementById('dpanel');
  function openDistrict(d){
    var mos = DATA[d];
    if (!mos) return;
    document.getElementById('dp-name').textContent = d + ' район';
    document.getElementById('dp-sub').textContent = mos.length + ' внутригородских округов · население: Росстат 01.01.2025';
    var dens = Math.max.apply(null, mos.map(function(m){ return m.d; }));
    document.getElementById('dp-dens').innerHTML = dens.toLocaleString('ru-RU') + '<small>чел/км² — самый плотный округ района</small>';
    var q = 'вспомни вечер в этом районе: какое окно горело, когда ты возвращался? что в нём было только твоим?';
    document.getElementById('dp-q').textContent = q;
    var box = document.getElementById('dp-mos');
    box.innerHTML = '';
    mos.forEach(function(m){
      var el = document.createElement('div');
      el.className = 'mol';
      el.innerHTML = '<span class="n">' + m.n + '</span><span class="d">' + m.d.toLocaleString('ru-RU') + ' чел/км²</span>'
        + '<div class="moexp" style="display:none"></div>';
      var open = false;
      el.addEventListener('click', function(){
        open = !open;
        var exp = el.querySelector('.moexp');
        if (!open){ exp.style.display = 'none'; return; }
        exp.style.display = 'block';
        var imgBox = exp.querySelector('.imgbox');
        imgBox.innerHTML = '<span style="color:#9c8bbd;font-size:13px">ищу настоящие фото этого места в свободном архиве…</span>';
        loadCommons(m.n, imgBox);
      });
      box.appendChild(el);
    });
    panel.classList.add('on');
    if (navigator.vibrate) navigator.vibrate(12);
  }
  window.openDistrict = openDistrict;
  var cache = {};
  function loadCommons(name, box){
    var key = name;
    if (cache[key]) { render(cache[key], box); return; }
    var q;
    if (/^N\\b|N \\d/.test(name) && DATA[name]) {
      q = 'Санкт-Петербург ' + DATA[name].dist + ' район';
    } else {
      q = name.replace(/^Муниципальный округ\\s*/i, '').replace(/^(г|п)\\s+/i, '').trim() + ' Санкт-Петербург';
    }
    var api = 'https://commons.wikimedia.org/w/api.php?action=query&format=json&origin=*'
      + '&generator=search&gsrnamespace=6&gsrlimit=8&prop=imageinfo&iiprop=url&iiurlwidth=900'
      + '&gsrsearch=' + encodeURIComponent(q);
    fetch(api)
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
        render(imgs, box);
      })
      .catch(function(){ render([], box); });
  }
  function render(imgs, box){
    var imgBox = box.querySelector('.imgbox');
    imgBox.innerHTML = '';
    if (!imgs.length){
      imgBox.innerHTML = '<span style="color:#9c8bbd;font-size:13px;display:block;padding:10px 0">'
        + 'свободных фото этого места в архиве не нашлось — остаётся цифра и твой вечер</span>';
      return;
    }
    imgs.slice(0, 2).forEach(function(im2, k){
      var im = document.createElement('img');
      im.src = im2.url; im.alt = im2.cap; im.loading = 'lazy';
      im.style.width = '100%'; im.style.maxHeight = k === 0 ? '240px' : '150px';
      im.style.objectFit = 'cover'; im.style.borderRadius = '3px'; im.style.marginBottom = '6px';
      imgBox.appendChild(im);
    });
    var cap = document.createElement('div');
    cap.style.cssText = 'font-size:11px;color:#8d7ab0;padding:2px 0 6px';
    cap.textContent = imgs[0].cap;
    imgBox.appendChild(cap);
  }
  function close(){ panel.classList.remove('on'); }
  document.getElementById('dp-close').addEventListener('click', close);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') close(); });

  // клик по району на SVG-карте → панель
  function bindMap(){
    document.querySelectorAll('#shapes .dist').forEach(function(p){
      if (p.dataset.bound) return;
      p.dataset.bound = '1';
      p.addEventListener('click', function(){
        var short = p.dataset.name;
        var d = null;
        Object.keys(DATA).forEach(function(k){ if (k.indexOf(short) === 0) d = k; });
        if (d) openDistrict(d);
      });
    });
  }
  if (document.readyState === 'complete') bindMap();
  else window.addEventListener('load', bindMap);
  setTimeout(bindMap, 800);
})();
</script>'''
new_js = new_js.replace('__DATA__', json.dumps(mo_by_d_json(), ensure_ascii=False))

h = h[:start] + new_js + h[end:]

io.open(P, 'w', encoding='utf-8').write(h)
print('v6: панель округа → реальные фото Wikimedia (парсинг в браузере), сгенеративные фото из карточек убраны')
print('размер:', os.path.getsize(P), 'байт')


def mo_by_d_json():
    import json as j
    mo = j.load(io.open(os.path.join(BASE, 'data', 'mo.json'), encoding='utf-8'))
    by_d = {}
    for it in mo:
        by_d.setdefault(it['district'], []).append({'n': it['name'], 'd': it['density']})
    return by_d
