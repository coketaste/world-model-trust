"""Build site/assets/data.js from results/*.json so the web pages always match the recorded results.

Usage: python scripts/build_site_data.py
"""
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = (pathlib.Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else ROOT / "site" / "assets") / "data.js"


def load(name):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else None


def num(x, nd=5):
    """JSON-safe number: inf/nan -> None."""
    if x is None or (isinstance(x, float) and (math.isinf(x) or math.isnan(x))):
        return None
    return round(float(x), nd)


def wp0():
    d = load("wp0_reproduce.json")
    return dict(
        pooled=d["pooled_auroc"], recorded=d["recorded"], bootstrap=d["bootstrap"],
        cases=[dict(world=c["world"], yaw=c["yaw"], ours=c["auroc_ours"], visibility=c["auroc_visibility"],
                    frustum=c["auroc_frustum"]) for c in d["per_case"]])


def wp1():
    out = {}
    for key, fname in (("preregistered", "wp1_results_run1_as_preregistered.json"), ("amended", "wp1_results_amended.json")):
        d = load(fname)
        if d is None:
            continue
        agg = d["aggregate"]
        out[key] = dict(policies=agg["per_policy_mean"], vs_uo=agg["vs_unknown_obstacle"],
                        n_goals=agg["n_goals_total"], gate_passed=agg["gate_passed"])
    return out


def wp3():
    a, s, st = load("wp3_stageA.json"), load("wp3_summary.json"), load("wp3_stress.json")
    cells = a["cells"]
    axes = {k: sorted({c[k] for c in cells}) for k in ("phi", "elev", "R", "floor_albedo", "depth")}
    rows = []
    for c in cells:
        rows.append([axes["phi"].index(c["phi"]), axes["elev"].index(c["elev"]), axes["R"].index(c["R"]),
                     axes["floor_albedo"].index(c["floor_albedo"]), axes["depth"].index(c["depth"])]
                    + [num(c[k]["std_logd_unit"], 4) for k in ("known", "albedo", "light", "both")]
                    + [num(c["A_known"]["std_logd_unit"], 4)])
    ref = a["reference"]
    spectrum = dict(no_shadow=[float(x) for x in ref["A_dil0.0_known"]["eig"]], with_shadow=[float(x) for x in ref["B_dil0.0_known"]["eig"]])
    return dict(
        spectrum=spectrum, axes=axes, cells=rows, cell_fields=["phi", "elev", "R", "albedo", "depth", "known", "albedo_unknown",
                                            "light_unknown", "both_unknown", "no_shadow"],
        S1=s["S1"], S2=s["S2"], S3=s["S3"], S4=s["S4"], gate=s["gate"],
        regimes=s["regimes"], noise=s["noise"], by_depth=s["by_depth"],
        stress=dict(texture=st["T1"], footprint=st["shadow_footprint"], light_error=st["T2"],
                    ref_std=st["fisher_std_known_ref"]))


def wp2():
    d = load("wp2_analysis.json")
    if d is None:
        return None
    levels = ["0.1", "0.2", "0.35", "0.5", "0.75", "1.0", "1.5", "2.0"]
    out = {}
    for var in ("A", "B", "C"):
        v = d[var]
        methods = [m for m in v["methods"] if m != "fpfh"]
        curves = {tol: {m: [num(v["curves"][f"succ_{tol}/{m}"][lv]["rate"], 4) for lv in levels] for m in methods} for tol in ("strict", "coarse")}
        basins = {tol: {m: num(v["basins"][f"succ_{tol}/{m}"]["mean"], 4) for m in methods} for tol in ("strict", "coarse")}
        comps = {}
        for tol in ("strict", "coarse"):
            for other in ("icp", "p2plane"):
                key = f"succ_{tol}: ot vs icp" if other == "icp" else f"succ_{tol}: p2plane vs icp"
                b = v["comparisons"][key]["basin"]
                comps[f"{tol}:{'ot' if other == 'icp' else 'p2plane'}_vs_icp"] = {k: num(b[k], 4) for k in ("ratio", "ratio_lo", "ratio_hi", "diff", "diff_lo", "diff_hi")}
        out[var] = dict(curves=curves, basins=basins, comparisons=comps, passed=bool(v["criterion"]["passed"]),
                        accuracy_ratio=num(v["criterion"]["accuracy_ratio"], 3), accuracy_n=v["criterion"]["accuracy_n"])
    sens = load("wp2_sensitivity_analysis.json")
    if sens is not None:
        keys = ("diff", "diff_lo", "diff_hi", "ratio", "ratio_lo", "ratio_hi")
        out["sensitivity"] = {tol: dict(
            basins={m: num(sens["C"][tol]["basin_mean"][m], 4) for m in ("icp", "p2plane", "ot10", "ot30", "ot100", "ot100+icp")},
            vs_icp={m: {k: num(sens["C"][tol]["comparisons"][f"{m} vs icp"]["basin"][k], 4) for k in keys} for m in ("ot10", "ot30", "ot100", "ot100+icp", "p2plane")})
            for tol in ("strict", "coarse")}
    out["levels"] = [float(x) for x in levels]
    fp = d["A"]["curves"]["succ_strict/fpfh"]
    out["fpfh_total_runs"] = int(sum(fp[lv]["n"] for lv in levels))
    out["fpfh_success_runs"] = int(round(sum(fp[lv]["rate"] * fp[lv]["n"] for lv in levels)))
    return out


def lit():
    """Last fenced json block of each literature map in docs/literature/ (empty list if the file is missing)."""
    out = {}
    for key, name in (("imaging", "LITERATURE-IMAGING.md"), ("physical", "LITERATURE-PHYSICAL-AI.md")):
        p = ROOT / "docs" / "literature" / name
        blocks = re.findall(r"```json\n(.*?)```", p.read_text(), re.S) if p.exists() else []
        out[key] = json.loads(blocks[-1]) if blocks else []
    return out


LIT = lit()
(OUT.parent / "lit.js").write_text("window.WMT_LIT = " + json.dumps(LIT, separators=(",", ":")) + ";\n")
print(f"wrote lit.js: imaging rows {len(LIT['imaging'])}, physical rows {len(LIT['physical'])}")

data = dict(wp0=wp0(), wp1=wp1(), wp3=wp3(), wp2=wp2())
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("window.WMT = " + json.dumps(data, separators=(",", ":"), default=str) + ";\n")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB); wp2 {'present' if data['wp2'] else 'pending'}")
