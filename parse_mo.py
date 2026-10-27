# -*- coding: utf-8 -*-
# Датасет МО Санкт-Петербурга: население 2025 (citypopulation) + площадь (Википедия) → плотность.
import json, re, io

def cells_of(tr):
    tds = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)
    out = []
    for t in tds:
        txt = re.sub(r'<[^>]+>', '', t)
        txt = txt.replace('&nbsp;', ' ').replace('&nbsp', '').strip()
        txt = re.sub(r'\s+', ' ', txt)
        out.append(txt)
    return out

def num(s):
    d = re.sub(r'[^\d]', '', s)
    return int(d) if d else None

DISTRICTS = ['Адмиралтейский','Василеостровский','Выборгский','Калининский','Кировский',
             'Колпинский','Красногвардейский','Красносельский','Кронштадтский','Курортный',
             'Московский','Невский','Петродворцовый','Петроградский','Приморский',
             'Пушкинский','Фрунзенский','Центральный']

def norm(s):
    s = s.lower().replace('ё', 'е')
    s = re.sub(r'[^\wа-я ]', ' ', s)
    for w in ['муниципальный', 'округ', 'поселок', 'посёлок', 'город', 'мо', 'n ']:
        s = s.replace(w, ' ')
    return re.sub(r'\s+', '', s)

# ---------- 1. население 2025 из citypopulation ----------
cp = io.open('data/cp.html', encoding='utf-8', errors='replace').read()
pop = {}
for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', cp, re.S):
    cs = cells_of(tr)
    if len(cs) < 7: continue
    native = cs[2].strip()
    if not native or not re.search(r'[а-яА-Я]', native): continue
    p = num(cs[6]) if re.match(r'^[\d\s,]+$', cs[6].strip()) else None
    if p and p > 200:
        pop[native] = p

# ---------- 2. площадь + район из Вики ----------
wiki = io.open('data/mo_wiki.html', encoding='utf-8', errors='replace').read()
wikis = []
for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', wiki, re.S):
    cs = cells_of(tr)
    if len(cs) < 4: continue
    idx_area = None
    for i, c in enumerate(cs):
        if re.match(r'^\d{1,3}(,\d{1,2})?$', c) and i > 2:
            idx_area = i; break
    if idx_area is None: continue
    area = float(cs[idx_area].replace(',', '.'))
    popw = None
    for c in cs[idx_area+1:idx_area+3]:
        if re.match(r'^[↗↘]?[\d\s]+$', c.strip()):
            popw = num(c); break
    district = None
    for c in cs:
        for d in DISTRICTS:
            if c.startswith(d) or d.startswith(c) and len(c) > 5:
                district = d
    if district is None:
        for c in cs:
            for d in DISTRICTS:
                if d.lower() in c.lower(): district = d
    if district is None: continue
    # название: первая ячейка с буквами после статусной
    name = None
    for i, c in enumerate(cs):
        if i >= idx_area: break
        if re.search(r'[а-яА-Я]', c) and not re.match(r'^\d{2}\.\d{2}', c) and c not in DISTRICTS \
           and 'мун' not in c.lower() and c.lower() not in ('город', 'посёлок', 'поселок') \
           and not re.match(r'^МО\b', c) and len(c) > 2 and i > 0:
            name = c; break
    if not name: continue
    wikis.append({'name': name.strip(), 'area_km2': area, 'pop_wiki': popw, 'district': district})

# ---------- 3. сопоставление: строгий точный матч, затем единственный contains-кандидат, затем перепись 2021 ----------
def find_pop(name, area_hint=None):
    key = norm(name)
    if key in pop: return pop[key], name, 'cp2025'
    cands = [k for k in pop if norm(k) == key]
    if len(cands) == 1: return pop[cands[0]], cands[0], 'cp2025'
    if len(key) >= 10:
        cands = [k for k in pop if len(norm(k)) >= 10 and (key in norm(k) or norm(k) in key)]
        if len(cands) == 1: return pop[cands[0]], cands[0], 'cp2025'
    return None, None, 'wiki2021'

items, misses, from_wiki = [], [], []
for w in wikis:
    p, matched, src = find_pop(w['name'])
    if p is None and w['pop_wiki']:
        p = w['pop_wiki']; src = 'wiki2021'
        from_wiki.append(w['name'])
    if p is None:
        misses.append(w['name']); continue
    items.append({
        'district': w['district'], 'name': w['name'], 'type': ('город' if 'город' in w['name'].lower() else ('посёлок' if 'посёлок' in w['name'].lower() or 'поселок' in w['name'].lower() else 'муниципальный округ')),
        'area_km2': w['area_km2'], 'pop_2025': p,
        'density': int(round(p / w['area_km2'])) if w['area_km2'] else None,
        'src': src
    })

items.sort(key=lambda x: -x['density'])
json.dump(items, io.open('data/mo.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

total = sum(x['pop_2025'] for x in items)
top = '\n'.join('%s (%s): %s чел/км2' % (x['name'], x['district'], format(x['density'], ',').replace(',', ' ')) for x in items[:5])
bot = '\n'.join('%s (%s): %s чел/км2' % (x['name'], x['district'], format(x['density'], ',').replace(',', ' ')) for x in items[-5:])
rep = 'записей: %d из 111\nнаселение сумма: %s (город 2025: 5 652 922)\nиз citypopulation 2025: %d | из переписи 2021 (фоллбэк): %d\nнепокрытые совсем (%d): %s\n\nТОП-5 плотных:\n%s\n\nТОП-5 просторных:\n%s\n' % (
    len(items), format(total, ',').replace(',', ' '),
    len(items) - len(from_wiki), len(from_wiki), len(misses), '; '.join(misses[:20]), top, bot)
io.open('data/МО-сводка.txt', 'w', encoding='utf-8').write(rep)
print(rep)
