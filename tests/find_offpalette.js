// Report WHICH elements carry an off-palette colour, so the fix targets the
// right selectors instead of guessing.
//   NODE_PATH=$(npm root -g) node find_offpalette.js <url>
const { chromium } = require('playwright');
const URL = process.argv[2];

function classify(str) {
  const m = String(str).match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
  const [r, g, b] = p;
  if (p.length > 3 && p[3] === 0) return null;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
  if (mx - mn <= 12) return (mx <= 24 || mn >= 236) ? null : { c: str, why: 'grey' };
  if (r > 120 && g < 90 && b < 90 && Math.abs(g - b) < 40) return null;
  return { c: str, why: 'hue' };
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-testid="stAppViewContainer"]', { timeout: 30000 });
  await page.waitForTimeout(3000);

  const visit = async (pageName) => {
    await page.getByTestId('stSidebar').getByText(pageName, { exact: true }).click();
    await page.waitForTimeout(2500);
    return page.evaluate((pn) => {
      const rows = [];
      document.querySelectorAll('*').forEach((el) => {
        const c = getComputedStyle(el);
        for (const prop of ['color', 'backgroundColor', 'borderTopColor', 'borderLeftColor',
          'borderBottomColor', 'borderRightColor', 'fill', 'stroke', 'outlineColor']) {
          const v = c[prop];
          if (!v) continue;
          const bad = (() => {
            const m = v.match(/rgba?\(([^)]+)\)/);
            if (!m) return null;
            const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
            const [r, g, b] = p;
            if (p.length > 3 && p[3] === 0) return null;
            const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
            if (mx - mn <= 12) return (mx <= 24 || mn >= 236) ? null : 'GREY';
            if (r > 120 && g < 90 && b < 90 && Math.abs(g - b) < 40) return null;
            return 'HUE';
          })();
          if (!bad) continue;
          const tid = el.getAttribute('data-testid');
          const bse = el.getAttribute('data-baseweb');
          rows.push({
            page: pn, prop, value: v, kind: bad,
            tag: el.tagName.toLowerCase(),
            testid: tid || '', baseweb: bse || '',
            cls: (el.className && el.className.toString().slice(0, 70)) || '',
            parentTestid: el.parentElement ? (el.parentElement.getAttribute('data-testid') || el.parentElement.getAttribute('data-baseweb') || '') : '',
          });
        }
      });
      return rows;
    }, pageName);
  };

  const all = [];
  for (const p of ['Home', 'Dashboard', 'Risk Checker', 'Student Data']) {
    all.push(...(await visit(p)));
  }
  await browser.close();

  const seen = new Map();
  for (const r of all) {
    const key = `${r.testid}|${r.baseweb}|${r.cls}|${r.prop}|${r.value}`;
    if (!seen.has(key)) seen.set(key, r);
  }
  console.log(`--- ${seen.size} distinct off-palette sources ---\n`);
  for (const r of seen.values()) {
    console.log(`${r.kind}  ${r.prop.padEnd(18)} ${r.value}`);
    console.log(`     tag=${r.tag}  testid=${r.testid || '-'}  baseweb=${r.baseweb || '-'}`);
    console.log(`     parent=${r.parentTestid || '-'}  cls=${r.cls || '-'}`);
    console.log(`     on page: ${r.page}\n`);
  }
})().catch((e) => { console.error('FATAL', e.message); process.exit(2); });