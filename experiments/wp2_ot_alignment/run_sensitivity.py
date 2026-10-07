"""WP2 post-hoc sensitivity: OT vs ICP at matched compute budget (see results/WP2-sensitivity.md for the plan).

  LD_LIBRARY_PATH=/tmp/wp2lib python experiments/wp2_ot_alignment/run_sensitivity.py run [--procs 4] [--budget-min 90]
  python experiments/wp2_ot_alignment/run_sensitivity.py analyze
Does not modify the original WP2 files. Per-job results are written incrementally to results/wp2_sensitivity_job_*.json (resumable; deletable after merge).
"""
import argparse
import hashlib
import importlib.util
import glob
import json
import multiprocessing as mp
import os
import re
import sys
import time
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from wmt.align import apply, icp_similarity  # noqa: E402
from wmt.wp2_align import IDENTITY, icp_point_to_plane_sim, ot_align, perturbation, pose_error  # noqa: E402

_spec = importlib.util.spec_from_file_location("wp2run", os.path.join(os.path.dirname(__file__), "run.py"))
wp2run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wp2run)

RES = os.path.join(ROOT, "results")
CACHE = RES                                              # per-job files results/wp2_sensitivity_job_*.json (resumable)
LEVELS = wp2run.LEVELS
OT_CFG = dict(rho=0.05, eps_start=0.5)                       # tuned in the original WP2 (at 10 stages); not re-tuned
OT_VARIANTS = {"ot10": (10, 6), "ot14x15": (14, 15), "ot30": (30, 6), "ot100": (100, 6)}
HYBRIDS = ("ot10", "ot100")
EVAL_CASES = ["elegant_library_with_fireplace_0", "elegant_library_with_fireplace_90", "elegant_library_with_fireplace_180",
              "elegant_library_with_fireplace_270", "rustic_kitchen_with_natural_light_0", "rustic_kitchen_with_natural_light_90",
              "rustic_kitchen_with_natural_light_180", "rustic_kitchen_with_natural_light_270"]
VARIANTS = ("A", "C")


def stable_seed(name, level, draw):
    h = hashlib.sha256(f"{name}|{level}|{draw}".encode()).digest()
    return int.from_bytes(h[:8], "little")


def worker(job):
    name, variant, draws = job
    tag = f"{variant}_{name}_d{'-'.join(map(str, draws))}"
    path = os.path.join(CACHE, "wp2_sensitivity_job_" + tag + ".json")
    if os.path.exists(path):
        return json.load(open(path)), 0.0
    t0 = time.time()
    pk, truth, E, E_ot, tgt_ot = wp2run.prepare(name, variant)
    tree = cKDTree(truth)
    nrm = wp2run.target_normals(truth)
    tau = pk["tau"]
    out = []
    for lev in LEVELS:
        for dr in draws:
            P = perturbation(lev, np.random.default_rng(stable_seed(name, lev, dr)))
            X0, X0_ot = apply(P, E), apply(P, E_ot)
            res = {"icp": wp2run.safe(icp_similarity, X0, tree, truth, IDENTITY, iters=100),
                   "p2plane": wp2run.safe(icp_point_to_plane_sim, X0, tree, truth, nrm, iters=100)}
            for lab, (stages, iters) in OT_VARIANTS.items():
                try:
                    s_ot = ot_align(X0_ot, tgt_ot, stages=stages, iters=iters, **OT_CFG)
                except (ValueError, RuntimeError):
                    s_ot = wp2run.BAD
                res[lab] = s_ot
                if lab in HYBRIDS:
                    res[lab + "+icp"] = wp2run.safe(icp_similarity, X0, tree, truth, s_ot, iters=30)
            for m, sim in res.items():
                if not (np.isfinite(sim[0]) and np.all(np.isfinite(sim[1])) and np.all(np.isfinite(sim[2]))):
                    err, acc = float("inf"), float("inf")
                else:
                    err = pose_error(sim, X0, E)
                    acc = float(np.median(tree.query(apply(sim, X0), k=1)[0]))
                out.append(dict(case=name, variant=variant, level=lev, draw=dr, method=m, err=err if np.isfinite(err) else None,
                                acc=acc if np.isfinite(acc) else None, succ_strict=bool(err <= 0.25 * tau), succ_coarse=bool(err <= 1.0 * tau), tau=tau))
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(path, "w"), allow_nan=False)
    return out, time.time() - t0


def run_pass(draws, procs):
    jobs = [(n, v, draws) for v in VARIANTS for n in EVAL_CASES]
    runs, t0 = [], time.time()
    with Pool(procs) as p:
        for k, (out, dt) in enumerate(p.imap_unordered(worker, jobs), 1):
            runs += out
            print(f"  job {k}/{len(jobs)} done ({dt:.0f}s; elapsed {(time.time() - t0) / 60:.1f} min)", flush=True)
    return runs, time.time() - t0



def merge():
    """Merge every per-job file into wp2_sensitivity_runs.json together with the (case, draw) coverage."""
    runs, avail = [], {}
    for f in sorted(glob.glob(os.path.join(RES, "wp2_sensitivity_job_*.json"))):
        m = re.match(r"wp2_sensitivity_job_([AC])_(.+)_d([\d-]+)\.json", os.path.basename(f))
        if not m:
            continue
        var, case, ds = m.group(1), m.group(2), [int(x) for x in m.group(3).split("-")]
        runs += json.load(open(f))
        avail.setdefault(var, {}).setdefault(case, set()).update(ds)
    cov = {v: {c: sorted(d) for c, d in cs.items()} for v, cs in avail.items()}
    json.dump(dict(coverage=cov, runs=runs), open(os.path.join(RES, "wp2_sensitivity_runs.json"), "w"), allow_nan=False)
    print(f"merged {len(runs)} runs; coverage: " + "; ".join(f"{v}: {len(cs)} cases" for v, cs in cov.items()))


def run_incremental(variants, draws, procs, budget_min):
    """One job per (draw, variant, case), draw-major, so any prefix is balanced across cases; stops at the time budget."""
    jobs = [(n, v, [dr]) for dr in draws for v in variants for n in EVAL_CASES]
    t0, done = time.time(), 0
    pool = Pool(procs)
    try:
        it = pool.imap_unordered(worker, jobs)
        while done < len(jobs):
            try:
                out, dt = it.next(timeout=30)
            except mp.TimeoutError:
                if time.time() - t0 > budget_min * 60:
                    print("time budget reached; stopping", flush=True)
                    break
                continue
            done += 1
            print(f"  job {done}/{len(jobs)} done ({dt:.0f}s; elapsed {(time.time() - t0) / 60:.1f} min)", flush=True)
    finally:
        pool.terminate()
        pool.join()
    merge()


def tables():
    """Print markdown tables from results/wp2_sensitivity_analysis.json."""
    a = json.load(open(os.path.join(RES, "wp2_sensitivity_analysis.json")))
    order = ["icp", "p2plane", "ot10", "ot14x15", "ot30", "ot100", "ot10+icp", "ot100+icp"]
    f3 = lambda x: "undefined" if x is None else f"{x:.3f}"
    fci = lambda b, k: "undefined (ICP basin 0 in every resample)" if b.get(k) is None else f"{b[k]:.2f} [{b[k + '_lo']:.2f}, {b[k + '_hi']:.2f}]"
    print(f"Coverage used (per variant: draws and cases): {json.dumps(a['coverage_used'])}\n")
    for var in ("C", "A"):
        if var not in a:
            continue
        for tol in ("strict", "coarse"):
            t = a[var][tol]
            print(f"#### Variant {var}, {tol} tolerance\n")
            print("Mean per-case basin (level units) and mean success over levels:\n")
            print("| method | mean basin | mean success (AUC) |\n|---|---|---|")
            for m in order:
                print(f"| {m} | {f3(t['basin_mean'][m])} | {f3(t['auc_mean'][m])} |")
            print("\nPooled success rate per level (Wilson 95% interval):\n")
            print("| method | " + " | ".join(str(l) for l in a["levels"]) + " |\n|---|" + "---|" * len(a["levels"]))
            for m in order:
                cells = []
                for l in a["levels"]:
                    c = t["curves"][m][str(l)]
                    cells.append("n/a" if c["rate"] is None else f"{c['rate']:.2f} ({c['lo']:.2f}-{c['hi']:.2f})")
                print(f"| {m} | " + " | ".join(cells) + " |")
            print("\nPaired case-level bootstrap (10,000 resamples; difference = first minus second, in basin level units):\n")
            print("| comparison | basin diff [95% CI] | basin ratio [95% CI] | AUC diff [95% CI] |\n|---|---|---|---|")
            for k, c in t["comparisons"].items():
                b, u = c["basin"], c["auc"]
                print(f"| {k} | {b['diff']:+.3f} [{b['diff_lo']:+.3f}, {b['diff_hi']:+.3f}] | {fci(b, 'ratio')} | {u['diff']:+.3f} [{u['diff_lo']:+.3f}, {u['diff_hi']:+.3f}] |")
            icp = t["basin_mean"]["icp"]
            if icp > 0:
                print("\nGap to ICP, (ICP - OT)/ICP in mean basin: " + ", ".join(f"{m} {100 * (icp - t['basin_mean'][m]) / icp:.0f}%" for m in ("ot10", "ot14x15", "ot30", "ot100", "ot100+icp")) + "\n")
            print("Per-world mean basin:\n")
            print("| world | " + " | ".join(order) + " |\n|---|" + "---|" * len(order))
            for w, row in t["per_world_basin"].items():
                print(f"| {w} | " + " | ".join(f3(row[m]) for m in order) + " |")
            print("\nFinal accuracy among runs where both methods succeed strictly (mean of per-run median-distance ratio vs ICP; below 1 is more accurate):\n")
            print("| method | n both succeed | mean accuracy ratio |\n|---|---|---|")
            for m, c in t["accuracy"].items():
                print(f"| {m} | {c['n_both']} | {f3(c['mean_ratio_vs_icp'])} |")
            print()


def run(procs, budget_min):
    t_all = time.time()
    runs, dt1 = run_pass([0, 1, 2], procs)
    used = [0, 1, 2]
    projected = dt1 * 2 / 3
    print(f"pass 1 took {dt1 / 60:.1f} min; projected pass 2 {projected / 60:.1f} min; budget {budget_min} min", flush=True)
    if (time.time() - t_all + projected) / 60 <= budget_min:
        r2, _ = run_pass([3, 4], procs)
        runs += r2
        used += [3, 4]
    else:
        print("pass 2 skipped by the runtime guard", flush=True)
    json.dump(dict(draws_used=used, runs=runs), open(os.path.join(RES, "wp2_sensitivity_runs.json"), "w"), allow_nan=False)
    print(f"saved {len(runs)} runs; draws used {used}; total {(time.time() - t_all) / 60:.1f} min")


# ------------------------------------------------------------------ analysis
def wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(max(0, c - h)), float(min(1, c + h))


def basin_of(succ_by_level):
    """Largest level such that all draws succeed at that level and every lower level; 0 if the lowest level fails."""
    b = 0.0
    for lev in LEVELS:
        if succ_by_level[lev]:
            b = lev
        else:
            break
    return b


def boot(b_a, b_b, n=10000, seed=0):
    """Case-level paired bootstrap of mean(b_a) - mean(b_b) and mean(b_a)/mean(b_b); exact bounds, undefined ratios counted."""
    b_a, b_b = np.asarray(b_a, float), np.asarray(b_b, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(b_a), (n, len(b_a)))
    ma, mb = b_a[idx].mean(1), b_b[idx].mean(1)
    d = ma - mb
    ok = mb > 0
    r = ma[ok] / mb[ok]
    out = dict(diff=float(b_a.mean() - b_b.mean()), diff_lo=float(np.percentile(d, 2.5)), diff_hi=float(np.percentile(d, 97.5)),
               ratio=(float(b_a.mean() / b_b.mean()) if b_b.mean() > 0 else None), n_undefined_ratio=int((~ok).sum()), n_boot=n)
    if ok.sum() > 0:
        out.update(ratio_lo=float(np.percentile(r, 2.5)), ratio_hi=float(np.percentile(r, 97.5)))
    else:
        out.update(ratio_lo=None, ratio_hi=None)
    return out


def analyze():
    d = json.load(open(os.path.join(RES, "wp2_sensitivity_runs.json")))
    runs, cov = d["runs"], d["coverage"]
    draws_used = {}
    methods = ["icp", "p2plane", "ot10", "ot14x15", "ot30", "ot100", "ot10+icp", "ot100+icp"]
    world = lambda c: c.rsplit("_", 1)[0]
    out = dict(n_runs=len(runs), levels=LEVELS)
    for var in VARIANTS:
        if var not in cov:
            continue
        common = sorted(set.intersection(*[set(v) for v in cov[var].values()]))
        keep = {c for c, v in cov[var].items() if set(common) <= set(v)}
        draws_used[var] = dict(draws=common, cases=sorted(keep))
        vr = [r for r in runs if r["variant"] == var and r["case"] in keep and r["draw"] in common]
        cases = sorted({r["case"] for r in vr})
        V = {}
        for tol in ("strict", "coarse"):
            key = "succ_" + tol
            curves, basins, auc = {}, {}, {}
            for m in methods:
                rm = [r for r in vr if r["method"] == m]
                curves[m] = {}
                for lev in LEVELS:
                    sel = [r for r in rm if r["level"] == lev]
                    k, n = sum(r[key] for r in sel), len(sel)
                    lo, hi = wilson(k, n)
                    curves[m][str(lev)] = dict(rate=k / n if n else None, lo=lo, hi=hi, n=n)
                basins[m], auc[m] = [], []
                for c in cases:
                    per = {lev: all(r[key] for r in rm if r["case"] == c and r["level"] == lev) for lev in LEVELS}
                    basins[m].append(basin_of(per))
                    auc[m].append(float(np.mean([np.mean([r[key] for r in rm if r["case"] == c and r["level"] == lev]) for lev in LEVELS])))
            comps = {}
            for m in methods:
                if m in ("icp",):
                    continue
                comps[m + " vs icp"] = dict(basin=boot(basins[m], basins["icp"]), auc=boot(auc[m], auc["icp"]))
            for m in ("ot10", "ot100", "ot100+icp"):
                comps[m + " vs p2plane"] = dict(basin=boot(basins[m], basins["p2plane"]), auc=boot(auc[m], auc["p2plane"]))
            worlds = {}
            for w in sorted({world(c) for c in cases}):
                ix = [i for i, c in enumerate(cases) if world(c) == w]
                worlds[w] = {m: float(np.mean([basins[m][i] for i in ix])) for m in methods}
            # accuracy among runs where both succeed (strict): mean of per-run acc ratio
            acc = {}
            for m in ("ot10", "ot100", "ot100+icp", "p2plane"):
                a = {(r["case"], r["level"], r["draw"]): r for r in vr if r["method"] == m}
                b = {(r["case"], r["level"], r["draw"]): r for r in vr if r["method"] == "icp"}
                ratios = [a[k]["acc"] / b[k]["acc"] for k in a if k in b and a[k]["succ_strict"] and b[k]["succ_strict"] and a[k]["acc"] and b[k]["acc"]]
                acc[m] = dict(n_both=len(ratios), mean_ratio_vs_icp=float(np.mean(ratios)) if ratios else None)
            V[tol] = dict(curves=curves, basin_per_case=basins, basin_mean={m: float(np.mean(basins[m])) for m in methods},
                          auc_mean={m: float(np.mean(auc[m])) for m in methods}, comparisons=comps, per_world_basin=worlds, accuracy=acc)
        out[var] = dict(cases=cases, **V)
    out["coverage_used"] = draws_used
    json.dump(out, open(os.path.join(RES, "wp2_sensitivity_analysis.json"), "w"), indent=1, allow_nan=False)
    print("wrote results/wp2_sensitivity_analysis.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["run", "run_incremental", "merge", "analyze", "tables", "smoke"])
    ap.add_argument("--variants", nargs="+", default=["C"])
    ap.add_argument("--draws", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--budget-min", type=float, default=90)
    a = ap.parse_args()
    if a.mode == "run":
        run(min(a.procs, 4), a.budget_min)
    elif a.mode == "run_incremental":
        run_incremental(a.variants, a.draws, min(a.procs, 4), a.budget_min)
    elif a.mode == "merge":
        merge()
    elif a.mode == "tables":
        tables()
    elif a.mode == "analyze":
        analyze()
    else:
        LEVELS[:] = [0.1, 0.5]
        t = time.time()
        out, dt = worker((EVAL_CASES[4], "C", [0]))
        print(len(out), "records in", round(dt, 1), "s;", sorted({r["method"] for r in out}))
        os.remove(os.path.join(CACHE, f"wp2_sensitivity_job_C_{EVAL_CASES[4]}_d0.json"))
