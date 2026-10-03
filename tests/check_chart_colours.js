// Read the ACTUAL rendered chart colours out of the Vega SVG, because the
// blue in Streamlit's default Vega-Lite theme is invisible to CSS overrides.
//   NODE_PATH=$(npm root -g) node check_chart_colours.js <url>
const { chromium } = require('playwright');
const URL = process.argv[2];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-testid="stAppViewContainer"]', { timeout: 30000 });
  await page.waitForTimeout(2500);
  await page.getByTestId('stSidebar').getByText('Dashboard', { exact: true }).click();
  await page.waitForTimeout(4000);

  const out = await page.evaluate(() => {
    const charts = [...document.querySelectorAll('[data-testid="stVegaLiteChart"], .vega-embed')];
    const info = charts.map((c, i) => {
      const marks = [...c.querySelectorAll('path, rect')].map((m) => getComputedStyle(m).fill);
      const texts = [...c.querySelectorAll('text')].map((m) => getComputedStyle(m).fill);
      const gridlines = [...c.querySelectorAll('path[stroke], line')].map((m) => getComputedStyle(m).stroke);
      const uniq = (a) => [...new Set(a)];
      return {
        index: i,
        markFills: uniq(marks),
        textFills: uniq(texts),
        strokes: uniq(gridlines),
        formColor: c.querySelector('form') ? getComputedStyle(c.querySelector('form')).color : null,
        formBorder: c.querySelector('form') ? getComputedStyle(c.querySelector('form')).borderTopColor : null,
      };
    });
    return info;
  });
  await browser.close();
  console.log('--- rendered Vega charts ---');
  out.forEach((c) => console.log(JSON.stringify(c, null, 2)));
})().catch((e) => { console.error('FATAL', e.message); process.exit(2); });