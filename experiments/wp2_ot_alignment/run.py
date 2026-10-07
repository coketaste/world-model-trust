"""WP2 runner: OT vs ICP convergence-basin sweep (see prereg/RQ2.md and its Amendments).

  python experiments/wp2_ot_alignment/run.py tune
  python experiments/wp2_ot_alignment/run.py eval --variants A B C
Needs LD_LIBRARY_PATH to contain a libusb-1.0.so.0 shim for open3d (see results/WP2.md).
"""
import argparse
import json
import os
import pickle
import sys
import time
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from wmt.align import apply, icp_similarity  # noqa: E402
from wmt.wp2_align import (IDENTITY, icp_point_to_plane_sim, ot_align, perturbation, pose_error,  # noqa: E402
                           voxel_pick)

CASES = os.path.join(ROOT, "out", "cases")
RES = os.path.join(ROOT, "results")
LEVELS = [0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0]
TUNE_WORLD = "warm_traditional_kitchen_interior"
N_ICP, N_OT_SRC, N_OT_TGT = 6000, 600, 1500          # amended sizes, see prereg Amendments
OT_STAGES, OT_ITERS = 10, 6


def case_files(tune):
    names = sorted(f[:-4] for f in os.listdir(CASES) if f.endswith(".pkl"))
    return [n for n in names if (n.startswith(TUNE_WORLD)) == tune]


def prepare(name, variant):
    pk = pickle.load(open(os.path.join(CASES, name + ".pkl"), "rb"))
    truth = pk["truth_pts"].astype(np.float64)
    if variant == "A":
        src_ref = apply(pk["sim"], pk["G"]["centers"][pk["seen"]].astype(np.float64))
    elif variant == "B":
        src_ref = apply(pk["sim"], pk["G"]["centers"].astype(np.float64))
    else:  # C: noisy truth subset in the viewing cone, reference = identity
        yaw = np.radians(pk["yaw"])
        fwd = np.array([np.sin(yaw), 0, np.cos(yaw)])
        r = np.linalg.norm(truth, axis=1)
        cosang = (truth @ fwd) / np.maximum(r, 1e-9)
        sel = (r > 0.3) & (cosang > np.cos(np.radians(50)))
        src_ref = truth[sel] + np.random.default_rng(7).normal(0, 0.02, (sel.sum(), 3))
    E = src_ref[voxel_pick(src_ref, N_ICP)]
    E_ot = E[voxel_pick(E, N_OT_SRC)]
    tgt_ot = truth[voxel_pick(truth, N_OT_TGT)]
    return pk, truth, E, E_ot, tgt_ot


def target_normals(truth):
    import open3d as o3d
    pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(truth))
    pc.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(20))
    return np.asarray(pc.normals)


def fpfh_align(E, truth, cache):
    import open3d as o3d
    vox = 0.15

    def feats(P):
        pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(P)).voxel_down_sample(vox)
        pc.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=2 * vox, max_nn=30))
        f = o3d.pipelines.registration.compute_fpfh_feature(pc, o3d.geometry.KDTreeSearchParamHybrid(radius=5 * vox, max_nn=100))
        return pc, f
    if "tgt" not in cache:
        cache["tgt"] = feats(truth)
    sp, sf = feats(E)
    tp, tf = cache["tgt"]
    reg = o3d.pipelines.registration
    res = reg.registration_ransac_based_on_feature_matching(
        sp, tp, sf, tf, True, 1.5 * vox, reg.TransformationEstimationPointToPoint(True), 3,
        [reg.CorrespondenceCheckerBasedOnDistance(1.5 * vox)], reg.RANSACConvergenceCriteria(20000, 0.99))
    M = np.asarray(res.transformation)
    s = float(np.cbrt(max(np.linalg.det(M[:3, :3]), 1e-12)))
    return s, M[:3, :3] / s, M[:3, 3]


BAD = (float("nan"), np.full((3, 3), np.nan), np.full(3, np.nan))


def safe(fn, *a, **k):
    """Run an alignment; a degenerate (NaN) solution that makes the KD-tree raise counts as a failed run."""
    try:
        out = fn(*a, **k)
        return out[0] if (isinstance(out, tuple) and len(out) == 2 and isinstance(out[1], list)) else out
    except ValueError:
        return BAD


def worker(job):
    name, variant, levels, draws, seed_base, ot_cfgs, methods, fpfh_draws = job
    cache_path = os.path.join(RES, "wp2_cache", f"{variant}_{name}_{'-'.join(sorted(ot_cfgs))}.json")
    if seed_base >= 1000 and os.path.exists(cache_path):
        return json.load(open(cache_path))
    t0 = time.time()
    pk, truth, E, E_ot, tgt_ot = prepare(name, variant)
    tree = cKDTree(truth)
    nrm = target_normals(truth) if "p2plane" in methods else None
    tau = pk["tau"]
    cidx = sum(map(ord, name)) % 997
    fcache = {}
    out = []
    for li, lev in enumerate(levels):
        for dr in range(draws):
            rng = np.random.default_rng(seed_base + 7919 * cidx + 101 * li + dr)
            P = perturbation(lev, rng)
            X0, X0_ot = apply(P, E), apply(P, E_ot)
            results = {}
            if "icp" in methods:
                results["icp"] = safe(icp_similarity, X0, tree, truth, IDENTITY, iters=100)
            if "p2plane" in methods:
                results["p2plane"] = safe(icp_point_to_plane_sim, X0, tree, truth, nrm, iters=100)
            for cname, cfg in ot_cfgs.items():
                s_ot = ot_align(X0_ot, tgt_ot, stages=OT_STAGES, iters=OT_ITERS, **cfg)
                results[cname] = s_ot
                if "hybrid" in methods:
                    results[cname + "+icp"] = safe(icp_similarity, X0, tree, truth, s_ot, iters=30)
            if "fpfh" in methods and dr < fpfh_draws:
                results["fpfh"] = safe(fpfh_align, X0, truth, fcache)
            for m, sim in results.items():
                if not (np.isfinite(sim[0]) and np.all(np.isfinite(sim[1])) and np.all(np.isfinite(sim[2]))):
                    err, acc = float("inf"), float("inf")      # degenerate (NaN) transform counts as failure
                else:
                    err = pose_error(sim, X0, E)
                    acc = float(np.median(tree.query(apply(sim, X0), k=1)[0]))
                out.append(dict(case=name, variant=variant, level=lev, draw=dr, method=m, err=err, acc=acc,
                                succ_strict=bool(err <= 0.25 * tau), succ_coarse=bool(err <= 1.0 * tau), tau=tau))
    print(f"  {name} {variant}: {len(out)} runs in {time.time() - t0:.0f}s", flush=True)
    if seed_base >= 1000:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        json.dump(out, open(cache_path, "w"))
    return out


def run_jobs(jobs, procs=4):
    with Pool(procs) as p:
        res = p.map(worker, jobs, chunksize=1)
    return [r for rs in res for r in rs]


def tune():
    grid = {f"ot_rho{rho}_eps{e0}": dict(rho=rho, eps_start=e0) for rho in (0.05, 0.1, 0.2, 0.5) for e0 in (0.5, 1.0, 2.0, 4.0)}
    jobs = [(n, v, [0.2, 0.5, 1.0], 3, 0, grid, ["ot"], 0) for n in case_files(True) for v in ("A", "B")]
    runs = run_jobs(jobs)
    summ = {}
    for r in runs:
        d = summ.setdefault(r["method"], dict(strict=0, coarse=0, n=0))
        d["strict"] += r["succ_strict"]
        d["coarse"] += r["succ_coarse"]
        d["n"] += 1
    best = max(summ, key=lambda k: (summ[k]["strict"] + summ[k]["coarse"], summ[k]["coarse"]))
    json.dump(dict(grid=summ, selected=best, selected_cfg=grid[best]), open(os.path.join(RES, "wp2_tuning.json"), "w"), indent=2)
    for k, v in sorted(summ.items(), key=lambda kv: -(kv[1]["strict"] + kv[1]["coarse"])):
        print(k, v)
    print("selected:", best, grid[best])


def evaluate(variants, draws):
    cfg = json.load(open(os.path.join(RES, "wp2_tuning.json")))["selected_cfg"]
    for v in variants:
        methods = ["icp", "p2plane", "ot", "hybrid"] + (["fpfh"] if v == "A" else [])
        jobs = [(n, v, LEVELS, draws, 1000, {"ot": cfg}, methods, 2) for n in case_files(False)]
        runs = run_jobs(jobs)
        json.dump(runs, open(os.path.join(RES, f"wp2_runs_{v}.json"), "w"))
        print(f"variant {v}: {len(runs)} runs saved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["tune", "eval"])
    ap.add_argument("--variants", nargs="+", default=["A", "B", "C"])
    ap.add_argument("--draws", type=int, default=5)
    a = ap.parse_args()
    os.makedirs(RES, exist_ok=True)
    tune() if a.mode == "tune" else evaluate(a.variants, a.draws)
