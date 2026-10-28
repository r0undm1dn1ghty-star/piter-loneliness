// v5 проверка + выгрузка JS для node --check
const fs = require('fs');
const h = fs.readFileSync('v4/index.html', 'utf8');
const scripts = [...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
fs.writeFileSync('v4/_c.js', scripts.join('\n;\n'));
console.log('скриптов:', scripts.length);
console.log('commons-парсинг в браузере:', h.includes('commons.wikimedia.org'));
console.log('старая простыня mol удалена:', !h.includes('class="mol"'));
console.log('victorfoto (референс):', (h.match(/victorfoto/g) || []).length);
console.log('кубик 3D:', h.includes('scene3d'));
console.log('дубль заголовка кубика:', (h.match(/брось кубик — вспомни вечер/g) || []).length);
