"""WP3 exploratory stress tests (NOT pre-registered; see Amendments in prereg/RQ3.md).

T1  Unknown albedo TEXTURE at spatial scale s (bilinear grid of log-albedo nodes, flat prior) + unknown light
    position/gain + unknown ambient: how does std(log d) degrade as the texture scale approaches the shadow size?
T2  Wrong-light bias: the light used by the estimator is displaced from the truth; first-order bias of the
    least-squares estimate of log d, b = J'^+ (I_true - I'(theta0)), vs the Fisher std.

Run: PYTHONPATH=src OMP_NUM_THREADS=4 python experiments/wp3_shadows/stress_wp3.py   -> results/wp3_stress.json
"""
import json
import os

import numpy as np
import torch

from wmt.wp3_shadow_model import ShadowModel, analyze, marginal_fisher

torch.set_num_threads(4)
RES = os.path.join(os.path.dirname(__file__), "..", "..", "results")
REF = dict(phi_deg=60, elev_deg=50, light_radius=0.1, albedo=0.6, depth=3.0, dil=0.3)
NU = 0.02
out = {}


def hat_columns(m, s, x_rng=(-9.0, 9.0), z_rng=(3.0, 15.0)):
    """Bilinear hat basis weights over the visible floor points: (N_pix, n_nodes), dropping empty nodes."""
    p = m.p.numpy()
    hit = m.hit.numpy()
    xs, zs = np.arange(x_rng[0], x_rng[1] + s, s), np.arange(z_rng[0], z_rng[1] + s, s)
    Wx = np.maximum(0, 1 - np.abs(p[:, 0:1] - xs[None]) / s)
    Wz = np.maximum(0, 1 - np.abs(p[:, 2:3] - zs[None]) / s)
    B = (Wx[:, :, None] * Wz[:, None, :]).reshape(len(p), -1) * hit[:, None]
    return B[:, B.sum(0) > 1e-9]


# ---------- T1 ----------
m = ShadowModel(**REF)
nuis = ("light", "ambient")
th0 = m.theta0(nuis)
J_core = m.jacobian(True, nuis)                       # 5 occluder + 4 light + 1 ambient
F_floor, a_cam = (t.detach().numpy() for t in m.parts(th0, True, nuis))
base = (1 - a_cam) * F_floor
t1 = {}
for s in (None, 4.0, 2.0, 1.0, 0.5):
    if s is None:
        J = J_core                                    # texture known (constant albedo), light + ambient unknown
    else:
        B = hat_columns(m, s)
        J = np.hstack([J_core, base[:, None] * B])    # d I / d log-albedo_k = (1 - a_cam) F w_k
    a = analyze(marginal_fisher(J, 1.0), 1.0)
    t1["known texture" if s is None else f"scale {s} m ({J.shape[1] - J_core.shape[1]} nodes)"] = dict(
        ratio=a["ratio"], std_logd_at_nu0p02=a["std_logd"] * NU, align=a["align"])
    print("T1", list(t1)[-1], t1[list(t1)[-1]], flush=True)
out["T1"] = t1

# shadow footprint size for context: width of the region with >50% transmittance loss, in metres on the floor
p = m.p.numpy()
hit = m.hit.numpy()
th = m.theta0(())
F_s, _ = (t.detach().numpy() for t in m.parts(th, True, ()))
F_ns, _ = (t.detach().numpy() for t in m.parts(th, False, ()))
shade = np.where(hit, 1 - F_s / np.maximum(F_ns, 1e-9), 0)
dark = (shade > 0.25) & hit
out["shadow_footprint"] = dict(n_px=int(dark.sum()),
                               x_extent_m=float(np.ptp(p[dark, 0])) if dark.any() else 0.0,
                               z_extent_m=float(np.ptp(p[dark, 2])) if dark.any() else 0.0,
                               max_darkening=float(shade.max()))
print("shadow footprint", out["shadow_footprint"])

# ---------- T2 ----------
rng = np.random.default_rng(0)
I_true = m.forward(m.theta0(()), True, ()).detach().numpy()
t2 = []
for delta in (0.05, 0.1, 0.3, 1.0):
    biases = []
    for _ in range(12):
        v = rng.normal(size=3)
        v /= np.linalg.norm(v)
        mw = ShadowModel(**REF)
        mw.L_true = m.L_true + delta * v
        th_w = mw.theta0(())
        Jw = mw.jacobian(True, ())
        r = I_true - mw.forward(th_w, True, ()).detach().numpy()
        b = np.linalg.lstsq(Jw, r, rcond=None)[0]
        biases.append(float(abs(b[2])))
    t2.append(dict(light_error_m=delta, median_abs_bias_logd=float(np.median(biases)), max_abs_bias_logd=float(np.max(biases))))
    print("T2", t2[-1], flush=True)
out["T2"] = t2
out["fisher_std_known_ref"] = analyze(marginal_fisher(m.jacobian(True, ()), 1.0), 1.0)["std_logd"] * NU
json.dump(out, open(os.path.join(RES, "wp3_stress.json"), "w"), indent=2)
print("wrote results/wp3_stress.json")
