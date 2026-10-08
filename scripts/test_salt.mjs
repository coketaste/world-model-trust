// Run: node scripts/test_salt.mjs (no npm dependencies).
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { validateMetadata, offset, section, velocityColor, surveyPoints } from '../site/assets/salt-volume.mjs';

const base = new URL('../site/assets/salt/', import.meta.url);
const meta = validateMetadata(JSON.parse(fs.readFileSync(new URL('metadata.json', base))));
for (const [name, details] of Object.entries(meta.files)) {
  const b = fs.readFileSync(new URL(name, base));
  assert.equal(b.length, details.bytes, name);
  assert.equal(createHash('sha256').update(b).digest('hex'), details.sha256, name);
}
// A deliberately non-cubic ramp catches axis swaps, depth reversal and strides.
const shape = [3, 4, 5], ramp = new Uint16Array(60);
for (let x = 0; x < 3; x++) for (let y = 0; y < 4; y++) for (let z = 0; z < 5; z++) ramp[offset(shape, x, y, z)] = 100*x + 10*y + z;
assert.deepEqual([...section(ramp, shape, 0, 2).values].slice(0, 8), [200,210,220,230,201,211,221,231]);
assert.deepEqual([...section(ramp, shape, 1, 3).values].slice(0, 6), [30,130,230,31,131,231]);
assert.deepEqual([...section(ramp, shape, 2, 4).values].slice(0, 6), [4,104,204,14,114,214]);
assert.throws(() => section(ramp, shape, 2, 5));
assert.throws(() => validateMetadata({ ...meta, shape: [3,4,5] }));
assert.deepEqual(velocityColor(1500), [68,1,84]);
assert.deepEqual(velocityColor(4500), [253,231,37]);
const narrow = surveyPoints('narrow', [13.5,13.5]), wide = surveyPoints('wide', [13.5,13.5]);
assert.equal(narrow.flat().length, 90); assert.equal(wide.flat().length, 90);
assert.equal(new Set(narrow[4].map(p => p[1])).size, 1);
assert.equal(new Set(wide[4].map(p => p[0])).size, 1);
assert(narrow.flat().every(p => p[2] === 0));
assert.deepEqual(surveyPoints('none', [13.5,13.5]), []);
const bytes = fs.readFileSync(new URL('velocity.bin', base));
const volume = new Uint16Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 2);
assert(volume.some(v => v === 4482));
assert(volume.every(v => v >= 1400 && v <= 7000));
assert.equal(meta.axes_km[2][0], .3); assert.equal(meta.axes_km[2].at(-1), 3.66);
assert.equal(meta.axes_km[0].at(-1), 13.5);
console.log('Salt asset hashes, volume indexing, slice orientation, colour scale and survey layouts passed.');
