// Рендер plan/*.svg -> PNG и PDF (A3, масштаб 1:100) через Chromium.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const dir = path.join(__dirname, '..', 'plan');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 3300, height: 1980 }, deviceScaleFactor: 1 });
  const pages = [];
  for (const f of [1, 2]) {
    const svg = fs.readFileSync(path.join(dir, `etazh-${f}.svg`), 'utf8');
    pages.push(svg);
    const png = svg.replace(/width="[^"]+mm" height="[^"]+mm"/, 'width="3300" height="1980"');
    await p.setContent(`<html><body style="margin:0">${png}</body></html>`);
    await p.screenshot({ path: path.join(dir, `etazh-${f}.png`), fullPage: true });
  }
  const html = `<html><head><style>@page{size:A3 landscape;margin:0}body{margin:0}
    .pg{width:420mm;height:296mm;display:flex;align-items:center;justify-content:center;page-break-after:always}</style></head>
    <body>${pages.map(s => `<div class="pg">${s}</div>`).join('')}</body></html>`;
  await p.setContent(html);
  await p.pdf({ path: path.join(dir, 'plan-doma.pdf'), format: 'A3', landscape: true, printBackground: true });
  await b.close();
  console.log('rendered');
})();
