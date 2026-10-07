"""Evaluate prereg/RQ3.md criteria from results/wp3_stageA.json; write results/wp3_summary.json and plots."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RES = os.path.join(os.path.dirname(__file__), "..", "..", "results")
d = json.load(open(os.path.join(RES, "wp3_stageA.json")))
cells = d["cells"]
STD_MAX, RATIO_MIN, NU_REF = 0.10, 1e-8, 0.02


def ok(stats, nu):
    return stats["ratio"] >= RATIO_MIN and stats["std_logd_unit"] * nu <= STD_MAX


def std(stats, nu):
    return stats["std_logd_unit"] * nu


summ = {}
# S1
s1 = d["S1"]
summ["S1"] = dict(ratio=s1["ratio"], align=s1["align"], passed=bool(s1["ratio"] <= 1e-9 and s1["align"] >= 0.999),
                  ratio_with_dilation=d["S1_with_dil0.3"]["ratio"])
# S2 + S4 at the reference configuration, noise 0.02
ref = d["reference"]
summ["S2"] = dict(ratio=ref["B_dil0.3_known"]["ratio"], std_logd=std(ref["B_dil0.3_known"], NU_REF),
                  passed=bool(ok(ref["B_dil0.3_known"], NU_REF)))
summ["S4"] = {m: dict(ratio=ref[f"B_dil0.3_{m}"]["ratio"], std_logd=std(ref[f"B_dil0.3_{m}"], NU_REF),
                      passed=bool(ok(ref[f"B_dil0.3_{m}"], NU_REF))) for m in ("albedo", "light", "both")}
summ["reference_A_baseline"] = dict(ratio=ref["A_dil0.3_known"]["ratio"], std_logd=std(ref["A_dil0.3_known"], NU_REF))

# S3: favorable cells (known mode)
fav = [c for c in cells if c["phi"] in (60, 90, 120) and c["elev"] in (35, 50, 65) and c["R"] <= 0.1 and c["floor_albedo"] == 0.6]
for nu in (0.005, 0.02):
    summ[f"S3_nu{nu}"] = dict(n=len(fav), frac=float(np.mean([ok(c["known"], nu) for c in fav])))
summ["S3"] = dict(frac=summ["S3_nu0.02"]["frac"], passed=bool(summ["S3_nu0.02"]["frac"] >= 0.5))
summ["gate"] = "PASS" if (summ["S1"]["passed"] and summ["S2"]["passed"] and summ["S3"]["passed"]) else "FAIL"
summ["gate_robust"] = bool(summ["gate"] == "PASS" and summ["S4"]["light"]["passed"])


# Fraction passing by regime (all depths, dil 0.3), by mode, noise 0.02
def frac(sel, mode, nu=NU_REF):
    cs = [c for c in cells if sel(c)]
    return dict(n=len(cs), frac=float(np.mean([ok(c[mode], nu) for c in cs])),
                median_std=float(np.median([std(c[mode], nu) for c in cs])))


regimes = {
    "all cells": lambda c: True,
    "favorable (lateral, mid elev, hard light, bright floor)": lambda c: c["phi"] in (60, 90, 120) and c["elev"] in (35, 50, 65) and c["R"] <= 0.1 and c["floor_albedo"] == 0.6,
    "light near camera axis (phi<=15)": lambda c: c["phi"] <= 15,
    "light behind occluder (phi>=150)": lambda c: c["phi"] >= 150,
    "overhead light (elev=80)": lambda c: c["elev"] == 80,
    "soft light R=0.6": lambda c: c["R"] == 0.6,
    "overhead and soft (elev=80, R=0.6)": lambda c: c["elev"] == 80 and c["R"] == 0.6,
    "dark floor (albedo 0.2)": lambda c: c["floor_albedo"] == 0.2,
    "bright floor (albedo 0.6)": lambda c: c["floor_albedo"] == 0.6,
}
summ["regimes"] = {r: {m: frac(sel, m) for m in ("known", "albedo", "light", "both")} for r, sel in regimes.items()}
summ["noise"] = {str(nu): {m: frac(regimes["all cells"], m, nu) for m in ("known", "albedo", "light", "both")} for nu in (0.005, 0.02, 0.05)}
summ["by_depth"] = {str(dp): {m: frac(lambda c, dp=dp: c["depth"] == dp, m) for m in ("known", "light")} for dp in (2.0, 3.0, 5.0)}
# model A baseline: should be inf everywhere
summ["A_baseline_frac_finite"] = float(np.mean([c["A_known"]["ratio"] >= 1e-10 for c in cells]))
# which direction is least informed with shadows (alignment with the old null direction)
summ["B_known_align_median"] = float(np.median([c["known"]["align"] for c in cells]))
json.dump(summ, open(os.path.join(RES, "wp3_summary.json"), "w"), indent=2)
print(json.dumps({k: summ[k] for k in ("S1", "S2", "S4", "S3", "gate", "gate_robust", "reference_A_baseline", "A_baseline_frac_finite")}, indent=2))
for r, v in summ["regimes"].items():
    print(f"{r:58s}", {m: f"{x['frac']:.2f} (med std {x['median_std']:.3f})" for m, x in v.items()})
print("noise", {k: {m: round(x["frac"], 2) for m, x in v.items()} for k, v in summ["noise"].items()})
print("depth", {k: {m: round(x["frac"], 2) for m, x in v.items()} for k, v in summ["by_depth"].items()})

# ---------------- plots ----------------
MUTED = "#898781"
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
wA, wB = np.array(ref["A_dil0.0_known"]["eig"]), np.array(ref["B_dil0.0_known"]["eig"])
x = np.arange(5)
ax[0].bar(x - 0.2, np.maximum(wA / wA[-1], 1e-20), 0.4, label="A: no shadow", color="#eb6834")
ax[0].bar(x + 0.2, wB / wB[-1], 0.4, label="B: with shadow", color="#2a78d6")
ax[0].set_yscale("log"); ax[0].set_ylim(1e-18, 2)
ax[0].set_xticks(x, ["λ1 (min)", "λ2", "λ3", "λ4", "λ5 (max)"])
ax[0].set_title("Fisher eigenvalues / λ_max, reference config (dil=0, known light)", fontsize=10, loc="left")
ax[0].legend(frameon=False)
phis = sorted({c["phi"] for c in cells})
for m, col in (("known", "#2a78d6"), ("albedo", "#1baf7a"), ("light", "#eda100"), ("both", "#4a3aa7")):
    ys = [np.median([std(c[m], NU_REF) for c in cells if c["phi"] == p and c["R"] <= 0.1 and c["floor_albedo"] == 0.6 and c["elev"] in (35, 50, 65)]) for p in phis]
    ax[1].plot(phis, ys, "-o", color=col, label=f"nuisance: {m}")
ax[1].axhline(STD_MAX, color=MUTED, ls="--"); ax[1].text(2, STD_MAX * 1.15, "bar: std(log d) = 0.10", color=MUTED, fontsize=8)
ax[1].set_yscale("log"); ax[1].set_xlabel("light azimuth φ (0 = camera side, 90 = lateral, 180 = behind occluder)")
ax[1].set_ylabel("std(log d), noise 0.02"); ax[1].set_title("Depth uncertainty vs light azimuth (hard light, bright floor)", fontsize=10, loc="left")
ax[1].legend(frameon=False, fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(RES, "wp3_spectrum_and_azimuth.png"), dpi=90); plt.close()

fig, axes = plt.subplots(1, 4, figsize=(15, 3.6))
elevs = sorted({c["elev"] for c in cells})
for a, m in zip(axes, ("known", "albedo", "light", "both")):
    Z = np.array([[np.median([std(c[m], NU_REF) for c in cells if c["phi"] == p and c["elev"] == e and c["R"] == 0.1 and c["floor_albedo"] == 0.6 and c["depth"] == 3.0])
                   for p in phis] for e in elevs])
    Z = np.where(np.isfinite(Z), Z, 10)
    im = a.imshow(np.log10(Z), origin="lower", vmin=-3, vmax=1, cmap="viridis_r", aspect="auto")
    a.set_xticks(range(len(phis)), phis, fontsize=7); a.set_yticks(range(len(elevs)), elevs, fontsize=7)
    a.set_title(f"nuisance: {m}", fontsize=10, loc="left"); a.set_xlabel("light azimuth φ (°)")
axes[0].set_ylabel("light elevation (°)")
fig.colorbar(im, ax=axes, label="log10 std(log d), noise 0.02")
plt.savefig(os.path.join(RES, "wp3_heatmaps.png"), dpi=90, bbox_inches="tight"); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
for m, col in (("known", "#2a78d6"), ("light", "#eda100")):
    for alb, ls in ((0.6, "-"), (0.2, "--")):
        ys = [np.median([std(c[m], NU_REF) for c in cells if c["R"] == R and c["floor_albedo"] == alb and c["phi"] in (60, 90, 120) and c["elev"] in (35, 50, 65)]) for R in (0.0, 0.1, 0.3, 0.6)]
        ax[0].plot((0.0, 0.1, 0.3, 0.6), ys, ls, marker="o", color=col, label=f"{m}, albedo {alb}")
ax[0].axhline(STD_MAX, color=MUTED, ls=":"); ax[0].set_yscale("log"); ax[0].set_xlabel("light radius R_l (m, at 4 m)")
ax[0].set_ylabel("median std(log d)"); ax[0].legend(frameon=False, fontsize=8); ax[0].set_title("Soft light and dark floor (lateral light)", fontsize=10, loc="left")
for m, col in (("known", "#2a78d6"), ("albedo", "#1baf7a"), ("light", "#eda100"), ("both", "#4a3aa7")):
    ax[1].plot((0.005, 0.02, 0.05), [summ["noise"][str(n)][m]["frac"] for n in (0.005, 0.02, 0.05)], "-o", color=col, label=m)
ax[1].set_xscale("log"); ax[1].set_xlabel("pixel noise"); ax[1].set_ylabel("fraction of all cells with std(log d) ≤ 0.10")
ax[1].legend(frameon=False, fontsize=8); ax[1].set_title("Noise sensitivity (all sweep cells)", fontsize=10, loc="left")
plt.tight_layout(); plt.savefig(os.path.join(RES, "wp3_soft_dark_noise.png"), dpi=90); plt.close()
print("plots written")
