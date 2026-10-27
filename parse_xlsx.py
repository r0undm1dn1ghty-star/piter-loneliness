# -*- coding: utf-8 -*-
# Официальный xlsx Росстата (численность населения РФ по МО на 01.01.2025) → датасет МО СПб.
import zipfile, json, re, io, os
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, 'data', 'mo_2025.xlsx')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

z = zipfile.ZipFile(SRC)
names = z.namelist()
shared = []
if 'xl/sharedStrings.xml' in names:
    root = ET.fromstring(z.read('xl/sharedStrings.xml'))
    for si in root.findall('m:si', NS):
        text = ''.join(t.text or '' for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'))
        shared.append(text)

def col_letter(ref):
    m = re.match(r'([A-Z]+)', ref)
    return m.group(1) if m else ''

def cellval(c):
    t = c.get('t')
    v = c.find('m:v', NS)
    if t == 's' and v is not None:
        return shared[int(v.text)]
    if t == 'inlineStr':
        isn = c.find('m:is', NS)
        if isn is not None:
            return ''.join(t.text or '' for t in isn.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'))
    return v.text if v is not None else ''

# найти лист с МО СПб: перебираем все листы, ищем строки с "Коломна" или "Адмиралтейский"
sheet_files = [n for n in names if re.match(r'xl/worksheets/sheet\d+\.xml', n)]
best = None
for sf in sheet_files:
    root = ET.fromstring(z.read(sf))
    found = 0
    for row in root.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
        cells = {}
        for c in row.findall('m:c', NS):
            cells[col_letter(c.get('r'))] = cellval(c)
        joined = ' '.join(str(x) for x in cells.values())
        if 'Коломна' in joined or 'Сенной округ' in joined:
            found += 1
    if found > 0 and (best is None or found > best[1]):
        best = (sf, found)
print('лист с МО СПб:', best)

if best:
    sf = best[0]
    root = ET.fromstring(z.read(sf))
    rows_out = []
    for row in root.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
        cells = {}
        for c in row.findall('m:c', NS):
            cells[col_letter(c.get('r'))] = cellval(c)
        vals = [str(v) for k, v in sorted(cells.items())]
        joined = ' | '.join(vals)
        if any(d in joined for d in ['Коломна', 'Сенной округ', 'Пискарёвка', 'Пискаревка', 'Юнтолово', 'Озеро Долгое']):
            rows_out.append(joined)
    io.open(os.path.join(BASE, 'data', 'rosstat_xlsx_sample.txt'), 'w', encoding='utf-8').write(
        '\n'.join(rows_out[:40]))
    print('строк-образцов:', len(rows_out))
    for s in rows_out[:8]:
        print(s[:200])
