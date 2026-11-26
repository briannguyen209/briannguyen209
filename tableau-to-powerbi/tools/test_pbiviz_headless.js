// Test custom visual (.pbiviz) ngoài Power BI: giải nén, nạp visual.js vào Chromium headless với host giả lập,
// đổ dữ liệu từ CSV mẫu (tổng Sales/Target theo SubCategory) và chụp ảnh.  Dùng: node tools/test_pbiviz_headless.js <file.pbiviz> <out.png>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process'), os = require('os');
const [pbiviz, out] = process.argv.slice(2);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pbx-'));
execSync(`unzip -q -o "${pbiviz}" -d "${tmp}"`);
const resDir = path.join(tmp, 'resources');
const res = JSON.parse(fs.readFileSync(path.join(resDir, fs.readdirSync(resDir)[0]), 'utf8'));
const guid = res.visual.guid;
const csv = fs.readFileSync(path.join(__dirname, '../data/superstore_sample.csv'), 'utf8').trim().split('\n');
const head = csv[0].split(','); const agg = {};
for (const line of csv.slice(1)) { const r = line.split(','); const k = r[head.indexOf('SubCategory')];
  agg[k] = agg[k] || [0, 0]; agg[k][0] += +r[head.indexOf('Sales')]; agg[k][1] += +r[head.indexOf('Target')]; }
const cats = Object.keys(agg).sort((a, b) => agg[b][0] - agg[a][0]);
const html = `<html><head><style>${res.content.css}</style></head><body style="margin:0;background:#fff">
<div id="v" style="width:700px;height:420px"></div>
<script>var powerbi = {visuals:{plugins:{}}};</script>
<script>${res.content.js}</script>
<script>
  const plugin = powerbi.visuals.plugins['${guid}'];
  const sid = k => ({ equals: o => o.getKey() === k, getKey: () => k, includes: () => false, hasIdentity: () => true });
  window.__tips = [];
  const host = {
    eventService: { renderingStarted(){}, renderingFinished(){ window.__done = true; }, renderingFailed(o, e){ window.__err = e; } },
    createSelectionManager: () => ({ select: id => Promise.resolve([id]), clear: () => Promise.resolve(), registerOnSelectCallback(){} }),
    createSelectionIdBuilder: () => { let k; const b = { withCategory(c, i){ k = c.values[i]; return b; }, createSelectionId: () => sid(k) }; return b; },
    tooltipService: { show: t => window.__tips.push(t), hide(){} , enabled: () => true },
  };
  const v = plugin.create({ element: document.getElementById('v'), host });
  const cats = ${JSON.stringify(cats)}, agg = ${JSON.stringify(agg)};
  v.update({ viewport: { width: 700, height: 420 }, type: 2, dataViews: [{ metadata: { objects: {} }, categorical: {
    categories: [{ source: { displayName: 'SubCategory', roles: { category: true } }, values: cats }],
    values: [ { source: { displayName: 'Sales', roles: { actual: true } }, values: cats.map(c => agg[c][0]) },
              { source: { displayName: 'Target', roles: { target: true } }, values: cats.map(c => agg[c][1]) } ] } }] });
</script></body></html>`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 700, height: 420 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.setContent(html); await p.waitForFunction(() => window.__done || window.__err, null, { timeout: 10000 });
  const rows = await p.$$eval('g.row', n => n.length);
  await p.hover('g.row >> nth=0'); await p.click('g.row >> nth=1');
  const tips = await p.evaluate(() => window.__tips.length);
  const opacity = await p.$$eval('g.row', n => n.map(e => e.style.opacity));
  await p.screenshot({ path: out });
  console.log(JSON.stringify({ rows, tooltipsShown: tips, opacityAfterClick: opacity, pageErrors: errs, renderError: await p.evaluate(() => window.__err || null) }));
  await b.close(); process.exit(errs.length || rows !== cats.length ? 1 : 0);
})();
