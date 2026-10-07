/* Small theme-aware SVG icons and drawing helpers (needs viz.js and figures.css).
   Every icon is Icons.<name>(label?) -> <svg viewBox="0 0 64 48">. With a label the icon is exposed to assistive technology
   (role="img"); without one it is decorative (aria-hidden). Colours come from CSS classes, so icons follow the light/dark theme. */
(function () {
  const E = V.el;
  const kids = (a) => a.flat().filter(Boolean);
  const root = (label, ...children) => {
    const s = E("svg", { viewBox: "0 0 64 48", class: "icon", focusable: "false" }, ...kids(children));
    if (label) { s.setAttribute("role", "img"); s.setAttribute("aria-label", label); } else s.setAttribute("aria-hidden", "true");
    return s;
  };
  const line = (x1, y1, x2, y2, c) => E("line", { x1, y1, x2, y2, class: c || "s-ink2 mid round" });
  const path = (d, c) => E("path", { d, class: c || "s-ink2 mid round nofill" });
  const poly = (points, c) => E("polygon", { points, class: c });
  const pl = (points, c) => E("polyline", { points, class: c || "s-ink2 mid round nofill" });
  const circ = (cx, cy, r, c) => E("circle", { cx, cy, r, class: c });
  const rect = (x, y, width, height, c, rx) => E("rect", { x, y, width, height, rx: rx || 0, class: c });
  const r1 = (n) => Math.round(n * 10) / 10;

  /* a line with its own arrowhead (the shared SVG marker is not available through V.el) */
  function arrow(x1, y1, x2, y2, c, head, size) {
    size = size || 4.5;
    const a = Math.atan2(y2 - y1, x2 - x1), ux = Math.cos(a), uy = Math.sin(a), bx = x2 - ux * size, by = y2 - uy * size;
    const pts = [[x2, y2], [bx - uy * size * 0.55, by + ux * size * 0.55], [bx + uy * size * 0.55, by - ux * size * 0.55]].map((p) => p.map(r1).join(",")).join(" ");
    return E("g", {}, line(x1, y1, r1(bx + ux * 0.5), r1(by + uy * 0.5), c || "s-ink2 mid round"), poly(pts, head || "f-ink2"));
  }

  const arcPts = (cx, cy, r, a0, a1) => [r1(cx + r * Math.cos(a0 * Math.PI / 180)), r1(cy + r * Math.sin(a0 * Math.PI / 180)), r1(cx + r * Math.cos(a1 * Math.PI / 180)), r1(cy + r * Math.sin(a1 * Math.PI / 180))];
  const arc = (cx, cy, r, a0, a1, c) => { const [x0, y0, x1, y1] = arcPts(cx, cy, r, a0, a1); return path(`M${x0} ${y0}A${r} ${r} 0 0 1 ${x1} ${y1}`, c || "s-s1 mid round nofill"); };

  const Icons = {
    /* grid of cells: lit wedge in front of a camera, an obstacle, and dim cells it hides */
    trustmap: (l) => {
      const m = ["110011", "11XX11", "011110", "001100"], cells = [];
      m.forEach((row, r) => [...row].forEach((ch, c) => cells.push(rect(5 + c * 9, 2 + r * 8, 8, 7, ch === "1" ? "f-o3" : ch === "X" ? "f-ink2" : "f-o1", 1.2))));
      return root(l, cells, poly("32,37 27.5,46 36.5,46", "f-ink"));
    },
    /* several overlaid, slightly different outlines of the same room */
    ensemble: (l) => {
      const room = "10,38 10,19 24,9 40,9 54,19 54,38 10,38";
      return root(l, E("g", { transform: "translate(-2.5,2)" }, pl(room, "s-s1 mid round nofill")), E("g", { transform: "translate(2.5,-2)" }, pl(room, "s-s2 mid round nofill")), E("g", {}, pl(room, "s-s3 mid round nofill")));
    },
    /* lamp, block, and the shadow it throws on the floor */
    shadow: (l) => root(l, line(2, 41, 62, 41, "s-axis mid"), circ(10, 8, 4.5, "f-s4"), line(10, 8, 40, 28, "s-s4 thin dash"), line(10, 8, 28, 28, "s-s4 thin dash"),
      rect(28, 16, 12, 12, "f-ink2", 1.5), E("rect", { x: 38.8, y: 39, width: 19.2, height: 4, class: "f-ink2", opacity: "0.45" })),
    /* a cantilever beam and its decaying vibration trace */
    params: (l) => {
      const pts = []; for (let x = 8; x <= 58; x += 1.5) pts.push(`${x},${r1(37 - 8 * Math.exp(-(x - 8) / 26) * Math.sin((x - 8) * 0.62))}`);
      return root(l, rect(3, 5, 5, 17, "f-ink2", 1), rect(8, 11, 44, 6, "f-o3", 2), arrow(47, 2, 47, 10, "s-ink2 mid round", "f-ink2", 3.5), pl(pts.join(" "), "s-s1 mid round nofill"));
    },
    /* wavefronts spreading from a source, reaching an object and reflecting */
    wave: (l) => root(l, [8, 17, 26].map((r) => arc(9, 24, r, -52, 52, "s-s1 mid round nofill")), circ(9, 24, 3, "f-s1"), circ(52, 24, 5.5, "f-ink2"), arc(52, 24, 10, 125, 235, "s-s2 mid round nofill")),
    /* a rover over a buried pipe, with a probe arc */
    inspect: (l) => root(l, line(2, 20, 62, 20, "s-axis mid"), rect(20, 9, 20, 8, "f-ink2", 2), circ(25, 19, 2.6, "f-ink"), circ(35, 19, 2.6, "f-ink"), arc(30, 20, 8, 35, 145, "s-s3 mid round nofill"), arc(30, 20, 15, 35, 145, "s-s3 mid round nofill"), rect(12, 36, 40, 7, "f-s2", 3.5)),
    /* two point sets and the correspondences that pull one onto the other */
    align: (l) => {
      const A = [[10, 38], [18, 38], [26, 38], [34, 38], [34, 30], [34, 22]], t = 14 * Math.PI / 180, cx = 22, cy = 30;
      const B = A.map(([x, y]) => [r1(cx + (x - cx) * Math.cos(t) - (y - cy) * Math.sin(t) + 8), r1(cy + (x - cx) * Math.sin(t) + (y - cy) * Math.cos(t) - 11)]);
      return root(l, B.map((b, i) => arrow(b[0], b[1] + 2, A[i][0], A[i][1] - 3, "s-ink2 thin", "f-ink2", 3)), A.map((p) => circ(p[0], p[1], 2.6, "f-s1")), B.map((p) => circ(p[0], p[1], 2.6, "f-s2")));
    },
    /* a path across a gridded map, around an obstacle */
    robot: (l) => {
      const g = []; for (let k = 1; k < 5; k++) g.push(line(r1(6 + 52 * k / 5), 4, r1(6 + 52 * k / 5), 40, "s-grid thin")); for (let k = 1; k < 4; k++) g.push(line(6, r1(4 + 36 * k / 4), 58, r1(4 + 36 * k / 4), "s-grid thin"));
      return root(l, rect(6, 4, 52, 36, "s-axis thin nofill", 3), g, rect(26.4, 13, 10.4, 18, "f-ink2", 1.5), pl("11,35 11,8.5 48,8.5", "s-s1 thick round nofill"), circ(11, 35, 3.2, "f-s3"), circ(50, 8.5, 3.2, "f-s2"));
    },
    /* a diffraction hyperbola collapsing to a point */
    migrate: (l) => {
      const pts = []; for (let x = 3; x <= 29; x += 1) pts.push(`${x},${r1(Math.sqrt(110 + 3.4 * (x - 16) * (x - 16)) - 4)}`);
      return root(l, pl(pts.join(" "), "s-s1 mid round nofill"), arrow(32, 24, 43, 24, "s-ink2 mid round", "f-ink2", 4), circ(53, 16, 2.8, "f-s2"), arc(53, 16, 7, 200, 340, "s-s2 thin round nofill"));
    },
    /* --- step and pipeline icons --- */
    openproblems: (l) => root(l, rect(16, 4, 32, 40, "s-ink2 mid nofill", 3), line(22, 12, 42, 12, "s-grid mid round"), line(22, 18, 38, 18, "s-grid mid round"), circ(32, 31, 8, "f-wash"), E("text", { x: 32, y: 37, "text-anchor": "middle", class: "t-big", style: "font-size:17px" }, "?")),
    seismic: (l) => root(l, line(2, 8, 62, 8, "s-axis mid"), poly("10,3 6,8 14,8", "f-ink"), circ(50, 8, 2.3, "f-ink2"), circ(56, 8, 2.3, "f-ink2"), path("M3 24Q16 20 32 24T61 24", "s-grid mid nofill"), path("M3 36Q16 32 32 36T61 36", "s-grid mid nofill"), pl("10,9 30,24 50,9", "s-s1 mid round nofill"), pl("10,9 36,36 56,9", "s-s2 mid round nofill dash")),
    flask: (l) => root(l, poly("21,31 43,31 51,42 13,42", "f-o3"), poly("26,5 38,5 38,17 51,42 13,42 26,17", "s-ink2 mid round nofill"), circ(28, 36, 2, "f-o1"), circ(36, 38, 1.8, "f-o1")),
    verify: (l) => root(l, circ(27, 21, 13, "s-ink2 mid nofill"), line(37, 31, 52, 44, "s-ink2 thick round"), path("M20.5 21.5L25.5 27L34.5 15", "s-s3 thick round nofill")),
    world: (l) => root(l, poly("32,5 53,16 32,27 11,16", "f-o1"), poly("11,16 32,27 32,45 11,34", "f-o3"), poly("53,16 32,27 32,45 53,34", "f-o5")),
    photo: (l) => root(l, rect(7, 12, 50, 31, "s-ink2 mid nofill", 4), rect(22, 6, 14, 6, "s-ink2 mid nofill", 2), circ(32, 27.5, 9.5, "s-ink2 mid nofill"), circ(32, 27.5, 4, "f-o3")),
    generator: (l) => {
      const dots = []; [47, 53, 59].forEach((x, i) => [17, 24, 31].forEach((y, j) => dots.push(circ(x, y, 2.1, (i + j) % 3 === 0 ? "f-o5" : "f-o3"))));
      return root(l, rect(2, 18, 11, 11, "f-o1", 2), arrow(14, 24, 19.5, 24, "s-ink2 mid round", "f-ink2", 3.5), rect(20, 9, 17, 30, "s-ink2 mid nofill", 4), circ(28.5, 17, 2.4, "f-s3"), circ(28.5, 24, 2.4, "f-s3"), circ(28.5, 31, 2.4, "f-s3"), arrow(38, 24, 43.5, 24, "s-ink2 mid round", "f-ink2", 3.5), dots);
    },
    grade: (l) => {
      const t = []; for (let x = 14; x <= 50; x += 6) t.push(line(x, 14, x, x % 12 === 2 ? 22 : 19, "s-ink2 thin"));
      return root(l, rect(6, 14, 52, 22, "s-ink2 mid nofill", 3), t, path("M21 29L28 34L42 25", "s-s3 thick round nofill"));
    },
    clock: (l) => root(l, circ(32, 24, 17, "s-ink2 mid nofill"), line(32, 24, 32, 13, "s-ink2 mid round"), line(32, 24, 40, 29, "s-ink2 mid round"), circ(32, 24, 1.8, "f-ink")),
  };
  Icons.names = Object.keys(Icons);
  Icons.util = { arrow, line, path, poly, pl, circ, rect, arc, root, r1 };
  window.Icons = Icons;

  /* icons fill whatever box they are placed in */
  const st = document.createElement("style");
  st.textContent = "svg.icon{display:block;width:100%;height:auto;overflow:visible}";
  document.head.append(st);
})();
