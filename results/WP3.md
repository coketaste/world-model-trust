# WP3 / RQ3 results: can shadows break the single-view depth–size ambiguity? (Stage A, CPU PoC)

Pre-registration: `prereg/RQ3.md` (SHA-256 and timestamp self-recorded before the first run in `results/wp3_prereg_hash.txt`; the file was not committed or tagged beforehand). Code: `src/wmt/wp3_shadow_model.py`, `experiments/wp3_shadows/`. Raw output: `results/wp3_stageA.json`, `wp3_summary.json`, `wp3_stress.json`. Plots: `wp3_spectrum_and_azimuth.png`, `wp3_heatmaps.png`, `wp3_soft_dark_noise.png` (generated, **not visually inspected**).

## Gate decision: **PASS** (S1 ∧ S2 ∧ S3), with S4 also passing at the reference configuration

This is a statement about **local identifiability under an idealised forward model** (Fisher information), not about accuracy on real photos.

| Criterion | Result | Verdict |
|---|---|---|
| S1: model A (no shadow), dil = 0: λ_min/λ_max ≤ 1e-9, null aligned ≥ 0.999 | 8.1e-18, alignment 1.0000 (same with dil = 0.3: 5.1e-18) | pass |
| S2: model B (shadow), reference config, noise 0.02: ratio ≥ 1e-8 and std(log d) ≤ 0.10 | ratio 2.7e-3, **std(log d) = 0.0049** (model A: ∞) | pass |
| S3: ≥ 50% of favorable cells meet S2 conditions | **74%** (40 of 54 cells); by depth z = 2 / 3 / 5: **22% / 100% / 100%** | pass |
| S4 (secondary): reference config with unknown albedo / unknown light / both | std(log d) = 0.0056 / 0.0109 / 0.0159 | pass |

Model A has a finite std(log d) in **0 of 1080** sweep cells (the null is exact everywhere). Model B fails to localise depth (std = ∞ or > 0.10) in 27% of all cells (known light), mostly for the geometric reason below.

## What the numbers say

*Slice note: figures such as 100% and 60% by light azimuth refer to the 54-setup favourable slice (lateral light, mid elevation, hard light, bright floor, known light); the regime table uses all 1,080 setups.*

**Setup.** One isotropic Gaussian occluder (centre (0, 0.3, 3.0), σ = 0.35 m, opacity 0.9), a Lambertian floor, one point/area light, a 96×72 pinhole camera. Parameters (az, el, log d, log σ, log opacity). Fisher information from autodiff (cross-checked against finite differences to 1e-5), nuisance parameters marginalised with a Schur complement under flat priors. With the shadow term the least-informed direction is still mostly the old (log d, log σ) direction (median alignment ≈ 1), but it now carries positive information.

**Where the shadow term works (known light, noise 0.02, depth 3, hard light, bright floor):**

| Light azimuth φ (0 = camera side, 90 = lateral, 180 = behind occluder) | 0 | 15 | 30 | 45 | 60 | 90 | 120 | 150 | 180 |
|---|---|---|---|---|---|---|---|---|---|
| fraction of cells with std(log d) ≤ 0.10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.80 | 0.60 | 0.60 |
| median std(log d) | 0.008 | 0.007 | 0.007 | 0.006 | 0.005 | 0.005 | 0.012 | 0.034 | 0.051 |

Light elevation 20°: 67% of cells pass; ≥ 35°: 100%. Light radius 0 → 0.6 m (at 4 m): no degradation (median std 0.006 → 0.007).

**Where it fails (and a prediction of mine that was wrong).**
- **Geometric condition, not a smooth degradation:** the shadow must land on floor pixels that are inside the frame and not covered by the occluder. Floor is visible only beyond z ≈ 3.46 m here (camera 1.5 m high, ±23° vertical half-FOV). At occluder z = 2 the shadow is mostly out of frame and the information vanishes (22% pass; median std ≈ 14). Across 135 cells the count of visibly darkened floor pixels correlates with std(log d): Spearman −0.74. Cells with no visibly darkened pixels (> 10%) have median std 1.9.
- I expected a **light near the camera axis (φ ≈ 0)** to hide the shadow behind the occluder. It did not fail with a known light (100% pass), because the 1.2 m-high occluder casts a long shadow that extends past its own silhouette. It degrades with an **unknown light** (80% pass, median std 0.044 at depth 3). **Light behind the occluder (φ ≥ 150)** casts the shadow toward the camera, mostly out of frame (60% pass).
- **Dark floor (albedo 0.2):** 69% pass, median std 0.028 vs 0.009 for a bright floor (shadow contrast scales with albedo).
- **Noise:** fraction of all cells passing at noise 0.005 / 0.02 / 0.05: known 79 / 73 / 64%, unknown light 78 / 65 / 51%, unknown light + albedo 77 / 62 / 44%.
- **Overhead soft light (elev 80°, R = 0.6):** no failure in this model (67% pass, entirely due to the depth effect).

## Exploratory stress tests (not pre-registered; see Amendments)

These probe the two most optimistic assumptions of the gate.

| Test | Result |
|---|---|
| **Unknown albedo texture** (log-albedo grid) + unknown light + unknown ambient, reference config, noise 0.02. Shadow footprint for reference: 1.2 m × 0.45 m, peak darkening 45% | known texture: std(log d) 0.012; texture scale 4 m: 0.027; 2 m: 0.071; **1 m: 0.110 (misses the 0.10 bar)**; **0.5 m: 0.293** |
| **Wrong light** (estimator's light displaced by δ, first-order bias of log d, 12 random directions) | δ = 0.05 m: 0.002 median (max 0.006); 0.1 m: 0.006; 0.3 m: 0.021 (max 0.038); 1.0 m: 0.037 (max 0.065) |

So the information collapses when unknown albedo structure has a scale comparable to the shadow itself, which is what real textured floors have. A light error of 1 m (25% of the light distance) biases log d by about 4–7% in this model.

## Honest scope

- **Inverse crime:** data and estimator use the same forward model. This shows local identifiability, not that the estimate would be accurate on real photos.
- **Idealised physics:** one isotropic Gaussian occluder with known colour/opacity-model, one Lambertian floor plane, a point or small area light, "max-response" Gaussian shadows, no interreflection, no multiple lights. Real indoor light is soft, multi-source and partly baked.
- **Splat worlds store appearance as colour**, with no separately modelled light or material, so the 12-case benchmark photos contain no real cast shadows and there is nothing real to test the idea on without circularity.
- **Prior art:** Methods that recover geometry from shadows or two-bounce light already exist, including ShadowNeuS (arXiv 2211.14086) and, with lidar, PlatoNeRF (arXiv 2312.14239); their exact capture requirements were not re-verified in the later literature review. The claim here, single image under one natural light, is only supported *in simulation*, and is most plausible for sunlit/outdoor scenes or single dominant indoor lamps.
- **Prior knowledge assumed:** light position, intensity and ambient level are known in the gate; the marginalised versions (unknown light, albedo, ambient) are the more honest figures.
- **Stage B was skipped:** the benchmark photos have no cast shadows (splat worlds store appearance as colour), so any shadow-consistency detection would be circular. Rendering shadows into the photos with our own light model would test only our own model.

## Seismic analogy

A single reflection traveltime cannot separate velocity from depth: a shallower reflector in slow rock looks like a deeper one in fast rock (Bickel 1990), and offset (moveout) resolves it. A single photo has the same null: near-and-small equals far-and-large, and camera baseline (parallax) would resolve it. A cast shadow plays the role of a multiple: energy that took a different path (here, a second "view" from the light's position, with a real baseline) and so illuminates a quantity the primary does not constrain. As in imaging with multiples, its usefulness depends on whether that secondary path lands inside the recorded aperture, which is exactly the "shadow in frame" condition found above.

## Reproduce

```bash
PYTHONPATH=src OMP_NUM_THREADS=4 venv/bin/python experiments/wp3_shadows/run_wp3.py      # ~3 min
PYTHONPATH=src venv/bin/python experiments/wp3_shadows/analyze_wp3.py
PYTHONPATH=src OMP_NUM_THREADS=4 venv/bin/python experiments/wp3_shadows/stress_wp3.py
venv/bin/python -m pytest -q tests/test_wp3_shadow.py
```
