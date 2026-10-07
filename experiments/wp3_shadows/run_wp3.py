"""WP3 Stage A: joint Fisher analysis of (depth, size) with and without the shadow term. See prereg/RQ3.md.

Run: PYTHONPATH=src OMP_NUM_THREADS=4 python experiments/wp3_shadows/run_wp3.py   (~minutes, CPU)
Writes results/wp3_stageA.json
"""
import itertools
import json
import os
import time

import numpy as np
import torch

from wmt.wp3_shadow_model import ShadowModel, analyze, marginal_fisher

torch.set_num_threads(4)
RES = os.path.join(os.path.dirname(__file__), "..", "..", "results")
MODES = {"known": (), "albedo": ("albedo",), "light": ("light",), "both": ("albedo", "light")}
PHIS = (0, 15, 30, 45, 60, 90, 120, 150, 180)
ELEVS = (20, 35, 50, 65, 80)
RADII = (0.0, 0.1, 0.3, 0.6)
ALBEDOS = (0.6, 0.2)
DEPTHS = (2.0, 3.0, 5.0)
REF = dict(phi_deg=60, elev_deg=50, light_radius=0.1, albedo=0.6, depth=3.0)


def cell_stats(model, shadow, nuis):
    a = analyze(marginal_fisher(model.jacobian(shadow, nuis), 1.0), 1.0)  # noise=1; std scales linearly with noise
    return dict(ratio=a["ratio"], align=a["align"], std_logd_unit=a["std_logd"], std_logsig_unit=a["std_logsig"],
                eig=a["eig"])


out = dict(prereg_hash=open(os.path.join(RES, "wp3_prereg_hash.txt")).read().split()[0])

# ---- S1: exact null, model A, dil = 0, reference light, known ----
m0 = ShadowModel(**REF, dil=0.0)
out["S1"] = cell_stats(m0, False, ())
out["S1_with_dil0.3"] = cell_stats(ShadowModel(**REF, dil=0.3), False, ())

# ---- reference configuration: A vs B, dil in {0, 0.3}, all modes ----
ref = {}
for dil in (0.0, 0.3):
    m = ShadowModel(**REF, dil=dil)
    for name, nuis in MODES.items():
        ref[f"B_dil{dil}_{name}"] = cell_stats(m, True, nuis)
    ref[f"A_dil{dil}_known"] = cell_stats(m, False, ())
out["reference"] = ref

# ---- sweep (dil = 0.3) ----
cells = []
t0 = time.time()
grid = list(itertools.product(PHIS, ELEVS, RADII, ALBEDOS, DEPTHS))
for n, (phi, e, R, alb, dep) in enumerate(grid):
    m = ShadowModel(phi_deg=phi, elev_deg=e, light_radius=R, albedo=alb, depth=dep, dil=0.3)
    row = dict(phi=phi, elev=e, R=R, floor_albedo=alb, depth=dep)
    for name, nuis in MODES.items():
        row[name] = cell_stats(m, True, nuis)
    row["A_known"] = cell_stats(m, False, ())
    cells.append(row)
    if n % 60 == 0:
        print(f"{n}/{len(grid)} cells, {time.time() - t0:.0f}s", flush=True)
out["cells"] = cells
json.dump(out, open(os.path.join(RES, "wp3_stageA.json"), "w"))
print("wrote results/wp3_stageA.json", f"({time.time() - t0:.0f}s)")
