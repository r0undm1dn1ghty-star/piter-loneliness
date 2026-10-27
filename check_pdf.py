import importlib.util, subprocess, sys
has_pypdf = importlib.util.find_spec('pypdf') is not None
has_pdftotext = subprocess.run(['where', 'pdftotext'], capture_output=True, text=True).returncode == 0
print('pypdf:', has_pypdf)
print('pdftotext:', has_pdftotext)
if has_pypdf:
    from pypdf import PdfReader
    r = PdfReader('data/rosstat_mo_072025.pdf')
    txt = '\n'.join((p.extract_text() or '') for p in r.pages)
    io = open('data/rosstat_mo_072025.txt', 'w', encoding='utf-8')
    io.write(txt); io.close()
    print('страниц:', len(r.pages), '| символов:', len(txt))
    print(txt[:600])
