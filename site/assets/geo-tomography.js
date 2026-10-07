/* Straight-ray tomography toy (pure, node-testable).
   Medium: N x N cells on the unit square holding a "slowness perturbation" in [0, 1].
   Acquisition: parallel-beam rays at several angles; the aperture controls the largest angle away from horizontal
   (small aperture = nearly horizontal rays only, like a cross-well survey; 90 = every direction).
   Data: d_i = sum_j L_ij m_j + noise.  Illumination: diag(J^T J)_j = sum_i L_ij^2 (J = L).
   Reconstruction: SIRT, a FIXED number of iterations from a zero start, so it is honest (not converged, not tuned). */
(function (root) {
  const N = 24;

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  function gauss(rng) { let u = 0, v = 0; while (u === 0) u = rng(); v = rng(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }

  /* true model: a round anomaly plus a small square, so there is something large and something small to resolve */
  function trueModel() {
    const m = new Float64Array(N * N);
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      const x = (i + 0.5) / N, y = (j + 0.5) / N;
      let v = 0;
      if ((x - 0.38) ** 2 + (y - 0.42) ** 2 < 0.17 ** 2) v = 1;
      if (x > 0.68 && x < 0.84 && y > 0.58 && y < 0.74) v = 0.7;
      m[j * N + i] = v;
    }
    return m;
  }

  /* rays: array of {x0,y0,x1,y1} clipped to the unit square. nAngles directions between -aperture and +aperture degrees
     (measured from the x axis), nOffsets parallel rays per direction. */
  function makeRays(apertureDeg, nAngles, nOffsets) {
    const rays = [];
    for (let k = 0; k < nAngles; k++) {
      const th = ((-apertureDeg + (k + 0.5) * (2 * apertureDeg) / nAngles) * Math.PI) / 180, dx = Math.cos(th), dy = Math.sin(th);
      // direction (dx, dy); offset along the normal (-dy, dx) through the centre of the square; cover the full diagonal
      for (let o = 0; o < nOffsets; o++) {
        const s = ((o + 0.5) / nOffsets - 0.5) * 1.5, cx = 0.5 - dy * s, cy = 0.5 + dx * s;
        const seg = clip(cx, cy, dx, dy);
        if (seg) rays.push(seg);
      }
    }
    return rays;
  }
  function clip(cx, cy, dx, dy) { // intersect the infinite line with the unit square
    let t0 = -2, t1 = 2;
    for (const [p, d] of [[cx, dx], [cy, dy]]) {
      if (Math.abs(d) < 1e-12) { if (p < 0 || p > 1) return null; continue; }
      let a = (0 - p) / d, b = (1 - p) / d; if (a > b) [a, b] = [b, a];
      t0 = Math.max(t0, a); t1 = Math.min(t1, b);
    }
    if (t1 - t0 < 1e-6) return null;
    return { x0: cx + t0 * dx, y0: cy + t0 * dy, x1: cx + t1 * dx, y1: cy + t1 * dy };
  }

  /* path length of each ray in each cell (dense sampling; sparse rows as {idx:Int32Array, len:Float64Array}) */
  function pathLengths(rays) {
    const rows = [];
    for (const r of rays) {
      const len = Math.hypot(r.x1 - r.x0, r.y1 - r.y0), steps = Math.max(2, Math.ceil(len * N * 12)), ds = len / steps, acc = new Map();
      for (let s = 0; s < steps; s++) {
        const t = (s + 0.5) / steps, x = r.x0 + t * (r.x1 - r.x0), y = r.y0 + t * (r.y1 - r.y0);
        const i = Math.min(N - 1, Math.max(0, Math.floor(x * N))), j = Math.min(N - 1, Math.max(0, Math.floor(y * N))), c = j * N + i;
        acc.set(c, (acc.get(c) || 0) + ds);
      }
      rows.push({ idx: Int32Array.from(acc.keys()), len: Float64Array.from(acc.values()) });
    }
    return rows;
  }

  function forward(rows, m) { return rows.map((r) => { let s = 0; for (let k = 0; k < r.idx.length; k++) s += r.len[k] * m[r.idx[k]]; return s; }); }

  function illumination(rows) { const I = new Float64Array(N * N); for (const r of rows) for (let k = 0; k < r.idx.length; k++) I[r.idx[k]] += r.len[k] * r.len[k]; return I; }

  function sirt(rows, d, iters) {
    const m = new Float64Array(N * N), rs = rows.map((r) => r.len.reduce((a, b) => a + b, 0) || 1), cs = new Float64Array(N * N);
    for (const r of rows) for (let k = 0; k < r.idx.length; k++) cs[r.idx[k]] += r.len[k];
    for (let it = 0; it < iters; it++) {
      const upd = new Float64Array(N * N);
      rows.forEach((r, i) => {
        let pred = 0; for (let k = 0; k < r.idx.length; k++) pred += r.len[k] * m[r.idx[k]];
        const res = (d[i] - pred) / rs[i];
        for (let k = 0; k < r.idx.length; k++) upd[r.idx[k]] += r.len[k] * res;
      });
      for (let c = 0; c < N * N; c++) if (cs[c] > 0) m[c] += upd[c] / cs[c];
    }
    return m;
  }

  function relError(m, truth) { let a = 0, b = 0; for (let c = 0; c < truth.length; c++) { a += (m[c] - truth[c]) ** 2; b += truth[c] ** 2; } return Math.sqrt(a / b); }

  /* one full experiment */
  function run({ aperture = 90, nAngles = 12, nOffsets = 28, noise = 0.02, iters = 40, seed = 1 } = {}) {
    const truth = trueModel(), rays = makeRays(aperture, nAngles, nOffsets), rows = pathLengths(rays), rng = mulberry32(seed);
    const clean = forward(rows, truth), d = clean.map((v) => v + noise * gauss(rng));
    const rec = sirt(rows, d, iters), I = illumination(rows);
    const imax = Math.max(...I);
    let unlit = 0; for (let c = 0; c < N * N; c++) if (I[c] < 0.02 * imax) unlit++;
    return { N, truth, rays, nRays: rays.length, illum: I, recon: rec, err: relError(rec, truth), unlitFraction: unlit / (N * N) };
  }

  /* point-spread function: image a single bright cell with the same acquisition and the same SIRT; returns the recon and
     its spread along x and y (standard deviations in cells), which shows smearing along the directions the rays never cross */
  function psf({ aperture = 90, nAngles = 12, nOffsets = 28, iters = 40, cell = [12, 12] } = {}) {
    const rows = pathLengths(makeRays(aperture, nAngles, nOffsets)), spike = new Float64Array(N * N);
    spike[cell[1] * N + cell[0]] = 1;
    const rec = sirt(rows, forward(rows, spike), iters);
    let w = 0, mx = 0, my = 0;
    for (let c = 0; c < N * N; c++) { const v = Math.max(0, rec[c]); w += v; mx += v * (c % N); my += v * Math.floor(c / N); }
    mx /= w; my /= w;
    let vx = 0, vy = 0;
    for (let c = 0; c < N * N; c++) { const v = Math.max(0, rec[c]); vx += v * ((c % N) - mx) ** 2; vy += v * (Math.floor(c / N) - my) ** 2; }
    return { N, recon: rec, sx: Math.sqrt(vx / w), sy: Math.sqrt(vy / w), cell };
  }

  root.GeoTomo = { N, mulberry32, trueModel, makeRays, pathLengths, forward, illumination, sirt, relError, run, psf };
})(typeof window !== "undefined" ? window : globalThis);
