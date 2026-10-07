"""WP1 sensitivity (post-hoc, exploratory; see results/WP1-sensitivity.md).

Variants of the AMENDED configuration (run.py --amended) that differ only in who receives amendment A2 (free blind zone):
  S0  as amended: trust policies get A2, unknown_obstacle (UO) does not (reproduction check)
  S1  symmetric: UO also gets A2
  S1b symmetric the other way: nobody gets A2
A3 (footprint disc) already applies to every non-oracle policy. Goals, seeds and maps are otherwise identical to run.py.
Run: OMP_NUM_THREADS=1 python experiments/wp1_robot_benchmark/run_sensitivity.py
"""
import importlib.util
import json
import os
import pickle
import sys
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
_argv = sys.argv
sys.argv = [_argv[0], "--amended"]
spec = importlib.util.spec_from_file_location("wp1run", os.path.join(HERE, "run.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)  # run.py guards main(), so only definitions load
sys.argv = _argv

from wmt import wp1_nav as nav  # noqa: E402
from wmt.align import apply, init_from_camera  # noqa: E402
from wmt.raster import yaw_camera  # noqa: E402
from wmt.stats import paired_bootstrap  # noqa: E402
from wmt.synth import TRUTH, YAWS, load_truth  # noqa: E402

RES = os.path.join(ROOT, "results")
POLICIES, TRUST = R.POLICIES, R.TRUST
VARIANTS = {"S0": dict(trust_blind=True, uo_blind=False), "S1": dict(trust_blind=True, uo_blind=True),
            "S1b": dict(trust_blind=False, uo_blind=False)}
UO = "unknown_obstacle"
_truth = {}


def run_case(idx, world, yaw, T, trust_blind, uo_blind):
    """Copy of run.run_case with AMENDED=True (A1-A4) and switches for who gets A2. Everything else is unchanged."""
    c = pickle.load(open(os.path.join(ROOT, "out", "cases", f"{world}_{yaw}.pkl"), "rb"))
    TP = T["centers"][T["opacity"] > 0.3]
    yT = nav.floor_height(TP)
    t_floor = nav.floor_grid(TP, yT)
    t_obst_infl = nav.inflate(nav.obstacle_grid(TP, yT))
    t_floor[nav.START] = True
    t_obst_infl[nav.START] = False
    t_free = t_floor & ~t_obst_infl
    Gc = c["G"]["centers"].astype(np.float64)
    prior_y = np.round(Gc[~c["from_photo"], 1], 3)
    vals, cnt = np.unique(prior_y, return_counts=True)
    y_floor_gen = float(vals[np.argsort(-cnt)[:2]].max())
    GP = apply(init_from_camera(yaw_camera(yaw)[0], np.zeros(3), yT / y_floor_gen), Gc)
    yG = yT
    g_obst = nav.obstacle_grid(GP, yG)
    g_obst_infl = nav.inflate(g_obst)
    seen = c["seen"]
    thr = np.percentile(c["abs_depth_std"][seen], R.ABSSTD_Q)
    floors = {"any": nav.floor_grid(GP, yG), "frustum": nav.floor_grid(GP, yG, c["in_frustum"]),
              "visibility": nav.floor_grid(GP, yG, c["coverage"] >= R.COVERAGE_THR),
              "ours": nav.floor_grid(GP, yG, seen & (c["abs_depth_std"] <= thr)), "seen": nav.floor_grid(GP, yG, seen)}
    free = {"no_mask": floors["any"] & ~g_obst_infl, "frustum": floors["frustum"] & ~g_obst_infl,
            "visibility": floors["visibility"] & ~g_obst_infl, "ours": floors["ours"] & ~g_obst_infl,
            UO: nav.wedge_free(g_obst, floors["any"], yaw, c["hfov_hat"]), "oracle": t_free}
    blind = nav.wedge_los(g_obst, yaw, c["hfov_hat"], r_max=nav.blind_radius(yT, c["hfov_hat"])) & ~g_obst_infl  # A2
    if trust_blind:
        for k in TRUST:
            free[k] = free[k] | blind
    if uo_blind:
        free[UO] = free[UO] | blind
    foot = nav.disc(0.3) & ~g_obst_infl  # A3 (all non-oracle policies, as in run.py)
    for k in free:
        if k != "oracle":
            free[k] = free[k] | foot
    for k in free:
        free[k] = free[k].copy()
        free[k][nav.START] = True
    d_t, _ = nav.dijkstra(t_free)
    ii, jj = np.meshgrid(np.arange(nav.N), np.arange(nav.N), indexing="ij")
    far = np.hypot(ii - nav.START[0], jj - nav.START[1]) * nav.CELL >= R.MIN_DIST
    cand = np.argwhere(np.isfinite(d_t) & far & t_free)
    is_seen = floors["seen"][cand[:, 0], cand[:, 1]]
    rng = np.random.default_rng(1000 + idx)
    a, b = np.nonzero(is_seen)[0], np.nonzero(~is_seen)[0]
    ta, tb = min(len(a), R.N_PER_STRATUM), min(len(b), R.N_PER_STRATUM)
    if ta < R.N_PER_STRATUM:
        tb = min(len(b), R.N_TOTAL - ta)
    if tb < R.N_PER_STRATUM:
        ta = min(len(a), R.N_TOTAL - tb)
    sel = np.concatenate([rng.choice(a, ta, replace=False), rng.choice(b, tb, replace=False)]) if len(cand) else np.array([], int)
    goals = [(tuple(cand[s]), "seen" if is_seen[s] else "unseen") for s in sel]
    out = {}
    for pol in POLICIES:
        dist, par = nav.dijkstra(free[pol])
        recs = []
        for g, stratum in goals:
            if not np.isfinite(dist[g]):
                recs.append(dict(planned=False, stratum=stratum))
                continue
            path = nav.extract_path(par, g, free[pol].shape)
            recs.append(dict(planned=True, fail=nav.execute(path, t_floor, t_obst_infl), stratum=stratum,
                             length=nav.path_length(path), opt=float(d_t[g] * nav.CELL)))
        out[pol] = recs
    return dict(world=world, yaw=yaw, n_goals=len(goals), n_seen=sum(s == "seen" for _, s in goals),
                blind_cells=int(blind.sum()), policies=out)


def run_variant(name):
    cfg = VARIANTS[name]
    cases, summ, i = [], [], 0
    for world in TRUTH:
        if world not in _truth:
            _truth[world] = load_truth(world)
        for yaw in YAWS:
            case = run_case(i, world, yaw, _truth[world], **cfg)
            cases.append({k: v for k, v in case.items() if k != "policies"})
            summ.append(R.summarize(case))
            i += 1
    return name, cases, summ


def boot_ci(a, b, alpha, n_boot=10000, seed=0):
    """Percentile interval of the mean paired difference over cases (same scheme as wmt.stats.paired_bootstrap)."""
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[np.isfinite(d)]
    if len(d) == 0:
        return dict(mean=float("nan"), lo=float("nan"), hi=float("nan"), n=0)
    means = np.random.default_rng(seed).choice(d, (n_boot, len(d)), replace=True).mean(1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(mean=float(d.mean()), lo=float(lo), hi=float(hi), n=int(len(d)))


def aggregate(cases, summ):
    out = {"means": {}, "vs_uo": {}, "strata": {}, "n_goals": int(sum(c["n_goals"] for c in cases)),
           "n_seen_goals": int(sum(c["n_seen"] for c in cases)), "cases_with_seen": int(sum(c["n_seen"] > 0 for c in cases)),
           "uo_completes_anything_in_cases": int(sum(s[UO]["completion"] > 0 for s in summ))}
    metrics = ("fail_rate", "completion", "planned_rate", "path_ratio_common")
    for p in POLICIES:
        out["means"][p] = {m: float(np.nanmean([s[p][m] for s in summ])) for m in metrics}
        out["means"][p]["n_common_cases_path_ratio"] = int(sum(np.isfinite(s[p]["path_ratio_common"]) for s in summ))
    for p in POLICIES:
        if p == UO:
            continue
        e = {}
        for m in ("fail_rate", "completion", "path_ratio_common"):
            a, b = [s[p][m] for s in summ], [s[UO][m] for s in summ]
            e[m] = dict(**paired_bootstrap(a, b), bonferroni_98_33=boot_ci(a, b, 0.05 / 3))
        e["safety_noninferior"] = bool(e["fail_rate"]["hi"] <= 0.02)
        e["benefit"] = bool(e["completion"]["lo"] > 0 or e["path_ratio_common"]["hi"] < 0)
        e["gate"] = bool(e["safety_noninferior"] and e["benefit"])
        out["vs_uo"][p] = e
    for st, key_c, key_f in (("seen", "completion_seen", "fail_seen"), ("unseen", "completion_unseen", "fail_unseen")):
        idx = [k for k, s in enumerate(summ) if np.isfinite(s[UO][key_c])]
        n_goals = int(sum(cases[k]["n_seen"] if st == "seen" else cases[k]["n_goals"] - cases[k]["n_seen"] for k in idx))
        ent = dict(n_cases=len(idx), n_goals=n_goals, means={}, vs_uo={})
        for p in POLICIES:
            ent["means"][p] = dict(completion=float(np.mean([summ[k][p][key_c] for k in idx])) if idx else float("nan"),
                                   fail_rate=float(np.mean([summ[k][p][key_f] for k in idx])) if idx else float("nan"))
            if p != UO and idx:
                ent["vs_uo"][p] = {m: paired_bootstrap([summ[k][p][kk] for k in idx], [summ[k][UO][kk] for k in idx])
                                   for m, kk in (("completion", key_c), ("fail_rate", key_f))}
        out["strata"][st] = ent
    return out


def main():
    with Pool(3) as pool:
        results = pool.map(run_variant, list(VARIANTS))
    summary = {}
    for name, cases, summ in results:
        agg = aggregate(cases, summ)
        summary[name] = agg
        json.dump(dict(variant=name, config=VARIANTS[name], aggregate=agg, per_case=summ, cases=cases),
                  open(os.path.join(RES, f"wp1_sensitivity_{name}.json"), "w"), indent=2)
    # reproduction check of S0 against the amended results
    ref = json.load(open(os.path.join(RES, "wp1_results_amended.json")))["aggregate"]
    diffs = []
    for p in POLICIES:
        for m in ("fail_rate", "completion"):
            diffs.append(abs(summary["S0"]["means"][p][m] - ref["per_policy_mean"][p][m]))
    for p in R.TRUST:
        for m in ("fail_rate", "completion"):
            r = ref["vs_unknown_obstacle"][p][m]
            s = summary["S0"]["vs_uo"][p][m]
            diffs += [abs(r["mean"] - s["mean"]), abs(r["lo"] - s["lo"]), abs(r["hi"] - s["hi"])]
    summary["S0_reproduction_max_abs_diff"] = float(max(diffs))
    json.dump(summary, open(os.path.join(RES, "wp1_sensitivity_summary.json"), "w"), indent=2)
    print("S0 reproduction max abs diff:", summary["S0_reproduction_max_abs_diff"])
    for name in VARIANTS:
        a = summary[name]
        print(name, {p: (round(a["means"][p]["completion"], 3), round(a["means"][p]["fail_rate"], 3)) for p in POLICIES})


if __name__ == "__main__":
    main()
