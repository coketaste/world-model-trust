// Node tests for the pure compute functions behind the geophysics primer widgets.
// Run: node scripts/test_primer.js   (no dependencies)
const path = require("path");
const A = (f) => require(path.join(__dirname, "..", "site", "assets", f));
A("geo-tomography.js"); A("geo-migration.js"); A("geo-moveout.js"); A("geo-multiples.js");
const T = globalThis.GeoTomo, M = globalThis.GeoMigration, O = globalThis.GeoMoveout, G = globalThis.GeoMultiples;

let passed = 0, failed = 0;
function test(name, fn) { try { fn(); passed++; console.log("ok   " + name); } catch (e) { failed++; console.log("FAIL " + name + "\n     " + e.message); } }
const ok = (c, msg) => { if (!c) throw new Error(msg); };
const near = (a, b, tol, msg) => ok(Math.abs(a - b) <= tol, `${msg || ""} expected ${b} +- ${tol}, got ${a}`);

/* ---------------- tomography ---------------- */
test("tomography: seeded runs are deterministic", () => {
  const a = T.run({ seed: 7 }), b = T.run({ seed: 7 }), c = T.run({ seed: 8, noise: 0.05 });
  ok(a.err === b.err, "same seed must give the same error");
  ok(a.err !== c.err, "a different seed and noise should change the error");
});
test("tomography: forward model reproduces a known path length", () => {
  // one horizontal ray through the middle of the square crosses N cells of width 1/N: total length 1
  const rows = T.pathLengths([{ x0: 0, y0: 0.5, x1: 1, y1: 0.5 }]);
  near(rows[0].len.reduce((a, b) => a + b, 0), 1, 1e-9, "path length");
  ok(rows[0].idx.length <= T.N + 1, "a horizontal ray should touch about N cells");
});
test("tomography: wider aperture reconstructs better (error falls)", () => {
  const e = [10, 30, 60, 90].map((aperture) => T.run({ aperture }).err);
  for (let i = 1; i < e.length; i++) ok(e[i] < e[i - 1], `error should fall with aperture: ${e.map((x) => x.toFixed(3)).join(", ")}`);
});
test("tomography: more directions reconstruct better", () => {
  ok(T.run({ nAngles: 20 }).err < T.run({ nAngles: 4 }).err, "20 directions should beat 4");
});
test("tomography: limited aperture smears along the ray direction (anisotropic point spread)", () => {
  const lim = T.psf({ aperture: 10 }), full = T.psf({ aperture: 90 });
  ok(lim.sx / lim.sy > 2, `limited aperture should smear mostly along x, ratio ${(lim.sx / lim.sy).toFixed(2)}`);
  near(full.sx / full.sy, 1, 0.1, "full aperture is isotropic");
});
test("tomography: noise-free data are matched better than the truth is recovered (honest, not converged)", () => {
  const r = T.run({ noise: 0, aperture: 90 });
  ok(r.err > 0.1, `fixed-iteration SIRT should not recover the model perfectly (error ${r.err.toFixed(3)})`);
});
test("tomography: illumination is non-negative and positive where rays pass", () => {
  const r = T.run({}); ok(Math.min(...r.illum) >= 0 && Math.max(...r.illum) > 0, "illumination range");
});

/* ---------------- migration ---------------- */
const v = 2.0, data = M.synthesize(M.scatterers(false), v);
test("migration: correct velocity focuses at the true diffractor", () => {
  const p = M.peak(M.migrate(data, v));
  near(p.x, 1.0, M.dx, "x position"); near(p.z, 0.8, M.dz, "z position");
  ok(p.amp > 0.8, `peak amplitude ${p.amp.toFixed(3)} should be close to 1`);
});
test("migration: wrong velocities lose most of the focus", () => {
  const best = M.peak(M.migrate(data, v)).amp;
  for (const vm of [1.5, 1.7, 2.3, 2.7]) {
    const a = Math.abs(M.peak(M.migrate(data, vm)).amp);
    ok(a < 0.55 * best, `vm=${vm}: amplitude ${a.toFixed(3)} should be well below ${best.toFixed(3)}`);
  }
});
test("migration: the diffraction is a hyperbola with its apex above the scatterer", () => {
  const apex = Math.max(...data[(M.NX - 1) / 2]); ok(apex > 0.9, "central trace should hold the strongest, unit-amplitude event");
  let tApex = 0, best = -1; data[(M.NX - 1) / 2].forEach((a, s) => { if (a > best) { best = a; tApex = s * M.DT; } });
  near(tApex, (2 * 0.8) / v, 2 * M.DT, "apex time = 2 z0 / v");
});
test("migration: a dipping reflector migrates without breaking the point focus", () => {
  const d2 = M.synthesize(M.scatterers(true), v), img = M.migrate(d2, v);
  ok(Math.abs(M.peak(img).amp) > 0.3, "image should still contain strong focused energy");
});

/* ---------------- moveout ---------------- */
test("moveout: curves with the same t0 coincide at zero offset and differ at wide offsets", () => {
  const vs = O.candidates(2.0, 0.3);
  for (const vv of vs) near(O.moveout(1.0, vv, 0), 1.0, 1e-12, "zero offset");
  ok(O.separation(1.0, vs[0], vs[2], 0.2) < O.separation(1.0, vs[0], vs[2], 2.0), "separation grows with offset");
  ok(O.separation(1.0, vs[0], vs[2], 2.0) > 0.2, "wide offsets should separate by well over 0.2 s here");
});
test("moveout: depth = v t0 / 2 and slower means shallower for the same time", () => {
  near(O.depth(1.0, 2.0), 1.0, 1e-12); ok(O.depth(1.0, 1.5) < O.depth(1.0, 2.5), "slower should be shallower");
});
test("moveout: matches t^2 = t0^2 + x^2/v^2", () => {
  const t = O.moveout(1.0, 2.0, 1.5); near(t * t, 1 + (1.5 * 1.5) / 4, 1e-12);
});

/* ---------------- multiples ---------------- */
test("multiples: point P has no primary coverage from any surface shot", () => { near(G.primaryCoverage(G.P.x), 0, 0, "coverage at P"); });
test("multiples: the shadow zone on the reflector contains P and is not the whole reflector", () => {
  const z = G.shadowZone(); ok(z.length >= 1, "a shadow zone exists");
  ok(z.some(([a, b]) => a <= G.P.x && G.P.x <= b), "P is inside it"); ok(z.every(([a, b]) => b - a < 0.9), "reflector is not entirely dark");
});
test("multiples: the internal multiple reaches P without crossing the obstacle", () => {
  ok(!G.multipleBlocked(), "no segment of the multiple should cross the obstacle");
  const [S, A, C, P] = G.multiplePath();
  near(C.x - A.x, P.x - C.x, 1e-9, "mirror law: equal horizontal steps up and back down"); near(A.z - C.z, P.z - C.z, 1e-9, "vertical legs are equal");
});
test("multiples: straight rays through the obstacle are blocked, ones beside it are not", () => {
  ok(G.blocked({ x: 0.5, z: 0 }, { x: 0.5, z: 1 }), "vertical through the middle"); ok(!G.blocked({ x: 0.05, z: 0 }, { x: 0.05, z: 1 }), "vertical beside it");
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
