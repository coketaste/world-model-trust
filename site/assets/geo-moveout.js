/* Velocity-depth ambiguity and moveout (pure, node-testable).
   Zero-offset two-way time of a flat reflector at depth z in a medium of velocity v:  t0 = 2 z / v.
   Many (v, z) pairs share the same t0. With source-receiver offset x the time becomes
   t(x) = sqrt(t0^2 + x^2 / v^2): the curvature (moveout) depends on v alone, so wide offsets (aperture) separate the pairs. */
(function (root) {
  const moveout = (t0, v, x) => Math.sqrt(t0 * t0 + (x * x) / (v * v));
  const depth = (t0, v) => (v * t0) / 2;

  /* candidate velocities around a central v: [v(1-spread), v, v(1+spread)] */
  const candidates = (v, spread) => [v * (1 - spread), v, v * (1 + spread)];

  function curves(t0, vs, xmax, n = 41) {
    return vs.map((v) => Array.from({ length: n }, (_, i) => { const x = (xmax * i) / (n - 1); return { x, t: moveout(t0, v, x) }; }));
  }
  /* largest time difference between two velocity candidates over offsets 0..xmax (seconds) */
  const separation = (t0, va, vb, xmax) => Math.abs(moveout(t0, va, xmax) - moveout(t0, vb, xmax));

  root.GeoMoveout = { moveout, depth, candidates, curves, separation };
})(typeof window !== "undefined" ? window : globalThis);
