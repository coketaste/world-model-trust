"""WP1 / RQ1 runner. Implements prereg/RQ1.md exactly. Run: OMP_NUM_THREADS=4 python experiments/wp1_robot_benchmark/run.py"""
import glob
import json
import os
import pickle
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from wmt import wp1_nav as nav  # noqa: E402
from wmt.align import apply, init_from_camera  # noqa: E402
from wmt.raster import yaw_camera  # noqa: E402
from wmt.stats import paired_bootstrap  # noqa: E402
from wmt.synth import TRUTH, YAWS, load_truth  # noqa: E402

POLICIES = ["no_mask", "frustum", "visibility", "ours", "unknown_obstacle", "oracle"]
TRUST = ["frustum", "visibility", "ours"]
COVERAGE_THR, ABSSTD_Q = 0.5, 80
N_PER_STRATUM, N_TOTAL, MIN_DIST = 20, 40, 1.0
RES = os.path.join(ROOT, "results")
AMENDED = "--amended" in sys.argv  # exploratory amendments A1-A3 (prereg/RQ1.md)


def run_case(idx, world, yaw, T):
    c = pickle.load(open(os.path.join(ROOT, "out", "cases", f"{world}_{yaw}.pkl"), "rb"))
    # ---- truth maps
    tm = T["opacity"] > 0.3
    TP = T["centers"][tm]
    yT = nav.floor_height(TP)
    t_floor = nav.floor_grid(TP, yT)
    t_obst_infl = nav.inflate(nav.obstacle_grid(TP, yT))
    t_floor[nav.START] = True
    t_obst_infl[nav.START] = False
    t_free = t_floor & ~t_obst_infl
    # ---- generated-world maps (aligned frame)
    Gc = c["G"]["centers"].astype(np.float64)
    if AMENDED:  # A4: align by known camera height + camera rotation instead of ICP
        prior_y = np.round(Gc[~c["from_photo"], 1], 3)
        vals, cnt = np.unique(prior_y, return_counts=True)
        y_floor_gen = float(vals[np.argsort(-cnt)[:2]].max())  # floor and ceiling faces are the two largest planar groups
        sim_h = init_from_camera(yaw_camera(yaw)[0], np.zeros(3), yT / y_floor_gen)
        GP = apply(sim_h, Gc)
    else:
        GP = apply(c["sim"], Gc)
    yG = yT if AMENDED else nav.floor_height(GP)  # A1
    g_obst = nav.obstacle_grid(GP, yG)
    g_obst_infl = nav.inflate(g_obst)
    seen = c["seen"]
    thr = np.percentile(c["abs_depth_std"][seen], ABSSTD_Q)
    floors = {
        "any": nav.floor_grid(GP, yG),
        "frustum": nav.floor_grid(GP, yG, c["in_frustum"]),
        "visibility": nav.floor_grid(GP, yG, c["coverage"] >= COVERAGE_THR),
        "ours": nav.floor_grid(GP, yG, seen & (c["abs_depth_std"] <= thr)),
        "seen": nav.floor_grid(GP, yG, seen),
    }
    free = {
        "no_mask": floors["any"] & ~g_obst_infl,
        "frustum": floors["frustum"] & ~g_obst_infl,
        "visibility": floors["visibility"] & ~g_obst_infl,
        "ours": floors["ours"] & ~g_obst_infl,
        "unknown_obstacle": nav.wedge_free(g_obst, floors["any"], yaw, c["hfov_hat"]),
        "oracle": t_free,
    }
    if AMENDED:
        r_b = nav.blind_radius(yT, c["hfov_hat"])
        blind = nav.wedge_los(g_obst, yaw, c["hfov_hat"], r_max=r_b) & ~g_obst_infl  # A2
        for k in TRUST:
            free[k] = free[k] | blind
        foot = nav.disc(0.3) & ~g_obst_infl  # A3
        for k in free:
            if k != "oracle":
                free[k] = free[k] | foot
    for k in free:
        free[k] = free[k].copy()
        free[k][nav.START] = True
    # ---- goals
    d_t, _ = nav.dijkstra(t_free)
    ii, jj = np.meshgrid(np.arange(nav.N), np.arange(nav.N), indexing="ij")
    far = np.hypot(ii - nav.START[0], jj - nav.START[1]) * nav.CELL >= MIN_DIST
    cand = np.argwhere(np.isfinite(d_t) & far & t_free)
    is_seen = floors["seen"][cand[:, 0], cand[:, 1]]
    rng = np.random.default_rng(1000 + idx)
    a, b = np.nonzero(is_seen)[0], np.nonzero(~is_seen)[0]
    ta, tb = min(len(a), N_PER_STRATUM), min(len(b), N_PER_STRATUM)
    if ta < N_PER_STRATUM:
        tb = min(len(b), N_TOTAL - ta)
    if tb < N_PER_STRATUM:
        ta = min(len(a), N_TOTAL - tb)
    sel = np.concatenate([rng.choice(a, ta, replace=False), rng.choice(b, tb, replace=False)]) if len(cand) else np.array([], int)
    goals = [(tuple(cand[s]), "seen" if is_seen[s] else "unseen") for s in sel]
    # ---- plan + execute
    out = {}
    for pol in POLICIES:
        dist, par = nav.dijkstra(free[pol])
        recs = []
        for g, stratum in goals:
            if not np.isfinite(dist[g]):
                recs.append(dict(planned=False, stratum=stratum))
                continue
            path = nav.extract_path(par, g, free[pol].shape)
            fail = nav.execute(path, t_floor, t_obst_infl)
            recs.append(dict(planned=True, fail=fail, stratum=stratum, length=nav.path_length(path),
                             opt=float(d_t[g] * nav.CELL)))
        out[pol] = recs
    return dict(world=world, yaw=yaw, n_goals=len(goals), n_seen=sum(s == "seen" for _, s in goals),
                floor_y_truth=yT, floor_y_gen=yG, truth_free_cells=int(t_free.sum()), policies=out)


def summarize(case):
    n = case["n_goals"]
    res = {}
    for pol, recs in case["policies"].items():
        planned = [r for r in recs if r["planned"]]
        fails = [r for r in planned if r["fail"]]
        res[pol] = dict(
            fail_rate=len(fails) / n, fail_given_planned=(len(fails) / len(planned)) if planned else float("nan"),
            completion=(len(planned) - len(fails)) / n, planned_rate=len(planned) / n,
            collisions=sum(r["fail"] == "collision" for r in planned) / n, falls=sum(r["fail"] == "fall" for r in planned) / n)
        for st in ("seen", "unseen"):
            rs = [r for r in recs if r["stratum"] == st]
            res[pol][f"fail_{st}"] = (sum(1 for r in rs if r["planned"] and r["fail"]) / len(rs)) if rs else float("nan")
            res[pol][f"completion_{st}"] = (sum(1 for r in rs if r["planned"] and not r["fail"]) / len(rs)) if rs else float("nan")
    uo = case["policies"]["unknown_obstacle"]
    for pol, recs in case["policies"].items():
        ratios = [r["length"] / r["opt"] for r, u in zip(recs, uo)
                  if r["planned"] and not r["fail"] and u["planned"] and not u["fail"] and r["opt"] > 0]
        res[pol]["path_ratio_common"] = float(np.mean(ratios)) if ratios else float("nan")
        res[pol]["n_common_with_uo"] = len(ratios)
    return res


def main():
    cases, summ = [], []
    i = 0
    for world in TRUTH:
        T = load_truth(world)
        for yaw in YAWS:
            case = run_case(i, world, yaw, T)
            s = summarize(case)
            cases.append(case)
            summ.append(s)
            print(f"{world[:22]:22s} yaw {yaw:3d} N={case['n_goals']:2d} (seen {case['n_seen']:2d}) | " +
                  " | ".join(f"{p[:5]} f={s[p]['fail_rate']:.2f} c={s[p]['completion']:.2f}" for p in POLICIES), flush=True)
            i += 1
    uo = "unknown_obstacle"
    agg = {"per_policy_mean": {}, "vs_unknown_obstacle": {}}
    for pol in POLICIES:
        agg["per_policy_mean"][pol] = {m: float(np.nanmean([s[pol][m] for s in summ]))
                                       for m in ("fail_rate", "completion", "planned_rate", "collisions", "falls",
                                                 "fail_seen", "fail_unseen", "completion_seen", "completion_unseen",
                                                 "path_ratio_common")}
    for pol in POLICIES:
        if pol == uo:
            continue
        entry = {}
        for m in ("fail_rate", "completion", "path_ratio_common"):
            entry[m] = paired_bootstrap([s[pol][m] for s in summ], [s[uo][m] for s in summ])
        gate_safe = entry["fail_rate"]["hi"] <= 0.02
        gate_benefit = entry["completion"]["lo"] > 0 or entry["path_ratio_common"]["hi"] < 0
        entry["passes_safety_noninferiority"] = bool(gate_safe)
        entry["passes_benefit"] = bool(gate_benefit)
        entry["passes_gate"] = bool(gate_safe and gate_benefit)
        agg["vs_unknown_obstacle"][pol] = entry
    agg["gate_passed"] = any(agg["vs_unknown_obstacle"][p]["passes_gate"] for p in TRUST)
    agg["n_goals_total"] = int(sum(c["n_goals"] for c in cases))
    os.makedirs(RES, exist_ok=True)
    json.dump(dict(aggregate=agg, per_case=summ, cases=[{k: v for k, v in c.items() if k != "policies"} for c in cases]),
              open(os.path.join(RES, "wp1_results_amended.json" if AMENDED else "wp1_results_run1_as_preregistered.json"), "w"), indent=2)
    print(json.dumps(agg, indent=2))


if __name__ == "__main__":
    main()
