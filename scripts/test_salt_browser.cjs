// Real-browser checks. Serve site/ on 127.0.0.1:8765 first.
// Install Playwright separately, then run:
// NODE_PATH=/path/to/node_modules PLAYWRIGHT_BROWSERS_PATH=/path/to/browsers node scripts/test_salt_browser.cjs
// Optional: SALT_BASE_URL and SALT_SCREENSHOTS (defaults to /tmp/wmt-salt-review).
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.SALT_BASE_URL || 'http://127.0.0.1:8765';
const shots = process.env.SALT_SCREENSHOTS || '/tmp/wmt-salt-review';

(async () => {
  fs.mkdirSync(shots, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${base}/salt.html`);
    await page.waitForFunction(() => window.saltViewer && !document.getElementById('salt-controls').disabled);
    const snapshot = () => page.evaluate(() => window.saltViewer.snapshot());
    const frame = () => page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
    await frame();
    assert((await snapshot()).drawCalls > 0);
    await page.screenshot({ path: path.join(shots, 'desktop.png'), fullPage: true });
    await page.locator('#salt-stage').screenshot({ path: path.join(shots, 'model.png') });
    const initial = await snapshot();
    for (const view of ['top', 'side', 'below']) {
      await page.locator(`[data-view="${view}"]`).click(); await frame();
      assert.notDeepEqual((await snapshot()).camera, initial.camera);
    }
    const canvas = page.locator('#salt-canvas-host canvas');
    await canvas.focus();
    const beforeKey = await snapshot(); await page.keyboard.press('ArrowRight'); await frame();
    assert.notDeepEqual((await snapshot()).camera, beforeKey.camera);
    const beforeDrag = await snapshot(), box = await canvas.boundingBox();
    await page.mouse.move(box.x + box.width/2, box.y + box.height/2);
    await page.mouse.down(); await page.mouse.move(box.x + box.width/2 + 80, box.y + box.height/2 + 20, { steps: 5 }); await page.mouse.up(); await frame();
    assert.notDeepEqual((await snapshot()).camera, beforeDrag.camera);
    await page.locator('#zoom-in').click(); await page.locator('#zoom-out').click();
    await page.locator('#show-salt').uncheck(); assert.equal((await snapshot()).saltVisible, false);
    await page.locator('#show-salt').check();
    await page.locator('#salt-opacity').fill('35'); assert.equal((await snapshot()).opacity, .35);
    for (const [a, id] of ['x', 'y', 'z'].entries()) {
      await page.locator(`#show-${id}`).check();
      const max = await page.locator(`#slice-${id}`).getAttribute('max');
      await page.locator(`#slice-${id}`).fill(max); await frame();
      assert.equal((await snapshot()).slices[a], Number(max));
      const endpoint = await page.evaluate(a => window.saltViewer.metadata.axes_km[a].at(-1).toFixed(2), a);
      assert.equal(await page.locator(`#${id}-value`).textContent(), `${endpoint} km`);
      await page.locator(`#slice-${id}`).fill('0');
    }
    await page.locator('#acquisition').selectOption('narrow'); assert.equal((await snapshot()).survey, 'narrow');
    await page.locator('#acquisition').selectOption('wide'); assert.equal((await snapshot()).survey, 'wide');
    await page.locator('#reset').click(); await frame();
    const reset = await snapshot();
    assert.deepEqual(reset.slices, initial.slices); assert.equal(reset.opacity, .85); assert.equal(reset.survey, 'none');
    await page.locator('#acquisition').selectOption('wide');
    await page.locator('#salt-stage').screenshot({ path: path.join(shots, 'survey.png') });
    await page.locator('#nav button').click(); await frame();
    await page.screenshot({ path: path.join(shots, 'dark.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 }); await frame();
    await page.screenshot({ path: path.join(shots, 'mobile.png'), fullPage: true });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert.deepEqual(errors, []);
    // Context loss must leave a useful static view and recover via Retry.
    await page.evaluate(() => document.querySelector('#salt-canvas-host canvas').getContext('webgl2').getExtension('WEBGL_lose_context').loseContext());
    await page.waitForFunction(() => document.getElementById('salt-controls').disabled);
    assert(await page.locator('#salt-fallback').isVisible());
    await page.locator('#retry').click();
    await page.waitForFunction(() => !document.getElementById('salt-controls').disabled);
    // Simulate missing volume data, then recover without a page reload.
    const fail = await browser.newPage();
    await fail.route('**/velocity.bin', route => route.fulfill({ status: 503, body: 'Unavailable' }));
    await fail.goto(`${base}/salt.html`);
    await fail.waitForFunction(() => !document.getElementById('retry').hidden);
    assert(await fail.locator('#salt-fallback').isVisible());
    await fail.unroute('**/velocity.bin'); await fail.locator('#retry').click();
    await fail.waitForFunction(() => !document.getElementById('salt-controls').disabled);
    const noGL = await browser.newPage();
    await noGL.addInitScript(() => { window.WebGLRenderingContext = undefined; });
    await noGL.goto(`${base}/salt.html`);
    await noGL.waitForFunction(() => !document.getElementById('retry').hidden);
    assert(await noGL.locator('#salt-fallback').isVisible());
    const noJS = await browser.newPage({ javaScriptEnabled: false });
    await noJS.goto(`${base}/salt.html`);
    assert(await noJS.locator('#salt-fallback').isVisible());
    assert(await noJS.locator('noscript').isVisible());
    assert(await noJS.locator('#salt-opacity').isDisabled());
    console.log(`Salt desktop/mobile rendering, controls, keyboard, drag, reset, context recovery, asset retry, no-WebGL and no-JavaScript checks passed. Screenshots: ${shots}`);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
