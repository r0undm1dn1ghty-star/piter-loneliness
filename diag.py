# -*- coding: utf-8 -*-
import re, io, os
BASE = os.path.dirname(os.path.abspath(__file__))
wiki = io.open(os.path.join(BASE, 'data', 'mo_wiki.html'), encoding='utf-8', errors='replace').read()

def cells_of(tr):
    tds = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)
    return [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t).replace('&nbsp;', ' ')).strip() for t in tds]

hits = []
for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', wiki, re.S):
    cs = cells_of(tr)
    j = ' '.join(cs)
    if 'Адмиралтейский округ' in j and '2,10' in j:
        hits.append(cs)
    if re.search(r'No 7\b', j) and '4,33' in j:
        hits.append(cs)
    if 'Невский округ' in j and ('25' in j or '13' in j):
        hits.append(['SKIP?'] + cs)
for h in hits[:4]:
    print('CELLS:', h)
    for i, c in enumerate(h):
        print('  [%d] %r' % (i, c))
    print('---')
