# -*- coding: utf-8 -*-
# Генерация снимков улиц по всем МО: pollinations, лимит 1/45 сек, ретраи.
import json, io, os, time, urllib.request, random, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'scenes_mo')
os.makedirs(OUT, exist_ok=True)
LOG = io.open(os.path.join(OUT, 'gen.log'), 'a', encoding='utf-8')

def log(s):
    LOG.write(s + '\n'); LOG.flush(); print(s, flush=True)

items = json.load(io.open(os.path.join(BASE, 'data', 'mo.json'), encoding='utf-8'))

CENTER = {'Центральный', 'Петроградский', 'Адмиралтейский', 'Василеостровский'}
SUBURB = {'Курортный', 'Пушкинский', 'Колпинский', 'Кронштадтский', 'Петродворцовый'}

def kind(district):
    if district in CENTER: return 'center'
    if district in SUBURB: return 'suburb'
    return 'sleep'

PROMPTS = {
 'center': 'old saint petersburg residential quarter at dusk, courtyard well between low baroque facades, wet granite, single warm window, mist, cinematic film still, film grain, photorealistic, no text',
 'sleep':  'soviет panel apartment blocks at dusk in saint petersburg, long courtyard, wet asphalt, warm lit windows, november slush, cinematic film still, film grain, photorealistic, no text',
 'suburb': 'outskirts of saint petersburg at dusk, low-rise houses, pine trees, thin fog over a canal, one street lamp, cinematic film still, film grain, photorealistic, no text'
}
PROMPTS['sleep'] = PROMPTS['sleep'].replace('soviет', 'soviet')

def fetch(prompt, dest):
    url = 'https://image.pollinations.ai/prompt/' + urllib.parse.quote(prompt) + \
          '?width=768&height=1024&nologo=true&seed=' + str(random.randint(1, 999999))
    for attempt in range(1, 7):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if r.status == 200 and len(data) > 20000:
                io.open(dest, 'wb').write(data)
                return len(data)
            log('  плохой ответ %s (%s байт), повтор' % (r.status, len(data)))
        except Exception as e:
            log('  ошибка: %s' % str(e)[:80])
        time.sleep(55)
    return None

manifest = {}
if os.path.exists(os.path.join(OUT, 'manifest.json')):
    manifest = json.load(io.open(os.path.join(OUT, 'manifest.json'), encoding='utf-8'))

idx = 0
for it in items:
    idx += 1
    slug = 'mo_%03d' % idx
    if slug in manifest and os.path.exists(os.path.join(OUT, slug + '.jpg')):
        log('%s %s: уже есть' % (slug, it['name'])); continue
    k = kind(it.get('district', ''))
    nm = it.get('name', '')
    itype = it.get('type') or ('город' if nm.startswith('г ') else ('посёлок' if nm.startswith('п ') else 'муниципальный округ'))
    p = PROMPTS[k]
    sz = fetch(p, os.path.join(OUT, slug + '.jpg'))
    if sz:
        manifest[slug] = {'name': it['name'], 'district': it['district'], 'type': itype,
                          'kind': k, 'density': it['density'], 'pop_2025': it['pop_2025']}
        json.dump(manifest, io.open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        log('%s %s: ok (%s)' % (slug, it['name'], sz))
    else:
        log('%s %s: ПРОВАЛ' % (slug, it['name']))
    time.sleep(48)

log('ВСЁ ГОТОВО: %d снимков' % len(manifest))
