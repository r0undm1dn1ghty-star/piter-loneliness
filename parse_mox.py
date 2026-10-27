# -*- coding: utf-8 -*-
# v3: официальный xlsx Росстата (население МО на 01.01.2025) + площади из Википедии → data/mo.json
import zipfile, json, re, io, os
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
DISTRICTS = ['Адмиралтейский','Василеостровский','Выборгский','Калининский','Кировский',
             'Колпинский','Красногвардейский','Красносельский','Кронштадтский','Курортный',
             'Московский','Невский','Петродворцовый','Петроградский','Приморский',
             'Пушкинский','Фрунзенский','Центральный']

def cells_of(tr):
    tds = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)
    return [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t).replace('&nbsp;', ' ')).strip() for t in tds]

def num(s):
    d = re.sub(r'[^\d]', '', s)
    return int(d) if d else None

def norm(s):
    s = s.lower().replace('ё', 'е')
    s = re.sub(r'[^\wа-я ]', ' ', s)
    s = re.sub(r'\b(n|no)\b', ' ', s)
    for w in ['муниципальный', 'округ', 'поселок', 'город']:
        s = s.replace(w, ' ')
    return re.sub(r'\s+', '', s)

# ---------- 1. население из официального xlsx ----------
z = zipfile.ZipFile(os.path.join(BASE, 'data', 'mo_2025.xlsx'))
names = z.namelist()
shared = []
if 'xl/sharedStrings.xml' in names:
    raw = z.read('xl/sharedStrings.xml').decode('utf-8', 'replace')
    shared = [re.sub(r'<[^>]+>', '', m) for m in re.findall(r'<si>(.*?)</si>', raw, re.S)]

def col_letter(ref):
    m = re.match(r'([A-Z]+)', ref)
    return m.group(1) if m else ''

def cellval(c):
    t = c.get('t')
    v = c.find(NS + 'v')
    if t == 's' and v is not None:
        return shared[int(v.text)]
    if t == 'inlineStr':
        return ''.join(t2.text or '' for t2 in c.iter(NS + 't'))
    return v.text if v is not None else ''

best = None
for sf in [n for n in names if re.match(r'xl/worksheets/sheet\d+\.xml', n)]:
    sroot = ET.fromstring(z.read(sf))
    found = 0
    for row in sroot.iter(NS + 'row'):
        cells = {}
        for c in row.findall(NS + 'c'):
            cells[col_letter(c.get('r'))] = cellval(c)
        j = ' '.join(str(x) for x in cells.values())
        if 'Коломна' in j and '40' in j: found += 1
    if found and (best is None or found > best[1]):
        best = (sf, found)
print('лист:', best)

official = {}
if best:
    sroot = ET.fromstring(z.read(best[0]))
    for row in sroot.iter(NS + 'row'):
        cells = {}
        for c in row.findall(NS + 'c'):
            cells[col_letter(c.get('r'))] = cellval(c)
        vals = [str(v).strip() for k, v in sorted(cells.items())]
        if not vals: continue
        code = vals[0]
        name = vals[1] if len(vals) > 1 else ''
        pop = num(vals[2]) if len(vals) > 2 else None
        if not code.startswith('40') or not (10 <= len(code) <= 11): continue
        if 'район' in name.lower() or name in ('Санкт-Петербург',): continue
        if not name: continue
        official[name] = {'code': code, 'pop_2025': pop}

print('официальных записей СПб в xlsx:', len(official))

# ---------- 2. площади из Вики ----------
wiki = io.open(os.path.join(BASE, 'data', 'mo_wiki.html'), encoding='utf-8', errors='replace').read()
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
    district = None
    for c in cs:
        for d in DISTRICTS:
            if d.lower() in c.lower(): district = d
    name = None
    for i, c in enumerate(cs):
        if i >= idx_area: break
        if re.search(r'[а-яА-Я0-9]', c) and not re.match(r'^\d{1,3}$', c.strip()) \
           and not re.match(r'^\d{2}\.\d{2}', c) and 'мун' not in c.lower() \
           and c.lower() not in ('город', 'посёлок', 'поселок') \
           and not re.match(r'^МО\b', c) and len(c) > 1 and i > 0:
            name = c; break
    if name is None and district:
        # номерные округа: название сидит в ячейке после статуса и может быть латиницей («No 15»)
        for i, c in enumerate(cs):
            if i >= idx_area: break
            if 'мун' in c.lower() or c.lower() in ('город', 'посёлок', 'поселок'):
                for c2 in cs[i+1:idx_area]:
                    if c2 and not re.match(r'^\d{2}\.\d{2}', c2) and not re.match(r'^МО\b', c2):
                        name = c2; break
            if name: break
    if name and district:
        if name.strip().lower() == district.strip().lower() and 'округ' not in name.lower():
            continue  # строка-итог по району, не МО
        wikis.append({'name': name.strip(), 'area_km2': area, 'district': district})

def norm(s):
    s = s.lower().replace('ё', 'е')
    s = re.sub(r'[^\wа-я ]', ' ', s)
    s = re.sub(r'\b(n|no)\b', ' ', s)
    for w in ['муниципальный', 'округ', 'поселок', 'город']:
        s = s.replace(w, ' ')
    return re.sub(r'\s+', '', s)

def find_area(name):
    key = norm(name)
    if key in wareas: return wareas[key]
    cands = [k for k in wareas if norm(k) == key]
    if len(cands) == 1: return wareas[cands[0]]
    if len(key) >= 6:
        cands = [k for k in wareas if len(norm(k)) >= 6 and (key in norm(k) or norm(k) in key)]
        if len(cands) == 1: return wareas[cands[0]]
    return None

wareas = {w['name']: w for w in wikis}

ALIAS = {
 'Муниципальный округ N 7': 'муниципальный округ No 7',
 'Муниципальный округ N 15': 'муниципальный округ No 15',
 'Муниципальный округ N 21': 'муниципальный округ No 21',
 'Муниципальный округ N 54': 'муниципальный округ No 54',
 'Муниципальный округ N 65': 'муниципальный округ No 65',
 'Муниципальный округ N 72': 'муниципальный округ No 72',
 'Муниципальный округ N 78': 'муниципальный округ No 78',
 'Муниципальный округ Морской': 'Округ Морской',
 'Муниципальный округ Ланское': 'Ланское',
 'Муниципальный округ Адмиралтейский округ': 'Адмиралтейский округ',
 'Муниципальный округ Невский округ': 'Невский округ',
 'г Колпино': 'Колпино', 'г Пушкин': 'Пушкин', 'г Красное Село': 'Красное Село',
 'г Кронштадт': 'Кронштадт', 'г Зеленогорск': 'Зеленогорск', 'г Сестрорецк': 'Сестрорецк',
 'г Петергоф': 'Петергоф', 'г Ломоносов': 'Ломоносов', 'г Павловск': 'Павловск',
 'п Тярлево': 'Тярлево', 'п Шушары': 'Шушары', 'п Александровская': 'Александровская',
 'п Металлострой': 'Металлострой', 'п Понтонный': 'Понтонный', 'п Саперный': 'Сапёрный',
 'п Усть-Ижора': 'Усть-Ижора', 'п Петро-Славянка': 'Петро-Славянка',
 'п Левашово': 'Левашово', 'п Парголово': 'Парголово', 'п Лисий Нос': 'Лисий Нос',
 'п Белоостров': 'Белоостров', 'п Комарово': 'Комарово', 'п Молодёжное': 'Молодёжное',
 'п Песочный': 'Песочный', 'п Репино': 'Репино', 'п Серово': 'Серово',
 'п Смолячково': 'Смолячково', 'п Солнечное': 'Солнечное', 'п Ушково': 'Ушково',
 'п Стрельна': 'Стрельна', 'п Горелово': 'Горелово'
}

items, misses = [], []
for name, o in sorted(official.items(), key=lambda kv: kv[1]['code']):
    if 'город федерального значения' in name:  # итог по городу — не МО
        continue
    lookup = ALIAS.get(name, name)
    wf = find_area(lookup)
    district = wf['district'] if wf else None
    area = wf['area_km2'] if wf else None
    p = o['pop_2025']
    if p is None or area is None:
        if len(misses) < 3:
            print('MISS:', repr(name), '| lookup:', repr(lookup if 'lookup' in dir() else '?'),
                  '| key:', repr(norm(lookup)) if ('lookup' in dir()) else '-',
                  '| wareas has similar:', [k for k in wareas if 'адмиралтейский' in norm(k)][:3])
        misses.append(name); continue
    items.append({'district': district or '?', 'name': name, 'code': o['code'],
                  'area_km2': area, 'pop_2025': p,
                  'density': int(round(p / area)) if area else None,
                  'src': 'rosstat 01.01.2025'})

items.sort(key=lambda x: -x['density'])
json.dump(items, io.open(os.path.join(BASE, 'data', 'mo.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

total = sum(x['pop_2025'] for x in items)
rep = ['записей: %d (официальный xlsx Росстата, население на 01.01.2025)' % len(items),
       'сумма населения: %s (справочно весь город: 5 652 922)' % format(total, ',').replace(',', ' '),
       'без площади (не сшлось с Вики): %s' % ('; '.join(misses) if misses else 'нет'),
       '',
       'ТОП-8 плотных:']
rep += ['%s (%s): %s чел/км2' % (x['name'], x['district'], format(x['density'], ',').replace(',', ' ')) for x in items[:8]]
rep += ['', 'ТОП-8 просторных:']
rep += ['%s (%s): %s чел/км2' % (x['name'], x['district'], format(x['density'], ',').replace(',', ' ')) for x in items[-8:]]
rep = '\n'.join(rep)
used = set(i['name'] for i in items)
unused = [w['name'] for w in wikis if w['name'] not in used]
rep += '\n\nВИКИ-имена без пары (%d): %s' % (len(unused), '; '.join(unused[:30]))
io.open(os.path.join(BASE, 'data', 'МО-сводка.txt'), 'w', encoding='utf-8').write(rep)
print(rep[:1700])
