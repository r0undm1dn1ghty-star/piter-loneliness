import os

src = r"C:\Users\Victor\Documents\hermes_obsidian_memory\personal_kb\01_projects_and_moves\розовый взгляд - личный бренд\спецпроект-питер-одиночество\карта-одиночества.html"
html = open(src, encoding='utf-8').read()

cube_css = """
/* ---------- кубик одиночества ---------- */
.cubesect{padding:66px 0 30px;border-top:1px solid var(--line)}
.cubesect .maphead{margin-bottom:10px}
.cubesect .sub{font-size:13px;color:var(--mute);max-width:52ch;margin-bottom:24px}
.stage{position:relative;height:250px;max-width:520px;margin:0 auto 20px;perspective:900px;overflow:hidden;
  -webkit-mask-image:linear-gradient(to bottom,transparent,#000 30%,#000 70%,transparent);
  mask-image:linear-gradient(to bottom,transparent,#000 30%,#000 70%,transparent)}
.drum{position:absolute;left:50%;top:50%;width:0;height:0;transform-style:preserve-3d}
.facet{position:absolute;left:-160px;top:-34px;width:320px;height:68px;display:flex;align-items:center;
  justify-content:center;text-align:center;font-size:14.5px;line-height:1.35;color:var(--mute);
  background:var(--ink2);border:1px solid rgba(232,93,168,.14);backface-visibility:hidden;padding:0 14px;
  border-radius:2px}
.facet.on{color:#fff;border-color:var(--rose);background:#2a1030;box-shadow:0 0 28px rgba(232,93,168,.25)}
.gostamp{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);font-size:10px;letter-spacing:.16em;
  color:var(--mute);font-variant-numeric:tabular-nums;text-transform:uppercase}
.rollbtn{display:block;margin:0 auto;background:none;border:none;cursor:pointer;color:var(--cloud);
  font:inherit;font-size:16px;padding:12px 4px 10px;border-bottom:2px solid var(--rose);transition:.22s}
.rollbtn:hover{color:var(--rose)}
.rollbtn:disabled{opacity:.42;cursor:default}
.scene{max-width:600px;margin:26px auto 0;border:1px solid var(--line);border-radius:2px;
  padding:24px 24px 22px;background:rgba(255,255,255,.014);opacity:0;transform:translateY(10px);transition:.45s ease}
.scene.on{opacity:1;transform:none}
.scene .sc-no{font-size:10.5px;letter-spacing:.18em;color:var(--rose);margin-bottom:12px;font-weight:600}
.scene .q{font-family:Georgia,serif;font-style:italic;font-size:clamp(17px,2.4vw,22px);line-height:1.45;margin-bottom:16px}
.scene .where{font-size:13.5px;color:var(--mute);line-height:1.6}
.scene .where b{color:var(--cloud)}
"""

cube_html = """
  <section class="cubesect">
    <div class="maphead">
      <h2>а теперь — брось кубик</h2>
      <span>12 сцен одинокого вечера &middot; одна выпадет</span>
    </div>
    <p class="sub">кликни район на карте выше — и выпавшая сцена привяжется к нему. без выбора сцена просто выпадет.</p>
    <div class="stage" id="stage">
      <div class="drum" id="drum"></div>
      <div class="gostamp" id="stamp">готов к броску</div>
    </div>
    <button class="rollbtn" id="roll">бросить кубик &rarr;</button>
    <div class="scene" id="scene">
      <div class="sc-no" id="scNo"></div>
      <p class="q" id="scQ"></p>
      <p class="where" id="scW"></p>
    </div>
  </section>

"""

cube_js = """
<script>
(function(){
  "use strict";
  var S = [
    {s:"окно", q:"сидел у окна, а за стеклом шёл снег — и было слышно, как внизу гудит машина"},
    {s:"кухня", q:"чай в два ночи: свет только над столом, и тишина такая, что слышно холодильник"},
    {s:"телефон", q:"листал ленту и знал, что не напишет никто — и всё равно листал"},
    {s:"балкон", q:"выходил на балкон просто подышать, а город внизу жил без тебя"},
    {s:"лифт", q:"ехал в лифте один и не смотрел на себя в зеркало"},
    {s:"двор", q:"двор, где горел один фонарь, и твои шаги были единственным звуком"},
    {s:"дорога", q:"шёл домой, когда окна чужих домов уже погасли, а твоё ещё нет"},
    {s:"метро", q:"последний вагон — вы с отражением ехали вдвоём"},
    {s:"комната", q:"свет от экрана ложился на потолок, и ты не выключал его до утра"},
    {s:"крыша", q:"залез на крышу один, и небо было тёмно-красное от города"},
    {s:"ванная", q:"вода шумела громче мыслей, и ты стоял под ней дольше, чем нужно"},
    {s:"подъезд", q:"подъезд, где мигала лампочка, а ты не спешил подниматься"}
  ];
  var drum = document.getElementById('drum'), N = S.length, R = 150, ang = 0, rolling = false;
  var facets = [], idx = 0, selected = null;

  document.querySelectorAll('.dist').forEach(function(p){
    p.addEventListener('click', function(){
      selected = { name: p.dataset.name, dens: Number(p.dataset.dens),
                   pop: Number(p.dataset.pop), area: Number(p.dataset.area) };
      document.querySelectorAll('.dist').forEach(function(q){ q.classList.remove('on'); });
      p.classList.add('on');
      if (document.getElementById('scene').classList.contains('on')) showScene();
    });
  });

  for (var k = 0; k < N; k++){
    var f = document.createElement('div');
    f.className = 'facet';
    f.textContent = S[k].s;
    f.style.transform = 'rotateX(' + (-k * (360 / N)) + 'deg) translateZ(' + R + 'px)';
    drum.appendChild(f);
    facets.push(f);
  }
  function paint(){
    drum.style.transform = 'translateZ(-' + R + 'px) rotateX(' + ang + 'deg)';
    var step = 360 / N;
    idx = ((Math.round(-ang / step) % N) + N) % N;
    facets.forEach(function(f, i){ f.classList.toggle('on', i === idx); });
  }
  paint();

  document.getElementById('roll').addEventListener('click', function(){
    if (rolling) return;
    rolling = true;
    this.disabled = true;
    document.getElementById('stamp').textContent = 'крутится…';
    var target = Math.floor(Math.random() * N);
    var step = 360 / N;
    var spins = 3 + Math.floor(Math.random() * 2);
    ang = -(target * step) - spins * 360;
    drum.style.transition = 'transform 3s cubic-bezier(0.15, 0.85, 0.15, 1)';
    drum.style.transform = 'translateZ(-' + R + 'px) rotateX(' + ang + 'deg)';
    var self = this;
    setTimeout(function(){
      drum.style.transition = '';
      rolling = false; self.disabled = false;
      paint();
      document.getElementById('stamp').textContent = 'выпало: ' + S[idx].s;
      showScene();
      if (navigator.vibrate) navigator.vibrate(18);
    }, 3050);
  });

  function showScene(){
    var sc = S[idx];
    document.getElementById('scNo').textContent = 'СЦЕНА ' + ('0' + (idx + 1)).slice(-2) + ' · ' + sc.s.toUpperCase();
    document.getElementById('scQ').textContent = '«' + sc.q + '»';
    var w;
    if (selected){
      w = 'район: <b>' + selected.name + '</b> — ' + selected.pop.toLocaleString('ru-RU') + ' человек на ' +
          selected.area.toLocaleString('ru-RU') + ' км², плотность ' + selected.dens.toLocaleString('ru-RU') + ' чел/км². ' +
          (selected.dens > 8000 ? 'очень тесно — и всё равно можно быть одному.' : 'просторно — и всё равно можно быть одному.');
    } else {
      w = 'район не выбран — кликни на карту выше, и сцена привяжется к нему.';
    }
    document.getElementById('scW').innerHTML = w;
    document.getElementById('scene').classList.add('on');
  }
})();
</script>
"""

html = html.replace("</style>", cube_css + "</style>")
html = html.replace('  <section class="outro">', cube_html + '  <section class="outro">')
html = html.replace("</body>", cube_js + "\n</body>")

out = r"C:\Users\Victor\Desktop\hermes_work\питер-одиночество\v2\index.html"
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(html)
print("собрано:", os.path.exists(out), os.path.getsize(out), "байт")
