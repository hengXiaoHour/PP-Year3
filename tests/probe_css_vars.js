// List the CSS custom properties Streamlit actually defines, and dump a few
// computed background-images, so the theme can override the real variables
// instead of guessing selector names.
//   NODE_PATH=$(npm root -g) node probe_css_vars.js <url>
const { chromium } = require('playwright');
const URL = process.argv[2];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-testid="stAppViewContainer"]', { timeout: 30000 });
  await page.waitForTimeout(3000);
  await page.getByTestId('stSidebar').getByText('Dashboard', { exact: true }).click();
  await page.waitForTimeout(3000);

  const out = await page.evaluate(() => {
    const collect = (el) => {
      const list = [];
      for (let sheet of document.styleSheets) {
        let rules;
        try { rules = sheet.cssRules; } catch { continue; }
        for (const rule of rules) {
          if (!rule.style) continue;
          for (const prop of rule.style) {
            if (prop.startsWith('--')) {
              const v = getComputedStyle(el).getPropertyValue(prop).trim();
              if (v) list.push(prop + ' = ' + v);
            }
          }
        }
      }
      return [...new Set(list)].sort();
    };
    const root = collect(document.documentElement);
    const app = document.querySelector('.stApp');
    const m = document.querySelector('[data-testid="stMetric"]');
    const alert = document.querySelector('[data-testid="stAlertContainer"]');
    return {
      rootVars: root,
      appBgImage: app ? getComputedStyle(app, '::before').backgroundImage.slice(0, 200) : null,
      appAfter: app ? getComputedStyle(app, '::after').backgroundImage.slice(0, 160) : null,
      metricBgImage: m ? getComputedStyle(m).backgroundImage : null,
      metricGradients: m ? (getComputedStyle(m).backgroundImage.match(/gradient\(/g) || []).length : 0,
      metricSizes: m ? getComputedStyle(m).backgroundSize : null,
      alertBg: alert ? getComputedStyle(alert).backgroundColor : null,
      alertParentBg: alert ? getComputedStyle(alert.parentElement).backgroundColor : null,
      alertBorder: alert ? getComputedStyle(alert.parentElement).borderLeftColor : null,
      themeAttr: document.querySelector('[data-testid="stAppViewContainer"]')?.getAttribute('data-theme'),
      bodyAttrs: document.body.getAttributeNames(),
    };
  });
  await browser.close();

  console.log('--- CSS custom properties Streamlit defines on <html> ---');
  out.rootVars.forEach((v) => console.log('  ' + v));
  console.log('\ndata-theme on app container:', out.themeAttr);
  console.log('body attributes:', JSON.stringify(out.bodyAttrs));
  console.log('\n--- dot field (.stApp::before) ---');
  console.log('  ', out.appBgImage);
  console.log('--- red bloom (.stApp::after) ---');
  console.log('  ', out.appAfter);
  console.log('\n--- metric plate ---');
  console.log('  gradient count:', out.metricGradients);
  console.log('  background-size:', out.metricSizes);
  console.log('  background-image:', (out.metricBgImage || '').slice(0, 220));
  console.log('\n--- success alert ---');
  console.log('  container bg:', out.alertBg);
  console.log('  parent bg   :', out.alertParentBg);
  console.log('  parent border-left:', out.alertBorder);
})().catch((e) => { console.error('FATAL', e.message); process.exit(2); });