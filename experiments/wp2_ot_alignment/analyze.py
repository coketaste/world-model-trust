"""WP2 analysis: basin widths, bootstrap CIs, criterion evaluation, plots. Reads results/wp2_runs_{A,B,C}.json."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
RES = os.path.join(ROOT, "results")
LEVELS = [0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0]
rng = np.random.default_rng(0)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def table(runs, method, key):
    """cases x levels -> success rate over draws (nan if method has no runs there)."""
    cases = sorted({r["case"] for r in runs})
    T = np.full((len(cases), len(LEVELS)), np.nan)
    for i, c in enumerate(cases):
        for j, lev in enumerate(LEVELS):
            rr = [r[key] for r in runs if r["case"] == c and r["method"] == method and r["level"] == lev]
            if rr:
                T[i, j] = np.mean(rr)
    return cases, T


def case_basin(row, need=1.0):
    """largest level such that success rate >= need at every level <= it (0 if the first level fails)."""
    b = 0.0
    for lev, v in zip(LEVELS, row):
        if np.isnan(v) or v < need - 1e-9:
            break
        b = lev
    return b


def pooled_basin(T, need=0.9):
    b = 0.0
    for lev, v in zip(LEVELS, np.nanmean(T, 0)):
        if np.isnan(v) or v < need:
            break
        b = lev
    return b


def boot_ratio(a, b, n=10000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    idx = rng.integers(0, len(a), (n, len(a)))
    num, den = a[idx].mean(1), b[idx].mean(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(den > 0, num / den, np.inf)
    diff = num - den
    return dict(ratio=float(a.mean() / b.mean()) if b.mean() > 0 else float("inf"),
                ratio_lo=float(np.percentile(ratio, 2.5)), ratio_hi=float(np.percentile(ratio, 97.5)),
                diff=float((a - b).mean()), diff_lo=float(np.percentile(diff, 2.5)), diff_hi=float(np.percentile(diff, 97.5)))


def accuracy_ratio(runs, m1, m0, key="succ_strict"):
    """mean reference-free accuracy (median NN distance to truth) of m1 / m0 over runs where both succeed."""
    d0 = {(r["case"], r["level"], r["draw"]): r for r in runs if r["method"] == m0}
    a1, a0 = [], []
    for r in runs:
        if r["method"] == m1:
            o = d0.get((r["case"], r["level"], r["draw"]))
            if o and r[key] and o[key]:
                a1.append(r["acc"])
                a0.append(o["acc"])
    return (float(np.mean(a1) / np.mean(a0)) if a1 else float("nan")), len(a1)


def analyse_variant(v):
    path = os.path.join(RES, f"wp2_runs_{v}.json")
    if not os.path.exists(path):
        return None
    runs = json.load(open(path))
    methods = sorted({r["method"] for r in runs})
    out = dict(methods=methods, curves={}, basins={}, auc={})
    for key in ("succ_strict", "succ_coarse"):
        for m in methods:
            cases, T = table(runs, m, key)
            if np.all(np.isnan(T)):
                continue
            ns = {lev: sum(1 for r in runs if r["method"] == m and r["level"] == lev) for lev in LEVELS}
            ks = {lev: sum(r[key] for r in runs if r["method"] == m and r["level"] == lev) for lev in LEVELS}
            out["curves"][f"{key}/{m}"] = {str(l): dict(rate=ks[l] / ns[l] if ns[l] else None, ci=wilson(ks[l], ns[l]), n=ns[l]) for l in LEVELS}
            if m != "fpfh":
                out["basins"][f"{key}/{m}"] = dict(per_case=[case_basin(r) for r in T], mean=float(np.mean([case_basin(r) for r in T])),
                                                   pooled90=pooled_basin(T))
                out["auc"][f"{key}/{m}"] = [float(np.nanmean(r)) for r in T]  # per-case mean success over levels
    out["comparisons"] = {}
    for key in ("succ_strict", "succ_coarse"):
        for m1, m0 in (("ot", "icp"), ("ot+icp", "icp"), ("ot", "p2plane"), ("p2plane", "icp")):
            if f"{key}/{m1}" in out["basins"] and f"{key}/{m0}" in out["basins"]:
                b1, b0 = out["basins"][f"{key}/{m1}"]["per_case"], out["basins"][f"{key}/{m0}"]["per_case"]
                a1, a0 = out["auc"][f"{key}/{m1}"], out["auc"][f"{key}/{m0}"]
                acc, nacc = accuracy_ratio(runs, m1, m0, key)
                out["comparisons"][f"{key}: {m1} vs {m0}"] = dict(
                    basin=boot_ratio(b1, b0), auc=boot_ratio(a1, a0), acc_ratio=acc, acc_n=nacc)
    # decision on the pre-registered criterion (strict, OT vs ICP-trimmed)
    c = out["comparisons"].get("succ_strict: ot vs icp")
    if c:
        icp_b = out["basins"]["succ_strict/icp"]["mean"]
        ot_b = out["basins"]["succ_strict/ot"]["mean"]
        if icp_b == 0:
            passed_basin = ot_b >= 0.35
            rule = "ICP basin = 0: pass iff OT basin >= 0.35"
        else:
            passed_basin = c["basin"]["ratio"] >= 1.5 and c["basin"]["ratio_lo"] > 1.0
            rule = "ratio >= 1.5 and CI lower > 1"
        acc_ok = (c["acc_ratio"] <= 1.10) if np.isfinite(c["acc_ratio"]) else False
        out["criterion"] = dict(rule=rule, basin_pass=bool(passed_basin), accuracy_pass=bool(acc_ok),
                                accuracy_ratio=c["acc_ratio"], accuracy_n=c["acc_n"], passed=bool(passed_basin and acc_ok))
    return out, runs


def plot(v, out):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    colors = {"icp": "#2a78d6", "p2plane": "#1baf7a", "ot": "#eb6834", "ot+icp": "#8b5cf6", "fpfh": "#898781"}
    for a, key, title in zip(ax, ("succ_strict", "succ_coarse"), ("strict: error <= 0.25 tau", "coarse: error <= 1.0 tau")):
        for m, col in colors.items():
            cv = out["curves"].get(f"{key}/{m}")
            if not cv:
                continue
            x = [l for l in LEVELS if cv[str(l)]["rate"] is not None]
            y = [cv[str(l)]["rate"] for l in x]
            lo = [cv[str(l)]["ci"][0] for l in x]
            hi = [cv[str(l)]["ci"][1] for l in x]
            a.plot(x, y, "-o", color=col, label=m, lw=2, ms=4)
            a.fill_between(x, lo, hi, color=col, alpha=0.12)
        a.axhline(0.9, color="k", ls="--", lw=0.8)
        a.set_xscale("log")
        a.set_xlabel("perturbation level f (scale +-40%f, rotation 30 deg f, translation 1 unit f)")
        a.set_title(f"variant {v}, {title}", loc="left", fontsize=10)
        a.set_ylim(-0.02, 1.02)
    ax[0].set_ylabel("success rate (pooled runs, Wilson 95% CI)")
    ax[0].legend(frameon=False)
    plt.tight_layout()
    plt.savefig(os.path.join(RES, f"wp2_basin_{v}.png"), dpi=110)
    plt.close()


if __name__ == "__main__":
    allout = {}
    for v in ("A", "B", "C"):
        r = analyse_variant(v)
        if r is None:
            continue
        out, runs = r
        allout[v] = out
        plot(v, out)
        print(f"\n=== variant {v} ===")
        for k, b in out["basins"].items():
            print(f"  basin {k:24s} mean {b['mean']:.3f}  pooled90 {b['pooled90']}")
        for k, c in out["comparisons"].items():
            print(f"  {k:36s} basin ratio {c['basin']['ratio']:.2f} [{c['basin']['ratio_lo']:.2f}, {c['basin']['ratio_hi']:.2f}] diff {c['basin']['diff']:+.3f} [{c['basin']['diff_lo']:+.3f}, {c['basin']['diff_hi']:+.3f}] "
                  f"| AUC diff {c['auc']['diff']:+.3f} [{c['auc']['diff_lo']:+.3f}, {c['auc']['diff_hi']:+.3f}] | acc ratio {c['acc_ratio']:.2f} (n={c['acc_n']})")
        print("  criterion:", out.get("criterion"))
    json.dump(allout, open(os.path.join(RES, "wp2_analysis.json"), "w"), indent=2, default=float)
