/* Zero-offset Kirchhoff-style migration toy (pure, node-testable).
   Units: km, s, km/s.  Constant true velocity.  Scatterers diffract energy that arrives at receiver x_r at
   t = 2 sqrt((x_r - x0)^2 + z0^2) / v   (a hyperbola in the data).
   Migration puts that energy back: image(x, z) = sum over traces of data(x_r, t = 2 sqrt((x - x_r)^2 + z^2) / v_m).
   If v_m equals the true v, all the contributions line up at the scatterer and add coherently; otherwise they do not. */
(function (root) {
  const X = 2.0, NX = 41, DT = 0.01, NT = 201, FPEAK = 10, ZMAX = 1.8, NZ = 37;
  const dx = X / (NX - 1), dz = ZMAX / (NZ - 1);

  function ricker(t) { const a = Math.PI * FPEAK * t; return (1 - 2 * a * a) * Math.exp(-a * a); }

  /* a point diffractor plus (optionally) a dipping reflector made of many closely spaced scatterers */
  function scatterers(withReflector) {
    const list = [{ x: 1.0, z: 0.8, a: 1 }];
    if (withReflector) {
      const x0 = 0.15, z0 = 0.35, x1 = 0.75, z1 = 0.95, n = 31;
      for (let k = 0; k < n; k++) { const f = k / (n - 1); list.push({ x: x0 + f * (x1 - x0), z: z0 + f * (z1 - z0), a: 0.12 }); }
    }
    return list;
  }

  /* data[r][s]: trace r (receiver at r*dx), time sample s (s*DT) */
  function synthesize(scat, v) {
    const data = [];
    for (let r = 0; r < NX; r++) {
      const tr = new Float64Array(NT), xr = r * dx;
      for (const p of scat) {
        const t0 = (2 * Math.hypot(xr - p.x, p.z)) / v;
        const s0 = Math.max(0, Math.floor((t0 - 0.12) / DT)), s1 = Math.min(NT - 1, Math.ceil((t0 + 0.12) / DT));
        for (let s = s0; s <= s1; s++) tr[s] += p.a * ricker(s * DT - t0);
      }
      data.push(tr);
    }
    return data;
  }

  function sample(tr, t) { const f = t / DT, i = Math.floor(f); if (i < 0 || i >= NT - 1) return 0; const w = f - i; return tr[i] * (1 - w) + tr[i + 1] * w; }

  /* image[iz][ix] */
  function migrate(data, vm) {
    const img = [];
    for (let iz = 0; iz < NZ; iz++) {
      const row = new Float64Array(NX), z = iz * dz;
      for (let ix = 0; ix < NX; ix++) {
        const x = ix * dx; let sum = 0;
        for (let r = 0; r < NX; r++) sum += sample(data[r], (2 * Math.hypot(x - r * dx, z)) / vm);
        row[ix] = sum / NX;
      }
      img.push(row);
    }
    return img;
  }

  function peak(img) {
    let best = 0, bx = 0, bz = 0;
    for (let iz = 0; iz < NZ; iz++) for (let ix = 0; ix < NX; ix++) if (Math.abs(img[iz][ix]) > Math.abs(best)) { best = img[iz][ix]; bx = ix * dx; bz = iz * dz; }
    return { amp: best, x: bx, z: bz };
  }

  root.GeoMigration = { X, NX, NT, DT, NZ, ZMAX, dx, dz, FPEAK, ricker, scatterers, synthesize, migrate, peak };
})(typeof window !== "undefined" ? window : globalThis);
