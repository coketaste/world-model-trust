/* Schematic geometry for primaries, multiples and a shadow zone (pure, node-testable). NOT a wave simulation.
   Coordinates: x across (0..1), z down (0..1). Surface at z = 0, reflector at z = 1.
   An obstacle (think of a high-contrast body) sits between them. Straight-ray primaries from surface shots to a
   point P on the reflector are blocked by it; an internal multiple (reflector -> underside of the obstacle -> reflector)
   reaches P from the side. */
(function (root) {
  const OBSTACLE = { x0: 0.15, x1: 0.85, z0: 0.25, z1: 0.4 };
  const REFLECTOR_Z = 1.0;
  const P = { x: 0.5, z: 1.0 };
  const SHOT = { x: 0.05, z: 0 };
  const A = { x: 0.2, z: 1.0 };   // where the primary from SHOT meets the reflector
  const C = { x: 0.35, z: OBSTACLE.z1 }; // underside of the obstacle
  // mirror law on a horizontal interface: A -> C goes up-right by (0.15, -0.6); C -> P goes down-right by (0.15, +0.6)

  /* does the open segment p -> q cross the obstacle's interior? (slab method, shrunk slightly so grazing the underside is allowed) */
  function blocked(p, q, o = OBSTACLE, eps = 1e-6) {
    const dx = q.x - p.x, dz = q.z - p.z;
    let t0 = 0, t1 = 1;
    for (const [p0, d, lo, hi] of [[p.x, dx, o.x0 + eps, o.x1 - eps], [p.z, dz, o.z0 + eps, o.z1 - eps]]) {
      if (Math.abs(d) < 1e-12) { if (p0 < lo || p0 > hi) return false; continue; }
      let a = (lo - p0) / d, b = (hi - p0) / d; if (a > b) [a, b] = [b, a];
      t0 = Math.max(t0, a); t1 = Math.min(t1, b);
      if (t0 >= t1) return false;
    }
    return t1 > t0;
  }

  /* fraction of surface shots (x in [0,1]) from which a straight primary reaches point (x, REFLECTOR_Z) */
  function primaryCoverage(x, nShots = 101) {
    let ok = 0;
    for (let i = 0; i < nShots; i++) if (!blocked({ x: i / (nShots - 1), z: 0 }, { x, z: REFLECTOR_Z })) ok++;
    return ok / nShots;
  }
  /* reflector x positions with no primary coverage at all (the shadow zone on the reflector), as a list of [x0,x1] */
  function shadowZone(n = 201) {
    const zone = []; let start = null;
    for (let i = 0; i < n; i++) {
      const x = i / (n - 1), dark = primaryCoverage(x, 61) === 0;
      if (dark && start === null) start = x;
      if (!dark && start !== null) { zone.push([start, (i - 1) / (n - 1)]); start = null; }
    }
    if (start !== null) zone.push([start, 1]);
    return zone;
  }
  const multiplePath = () => [SHOT, A, C, P];
  const multipleBlocked = () => { const p = multiplePath(); for (let i = 0; i < p.length - 1; i++) if (blocked(p[i], p[i + 1])) return true; return false; };

  root.GeoMultiples = { OBSTACLE, REFLECTOR_Z, P, SHOT, A, C, blocked, primaryCoverage, shadowZone, multiplePath, multipleBlocked };
})(typeof window !== "undefined" ? window : globalThis);
