/* Analogy figures for the Geophysics and Literature pages: a seismic survey beside a photo survey, a processing-chain schematic,
   the toolkit map, small skill icons, and the literature status matrix. Inline SVG, theme-aware through the utility classes in
   figures.css (no hard-coded colours). SVG elements are created with the SVG namespace here (V.el does not know every tag, for
   example marker and ellipse). All drawings are generic schematics. */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  let uid = 0;

  function svgEl(tag, attrs, ...kids) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) { if (v == null || v === false) continue; n.setAttribute(k, v === true ? "" : v); }
    for (const kid of kids.flat()) if (kid != null) n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return n;
  }
  const T = (x, y, s, cls, anchor) => svgEl("text", { x, y, class: cls || "t", "text-anchor": anchor || "start" }, s);
  const L = (x1, y1, x2, y2, cls, extra) => svgEl("line", Object.assign({ x1, y1, x2, y2, class: cls }, extra || {}));
  const R = (x, y, w, h, cls, rx, extra) => svgEl("rect", Object.assign({ x, y, width: w, height: h, class: cls, rx: rx || 0 }, extra || {}));
  const C = (cx, cy, r, cls, extra) => svgEl("circle", Object.assign({ cx, cy, r, class: cls }, extra || {}));
  const P = (d, cls, extra) => svgEl("path", Object.assign({ d, class: cls }, extra || {}));
  const POLY = (points, cls, extra) => svgEl("polygon", Object.assign({ points, class: cls }, extra || {}));
  const G = (attrs, ...kids) => svgEl("g", attrs, ...kids);
  const op = (v) => ({ style: `opacity:${v}` });

  /* root svg with arrowhead markers; wide figures scroll sideways on narrow screens instead of shrinking the text */
  function root(w, h, minW) {
    const s = svgEl("svg", { viewBox: `0 0 ${w} ${h}`, class: "diagram", role: "img", preserveAspectRatio: "xMidYMid meet", style: `min-width:${minW || 600}px` });
    const id = "an-arr-" + ++uid;
    s.arrowId = id;
    s.append(svgEl("defs", {}, svgEl("marker", { id, viewBox: "0 0 10 10", refX: "8.5", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" }, svgEl("path", { d: "M0,1 L9,5 L0,9 Z", class: "f-ink2" }))));
    return s;
  }
  const arrow = (s, x1, y1, x2, y2, cls, both) => L(x1, y1, x2, y2, cls || "s-ink2 mid", Object.assign({ "marker-end": `url(#${s.arrowId})` }, both ? { "marker-start": `url(#${s.arrowId})` } : {}));
  const pill = (cx, cy, n) => G({}, C(cx, cy, 9, "f-accent"), svgEl("text", { x: cx, y: cy + 4, class: "t-strong", "text-anchor": "middle", style: "fill:var(--surface)" }, String(n)));
  const wrap = (fig) => { fig.style.overflowX = "auto"; return fig; };

  /* ---------- small icons for the ten seismic skills ---------- */
  const ST = "nofill s-ink2 mid round", AC = "nofill s-accent mid round", GR = "nofill s-axis thin";
  const ICONS = {
    tomography: () => [R(3, 3, 18, 18, ST, 2), L(9, 3, 9, 21, GR), L(15, 3, 15, 21, GR), L(3, 9, 21, 9, GR), L(3, 15, 21, 15, GR), L(2, 8, 22, 16, AC), L(2, 17, 22, 7, AC)],
    migration: () => [P("M3 6 Q12 22 21 6", ST), C(12, 16.5, 2.4, "f-accent"), L(12, 4, 12, 12, AC, { "stroke-dasharray": "2 2" })],
    multiples: () => [L(3, 5, 21, 5, GR), L(3, 19, 21, 19, GR), P("M4 5 L9 19 L14 5 L19 19", AC)],
    fwi: () => [P("M19.5 10 A8 8 0 1 0 19 15", ST), P("M20 4.5 L19.5 10 L14 9", AC)],
    illumination: () => [POLY("12,3 4,21 20,21", ST), C(12, 12, 1.6, "f-accent"), C(9, 17, 1.6, "f-accent"), C(15, 17, 1.6, "f-accent")],
    ambiguity: () => [L(2, 12, 22, 6, "nofill s-axis thin"), L(2, 12, 22, 18, "nofill s-axis thin"), C(8, 12, 2, ST), C(16, 12, 5, AC)],
    misfit: () => [P("M2 9 Q5 3 8 9 T14 9 T20 9", ST), P("M2 18 Q5 12 8 18 T14 18 T20 18", AC)],
    uq: () => [P("M2 17 Q8 5 14 13 T22 8", ST, op(0.45)), P("M2 14 Q8 6 14 15 T22 11", ST, op(0.45)), P("M2 19 Q8 9 14 11 T22 6", ST, op(0.45)), P("M2 16 Q8 7 14 13 T22 9", AC)],
    survey: () => [C(5, 7, 1.3, "f-ink2"), C(10, 7, 1.3, "f-ink2"), C(15, 7, 1.3, "f-ink2"), C(20, 7, 1.3, "f-ink2"), C(5, 12, 1.3, "f-ink2"), C(10, 12, 1.3, "f-ink2"), C(5, 17, 1.3, "f-ink2"), C(10, 17, 1.3, "f-ink2"), C(15, 17, 1.3, "f-ink2"), C(20, 17, 1.3, "f-ink2"), C(20, 12, 1.3, "f-ink2"), C(15, 12, 4.6, AC)],
    wave: () => [C(5, 12, 1.9, "f-accent"), P("M8.5 7.5 A6 6 0 0 1 8.5 16.5", ST), P("M12 4.5 A10 10 0 0 1 12 19.5", ST), P("M15.5 2 A14 14 0 0 1 15.5 22", ST)],
  };
  const ICON_ORDER = ["tomography", "migration", "multiples", "fwi", "illumination", "ambiguity", "misfit", "uq", "survey", "wave"];
  function icon(name, size) {
    const s = svgEl("svg", { viewBox: "0 0 24 24", width: size || 20, height: size || 20, "aria-hidden": "true", focusable: "false", class: "skill-icon", style: "flex:none;display:inline-block;vertical-align:-4px" });
    (ICONS[name] || ICONS.tomography)().forEach((n) => s.append(n));
    return s;
  }
  const iconAt = (i, size) => icon(ICON_ORDER[i], size);

  /* ---------- 1. a seismic survey and a photo survey ask the same question ---------- */
  function banner(mount) {
    const s = root(760, 416, 640);
    s.append(T(24, 24, "Seismic survey: a vertical slice", "t-strong"), T(414, 24, "Photo survey: a room seen from above", "t-strong"));

    /* left panel: layered ground, a dense body, rays and the shadow zone beneath the body */
    s.append(R(20, 34, 330, 262, "f-page", 10),
      R(24, 60, 322, 60, "f-o1", 0, op(0.3)), R(24, 120, 322, 80, "f-o2", 0, op(0.3)), R(24, 200, 322, 92, "f-o3", 0, op(0.3)),
      L(24, 60, 346, 60, "s-ink mid"), L(24, 120, 346, 120, "s-axis thin"), L(24, 200, 346, 200, "s-ink thick"),
      T(30, 193, "reflector", "t-muted"));
    [70, 100, 130, 160, 190, 220, 250, 280].forEach((x) => s.append(C(x, 60, 3, "f-s1")));
    [40, 306].forEach((x) => s.append(POLY(`${x - 6},50 ${x + 6},50 ${x},60`, "f-s2")));
    s.append(POLY("152,104 180,94 232,98 252,118 244,152 196,166 160,150", "f-o5", op(0.85)), T(202, 88, "dense body", "t-muted", "middle"));
    const ray = "nofill s-s1 thin", blocked = "nofill s-s2 thin dash";
    s.append(P("M40 60 L85 200 L130 60", ray), P("M40 60 L100 200 L160 60", ray), P("M306 60 L293 200 L280 60", ray), P("M306 60 L278 200 L250 60", ray),
      P("M40 60 L115 200", ray), P("M115 200 L156 123", blocked), P("M306 60 L248 200", ray), P("M248 200 L230 156", blocked));
    [[156, 123], [230, 156]].forEach(([x, y]) => s.append(L(x - 4, y - 4, x + 4, y + 4, "s-s2 mid round"), L(x - 4, y + 4, x + 4, y - 4, "s-s2 mid round")));
    s.append(L(150, 212, 250, 212, "s-s2 thick"), L(150, 206, 150, 218, "s-s2 mid"), L(250, 206, 250, 218, "s-s2 mid"), T(192, 242, "shadow zone", "t-muted"),
      T(190, 47, "sources and receivers", "t-muted"));
    s.append(pill(176, 43, 1), pill(334, 148, 2), pill(36, 132, 3), pill(178, 238, 4));
    s.append(R(20, 34, 330, 262, "nofill s-grid thin", 10));

    /* right panel: a camera, an occluder and the region behind it that no view reaches */
    s.append(R(410, 34, 330, 262, "f-page", 10), R(420, 60, 310, 230, "f-surface s-ink2 thin", 3),
      R(440, 112, 38, 34, "f-o2", 4, op(0.8)), R(668, 118, 34, 30, "f-o2", 4, op(0.8)),
      POLY("575,62 430,290 720,290", "f-wash"), L(575, 62, 430, 290, "s-accent thin dash"), L(575, 62, 720, 290, "s-accent thin dash"),
      POLY("545,190 605,190 628,290 522,290", "f-grid s-ink2 thin dash"), R(545, 176, 60, 34, "f-o5", 4), T(575, 170, "occluder", "t-muted", "middle"),
      R(563, 44, 24, 13, "f-s1", 3), POLY("570,57 580,57 575,63", "f-s1"), T(595, 54, "camera", "t-muted"),
      L(430, 290, 522, 290, "s-accent thick"), L(628, 290, 720, 290, "s-accent thick"), L(522, 290, 628, 290, "s-axis thick dash"),
      T(634, 258, "hidden region", "t-muted"));
    s.append(pill(543, 51, 1), pill(459, 100, 2), pill(452, 228, 3), pill(575, 252, 4), R(410, 34, 330, 262, "nofill s-grid thin", 10));

    /* mapping legend: dashed links between the two vocabularies */
    const pairs = [["source, receiver", "camera, pixel"], ["velocity model", "the scene"], ["illumination", "view coverage"], ["shadow zone", "hidden region"]];
    pairs.forEach(([a, b], i) => {
      const x0 = 170, y = 334 + i * 24;
      s.append(pill(x0 + 10, y - 4, i + 1), T(x0 + 26, y, a, "t"), arrow(s, x0 + 156, y - 4, x0 + 192, y - 4, "s-accent thin dash", true), T(x0 + 202, y, b, "t"));
    });
    const cap = V.el("span", {}, V.el("b", {}, "A seismic survey and a photo survey ask the same question:"), " where do the measurements constrain the model, and where are they silent? Schematic with straight rays; not a simulation.");
    mount.append(wrap(V.figure(s, cap, "Left: a vertical slice of layered ground with sources, receivers, a dense body and a shadow zone that primary rays do not reach. Right: a room seen from above with a camera, an occluder and a hidden region. Dashed links pair source and receiver with camera and pixel, velocity model with scene, illumination with view coverage, and shadow zone with hidden region.")));
  }

  /* ---------- 2. from data to image: two generic workflows, side by side ---------- */
  function chain(mount) {
    const s = root(776, 282, 656), W = 128, X = (i) => 16 + i * 150;
    const box = (i, y, title, l1, l2, tone) => G({}, R(X(i), y, W, 62, tone || "f-surface s-ink2 thin", 8), T(X(i) + W / 2, y + 22, title, "t-strong", "middle"), T(X(i) + W / 2, y + 39, l1, "t-muted", "middle"), T(X(i) + W / 2, y + 53, l2, "t-muted", "middle"));
    s.append(T(16, 20, "Seismic imaging (generic workflow)", "t-strong"));
    [["Acquisition", "sources, receivers,", "survey design"], ["Processing", "filtering, multiples,", "velocity analysis"], ["Imaging", "migration puts", "echoes in place"], ["Inversion", "tomography, FWI:", "fit a model to data"], ["Interpretation", "targets, geology,", "uncertainty"]]
      .forEach(([a, b, c], i) => s.append(box(i, 44, a, b, c)));
    for (let i = 0; i < 4; i++) s.append(arrow(s, X(i) + W + 2, 75, X(i + 1) - 2, 75, "s-ink2 mid"));
    s.append(P("M530 42 C530 22 380 22 380 42", "nofill s-ink2 thin dash", { "marker-end": `url(#${s.arrowId})` }), T(455, 20, "update the model, repeat", "t-muted", "middle"));

    s.append(T(16, 186, "Spatial-AI pipeline (generic workflow)", "t-strong"));
    [["Capture", "photos, video,", "text prompts"], ["Calibration", "camera poses,", "scale and axes"], ["Reconstruct or", "generate the", "3D world"], ["Refinement", "differentiable", "rendering, losses"], ["Use by a robot", "simulation,", "planning, training"]]
      .forEach(([a, b, c], i) => s.append(box(i, 196, a, b, c)));
    for (let i = 0; i < 4; i++) s.append(arrow(s, X(i) + W + 2, 227, X(i + 1) - 2, 227, "s-ink2 mid"));

    /* where the project's ideas plug in */
    [[2, "illumination: trust map", 156], [3, "misfit design", 116], [4, "ensembles, uncertainty", 156]].forEach(([i, label, w]) => {
      const cx = X(i) + W / 2;
      s.append(L(cx, 106, cx, 134, "s-accent thin dash"), L(cx, 160, cx, 196, "s-accent thin dash"), R(cx - w / 2, 134, w, 26, "f-wash s-accent thin", 13), T(cx, 151, label, "t", "middle"));
    });
    const cap = V.el("span", {}, V.el("b", {}, "Two workflows, one shape."), " Pills mark where this project's ideas plug in: an illumination-based trust map at the reconstruction step, misfit design where models are refined against data, and ensembles to express uncertainty. A generic schematic: real workflows loop, branch and vary.");
    mount.append(wrap(V.figure(s, cap, "Two five-step rows. Seismic imaging: acquisition, processing, imaging, inversion, interpretation, with a loop from inversion back to imaging. Spatial AI: capture, calibration, reconstruction or generation, refinement by differentiable rendering, use by a robot. Three dashed links mark where illumination, misfit design and ensembles plug in.")));
  }

  /* ---------- 3. toolkit map: open problems the public pages describe, and the seismic skills that might speak to them ---------- */
  const PROBLEMS = [["What the input constrains", "unseen parts are filled in"], ["Scale and physical validity", "plausible geometry and scale"], ["Uncertain physical properties", "shape, weight, friction"], ["Sim-to-real alignment", "the sim-to-real gap"]];
  const EDGES = [[0], [0], [0, 1], [2, 3], [0], [1, 0], [3, 2], [0, 2], [0, 2], [2]];
  const LVL_WORD = { tested: "tested", partly: "partly", none: "not tested" };

  function toolkitMap(mount, skills, onSelect) {
    const s = root(760, 474, 640), px = 330, pw = 410, pillH = 32, step = 40, bh = 76;
    const by = (j) => 36 + j * 105, pcy = (i) => 40 + i * step + pillH / 2;
    s.append(T(20, 22, "Open problems the public pages describe", "t-strong"), T(px, 22, "Seismic skills (click one)", "t-strong"));
    PROBLEMS.forEach(([a, b], j) => s.append(G({}, R(20, by(j), 240, bh, "f-wash s-accent thin", 10), T(32, by(j) + 30, a, "t-strong"), T(32, by(j) + 50, b, "t-muted"))));
    const edges = [], rects = [];
    skills.forEach((sk, i) => EDGES[i].forEach((j) => {
      const y1 = by(j) + bh / 2, y2 = pcy(i), e = P(`M260 ${y1} C295 ${y1} 295 ${y2} ${px} ${y2}`, "nofill s-axis thin");
      edges.push([i, e]); s.append(e);
    }));
    let current = -1, hover = -1;
    const paint = () => {
      edges.forEach(([i, e]) => e.setAttribute("class", i === current || i === hover ? "nofill s-accent mid" : "nofill s-axis thin"));
      rects.forEach((r, i) => r.setAttribute("class", i === current ? "f-wash s-accent mid" : "f-surface s-ink2 thin"));
    };
    skills.forEach((sk, i) => {
      const y = 40 + i * step, cy = y + pillH / 2, mx = px + pw - 22;
      const rect = R(px, y, pw, pillH, "f-surface s-ink2 thin", 16); rects.push(rect);
      const ic = iconAt(i, 20); ic.setAttribute("x", px + 9); ic.setAttribute("y", y + 6);
      const mark = sk.lvl === "tested" ? C(mx, cy, 6, "f-s1")
        : sk.lvl === "partly" ? G({}, C(mx, cy, 6, "nofill s-s1 mid"), P(`M${mx} ${cy - 6} A6 6 0 0 0 ${mx} ${cy + 6} Z`, "f-s1"))
        : C(mx, cy, 6, "nofill s-ink2 mid");
      const g = G({ style: "cursor:pointer" }, svgEl("title", {}, `${sk.name}: ${LVL_WORD[sk.lvl] || ""}`), rect, ic, T(px + 38, cy + 4, sk.name, "t"), T(mx - 14, cy + 4, LVL_WORD[sk.lvl] || "", "t-muted", "end"), mark);
      g.addEventListener("click", () => onSelect(i));
      g.addEventListener("pointerenter", () => { hover = i; paint(); });
      g.addEventListener("pointerleave", () => { hover = -1; paint(); });
      s.append(g);
    });
    s.append(C(28, 452, 6, "f-s1"), T(40, 456, "tested here", "t"),
      G({}, C(200, 452, 6, "nofill s-s1 mid"), P("M200 446 A6 6 0 0 0 200 458 Z", "f-s1")), T(212, 456, "partly tested", "t"),
      C(400, 452, 6, "nofill s-ink2 mid"), T(412, 456, "not tested", "t"));
    paint();
    const cap = V.el("span", {}, V.el("b", {}, "Which skills might speak to which open problem."), " Lines are hypotheses, not findings; the marker on each skill shows how far this project has tested it (filled: an experiment or simulation here; half: synthetic or inconclusive; ring: not tested). Selecting a skill here opens its panel below.");
    mount.append(wrap(V.figure(s, cap, "Map linking four open problems described on World Labs' public pages (what the input constrains, scale and physical validity, uncertain physical properties, sim-to-real alignment) to ten seismic skills, with a marker for how far each skill was tested in this project.")));
    return { select(i) { current = i; paint(); } };
  }

  /* ---------- 4. literature status matrix (data-driven) ---------- */
  function litMatrix(mount, rows, onPick) {
    const cats = ["Done", "Partly done", "Active", "Open"], xs = [420, 505, 590, 675], rowH = 20, groupH = 28;
    const groups = [["imaging", "Imaging methods"], ["physical", "Physical AI"]].map(([k, label]) => [label, rows.filter((r) => r.source === k)]).filter(([, rs]) => rs.length);
    const refs = (r) => r.refs1.length + r.refs2.length, maxRefs = Math.max(1, ...rows.map(refs));
    const H = 56 + groups.length * groupH + rows.length * rowH + 16;
    const s = svgEl("svg", { viewBox: `0 0 820 ${H}`, class: "diagram", role: "img", "aria-label": "Matrix of literature concept rows against the status of their transfer to vision and robotics: done, partly done, active, open. Right bars show the number of references.", style: "min-width:680px" });
    ["Done", "Partly", "Active", "Open"].forEach((c, i) => s.append(T(xs[i], 20, c, "t-strong", "middle"), T(xs[i], 36, ["exists", "in part", "in progress", "not found yet"][i], "t-muted", "middle")));
    s.append(T(720, 20, "references", "t-strong"));
    let y = 48;
    const tableRows = [];
    groups.forEach(([label, rs]) => {
      s.append(L(12, y + 2, 808, y + 2, "s-axis thin"), T(20, y + 20, `${label} (${rs.length})`, "t-strong"));
      cats.forEach((c, k) => s.append(T(xs[k], y + 20, String(rs.filter((r) => r.cat === c).length), "t-muted", "middle")));
      y += groupH;
      rs.forEach((r, n) => {
        const k = cats.indexOf(r.cat), len = Math.round(46 * refs(r) / maxRefs), name = r.title.length > 54 ? r.title.slice(0, 52) + "…" : r.title;
        const g = G({ style: "cursor:pointer" }, svgEl("title", {}, `${r.title}: ${r.cat}; ${refs(r)} references. Click to open it below.`));
        if (n % 2 === 0) g.append(R(12, y, 796, rowH, "f-grid", 4, op(0.5)));
        g.append(T(20, y + 14, name, "t"));
        if (k >= 0) g.append(C(xs[k], y + 10, 6, `f-s${k + 1}`)); else g.append(T(xs[0], y + 14, "–", "t-muted", "middle"));
        g.append(R(720, y + 6, Math.max(2, len), 8, "f-ink2", 3, op(0.45)), T(720 + Math.max(2, len) + 5, y + 14, String(refs(r)), "t-muted"), R(12, y, 796, rowH, "", 0, { fill: "transparent", style: "cursor:pointer" }));
        g.addEventListener("click", () => onPick && onPick(r));
        s.append(g);
        tableRows.push([r.title, label, r.cat, String(refs(r))]);
        y += rowH;
      });
    });
    const c = V.card(mount, { title: "Where each transfer stands", sub: "Each row is a concept; the dot shows how far its transfer to vision and robotics has gone, as found in this search. Click a row to open it below.", legend: cats.map((l, i) => ({ label: l, color: `var(--s${i + 1})`, shape: "dot" })) });
    c.body.append(s);
    V.addTable(c, ["Concept", "Area", "Status", "References"], tableRows);
    return c;
  }

  window.Analogy = { banner, chain, toolkitMap, litMatrix, icon, iconAt, ICON_ORDER };
})();
