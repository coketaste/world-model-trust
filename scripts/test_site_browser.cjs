// Serve site/ over HTTP, then run with Playwright installed:
// NODE_PATH=/path/to/node_modules node scripts/test_site_browser.cjs
// SITE_BASE_URL defaults to http://127.0.0.1:8765.
// SITE_SCREENSHOTS defaults to /tmp/wmt-site-review.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.SITE_BASE_URL || 'http://127.0.0.1:8765';
const output = process.env.SITE_SCREENSHOTS || '/tmp/wmt-site-review';
const pages = fs.readdirSync(path.resolve(__dirname, '../site')).filter(f => f.endsWith('.html'));

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  fs.mkdirSync(output, { recursive: true });
  let cases = 0;
  try {
    for (const width of [1440, 390, 320]) for (const file of pages) {
      const page = await browser.newPage({ viewport: { width, height: 960 }, hasTouch: width < 700, reducedMotion: 'reduce' });
      const errors = [], failures = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('response', r => { if (r.status() >= 400) failures.push(`${r.status()}: ${r.url()}`); });
      await page.goto(`${base}/${file}`);
      if (file === 'salt.html') await page.waitForFunction(() => window.saltViewer);
      const overflow = () => page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      assert.equal(await overflow(), false, `${file} overflows at ${width}px`);
      assert.equal(await page.locator('#nav a.link').count(), 6);
      assert(!/\[object (?:HTML|SVG|Text)/.test(await page.locator('main').innerText()), `${file}: DOM nodes rendered as text`);
      if (file === 'geophysics.html' || file === 'salt.html') {
        assert.equal(await page.locator('.subnav [aria-current="page"]').getAttribute('href'), file);
        assert.equal(await page.locator('.subnav a[href="salt.html"]').count(), 1);
      }
      // Every rendered link to a local anchor must have a target on this page.
      const missingAnchors = await page.evaluate(() => [...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href').slice(1)).filter(id => id && !document.getElementById(decodeURIComponent(id))));
      assert.deepEqual(missingAnchors, [], `${file}: missing anchor targets`);
      if (width === 1440) {
        // Exercise all existing segmented groups, sliders, checkboxes and tables.
        for (let g = 0; g < await page.locator('.seg').count(); g++) {
          const group = page.locator('.seg').nth(g);
          for (let b = 0; b < await group.locator('button').count(); b++) {
            const button = group.locator('button').nth(b); await button.click();
            assert.equal(await button.getAttribute('aria-pressed'), 'true');
            assert.equal(await group.locator('[aria-pressed="true"]').count(), 1);
          }
        }
        for (let i = 0; i < await page.locator('input[type="range"]').count(); i++) {
          const slider = page.locator('input[type="range"]').nth(i);
          if (!await slider.isVisible() || !await slider.isEnabled()) continue;
          const initial = await slider.inputValue();
          for (const attr of ['min', 'max']) {
            await slider.fill(await slider.getAttribute(attr));
            assert(await slider.evaluate(el => { const value = el.closest('label').querySelector('.val'); return value && value.textContent.trim() && !value.textContent.includes('NaN'); }));
          }
          await slider.fill(initial);
        }
        for (const cb of await page.locator('input[type="checkbox"]').all()) {
          if (await cb.isVisible() && await cb.isEnabled()) { const checked = await cb.isChecked(); await cb.setChecked(!checked); await cb.setChecked(checked); }
        }
        for (const button of await page.getByRole('button', { name: 'Table view', exact: true }).elementHandles()) {
          await button.click(); assert.equal(await button.textContent(), 'Chart view');
          assert(await button.evaluate(el => !el.closest('.chartcard').querySelector('.tablewrap').hidden));
          await button.click();
        }
      }
      if (file === 'geophysics.html') {
        assert.equal(await page.locator('#primer > .wg').count(), 5);
        // These rays existed in the DOM before the fix, but CSS erased stroke.
        for (const selector of ['#w-tomo .wg-grid line', '#w-multiples svg line[style*="opacity"]']) {
          const rays = await page.locator(selector).evaluateAll(nodes => nodes.map(n => ({ stroke: getComputedStyle(n).stroke, opacity: +getComputedStyle(n).opacity })));
          assert(rays.length >= 7); assert(rays.every(r => r.stroke !== 'none' && r.opacity > 0 && r.opacity < 1));
        }
        const readout = page.locator('#w-tomo .wg-readout');
        const before = await readout.textContent();
        const aperture = page.getByRole('slider', { name: 'Aperture: largest ray angle from horizontal' });
        await aperture.fill('10'); assert.notEqual(await readout.textContent(), before); await aperture.fill('90');
        await page.getByRole('button', { name: 'Add the multiple', exact: true }).click();
        assert(await page.locator('#w-multiples svg polyline').isVisible());
        await page.getByRole('button', { name: 'Primary rays only', exact: true }).click();
        assert(!await page.locator('#w-multiples svg polyline').isVisible());
        // Section links must clear the actual sticky header, not a fixed 72px.
        for (const id of ['documented', 'methods-in-pictures', 'w-tomo', 'w-migration', 'w-moveout', 'w-multiples', 'w-fwi', 'toolkit']) {
          await page.locator(`a[href="#${id}"]`).first().click();
          const position = await page.evaluate(id => ({ target: document.getElementById(id).getBoundingClientRect().top, nav: document.getElementById('nav').getBoundingClientRect().bottom }), id);
          assert(position.target >= position.nav + 10, `${id} obscured at ${width}px: ${JSON.stringify(position)}`);
        }
        await page.locator('a[href="#w-tomo"]').first().click();
        await page.screenshot({ path: path.join(output, `primer-${width}.png`) });
        await page.getByRole('button', { name: 'Toggle colour theme' }).click();
        assert(await page.locator('#w-tomo .wg-grid line').first().evaluate(n => getComputedStyle(n).stroke !== 'none'));
        await page.screenshot({ path: path.join(output, `primer-dark-${width}.png`) });
      }
      if (file === 'literature.html' && width === 1440) {
        const search = page.getByRole('searchbox', { name: 'Search', exact: true });
        await search.fill('no-such-concept-xyz'); assert.equal(await page.locator('#rows details').count(), 0);
        await search.fill(''); assert(await page.locator('#rows details').count() > 0);
      }
      // Check all images, including lazily loaded reference figures.
      await page.evaluate(async () => { await Promise.all([...document.images].map(i => { i.loading = 'eager'; return i.decode().catch(() => {}); })); });
      assert.deepEqual(await page.evaluate(() => [...document.images].filter(i => !i.naturalWidth).map(i => i.src)), [], `${file}: broken images`);
      assert.equal(await overflow(), false, `${file} overflows after interaction at ${width}px`);
      assert(!/\[object (?:HTML|SVG|Text)/.test(await page.locator('main').innerText()), `${file}: DOM nodes rendered as text after interaction`);
      assert.deepEqual(errors, [], `${file}: runtime errors`); assert.deepEqual(failures, [], `${file}: failed assets`);
      console.log(`PASS ${width}px ${file}`); cases++;
      await page.close();
    }
    // Style merging must not depend on attribute insertion order. Explicit
    // authored CSS still overrides a conflicting presentation colour.
    const page = await browser.newPage(); await page.goto(`${base}/geophysics.html`);
    assert(await page.evaluate(() => [
      { stroke: 'red', style: 'opacity:.5' }, { style: 'opacity:.5', stroke: 'red' }
    ].every(attrs => { const n = V.el('line', attrs); return n.style.stroke === 'red' && n.style.opacity === '0.5'; })));
    assert.equal(await page.evaluate(() => V.el('rect', { fill: 'red', style: 'fill:blue;opacity:.5' }).style.fill), 'blue');
    assert(await page.evaluate(() => {
      const node = V.el('p', {}, 'Examples: ', [[V.el('a', { href: '#main' }, 'one')], ['; ', [V.el('a', { href: '#main' }, 'two')]]]);
      return node.textContent === 'Examples: one; two' && node.querySelectorAll('a').length === 2;
    }));
    console.log(`${cases} page/viewport cases passed; SVG style regression checks passed. Screenshots: ${output}`);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
