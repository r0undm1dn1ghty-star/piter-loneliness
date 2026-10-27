// проверка v3: скрипты + ключевые маркеры
const fs = require('fs');
const h = fs.readFileSync('v3/index.html', 'utf8');
const scripts = [...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
fs.writeFileSync('v3/_c.js', scripts.join('\n;\n'));
console.log('скриптов:', scripts.length);
console.log('фото в HTML:', (h.match(/mo\/mo_/g) || []).length);
console.log('кубик 3D:', h.includes('scene3d'), '| старый барабан:', h.includes("class='drum'") || h.includes('id="drum"'));
console.log('новая палитра:', (h.match(/#1a0b2e/g) || []).length, '| старая #170b1e:', (h.match(/#170b1e/g) || []).length);
console.log('финал-тайтл главный:', h.indexOf('rTitle') > -1);
console.log('честность v2:', h.includes('РБК отдельно писал'));
console.log('hero v2:', h.includes('я проверил цифры'));
