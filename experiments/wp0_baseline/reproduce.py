"""WP0: reproduce the 4.1 baseline on the migrated code and compare with recorded numbers.

Recorded (the author's earlier illumination study, not part of this repository; pooled over 12 cases, rank-normalised pooling):
  AUROC all: ours 1-R 0.8346, visibility 0.8317, frustum 0.7428
Tolerance for 'reproduced': |difference| <= 0.01.
Per-case results are also bootstrapped (paired over cases): ours vs visibility, ours vs frustum.

Run: python experiments/wp0_baseline/reproduce.py   (~5-10 min CPU)
"""
import json
import os
import pickle
import sys

import numpy as np
from scipy.stats import rankdata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from wmt.benchmark import build_case  # noqa: E402
from wmt.stats import auroc, paired_bootstrap  # noqa: E402
from wmt.synth import TRUTH, YAWS, load_truth  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "out", "cases")
RES = os.path.join(os.path.dirname(__file__), "..", "..", "results")
os.makedirs(OUT, exist_ok=True)
os.makedirs(RES, exist_ok=True)
RECORDED = {"ours": 0.8346, "visibility": 0.8317, "frustum": 0.7428}

per_case, pooled = [], {k: [] for k in ("ours", "visibility", "frustum")}
for world in TRUTH:
    T = load_truth(world)
    for yaw in YAWS:
        path = os.path.join(OUT, f"{world}_{yaw}.pkl")
        if os.path.exists(path):
            case = pickle.load(open(path, "rb"))
        else:
            case = build_case(world, yaw, truth=T)
            pickle.dump(case, open(path, "wb"))
        scores = {"ours": 1 - case["R"], "visibility": -case["coverage"], "frustum": (~case["in_frustum"]).astype(float)}
        e = case["err"] / case["tau"]
        a = {k: auroc(v, case["bad"]) for k, v in scores.items()}
        per_case.append(dict(world=world, yaw=yaw, **{f"auroc_{k}": round(v, 4) for k, v in a.items()}))
        for k, v in scores.items():
            pooled[k].append((rankdata(v) / len(v), e))
        print(world[:24], yaw, {k: round(v, 3) for k, v in a.items()}, flush=True)

pool_auroc = {k: round(auroc(np.concatenate([u for u, _ in v]), np.concatenate([e for _, e in v]) > 1), 4)
              for k, v in pooled.items()}
boot = {
    "ours_vs_visibility": paired_bootstrap([c["auroc_ours"] for c in per_case], [c["auroc_visibility"] for c in per_case]),
    "ours_vs_frustum": paired_bootstrap([c["auroc_ours"] for c in per_case], [c["auroc_frustum"] for c in per_case]),
}
diff = {k: round(pool_auroc[k] - RECORDED[k], 4) for k in RECORDED}
reproduced = all(abs(d) <= 0.01 for d in diff.values())
out = dict(pooled_auroc=pool_auroc, recorded=RECORDED, diff=diff, reproduced=reproduced, bootstrap=boot, per_case=per_case)
json.dump(out, open(os.path.join(RES, "wp0_reproduce.json"), "w"), indent=2)
print(json.dumps({k: out[k] for k in ("pooled_auroc", "diff", "reproduced", "bootstrap")}, indent=2))
