// Рендер чертежей вентиляции: plan/vent-*.svg -> PNG, + PDF (A3, 1:100) вместе со спецификацией.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const dir = path.join(__dirname, '..', 'plan');
  const names = ['vent-1-etazh-2', 'vent-2-krovlya', 'vent-5-elektrika', 'vent-3-etazh-1'];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 3300, height: 1980 } });
  const pages = [];
  for (const n of names) {
    const svg = fs.readFileSync(path.join(dir, n + '.svg'), 'utf8');
    pages.push(svg);
    await p.setContent(`<html><body style="margin:0">${svg.replace(/width="[^"]+mm" height="[^"]+mm"/, 'width="3300" height="1980"')}</body></html>`);
    await p.screenshot({ path: path.join(dir, n + '.png') });
  }
  await p.setContent(`<html><head><style>@page{size:A3 landscape;margin:0}body{margin:0}
    .pg{width:420mm;height:296mm;display:flex;align-items:center;justify-content:center;page-break-after:always}</style></head>
    <body>${pages.map(s => `<div class="pg">${s}</div>`).join('')}</body></html>`);
  await p.pdf({ path: path.join(dir, '_vent-plans.pdf'), format: 'A3', landscape: true, printBackground: true });
  await p.goto('file://' + path.join(dir, 'vent-6-fasad.html'));
  await p.pdf({ path: path.join(dir, '_vent-fasad.pdf'), format: 'A3', landscape: true, printBackground: true });
  await p.setViewportSize({ width: 1587, height: 1123 });
  await p.screenshot({ path: path.join(dir, 'vent-6-fasad.png'), fullPage: true });
  await p.goto('file://' + path.join(dir, 'vent-4-spec.html'));
  await p.pdf({ path: path.join(dir, '_vent-spec.pdf'), format: 'A3', landscape: true, printBackground: true });
  await p.setViewportSize({ width: 1587, height: 1123 });
  await p.screenshot({ path: path.join(dir, 'vent-4-spec.png'), fullPage: true });
  await b.close();
})();
