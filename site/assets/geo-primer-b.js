/* Primer widgets, part B: moveout, multiples schematic, FWI loop. Needs viz.js and geo-primer-a.js. No innerHTML. */
(function (root) {
  const E = V.el, A = GeoPrimerA;

  /* ---------- 3. velocity-depth ambiguity and moveout ---------- */
  function moveoutWidget(mount) {
    const O = GeoMoveout, st = { spread: 0.3, xmax: 1.2 }, T0 = 1.0, V0 = 2.0, XD = 2.4, TD0 = 1.0, TD1 = 2.4;
    const W = 560, H = 320, padL = 46, padT = 10, plotW = W - padL - 14, plotH = H - padT - 40;
    const sx = V.scale(0, XD, padL, padL + plotW), sy = V.scale(TD0, TD1, padT, padT + plotH);
    const svg = E("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart wg-svg", role: "img", "aria-label": "Arrival time against offset for three candidate velocities that share the same zero-offset time" });
    const g = E("g", { class: "grid" });
    [1.0, 1.5, 2.0].forEach((t) => { g.append(E("line", { x1: padL, x2: padL + plotW, y1: sy(t), y2: sy(t) })); svg.append(E("text", { x: padL - 6, y: sy(t) + 4, "text-anchor": "end" }, t.toFixed(1))); });
    [0, 0.5, 1, 1.5, 2].forEach((x) => svg.append(E("text", { x: sx(x), y: padT + plotH + 16, "text-anchor": "middle" }, String(x))));
    svg.prepend(g);
    svg.append(E("text", { x: padL + plotW / 2, y: H - 4, "text-anchor": "middle" }, "source–receiver offset (km)"), E("text", { x: 12, y: padT + plotH / 2, "text-anchor": "middle", transform: `rotate(-90 12 ${padT + plotH / 2})` }, "two-way time (s)"));
    const COL = ["var(--s1)", "var(--s2)", "var(--s3)"], lines = COL.map((c) => E("polyline", { fill: "none", stroke: c, "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" }));
    const dots = COL.map((c) => E("circle", { r: 4.5, fill: c, stroke: "var(--surface)", "stroke-width": 2 }));
    const edge = E("line", { stroke: "var(--axis)", "stroke-width": 1 });
    svg.append(edge, ...lines, ...dots);
    const legend = E("div", { class: "legend" }), readout = document.createTextNode("");
    function update() {
      const vs = O.candidates(V0, st.spread), cv = O.curves(T0, vs, st.xmax, 41);
      cv.forEach((c, i) => { lines[i].setAttribute("points", c.map((p) => `${sx(p.x).toFixed(1)},${sy(p.t).toFixed(1)}`).join(" ")); const last = c[c.length - 1]; dots[i].setAttribute("cx", sx(last.x)); dots[i].setAttribute("cy", sy(last.t)); });
      edge.setAttribute("x1", sx(st.xmax)); edge.setAttribute("x2", sx(st.xmax)); edge.setAttribute("y1", padT); edge.setAttribute("y2", padT + plotH);
      legend.replaceChildren(...vs.map((v, i) => E("span", {}, E("i", { style: `background:${COL[i]}` }), `v = ${v.toFixed(2)} km/s, so depth ${O.depth(T0, v).toFixed(2)} km`)));
      const dtms = O.separation(T0, vs[0], vs[2], st.xmax) * 1000;
      readout.textContent = `All three models give the same time at zero offset (${T0.toFixed(2)} s) but place the reflector at ${O.depth(T0, vs[0]).toFixed(2)}, ${O.depth(T0, vs[1]).toFixed(2)} or ${O.depth(T0, vs[2]).toFixed(2)} km. At ${st.xmax.toFixed(1)} km offset the slowest and fastest curves differ by ${dtms.toFixed(0)} ms. If the arrival times cannot be picked to better than that, the velocity (and so the depth) cannot be told apart.`;
    }
    const controls = [A.slider("How different the candidate velocities are", { min: 0.1, max: 0.4, step: 0.05, value: st.spread, fmt: (v) => "±" + Math.round(v * 100) + "%" }, (v) => { st.spread = v; update(); }).node,
      A.slider("Widest offset recorded", { min: 0.2, max: XD, step: 0.2, value: st.xmax, unit: " km", fmt: (v) => v.toFixed(1) }, (v) => { st.xmax = v; update(); }).node];
    mount.append(A.widget("w-moveout", {
      title: "Velocity–depth ambiguity: why offset matters",
      idea: "With a source and receiver at the same spot, a reflection time only gives depth divided by velocity, so a slower medium with a shallower reflector looks identical to a faster one with a deeper reflector. Recording at wider offsets bends the curve, and for a given zero-offset time the amount of bending depends on the velocity.",
      controls, body: E("div", {}, legend, E("figure", { class: "wg-panel" }, svg, E("figcaption", {}, E("b", {}, "Reflection time against offset."), " Flat reflector, t² = t₀² + x²/v², t₀ = 1.00 s. The dots mark the widest offset recorded."))), readout,
      caption: "Textbook hyperbolic moveout for a single flat layer. Real data add dip, anisotropy, noise and many layers, which make velocity analysis harder than this picture suggests.",
      tryThis: ["Set the widest offset to 0.2 km: the three curves are almost on top of each other, so the depth is ambiguous.", "Widen it to 2.0 km: the curves separate and the velocity can be measured.", "Shrink the spread to ±10%: even wide offsets struggle to separate models that are close."],
      why: "A single photo has the same trade-off: a small near object and a large far one can look identical, just as depth and velocity do here. A second viewpoint (a baseline, giving parallax) plays the role that offset plays in seismic data. The project's shadows page shows another way to break the trade-off."
    })); update();
  }

  /* ---------- 4. multiples and shadow zones (schematic) ---------- */
  function multiplesWidget(mount) {
    const G = GeoMultiples, st = { showMultiple: false }, W = 760, H = 300, X = (x) => 40 + 680 * x, Z = (z) => 30 + 220 * z;
    const svg = E("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart wg-svg", role: "img", "aria-label": "Schematic: primary rays are blocked by an obstacle and cannot reach a point on the reflector; an internal multiple reaches it from the side" });
    const O = G.OBSTACLE, zone = G.shadowZone();
    svg.append(E("line", { x1: X(0), x2: X(1), y1: Z(0), y2: Z(0), stroke: "var(--ink2)", "stroke-width": 2 }), E("text", { x: X(0), y: Z(0) - 8 }, "surface: sources and receivers"),
      E("line", { x1: X(0), x2: X(1), y1: Z(G.REFLECTOR_Z), y2: Z(G.REFLECTOR_Z), stroke: "var(--ink2)", "stroke-width": 2 }), E("text", { x: X(0), y: Z(G.REFLECTOR_Z) + 18 }, "reflector"),
      E("rect", { x: X(O.x0), y: Z(O.z0), width: X(O.x1) - X(O.x0), height: Z(O.z1) - Z(O.z0), fill: "var(--axis)", rx: 3 }), E("text", { x: X(0.5), y: Z((O.z0 + O.z1) / 2) + 4, "text-anchor": "middle", class: "strong" }, "obstacle"));
    zone.forEach(([a, b]) => svg.append(E("line", { x1: X(a), x2: X(b), y1: Z(G.REFLECTOR_Z) - 3, y2: Z(G.REFLECTOR_Z) - 3, stroke: "var(--s2)", "stroke-width": 7 })));
    // primaries from 7 shots to P, drawn until they enter the obstacle
    const shots = Array.from({ length: 7 }, (_, k) => 0.05 + k * 0.15), entry = (s) => { for (let t = 0; t <= 1; t += 0.002) { const q = { x: s.x + (G.P.x - s.x) * t, z: G.P.z * t }; if (q.x > O.x0 && q.x < O.x1 && q.z > O.z0 && q.z < O.z1) return { q, t }; } return null; };
    let reached = 0;
    shots.forEach((x) => {
      const s = { x, z: 0 }, en = entry(s);
      if (!en) { reached++; svg.append(E("line", { x1: X(s.x), y1: Z(0), x2: X(G.P.x), y2: Z(G.P.z), stroke: "var(--ink2)", "stroke-width": 1, style: "opacity:.6" })); return; }
      svg.append(E("line", { x1: X(s.x), y1: Z(0), x2: X(en.q.x), y2: Z(en.q.z), stroke: "var(--ink2)", "stroke-width": 1, style: "opacity:.6" }), E("path", { d: `M${X(en.q.x) - 4},${Z(en.q.z) - 4}l8,8m0,-8l-8,8`, stroke: "var(--ink2)", "stroke-width": 1.5, fill: "none" }));
    });
    const multi = E("g", { style: "display:none" }), mp = G.multiplePath();
    multi.append(E("polyline", { fill: "none", stroke: "var(--s1)", "stroke-width": 2.5, "stroke-linejoin": "round", points: mp.map((p) => `${X(p.x)},${Z(p.z)}`).join(" ") }));
    [["S", mp[0], -10, -6], ["A", mp[1], -4, 16], ["C", mp[2], -4, 18], ["P", mp[3], 8, 16]].forEach(([n, p, dx, dz]) => multi.append(E("circle", { cx: X(p.x), cy: Z(p.z), r: 4.5, fill: "var(--s1)", stroke: "var(--surface)", "stroke-width": 2 }), E("text", { x: X(p.x) + dx, y: Z(p.z) + dz, class: "strong" }, n)));
    svg.append(multi, E("circle", { cx: X(G.P.x), cy: Z(G.P.z), r: 5, fill: "var(--ink)", stroke: "var(--surface)", "stroke-width": 2 }));
    const legend = E("div", { class: "legend" }, E("span", {}, E("i", { style: "background:var(--ink2)" }), "primary ray (stops at the obstacle)"), E("span", {}, E("i", { style: "background:var(--s1)" }), "internal multiple"), E("span", {}, E("i", { style: "background:var(--s2)" }), "shadow zone of the primaries on the reflector"));
    const readout = document.createTextNode(""), zt = zone.map(([a, b]) => `${a.toFixed(2)} to ${b.toFixed(2)}`).join(" and ");
    function update() {
      multi.style.display = st.showMultiple ? "" : "none";
      readout.textContent = `${reached} of ${shots.length} straight primary rays reach the marked point P; it lies in the primaries' shadow zone (reflector positions ${zt} across). ` + (st.showMultiple ? `The multiple S, A, C, P goes down beside the obstacle, reflects off the reflector, bounces off the underside of the obstacle and arrives at P from the side. None of its segments cross the obstacle.` : "Press the second button to add the multiple.");
    }
    const seg = E("div", { class: "seg", role: "group", "aria-label": "Which paths to show" });
    [[false, "Primary rays only"], [true, "Add the multiple"]].forEach(([k, t]) => { const b = E("button", { type: "button", "aria-pressed": String(st.showMultiple === k) }, t); b.addEventListener("click", () => { st.showMultiple = k; seg.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b))); update(); }); seg.append(b); });
    mount.append(A.widget("w-multiples", {
      title: "Multiples and shadow zones: a second path can reach where the first cannot",
      idea: "Primary reflections travel once down and once up. A multiple bounces more than once. Behind a strong obstacle, primaries may never arrive, but a multiple that bounces underneath can arrive from another direction and carry information about the shadowed region.",
      controls: [E("div", { class: "control-group" }, E("span", {}, "Paths shown"), seg)], body: E("div", {}, legend, E("figure", { class: "wg-panel" }, svg, E("figcaption", {}, E("b", {}, "A schematic, not a simulation."), " Straight rays, one flat reflector, one block-shaped obstacle. The point P is under the obstacle."))), readout,
      caption: "Multiples are often treated as noise and attenuated, and surface-related multiples (which bounce at the free surface) are the usual target. Internal multiples, as drawn here, are harder to handle. Methods that use multiples as signal, such as full-wavefield migration, exist but depend on good models; in practice multiples also interfere with primaries.",
      tryThis: ["With primaries only, note that every ray is stopped at the obstacle and the orange bar marks what they cannot reach.", "Add the multiple: the blue path reaches P without crossing the obstacle.", "Compare with the shadows page: a cast shadow is likewise light that took a different path and so reveals something a direct view does not."],
      why: "Inside a room, a cast shadow or a second light bounce is a path that a direct view does not use. The project's shadows page asks whether such a path can resolve a depth ambiguity, and shows that it can only in an idealised simulation, and only when the shadow lands where the camera can see it."
    })); update();
  }

  /* ---------- 5. the FWI loop (static diagram) ---------- */
  function fwiWidget(mount) {
    const W = 760, H = 330, BW = 96, BH = 60, GAP = 14, X0 = 100;
    const svg = E("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart wg-svg", role: "img", "aria-label": "Two parallel loops: full-waveform inversion and inverse rendering share the same steps of simulate, compare, back-propagate, take a gradient and update" });
    const defs = E("defs", {}, E("marker", { id: "arr", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" }, E("path", { d: "M0,0L10,5L0,10z", fill: "var(--ink2)" })));
    svg.append(defs);
    const rows = [
      { y: 52, color: "var(--s1)", label: "Seismic full-waveform inversion", steps: [["Model", "velocity, density"], ["Forward", "simulate the waves"], ["Compare", "predicted vs recorded"], ["Adjoint", "send the residual back"], ["Gradient", "forward × adjoint"], ["Update", "step the model"]] },
      { y: 202, color: "var(--s2)", label: "Inverse rendering and splat training", steps: [["Scene", "3D Gaussians"], ["Render", "draw an image"], ["Compare", "render vs photo"], ["Backpropagate", "reverse-mode autodiff"], ["Gradient", "per-splat"], ["Update", "step the splats"]] }];
    rows.forEach((r) => {
      svg.append(E("text", { x: X0, y: r.y - 16, class: "strong" }, r.label));
      r.steps.forEach(([a, b], i) => {
        const x = X0 + i * (BW + GAP);
        svg.append(E("rect", { x, y: r.y, width: BW, height: BH, rx: 8, fill: "var(--surface)", stroke: r.color, "stroke-width": 2 }), E("text", { x: x + BW / 2, y: r.y + 26, "text-anchor": "middle", class: "strong" }, a), E("text", { x: x + BW / 2, y: r.y + 44, "text-anchor": "middle" }, b));
        if (i < r.steps.length - 1) svg.append(E("line", { x1: x + BW + 1, x2: x + BW + GAP - 1, y1: r.y + BH / 2, y2: r.y + BH / 2, stroke: "var(--ink2)", "stroke-width": 1.5, "marker-end": "url(#arr)" }));
      });
      const xl = X0 + 5 * (BW + GAP) + BW / 2, xr = X0 + BW / 2, yb = r.y + BH + 22;
      svg.append(E("path", { d: `M${xl},${r.y + BH + 1} V${yb} H${xr} V${r.y + BH + 2}`, fill: "none", stroke: "var(--ink2)", "stroke-width": 1.5, "marker-end": "url(#arr)" }), E("text", { x: (xl + xr) / 2, y: yb + 14, "text-anchor": "middle" }, "repeat until the misfit stops improving"));
    });
    svg.append(E("text", { x: 8, y: 52 + BH / 2 + 4 }, "waves"), E("text", { x: 8, y: 202 + BH / 2 + 4 }, "light"));
    mount.append(A.widget("w-fwi", {
      title: "The full-waveform inversion loop, and its twin in inverse rendering",
      idea: "Both methods guess a model, predict what would be measured, compare with the real measurement, and use the adjoint (reverse-mode gradient) to learn how to change the model. Only the physics in the forward step differs.",
      controls: null, body: E("figure", { class: "wg-panel" }, svg, E("figcaption", {}, E("b", {}, "The same loop twice."), " Top: waves. Bottom: images. The gradient in FWI is the zero-lag cross-correlation of the forward wavefield (for acoustic velocity, its second time derivative) and the back-propagated residual wavefield, an imaging condition closely related to migration's.")), readout: null,
      caption: "Cycle skipping: if the predicted arrival is off by more than about half a period, the misfit can pull the model toward a wrong local minimum. The alignment page has a one-dimensional toy of this and shows an optimal-transport misfit that avoids it there. The step list is simplified; real implementations add regularisation, step-length search, multiscale schedules and preconditioning.",
      tryThis: ["Follow the arrows in the top row, then the bottom row, and notice that every step has a counterpart.", "Look for what is different: the forward step (a wave equation versus a renderer) and what the model contains (velocities versus Gaussian splats).", "Open the alignment page and slide the feature width to see cycle skipping in a toy misfit."],
      why: "Because the machinery is shared, a geophysicist's habits carry over directly: checking gradients, asking what the data cannot constrain, watching for local minima, and keeping an eye on trade-offs between parameters. They carry over as habits, not as new algorithms; the literature page lists the existing work."
    }));
  }

  root.GeoPrimerB = { moveoutWidget, multiplesWidget, fwiWidget };
})(typeof window !== "undefined" ? window : globalThis);
