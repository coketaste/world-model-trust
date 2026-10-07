// Smoke test: loads every site page in jsdom and exercises the controls. Needs: npm install jsdom (not saved in the repo).
// Run: NODE_PATH=$(npm root) node scripts/smoke_site.js
// jsdom has no layout engine, so this checks for runtime errors and structure, not visual appearance.
const { JSDOM, VirtualConsole } = require("jsdom");
const path = require("path"), fs = require("fs");
const SITE = path.resolve(__dirname, "..", "site");
(async () => {
  let bad = 0;
  for (const page of ["index", "ideas", "geophysics", "experiments", "illumination", "robots", "shadows", "alignment", "literature", "method"]) {
    const errors = [];
    const vc = new VirtualConsole();
    vc.on("jsdomError", (e) => errors.push("jsdomError: " + (e.detail && e.detail.stack ? e.detail.stack.split("\n").slice(0, 3).join(" | ") : e.message)));
    vc.on("error", (e) => errors.push("console.error: " + e));
    if (!fs.existsSync(path.join(SITE, page + ".html"))) { console.log(page + ": (not built yet)"); continue; }
    const dom = await JSDOM.fromFile(path.join(SITE, page + ".html"), { runScripts: "dangerously", resources: "usable", pretendToBeVisual: true, virtualConsole: vc, url: "file://" + SITE + "/" + page + ".html", beforeParse(w) { w.matchMedia = () => ({ matches: false, addEventListener() {}, addListener() {} }); w.SVGElement.prototype.createSVGPoint = () => ({ x: 0, y: 0, matrixTransform() { return this; } }); } });
    await new Promise((r) => setTimeout(r, 600));
    const d = dom.window.document;
    const svgs = d.querySelectorAll("svg.chart").length, cards = d.querySelectorAll(".chartcard").length, nav = d.querySelectorAll("#nav a.link").length;
    console.log(`${page}: svg.chart=${svgs} chartcards=${cards} nav links=${nav} errors=${errors.length}`);
    const tabstops = d.querySelectorAll("[tabindex='0']").length, kb = d.querySelector("svg[tabindex='0'][role='group']");
    let kbOk = "n/a";
    if (kb) { kb.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true })); kbOk = !!d.querySelector("#tip.on"); }
    console.log(`   tabstops=${tabstops} keyboard-tooltip=${kbOk}`);
    // every segmented group keeps exactly one pressed button; every slider readout follows its value
    let segBad = 0, sliderBad = 0, nSeg = 0, nSlider = 0;
    d.querySelectorAll(".seg").forEach((g) => { nSeg++; g.querySelectorAll("button").forEach((b) => { b.click(); if (g.querySelectorAll("button[aria-pressed='true']").length !== 1 || b.getAttribute("aria-pressed") !== "true") segBad++; }); });
    d.querySelectorAll("input[type=range]").forEach((i) => { nSlider++; i.value = i.max; i.dispatchEvent(new dom.window.Event("input")); const out = i.parentElement.querySelector(".val"); if (!out || !out.textContent.trim() || out.textContent.includes("NaN")) sliderBad++; });
    console.log(`   controls ok=${segBad === 0 && sliderBad === 0} (seg groups ${nSeg}, sliders ${nSlider})`);
    if (segBad || sliderBad) errors.push(`controls broken: seg ${segBad}, slider ${sliderBad}`);
    errors.forEach((e) => console.log("   ", e));
    bad += errors.length;
    // exercise controls
    if (page === "robots") { const b = d.querySelectorAll("#run-filters button")[1]; b.click(); console.log("   robots after toggle: bars=", d.querySelectorAll("#bars svg").length, "forests=", d.querySelectorAll("#forests svg").length); }
    if (page === "shadows") { d.querySelectorAll("#heat-controls .seg button").forEach((b) => b.click()); d.querySelectorAll("input[type=range]").forEach((i) => { i.value = i.max; i.dispatchEvent(new dom.window.Event("input")); }); console.log("   shadows heat rects=", d.querySelectorAll("#heat rect.mark").length, "stats=", d.getElementById("heat-stats").textContent.slice(0, 80)); console.log("   geo stats:", d.getElementById("geo-stats").textContent); }
    if (page === "illumination") { d.querySelectorAll("#demo-controls .seg button")[1].click(); console.log("   demo stats:", d.getElementById("demo-stats").textContent.slice(0, 160)); console.log("   dots:", d.querySelectorAll("#demo circle").length); }
    if (page === "geophysics") { const bs = d.querySelectorAll("#skills button"); bs.forEach((b) => b.click()); console.log("   skills:", bs.length, "| ledger rows:", d.querySelectorAll("#ledger tr").length, "quotes:", d.querySelectorAll("#quotes .card").length, "lessons:", d.querySelectorAll("#lessons-grid .card").length); }
    if (page === "literature") { console.log("   rows:", d.querySelectorAll("#rows details").length, "refs:", d.querySelectorAll("#reftable tbody tr").length, d.getElementById("count").textContent); }
    if (page === "alignment") { d.querySelectorAll("#rfilters .seg button").forEach((b) => b.click()); console.log("   wp2 cards:", d.querySelectorAll("#rcharts .chartcard, #rforest .chartcard").length, "notes:", d.querySelectorAll("#rnotes .card").length, "gate:", d.getElementById("gate-text").textContent.slice(0, 140)); console.log("   minima:", d.getElementById("minima").textContent); }
    dom.window.close();
  }
  console.log(bad ? "ERRORS FOUND" : "all pages ran without errors");
})();
