// Verify the VISWA theme by reading COMPUTED styles off every element, and
// prove the palette really is black / white / red only.
// Also captures screenshots.
//
//   NODE_PATH=$(npm root -g) node verify_theme.js <url> <outdir>

const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://127.0.0.1:8691';
const OUT = process.argv[3] || '/tmp/opencode/viswa-shots';
require('fs').mkdirSync(OUT, { recursive: true });

const results = [];
const ok = (name, got, want) => results.push({ name, got, want, pass: JSON.stringify(got) === JSON.stringify(want) });

// Classify a computed colour into the three-hue signature palette.
function classify(str) {
  const m = String(str).match(/rgba?\(([^)]+)\)/);
  if (!m) return { kind: 'other', raw: str };
  const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
  const [r, g, b] = p;
  const a = p.length > 3 ? p[3] : 1;
  if (a === 0) return { kind: 'transparent', raw: str };
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
  if (mx - mn <= 12) {
    if (mx <= 24) return { kind: 'black', raw: str };
    if (mn >= 236) return { kind: 'white', raw: str };
    return { kind: 'GREY-OFF-PALETTE', raw: str };
  }
  if (r > 120 && g < 90 && b < 90 && Math.abs(g - b) < 40) return { kind: 'red', raw: str };
  return { kind: 'OFF-HUE', raw: str };
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-testid="stAppViewContainer"]', { timeout: 30000 });
  await page.waitForTimeout(3500);

  const shoot = async (name) => {
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
  };

  const probe = async () => page.evaluate(() => {
    const g = (s) => document.querySelector(s);
    const cs = (e) => (e ? getComputedStyle(e) : null);
    const app = g('.stApp');
    const before = app ? getComputedStyle(app, '::before') : null;
    const after = app ? getComputedStyle(app, '::after') : null;
    const sub = g('h2, h3, h4');
    const btn = g('.stButton > button');
    return {
      bodyBg: cs(document.body) && cs(document.body).backgroundColor,
      appBg: app && cs(app).backgroundColor,
      appColor: app && cs(app).color,
      dotLayers: before ? before.backgroundImage.split(/gradient\(/).length - 1 : 0,
      dotSizes: before ? before.backgroundSize : '',
      dotMask: before ? (before.maskImage || before.webkitMaskImage) : '',
      bloom: after ? after.backgroundImage : '',
      subColor: sub && cs(sub).color,
      subBorder: sub && cs(sub).borderLeftColor,
      subLetter: sub && cs(sub).letterSpacing,
      subSize: sub && cs(sub).fontSize,
      subPadLeft: sub && cs(sub).paddingLeft,
      btnBg: btn && cs(btn).backgroundColor,
      btnBorder: btn && cs(btn).borderTopColor,
      btnColor: btn && cs(btn).color,
      btnTransform: btn && cs(btn).textTransform,
      sideBorder: (() => { const s = g('[data-testid="stSidebar"]'); return s && cs(s).borderRightColor; })(),
      // every colour anywhere on the page
      allColors: (() => {
        const out = new Set();
        document.querySelectorAll('*').forEach((el) => {
          const c = getComputedStyle(el);
          ['color', 'backgroundColor', 'borderTopColor', 'borderLeftColor',
           'borderBottomColor', 'borderRightColor', 'outlineColor', 'fill', 'stroke']
            .forEach((p) => { if (c[p] && c[p] !== 'rgba(0, 0, 0, 0)') out.add(c[p]); });
        });
        return [...out];
      })(),
    };
  });

  const home = await probe();
  console.log('--- HOME computed ---');
  for (const [k, v] of Object.entries(home)) {
    if (k === 'allColors') { console.log('  allColors', v.length, 'distinct'); continue; }
    console.log('  ' + k.padEnd(13), String(v).slice(0, 92));
  }
  await shoot('01-home');

  await page.getByTestId('stSidebar').getByText('Dashboard', { exact: true }).click();
  await page.waitForTimeout(3200);
  const dash = await probe();
  const metric = await page.evaluate(() => {
    const m = document.querySelector('[data-testid="stMetric"]');
    if (!m) return null;
    const c = getComputedStyle(m);
    return {
      bg: c.backgroundColor,
      border: c.borderTopColor,
      dots: c.backgroundImage.split(/gradient\(/).length - 1,
      label: (() => { const l = m.querySelector('[data-testid="stMetricLabel"]');
        return l ? getComputedStyle(l).color : null; })(),
      value: (() => { const v = m.querySelector('[data-testid="stMetricValue"]');
        return v ? getComputedStyle(v).color : null; })(),
    };
  });
  console.log('--- DASHBOARD metric plate ---');
  console.log(JSON.stringify(metric, null, 2));
  const charts = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('[data-testid="stVegaLiteChart"]').forEach((c) => {
      const bars = [...c.querySelectorAll('[role="graphics-symbol"]')]
        .map((m) => getComputedStyle(m).fill);
      const grid = c.querySelector('.role-axis-grid line');
      out.push({
        bars: [...new Set(bars)],
        grid: grid ? getComputedStyle(grid).stroke : null,
      });
    });
    return out;
  });
  console.log('--- DASHBOARD charts ---');
  console.log(JSON.stringify(charts, null, 2));
  await shoot('02-dashboard');

  await page.getByTestId('stSidebar').getByText('Risk Checker', { exact: true }).click();
  await page.waitForTimeout(2500);
  const submit = await page.evaluate(() => {
    const b = document.querySelector('.stFormSubmitButton > button');
    return b ? { bg: getComputedStyle(b).backgroundColor,
                 kind: b.getAttribute('kind') } : null;
  });
  console.log('--- RISK CHECKER submit ---');
  console.log(JSON.stringify(submit));
  await shoot('03-risk-checker');

  const bodyText = await page.evaluate(() => document.body.innerText);
  await browser.close();

  // ---- assertions ----
  const bad = [];
  const kinds = {};
  for (const c of [...home.allColors, ...dash.allColors]) {
    const k = classify(c);
    kinds[k.kind] = (kinds[k.kind] || 0) + 1;
    if (k.kind === 'GREY-OFF-PALETTE' || k.kind === 'OFF-HUE') bad.push(c);
  }
  console.log('\n--- colour census (every colour on the page) ---');
  for (const [k, n] of Object.entries(kinds)) console.log(`  ${k.padEnd(18)} ${n}`);

  ok('body is black', classify(home.bodyBg).kind, 'black');
  ok('app is black', classify(home.appBg).kind, 'black');
  ok('app text is white', classify(home.appColor).kind, 'white');
  ok('three stacked dot fields', home.dotLayers, 3);
  ok('dot fields are 66/22/11px', home.dotSizes, '66px 66px, 22px 22px, 11px 11px');
  ok('dot field is masked', /radial-gradient/.test(home.dotMask || ''), true);
  ok('red bloom present at the top', /rgba?\(204, 0, 0/.test(home.bloom || ''), true);
  ok('section head is white-alpha', classify(home.subColor).kind, 'white');
  ok('section head rule is red', classify(home.subBorder).kind, 'red');
  ok('section head is 11px mono', home.subSize, '11px');
  ok('section head text clears the red rule (>=10px padding)',
    parseFloat(home.subPadLeft) >= 10, true);
  ok('Click Me text is white', classify(home.btnColor).kind, 'white');
  ok('Click Me is uppercased', home.btnTransform, 'uppercase');
  ok('sidebar divider is white-alpha', classify(home.sideBorder).kind, 'white');
  // Home's only button is the secondary Click Me: ghost, not red.
  ok('secondary Click Me is transparent (ghost)', home.btnBg, 'rgba(0, 0, 0, 0)');
  ok('ghost button border is white-alpha', classify(home.btnBorder).kind, 'white');
  ok('primary Check Risk is solid red', submit && classify(submit.bg).kind, 'red');
  ok('score chart bars are white, not red', charts[0] &&
    charts[0].bars.some((b) => classify(b).kind === 'white') &&
    charts[0].bars.every((b) => classify(b).kind !== 'red'), true);
  ok('risk chart bars are red', charts[1] &&
    charts[1].bars.map(classify).some((k) => k.kind === 'red'), true);
  ok('chart gridlines are soft (0.22)', charts[0] && charts[0].grid, 'rgba(255, 255, 255, 0.22)');
  ok('metric plate is black/white alpha', classify(metric.bg).kind, 'white');
  ok('metric plate has dot texture + ticks', metric.dots, 9);
  ok('metric label is white-alpha', classify(metric.label).kind, 'white');
  ok('metric value is white', classify(metric.value).kind, 'white');
  ok('NO off-palette colours anywhere', bad, []);

  console.log('\n--- theme assertions ---');
  let failed = 0;
  for (const r of results) {
    if (!r.pass) failed++;
    console.log('  [' + (r.pass ? 'PASS' : 'FAIL') + '] ' + r.name +
      (r.pass ? '' : '   got=' + JSON.stringify(r.got) + ' want=' + JSON.stringify(r.want)));
  }
  if (bad.length) console.log('\noff-palette colours seen:', [...new Set(bad)].slice(0, 12));
  console.log('\nscreenshots in ' + OUT);
  console.log((results.length - failed) + '/' + results.length + ' theme checks passed');
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error('FATAL', e.message); process.exit(2); });