// Shared, dependency-free volume indexing and validation (also used by tests).
export function offset(shape, x, y, z) {
  return (x * shape[1] + y) * shape[2] + z;
}

export function validateMetadata(m) {
  if (m.schema !== 1 || !Array.isArray(m.shape) || m.shape.length !== 3 ||
      !m.shape.every(n => Number.isInteger(n) && n >= 2 && n <= 1024)) throw new Error('Unsupported salt volume dimensions');
  if (!Array.isArray(m.axes_km) || m.axes_km.length !== 3) throw new Error('Missing model axes');
  m.axes_km.forEach((a, i) => {
    if (a.length !== m.shape[i] || !a.every((v, j) => Number.isFinite(v) && (j === 0 || v > a[j - 1]))) throw new Error('Invalid model coordinates');
  });
  for (const name of ['velocity.bin', 'vertices.bin', 'triangles.bin']) {
    if (!Number.isInteger(m.files?.[name]?.bytes) || m.files[name].bytes <= 0) throw new Error('Missing asset size');
  }
  if (m.files['velocity.bin'].bytes !== m.shape.reduce((a, b) => a * b, 2)) throw new Error('Volume size does not match dimensions');
  return m;
}

// Texture columns/rows follow the remaining model axes in ascending order.
export function section(volume, shape, axis, index) {
  if (![0, 1, 2].includes(axis) || !Number.isInteger(index) || index < 0 || index >= shape[axis]) throw new Error('Slice outside model');
  const other = [0, 1, 2].filter(a => a !== axis);
  const width = shape[other[0]], height = shape[other[1]];
  const values = new Uint16Array(width * height), p = [0, 0, 0];
  p[axis] = index;
  for (let j = 0; j < height; j++) {
    p[other[1]] = j;
    for (let i = 0; i < width; i++) {
      p[other[0]] = i;
      values[j * width + i] = volume[offset(shape, ...p)];
    }
  }
  return { width, height, values, other };
}

const STOPS = [[68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37]];
export function velocityColor(v) {
  const t = Math.max(0, Math.min(1, (v - 1500) / 3000)) * 4;
  const i = Math.min(3, Math.floor(t)), f = t - i;
  return STOPS[i].map((c, k) => Math.round(c * (1 - f) + STOPS[i + 1][k] * f));
}

export function surveyPoints(kind, extent) {
  if (kind === 'none') return [];
  const [xmax, ymax] = extent, lines = [];
  // Same marker count in both layouts: contrast directions, not sample count.
  for (let line = 0; line < 6; line++) {
    const points = [];
    for (let i = 0; i < 15; i++) {
      const along = .08 + .84 * i / 14, across = .2 + .6 * line / 5;
      const cross = kind === 'wide' && line >= 3;
      points.push(cross ? [across * xmax, along * ymax, 0] : [along * xmax, across * ymax, 0]);
    }
    lines.push(points);
  }
  return lines;
}
