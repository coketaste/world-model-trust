/* Primer widgets, part A: shared helpers + tomography + migration. Needs viz.js (V.el). No innerHTML anywhere. */
(function (root) {
  const E = V.el;
  const mix = (cssVar, pct) => `color-mix(in srgb, var(${cssVar}) ${Math.max(0, Math.min(100, pct)).toFixed(0)}%, var(--surface))`;

  /* labelled range input; returns {node, get, set} and calls onInput(value) */
  function slider(label, { min, max, step, value, unit = "", fmt = (v) => v }, onInput) {
    const out = E("span", { class: "val" }, fmt(value) + unit);
    const inp = E("input", { type: "range", min, max, step, value, "aria-label": label });
    inp.addEventListener("input", () => { out.textContent = fmt(+inp.value) + unit; onInput(+inp.value); });
    return { node: E("label", {}, E("span", {}, label + " ", out), inp), get: () => +inp.value };
  }

  /* one illustrated widget: title, one-sentence idea, controls, picture(s), readout, try-this list, why-it-matters line */
  function widget(id, { title, idea, controls, body, readout, tryThis, why, caption }) {
    return E("section", { class: "wg card", id, "aria-labelledby": id + "-h" },
      E("h3", { id: id + "-h" }, title),
      E("p", { class: "wg-idea" }, idea),
      controls && controls.length ? E("div", { class: "filters wg-controls" }, controls) : null,
      body,
      readout ? E("p", { class: "wg-readout", role: "status", "aria-live": "polite" }, readout) : null,
      caption ? E("p", { class: "small muted wg-caption" }, caption) : null,
      E("div", { class: "grid g2 wg-notes" },
        E("div", {}, E("h4", {}, "Try this"), E("ul", { class: "small" }, tryThis.map((t) => E("li", {}, t)))),
        E("div", {}, E("h4", {}, "Why it matters for spatial AI and robots"), E("p", { class: "small" }, why))));
  }

  function grid(n, host, className) {
    const svg = E("svg", { viewBox: `0 0 ${n} ${n}`, class: "wg-grid " + (className || ""), role: "img", "shape-rendering": "crispEdges" }), cells = [];
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) { const r = E("rect", { x: i, y: j, width: 1.02, height: 1.02 }); svg.append(r); cells.push(r); }
    host.append(svg); return { svg, cells };
  }

  /* ---------- 1. tomography and illumination ---------- */
  function tomography(mount) {
    const T = GeoTomo, N = T.N, st = { aperture: 90, nAngles: 12, noise: 0.02 };
    const mk = (cap, label) => { const fig = E("figure", { class: "wg-panel" }); const g = grid(N, fig); fig.append(E("figcaption", {}, E("b", {}, cap), " ", label)); return { fig, ...g }; };
    const pTrue = mk("A. True model.", "A round anomaly and a small square."), pIll = mk("B. Illumination.", "How strongly the rays constrain each cell (diagonal of JᵀJ)."),
      pRec = mk("C. Image from the rays.", "Reconstruction after a fixed 40 iterations."), pPsf = mk("D. Point spread.", "How the same survey images one single bright cell.");
    const rayLayer = E("g", { style: "pointer-events:none" }); pTrue.svg.append(rayLayer);
    const readout = document.createTextNode("");
    const panels = E("div", { class: "wg-panels" }, pTrue.fig, pIll.fig, pRec.fig, pPsf.fig);
    const paint = (cells, vals, scale) => cells.forEach((r, c) => r.style.setProperty("fill", mix("--s1", (Math.max(0, Math.min(1, vals[c] / scale))) * 100)));
    function update() {
      const res = T.run({ aperture: st.aperture, nAngles: st.nAngles, noise: st.noise }), ps = T.psf({ aperture: st.aperture, nAngles: st.nAngles });
      paint(pTrue.cells, res.truth, 1);
      const imax = Math.max(...res.illum); paint(pIll.cells, res.illum, imax);
      paint(pRec.cells, res.recon, 1);
      const pmax = Math.max(...ps.recon); paint(pPsf.cells, ps.recon, pmax);
      const step = Math.max(1, Math.floor(res.rays.length / 36));
      rayLayer.replaceChildren(...res.rays.filter((_, i) => i % step === 0).map((r) => E("line", { x1: r.x0 * N, y1: r.y0 * N, x2: r.x1 * N, y2: r.y1 * N, stroke: "var(--ink2)", "stroke-width": 0.08, style: "opacity:.55" })));
      readout.textContent = `Aperture ±${st.aperture}°, ${st.nAngles} directions: ${res.nRays} rays. Reconstruction error ${(res.err * 100).toFixed(0)}% of the model's size. A single point is smeared to ${ps.sx.toFixed(1)} cells wide and ${ps.sy.toFixed(1)} cells tall (a 1:1 ratio means no preferred smear direction; here ${(ps.sx / ps.sy).toFixed(1)}:1).`;
    }
    const controls = [
      slider("Aperture: largest ray angle from horizontal", { min: 10, max: 90, step: 5, value: st.aperture, unit: "°" }, (v) => { st.aperture = v; update(); }).node,
      slider("Number of ray directions", { min: 4, max: 24, step: 2, value: st.nAngles }, (v) => { st.nAngles = v; update(); }).node,
      slider("Noise in the measurements", { min: 0, max: 0.1, step: 0.01, value: st.noise, fmt: (v) => v.toFixed(2) }, (v) => { st.noise = v; update(); }).node];
    const w = widget("w-tomo", {
      title: "Tomography and illumination: what do the rays actually constrain?",
      idea: "Straight rays cross a medium and each one measures a total along its path. Where rays cross from many directions, the image is sharp. Where they cross from only a few, it smears along those directions.",
      controls, body: panels, readout,
      caption: "Stronger colour means a larger value in every panel. This is a deliberately simple straight-ray model with a fixed number of reconstruction iterations (not tuned, so the error stays visibly above zero). Real seismic tomography uses bent rays or wavefields, but the lesson about angular coverage is the same.",
      tryThis: ["Drag the aperture down to 10°. Panel B still looks evenly lit, yet panel D shows the point smeared along the ray direction. Illumination alone does not show missing directions; the point-spread function does.", "Raise the aperture back to 90° and watch the error and the smear shrink.", "Add noise: the error rises, and the smear is not the only problem."],
      why: "A camera view is a bundle of rays from one place. Many photos from similar places leave the same missing directions, so some depth information stays unconstrained. This is why a per-splat illumination map helps, and why resolution analysis (the point-spread function) says more than a coverage count."
    });
    mount.append(w); update();
  }

  /* ---------- 2. migration ---------- */
  function migration(mount) {
    const M = GeoMigration, st = { vm: 2.0, refl: false }, TRUEV = 2.0;
    let data = M.synthesize(M.scatterers(st.refl), TRUEV), best = M.peak(M.migrate(data, TRUEV)).amp;
    const W = 340, H = 300, padL = 34, padT = 8, plotW = W - padL - 8, plotH = H - padT - 26;
    const dsvg = E("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart wg-svg", role: "img", "aria-label": "Zero-offset data: wiggle traces with a diffraction hyperbola" });
    const isvg = E("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart wg-svg", role: "img", "aria-label": "Migrated image: energy focuses at the true diffractor when the velocity is right" });
    const sxD = (x) => padL + (x / M.X) * plotW, syD = (t) => padT + (t / ((M.NT - 1) * M.DT)) * plotH, syI = (z) => padT + (z / M.ZMAX) * plotH;
    // axes text
    const axes = (svg, xl, yl, yticks, yfun) => { svg.append(E("text", { x: padL + plotW / 2, y: H - 4, "text-anchor": "middle" }, xl), E("text", { x: 10, y: padT + plotH / 2, "text-anchor": "middle", transform: `rotate(-90 10 ${padT + plotH / 2})` }, yl)); yticks.forEach((t) => svg.append(E("text", { x: padL - 4, y: yfun(t) + 4, "text-anchor": "end" }, String(t)))); [0, 1, 2].forEach((x) => svg.append(E("text", { x: sxD(x), y: padT + plotH + 14, "text-anchor": "middle" }, String(x)))); svg.append(E("rect", { x: padL, y: padT, width: plotW, height: plotH, fill: "none", stroke: "var(--axis)", "stroke-width": 1 })); };
    axes(dsvg, "position along the line (km)", "two-way time (s)", [0, 0.5, 1, 1.5, 2], syD); axes(isvg, "position along the line (km)", "depth (km)", [0, 0.5, 1, 1.5], syI);
    const traceLayer = E("g"), hyp = E("polyline", { fill: "none", stroke: "var(--s3)", "stroke-width": 1.5 });
    dsvg.append(traceLayer, hyp);
    const cells = [], imgLayer = E("g");
    const cw = plotW / M.NX, ch = plotH / M.NZ;
    for (let iz = 0; iz < M.NZ; iz++) for (let ix = 0; ix < M.NX; ix++) { const r = E("rect", { x: padL + ix * cw - cw / 2, y: padT + iz * ch - ch / 2, width: cw + 0.4, height: ch + 0.4 }); imgLayer.append(r); cells.push(r); }
    const truth = E("circle", { cx: sxD(1.0), cy: syI(0.8), r: 7, fill: "none", stroke: "var(--ink)", "stroke-width": 1.5 });
    isvg.append(imgLayer, truth);
    const readout = document.createTextNode("");
    function drawData() {
      const amp = M.dx * plotW / M.X * 1.6;
      traceLayer.replaceChildren(...data.map((tr, r) => E("polyline", { fill: "none", stroke: "var(--ink2)", "stroke-width": 0.8, points: Array.from(tr).map((a, s) => `${(sxD(r * M.dx) + a * amp).toFixed(1)},${syD(s * M.DT).toFixed(1)}`).join(" ") })));
      hyp.setAttribute("points", Array.from({ length: 41 }, (_, i) => { const x = (M.X * i) / 40; return `${sxD(x).toFixed(1)},${syD((2 * Math.hypot(x - 1.0, 0.8)) / TRUEV).toFixed(1)}`; }).join(" "));
    }
    function update() {
      const img = M.migrate(data, st.vm), pk = M.peak(img);
      for (let iz = 0; iz < M.NZ; iz++) for (let ix = 0; ix < M.NX; ix++) { const a = img[iz][ix] / best; cells[iz * M.NX + ix].style.setProperty("fill", a >= 0 ? mix("--s1", a * 100) : mix("--s2", -a * 100)); }
      readout.textContent = `True velocity ${TRUEV.toFixed(1)} km/s, migration velocity ${st.vm.toFixed(2)} km/s. Strongest point in the image: ${(Math.abs(pk.amp) / Math.abs(best) * 100).toFixed(0)}% of the best possible focus, at ${pk.x.toFixed(2)} km across and ${pk.z.toFixed(2)} km deep (the true diffractor is at 1.00 and 0.80).` + (st.refl ? " With the reflector switched on, the strongest point can lie on the reflector instead." : "");
    }
    const cb = E("input", { type: "checkbox", "aria-label": "Add a dipping reflector" }); cb.addEventListener("change", () => { st.refl = cb.checked; data = M.synthesize(M.scatterers(st.refl), TRUEV); best = M.peak(M.migrate(data, TRUEV)).amp; drawData(); update(); });
    const controls = [slider("Migration velocity", { min: 1.4, max: 3.0, step: 0.05, value: st.vm, unit: " km/s", fmt: (v) => v.toFixed(2) }, (v) => { st.vm = v; update(); }).node, E("label", {}, E("span", {}, "Also add a dipping reflector "), cb)];
    const legend = E("div", { class: "legend" }, E("span", {}, E("i", { style: "background:var(--s3)" }), "diffraction hyperbola (computed)"), E("span", {}, E("i", { style: "background:var(--s1)" }), "positive amplitude"), E("span", {}, E("i", { style: "background:var(--s2)" }), "negative amplitude"), E("span", {}, E("i", { class: "dot", style: "background:transparent;border:2px solid var(--ink)" }), "true diffractor position"));
    const body = E("div", {}, legend, E("div", { class: "wg-panels two" }, E("figure", { class: "wg-panel" }, dsvg, E("figcaption", {}, E("b", {}, "Data."), " Each trace is what one receiver records: the diffractor appears as a curve (a hyperbola).")), E("figure", { class: "wg-panel" }, isvg, E("figcaption", {}, E("b", {}, "Migrated image."), " Each image point sums the data along the curve it would have produced."))));
    mount.append(widget("w-migration", {
      title: "Migration: put the energy back where it came from",
      idea: "A buried point scatters waves, so a receiver line records it as a curve. Migration sums the data along the curve each image point would produce. If the velocity is right, the sums line up at the true position and the point comes into focus.",
      controls, body, readout,
      caption: "Zero-offset, constant-velocity Kirchhoff-style sum with no amplitude weights or aperture taper: a teaching model, not production migration. Migration relies on a time axis and, for waves, phase. An ordinary photograph has neither, so this does not apply to RGB images directly. Time-of-flight sensors are different: Lindell et al. (2019) adapted seismic f-k migration to image around corners with transient light.",
      tryThis: ["Set the migration velocity to the true 2.0 km/s: the point focuses and the readout reaches 100%.", "Move the velocity too low or too high: the energy smears into curved arcs and the peak drops.", "Add the dipping reflector: it is built from many scatterers, so migration moves its energy to the right dip and position."],
      why: "Migration is back-projection with a physical model of how energy travels. Anything that records echoes or time of flight (radar, sonar, ultrasound, transient light) can use the same idea, which is one reason non-optical sensors are an active area for robots."
    })); drawData(); update();
  }

  root.GeoPrimerA = { slider, widget, mix, tomography, migration };
})(typeof window !== "undefined" ? window : globalThis);
