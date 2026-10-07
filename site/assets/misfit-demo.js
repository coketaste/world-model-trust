/* 1D cycle-skipping toy: L2 misfit vs Wasserstein-2 misfit between a pattern and a shifted copy (pure, node-testable). */
(function (root) {
  const N = 2800, X0 = -14, X1 = 14, dx = (X1 - X0) / (N - 1);
  const xs = Array.from({ length: N }, (_, i) => X0 + i * dx);

  /* pattern: several narrow bumps (a repeated "event"), positive so it is a valid density for optimal transport */
  function pattern(shift, width) {
    const centres = [-3, -1.2, 0.6, 2.4].map((c) => c + shift);
    return xs.map((x) => centres.reduce((s, c, i) => s + (1 + 0.3 * i) * Math.exp(-0.5 * ((x - c) / width) ** 2), 0));
  }
  const norm = (p) => { const s = p.reduce((a, b) => a + b, 0) * dx; return p.map((v) => v / s); };

  const l2 = (p, q) => p.reduce((s, v, i) => s + (v - q[i]) ** 2, 0) * dx;

  function quantiles(p, M = 800) {
    const cdf = []; let c = 0;
    for (let i = 0; i < p.length; i++) { c += p[i] * dx; cdf.push(c); }
    const out = []; let j = 0;
    for (let k = 0; k < M; k++) {
      const u = (k + 0.5) / M;
      while (j < cdf.length - 1 && cdf[j] < u) j++;
      out.push(xs[j]);
    }
    return out;
  }
  const w2 = (p, q) => { const a = quantiles(p), b = quantiles(q); return a.reduce((s, v, i) => s + (v - b[i]) ** 2, 0) / a.length; };

  /* misfit curves over shifts in [-S, S] */
  function curves(width, S = 5, n = 81) {
    const base = norm(pattern(0, width)), out = [];
    for (let i = 0; i < n; i++) {
      const s = -S + (2 * S * i) / (n - 1), q = norm(pattern(s, width));
      out.push({ shift: s, l2: l2(base, q), w2: w2(base, q) });
    }
    const mx = (k) => Math.max(...out.map((o) => o[k]));
    const m1 = mx("l2"), m2 = mx("w2");
    return out.map((o) => ({ shift: o.shift, l2: o.l2 / m1, w2: o.w2 / m2 }));
  }
  /* number of local minima of a sampled curve (counting a flat-bottom as one) */
  function localMinima(vals) {
    let c = 0;
    for (let i = 1; i < vals.length - 1; i++) if (vals[i] < vals[i - 1] - 1e-9 && vals[i] <= vals[i + 1] + 1e-12) c++;
    return c;
  }
  root.MisfitDemo = { pattern, norm, l2, w2, curves, localMinima };
})(typeof window !== "undefined" ? window : globalThis);
