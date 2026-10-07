/* 2D "flashlight" toy: which boundary points does the prompt photo constrain?
   Pure geometry (no DOM) so it can be unit-tested in node. Tiers: 0 imagined, 1 seen (depth from prior), 2 seen with parallax. */
(function (root) {
  const ROOM = { x0: 40, y0: 30, x1: 600, y1: 420 };
  const OBSTACLES = [{ x: 235, y: 215, w: 130, h: 70 }, { x: 440, y: 110, w: 50, h: 100 }];

  function rectEdges(r) {
    const a = [r.x, r.y], b = [r.x + r.w, r.y], c = [r.x + r.w, r.y + r.h], d = [r.x, r.y + r.h];
    return [[a, b], [b, c], [c, d], [d, a]];
  }

  function samplePoints(step = 4) {
    const pts = [], r = ROOM;
    const line = (p, q, kind) => { const n = Math.max(1, Math.round(Math.hypot(q[0] - p[0], q[1] - p[1]) / step)); for (let i = 0; i < n; i++) pts.push({ x: p[0] + (q[0] - p[0]) * (i / n), y: p[1] + (q[1] - p[1]) * (i / n), kind }); };
    line([r.x0, r.y0], [r.x1, r.y0], "wall"); line([r.x1, r.y0], [r.x1, r.y1], "wall");
    line([r.x1, r.y1], [r.x0, r.y1], "wall"); line([r.x0, r.y1], [r.x0, r.y0], "wall");
    OBSTACLES.forEach((o) => rectEdges(o).forEach(([p, q]) => line(p, q, "object")));
    return pts;
  }

  /* proper segment intersection parameter t along p->q, or null */
  function hitT(p, q, a, b) {
    const rx = q[0] - p[0], ry = q[1] - p[1], sx = b[0] - a[0], sy = b[1] - a[1];
    const den = rx * sy - ry * sx;
    if (Math.abs(den) < 1e-9) return null;
    const t = ((a[0] - p[0]) * sy - (a[1] - p[1]) * sx) / den, u = ((a[0] - p[0]) * ry - (a[1] - p[1]) * rx) / den;
    return t > 1e-6 && t < 1 && u >= 0 && u <= 1 ? t : null;
  }

  const EDGES = OBSTACLES.flatMap(rectEdges);

  /* does camera {x,y,heading(deg),fov(deg)} see point p? 'outside' = not in the wedge, 'hidden' = in wedge but occluded */
  function view(cam, p) {
    const dx = p.x - cam.x, dy = p.y - cam.y;
    let da = Math.atan2(dy, dx) * 180 / Math.PI - cam.heading;
    da = ((da + 540) % 360) - 180;
    if (Math.abs(da) > cam.fov / 2) return "outside";
    for (const [a, b] of EDGES) { const t = hitT([cam.x, cam.y], [p.x, p.y], a, b); if (t !== null && t < 0.999) return "hidden"; }
    return "seen";
  }

  function parallaxDeg(c1, c2, p) {
    const a1 = Math.atan2(p.y - c1.y, p.x - c1.x), a2 = Math.atan2(p.y - c2.y, p.x - c2.x);
    let d = Math.abs(a1 - a2) * 180 / Math.PI;
    return d > 180 ? 360 - d : d;
  }

  /* cams: array of cameras (1 or 2). Returns per-point tier plus summary stats. */
  function compute(cams, minParallax, pts = samplePoints()) {
    const out = pts.map((p) => {
      const v = cams.map((c) => view(c, p));
      const seenBy = v.filter((s) => s === "seen").length;
      let tier = 0, why = "outside";
      if (seenBy >= 1) {
        tier = 1; why = "seen";
        if (seenBy >= 2 && parallaxDeg(cams[0], cams[1], p) >= minParallax) tier = 2;
      } else if (v.some((s) => s === "hidden")) why = "hidden";
      return { ...p, tier, why };
    });
    const n = out.length, c = (f) => out.filter(f).length;
    const imagined = c((p) => p.tier === 0), hidden = c((p) => p.why === "hidden"), seen = c((p) => p.tier >= 1);
    const inFrame = seen + hidden;
    return { pts: out, n, imagined: imagined / n, outside: (imagined - hidden) / n, hidden: hidden / n, seen: seen / n,
      parallax: c((p) => p.tier === 2) / n, hiddenOfInFrame: inFrame ? hidden / inFrame : 0 };
  }

  root.Demo = { ROOM, OBSTACLES, samplePoints, view, parallaxDeg, compute, rectEdges };
})(typeof window !== "undefined" ? window : globalThis);
