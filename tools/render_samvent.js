// plan/samvent.svg -> plan/samvent.pdf (A3, 1 лист) и plan/samvent.png
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const dir = path.join(__dirname, '..', 'plan');
  const svg = fs.readFileSync(path.join(dir, 'samvent.svg'), 'utf8');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 2970, height: 2100 } });
  await p.setContent(`<html><body style="margin:0">${svg.replace('width="420mm" height="297mm"', 'width="2970" height="2100"')}</body></html>`);
  await p.screenshot({ path: path.join(dir, 'samvent.png') });
  await p.setContent(`<html><head><style>@page{size:A3 landscape;margin:0}body{margin:0}</style></head><body>${svg}</body></html>`);
  await p.pdf({ path: path.join(dir, 'samvent.pdf'), format: 'A3', landscape: true, printBackground: true });
  await b.close();
})();
