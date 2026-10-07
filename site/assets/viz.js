/* Shared helpers: DOM builder, tooltip, nav, chart cards, table views, bar / dot / forest charts.
   Classic script (no modules) so pages also work from file://. Untrusted strings only ever go through textContent. */
(function () {
  const SVG_TAGS = new Set(["svg", "g", "path", "line", "rect", "circle", "ellipse", "text", "tspan", "polygon", "polyline", "defs", "pattern", "title", "clipPath", "marker", "linearGradient", "radialGradient", "stop", "use", "mask"]);
  const NS = "http://www.w3.org/2000/svg";

  function el(tag, attrs, ...kids) {
    const n = SVG_TAGS.has(tag) ? document.createElementNS(NS, tag) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "fill" || k === "stroke") n.style.setProperty(k, v);
      else if (k === "class") n.setAttribute("class", v);
      else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null) n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return n;
  }

  const scale = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);

  function niceTicks(min, max, n = 5) {
    const span = max - min, raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || raw;
    const out = [];
    for (let t = Math.ceil(min / step) * step; t <= max + step * 1e-6; t += step) out.push(+t.toFixed(10));
    return out;
  }

  const fmt = {
    n: (v, d = 3) => (v == null || !isFinite(v) ? "n/a" : (+v.toFixed(d)).toString().replace("-", "−")),
    pct: (v, d = 0) => (v == null || !isFinite(v) ? "n/a" : (100 * v).toFixed(d) + "%"),
    sci: (v) => (v == null ? "n/a" : v === 0 ? "0" : v.toExponential(1)),
    signed: (v, d = 3) => (v == null ? "n/a" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d)),
    ci: (m, lo, hi, d = 3) => `${fmt.signed(m, d)} [${fmt.signed(lo, d)}, ${fmt.signed(hi, d)}]`,
  };

  /* ---------- tooltip: one element, textContent only ---------- */
  let tipEl;
  function tipNode() {
    if (!tipEl) { tipEl = el("div", { id: "tip", role: "tooltip" }); document.body.append(tipEl); }
    return tipEl;
  }
  const tip = {
    show(title, rows, x, y) {
      const t = tipNode();
      t.replaceChildren(el("div", { class: "t" }, title),
        ...rows.map((r) => el("div", { class: "r" }, r.color ? el("span", { class: "k", style: `background:${r.color}` }) : null, el("b", {}, r.value), el("span", { class: "ink2" }, r.label))));
      t.classList.add("on");
      const w = t.offsetWidth, h = t.offsetHeight;
      t.style.left = Math.max(8, Math.min(window.innerWidth - w - 8, x + 14)) + "px";
      t.style.top = Math.max(8, Math.min(window.innerHeight - h - 8, y + 14)) + "px";
    },
    hide() { if (tipEl) tipEl.classList.remove("on"); },
  };
  /* Pointer hover shows a tooltip. Keyboard: each chart svg is ONE tab stop; arrow keys step through its marks (see enhance below).
     Hit rects are aria-hidden: the table view is the screen-reader route to every value. */
  function attachTip(node, fn) {
    node.setAttribute("aria-hidden", "true");
    const place = (e) => { const d = fn(); tip.show(d.title, d.rows, e.clientX, e.clientY); };
    node.addEventListener("pointermove", place); node.addEventListener("pointerenter", place);
    node.addEventListener("pointerleave", (e) => { if (e.pointerType !== "touch") tip.hide(); });
    node._show = () => { const d = fn(); const b = node.getBoundingClientRect(); tip.show(d.title, d.rows, b.left + b.width / 2, b.top + b.height / 2); };
  }
  document.addEventListener("pointerdown", (e) => { if (!(e.target.classList && e.target.classList.contains("hit"))) tip.hide(); });

  /* one tab stop per chart: arrow keys / Home / End step through every mark that registered a _show or _items */
  function marksOf(svg) { return [...svg.querySelectorAll(".hit")].flatMap((n) => n._items || (n._show ? [n._show] : [])); }
  function enhance(svg) {
    if (svg._kn || !marksOf(svg).length) return;
    svg._kn = true; let i = -1;
    svg.setAttribute("tabindex", "0"); svg.setAttribute("role", "group");
    svg.setAttribute("aria-description", "Use the arrow keys to read values one at a time, or open the table view.");
    svg.addEventListener("keydown", (e) => {
      const m = marksOf(svg); if (!m.length) return;
      let n = i;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") n = Math.min(m.length - 1, i + 1);
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") n = Math.max(0, i < 0 ? 0 : i - 1);
      else if (e.key === "Home") n = 0; else if (e.key === "End") n = m.length - 1;
      else if (e.key === "Escape") { tip.hide(); i = -1; return; } else return;
      e.preventDefault(); i = n; m[n]();
    });
    svg.addEventListener("blur", () => { tip.hide(); i = -1; });
  }
  const scan = (root) => { if (!root || root.nodeType !== 1) return; if (root.matches && root.matches("svg")) enhance(root); if (root.querySelectorAll) root.querySelectorAll("svg").forEach(enhance); };
  new MutationObserver((muts) => { for (const m of muts) { const s = m.target.ownerSVGElement || (m.target.tagName === "svg" ? m.target : null); if (s) enhance(s); m.addedNodes.forEach(scan); } })
    .observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => document.querySelectorAll("svg").forEach(enhance));

  /* ---------- theme + nav ---------- */
  const store = { get() { try { return localStorage.getItem("wmt-theme"); } catch (e) { return null; } }, set(v) { try { localStorage.setItem("wmt-theme", v); } catch (e) { /* storage unavailable: theme still applies for this page view */ } } };
  let themeOverride = null;
  function applyTheme() {
    const t = themeOverride || store.get();
    if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
  }
  applyTheme();

  const PAGES = [["index.html", "Overview"], ["ideas.html", "Ideas"], ["geophysics.html", "Geophysics"], ["experiments.html", "Experiments"], ["literature.html", "Literature"], ["method.html", "Method"]];
  const EXPERIMENTS = [["experiments.html", "All experiments"], ["illumination.html", "Illumination"], ["robots.html", "Robots"], ["shadows.html", "Shadows"], ["alignment.html", "Alignment"]];
  const ORDER = ["index.html", "ideas.html", "geophysics.html", "experiments.html", "illumination.html", "robots.html", "shadows.html", "alignment.html", "literature.html", "method.html"];
  const TITLES = { "index.html": "Overview", "ideas.html": "Ideas: what could be contributed", "geophysics.html": "Geophysics methods, explained", "experiments.html": "The experiments", "illumination.html": "Experiment: illumination", "robots.html": "Experiment: robots", "shadows.html": "Experiment: shadows", "alignment.html": "Experiment: alignment", "literature.html": "What already exists", "method.html": "Method and limits" };

  function nav(current) {
    const mount = document.getElementById("nav");
    if (!mount) return;
    const dark = () => (document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark";
    const btn = el("button", { class: "ghost", type: "button", "aria-label": "Toggle colour theme" }, dark() ? "Light" : "Dark");
    btn.addEventListener("click", () => { themeOverride = dark() ? "light" : "dark"; store.set(themeOverride); applyTheme(); btn.textContent = dark() ? "Light" : "Dark"; window.dispatchEvent(new Event("themechange")); });
    const main = document.querySelector("main"); if (main && !main.id) main.id = "main";
    document.body.prepend(el("a", { class: "sr skip", href: "#main" }, "Skip to content"));
    const inExp = EXPERIMENTS.some(([h]) => h === current);
    mount.className = "nav";
    mount.append(el("div", { class: "wrap" }, el("a", { class: "brand", href: "index.html" }, "world-model-trust"),
      ...PAGES.map(([h, l]) => el("a", { class: "link", href: h, "aria-current": h === current ? "page" : (h === "experiments.html" && inExp ? "true" : null) }, l)), el("span", { class: "spacer" }), btn));
    if (inExp) mount.append(el("nav", { class: "subnav", "aria-label": "Experiments" }, el("div", { class: "wrap" }, ...EXPERIMENTS.map(([h, l]) => el("a", { href: h, "aria-current": h === current ? "page" : null }, l)))));
    pager(current); autoToc(); disclaimer();
  }

  const REPO = "https://github.com/coketaste/world-model-trust";
  /* standard notice appended to the footer of every page */
  function disclaimer() {
    const main = document.querySelector("main");
    if (!main) return;
    let foot = main.querySelector("footer");
    if (!foot) { foot = el("footer", {}); main.append(foot); }
    foot.append(el("p", { class: "disclaimer" },
      "Independent research project, not affiliated with or endorsed by World Labs or any other company named. Built only from public information; the views are the author's own. World Labs, Marble, Atlas, RTFM and Spark are names of their owners. Code: MIT. Text and original figures: CC BY 4.0, except third-party material. See ",
      el("a", { href: REPO + "/blob/main/NOTICE.md", rel: "noopener" }, "NOTICE"), ". Questions or concerns: ", el("a", { href: REPO + "/issues", rel: "noopener" }, "open an issue"), "."));
  }

  function pager(current) {
    const i = ORDER.indexOf(current), main = document.querySelector("main");
    if (i < 0 || !main) return;
    const link = (h, dir) => el("a", { href: h, class: dir }, el("span", { class: "dir" }, dir === "next" ? "Next" : "Previous"), el("b", {}, TITLES[h]));
    const box = el("nav", { class: "pager", "aria-label": "Reading order" }, i > 0 ? link(ORDER[i - 1], "prev") : el("span"), i < ORDER.length - 1 ? link(ORDER[i + 1], "next") : el("span"));
    const foot = main.querySelector("footer");
    if (foot) main.insertBefore(box, foot); else main.append(box);
  }

  function autoToc() {
    if (!document.body.hasAttribute("data-autotoc")) return;
    const hs = [...document.querySelectorAll("main h2")]; if (hs.length < 3) return;
    const used = new Set();
    hs.forEach((h) => { if (!h.id) { let s = h.textContent.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "section", k = s, n = 2; while (used.has(k)) k = s + "-" + n++; h.id = k; } used.add(h.id); });
    const toc = el("nav", { class: "toc", "aria-label": "On this page" }, ...hs.map((h) => el("a", { href: "#" + h.id }, h.textContent)));
    const hero = document.querySelector("main .hero"); if (hero) hero.after(toc); else document.querySelector("main").prepend(toc);
  }

  function badge(kind, text) {
    const icons = { pass: "M3 8.5l3 3 7-7", fail: "M4 4l8 8M12 4l-8 8", mixed: "M8 3v6M8 12v.5", run: "M8 3v5l3 2" };
    return el("span", { class: "badge " + kind }, el("svg", { viewBox: "0 0 16 16", "aria-hidden": "true" }, el("path", { d: icons[kind], fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" })), text);
  }

  /* ---------- chart card with legend and table-view twin ---------- */
  function card(mount, { title, sub, legend }) {
    const body = el("div", { class: "chartbody" });
    const tools = el("div", { class: "tools" });
    const root = el("section", { class: "chartcard" }, el("header", {}, el("h3", {}, title), tools), sub ? el("p", { class: "sub" }, sub) : null,
      legend && legend.length > 1 ? el("div", { class: "legend" }, legend.map((l) => el("span", {}, el("i", { class: l.shape === "dot" ? "dot" : "", style: `background:${l.color}` }), l.label))) : null, body);
    mount.append(root);
    return { root, body, tools };
  }
  function addTable(c, columns, rows) {
    const wrap = el("div", { class: "tablewrap", hidden: true }, el("table", {}, el("thead", {}, el("tr", {}, columns.map((h, i) => el("th", { class: i ? "num" : "" }, h)))),
      el("tbody", {}, rows.map((r) => el("tr", {}, r.map((v, i) => el("td", { class: i ? "num" : "" }, v == null ? "n/a" : v)))))));
    c.root.append(wrap);
    const b = el("button", { class: "ghost", type: "button" }, "Table view");
    b.addEventListener("click", () => { const on = wrap.hidden; wrap.hidden = !on; c.body.hidden = on; b.textContent = on ? "Chart view" : "Table view"; });
    c.tools.append(b);
  }

  /* ---------- horizontal bars: single series, one colour; value at the tip; hit row >= 28px ---------- */
  function roundedEnd(x0, y, w, h, r) {
    r = Math.min(r, w, h / 2);
    return `M${x0},${y}H${x0 + w - r}Q${x0 + w},${y} ${x0 + w},${y + r}V${y + h - r}Q${x0 + w},${y + h} ${x0 + w - r},${y + h}H${x0}Z`;
  }
  function hbars(c, { items, max, color = "var(--s1)", valueFmt, unit = "", ref, labelW = 150, rowH = 34 }) {
    const W = 760, padR = 70, x0 = labelW, plotW = W - labelW - padR, H = items.length * rowH + 34;
    const sx = scale(0, max, 0, plotW);
    const svg = el("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": c.root.querySelector("h3").textContent });
    const g = el("g", { class: "grid" });
    niceTicks(0, max, 4).forEach((t) => { g.append(el("line", { x1: x0 + sx(t), x2: x0 + sx(t), y1: 0, y2: H - 28 })); svg.append(el("text", { x: x0 + sx(t), y: H - 12, "text-anchor": "middle" }, valueFmt ? valueFmt(t) : t + unit)); });
    svg.prepend(g);
    svg.append(el("line", { class: "axis", x1: x0, x2: x0, y1: 0, y2: H - 28 }));
    items.forEach((it, i) => {
      const y = i * rowH, bh = 20, by = y + (rowH - bh) / 2, w = Math.max(sx(it.value), 0);
      svg.append(el("text", { x: x0 - 10, y: y + rowH / 2 + 4, "text-anchor": "end", class: it.strong ? "strong" : "ink2" }, it.label));
      const mark = el("path", { class: "mark", d: w > 0 ? roundedEnd(x0, by, w, bh, 4) : "M0,0", fill: it.color || color });
      svg.append(mark, el("text", { x: x0 + w + 8, y: y + rowH / 2 + 4, class: "strong" }, valueFmt ? valueFmt(it.value) : it.value + unit));
      const hit = el("rect", { class: "hit", x: 0, y, width: W, height: rowH });
      attachTip(hit, () => ({ title: it.label, rows: [{ value: valueFmt ? valueFmt(it.value) : it.value + unit, label: it.tipLabel || "", color: it.color || color }, ...(it.extra || [])] }));
      hit.addEventListener("pointerenter", () => mark.style.opacity = 0.8); hit.addEventListener("pointerleave", () => mark.style.opacity = 1);
      hit.addEventListener("focus", () => mark.style.opacity = 0.8); hit.addEventListener("blur", () => mark.style.opacity = 1);
      svg.append(hit);
    });
    if (ref) { const rx = x0 + sx(ref.value); svg.append(el("line", { class: "axis", x1: rx, x2: rx, y1: 0, y2: H - 28, stroke: "var(--ink2)" }), el("text", { x: rx + 4, y: 10, class: "ink2" }, ref.label)); }
    c.body.replaceChildren(svg);
  }

  /* ---------- dot plot: categories x series, hover row shows every series ---------- */
  function dotPlot(c, { rows, series, domain, labelW = 190, rowH = 30, tickFmt = (t) => t, valueFmt = (v) => fmt.n(v, 3) }) {
    const W = 760, padR = 24, x0 = labelW, plotW = W - labelW - padR, H = rows.length * rowH + 34, sx = scale(domain[0], domain[1], 0, plotW);
    const svg = el("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": c.root.querySelector("h3").textContent });
    const g = el("g", { class: "grid" });
    niceTicks(domain[0], domain[1], 5).forEach((t) => { g.append(el("line", { x1: x0 + sx(t), x2: x0 + sx(t), y1: 0, y2: H - 28 })); svg.append(el("text", { x: x0 + sx(t), y: H - 12, "text-anchor": "middle" }, tickFmt(t))); });
    svg.prepend(g);
    rows.forEach((r, i) => {
      const y = i * rowH, cy = y + rowH / 2;
      svg.append(el("text", { x: x0 - 10, y: cy + 4, "text-anchor": "end", class: "ink2" }, r.label));
      const vals = series.map((s) => r.values[s.key]);
      svg.append(el("line", { x1: x0 + sx(Math.min(...vals)), x2: x0 + sx(Math.max(...vals)), y1: cy, y2: cy, stroke: "var(--axis)", "stroke-width": 2 }));
      series.slice().reverse().forEach((s) => svg.append(el("circle", { class: "mark", cx: x0 + sx(r.values[s.key]), cy, r: 5, fill: s.color, stroke: "var(--surface)", "stroke-width": 2 })));
      const hit = el("rect", { class: "hit", x: 0, y, width: W, height: rowH });
      attachTip(hit, () => ({ title: r.label, rows: series.map((s) => ({ value: valueFmt(r.values[s.key]), label: s.label, color: s.color })) }));
      svg.append(hit);
    });
    c.body.replaceChildren(svg);
  }

  /* ---------- forest: mean + 95% CI per comparison, zero reference line ---------- */
  function forest(c, { items, domain, color = "var(--s1)", labelW = 230, rowH = 44, d = 3, unit = "" }) {
    const W = 760, padR = 190, x0 = labelW, plotW = W - labelW - padR, H = items.length * rowH + 34, sx = scale(domain[0], domain[1], 0, plotW);
    const svg = el("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": c.root.querySelector("h3").textContent });
    const g = el("g", { class: "grid" });
    niceTicks(domain[0], domain[1], 5).forEach((t) => { g.append(el("line", { x1: x0 + sx(t), x2: x0 + sx(t), y1: 0, y2: H - 28 })); svg.append(el("text", { x: x0 + sx(t), y: H - 12, "text-anchor": "middle" }, fmt.n(t, 3) + unit)); });
    svg.prepend(g);
    svg.append(el("line", { class: "axis", x1: x0 + sx(0), x2: x0 + sx(0), y1: 0, y2: H - 28, stroke: "var(--ink2)" }));
    items.forEach((it, i) => {
      const y = i * rowH, cy = y + rowH / 2;
      svg.append(el("text", { x: x0 - 10, y: cy + 4, "text-anchor": "end", class: "ink2" }, it.label),
        el("line", { x1: x0 + sx(it.lo), x2: x0 + sx(it.hi), y1: cy, y2: cy, stroke: it.color || color, "stroke-width": 2, "stroke-linecap": "round" }),
        el("circle", { class: "mark", cx: x0 + sx(it.mean), cy, r: 5, fill: it.color || color, stroke: "var(--surface)", "stroke-width": 2 }),
        el("text", { x: x0 + plotW + 14, y: cy + 4, class: "strong" }, fmt.signed(it.mean, d) + unit), el("text", { x: x0 + plotW + 14, y: cy + 18 }, `[${fmt.signed(it.lo, d)}, ${fmt.signed(it.hi, d)}]`));
      const hit = el("rect", { class: "hit", x: 0, y, width: W, height: rowH });
      attachTip(hit, () => ({ title: it.label, rows: [{ value: fmt.ci(it.mean, it.lo, it.hi, d) + unit, label: "mean and 95% CI" }].concat(it.extra || []) }));
      svg.append(hit);
    });
    c.body.replaceChildren(svg);
  }


  /* segmented control: returns a <label> to append to a .filters row; onChange runs after the state setter */
  function seg(label, options, get, set, onChange) {
    const g = el("div", { class: "seg", role: "group", "aria-label": label });
    options.forEach(([k, t]) => {
      const b = el("button", { type: "button", "aria-pressed": String(get() === k) }, t);
      b.addEventListener("click", () => { set(k); g.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b))); onChange(); });
      g.append(b);
    });
    return el("label", {}, el("span", {}, label), g);
  }

  /* range slider with a live value readout; returns a <label> */
  function slider(label, get, set, min, max, step, unit, onInput, format) {
    const show = format || ((v) => v + unit);
    const out = el("span", { class: "val" }, show(get())), inp = el("input", { type: "range", min, max, step, value: get(), "aria-label": label });
    inp.addEventListener("input", () => { set(+inp.value); out.textContent = show(get()); onInput(); });
    return el("label", {}, el("span", {}, label + " ", out), inp);
  }

  /* link for an arXiv id, a DOI, or a bare arXiv number */
  const refUrl = (id) => !id ? null : /^arxiv:/i.test(id) ? "https://arxiv.org/abs/" + id.slice(6) : /^doi:/i.test(id) ? "https://doi.org/" + id.slice(4)
    : /^\d{4}\.\d{4,5}(v\d+)?$/.test(id) ? "https://arxiv.org/abs/" + id : /^10\.\d{4,9}\//.test(id) ? "https://doi.org/" + id : null;


  /* diagram helpers: build a theme-aware inline SVG and wrap it in a captioned figure */
  function diagram(w, h, ...children) {
    const svg = el("svg", { class: "diagram", viewBox: `0 0 ${w} ${h}`, role: "img", preserveAspectRatio: "xMidYMid meet" });
    svg.append(el("defs", {}, el("marker", { id: "arr", viewBox: "0 0 10 10", refX: "8", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" }, el("path", { d: "M0,1 L9,5 L0,9 Z", fill: "var(--ink2)" }))), ...children.flat().filter(Boolean));
    return svg;
  }
  function figure(svg, caption, label) {
    if (label) svg.setAttribute("aria-label", label);
    return el("figure", { class: "fig-svg" }, svg, caption ? el("figcaption", {}, caption) : null);
  }

  window.V = { el, scale, fmt, tip, attachTip, nav, badge, card, addTable, hbars, dotPlot, forest, seg, slider, refUrl , diagram, figure};
})();
