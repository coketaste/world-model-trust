# Pre-registration: RQ3 — can shadows act like "multiples" to break the single-view depth–size ambiguity?

Commit/tag before running (hash recorded in results/wp3_prereg_hash.txt). Later changes go in "Amendments".

- **Date / author:** 2026-10-02 / WP3 (for the repository authors)
- **Research question:** In a single photo, a splat's depth d and size σ are jointly unobservable (move along the camera ray and scale proportionally: the image is unchanged). Does adding the cast shadow of that splat on a floor, lit by a point/area light, make the joint (depth, size) locally identifiable, and when does it not?
- **Hypothesis (falsifiable):** With the shadow term, the joint Fisher information over the occluder parameters has λ_min/λ_max well above numerical zero, and the marginal std of log d is ≤ 0.10, in the reference configuration and in most of the *favorable* sweep cells (below). Without the shadow term the null is exact (λ_min/λ_max ≤ 1e-9 when the pixel-space dilation is 0).

## Stage A (controlled, CPU, analytic forward model in torch float64)

**Scene.** Camera at origin, OpenCV axes (x right, y down, z forward), HFOV 60°, 96×72 px. Floor plane y = 1.5 (up is −y), Lambertian, albedo a. Background constant 0.5 where the ray misses the floor. One isotropic Gaussian occluder: centre c = d·r̂(az, el), std σ (metres), peak opacity o, colour 0.8. True reference: c = (0, 0.3, 3.0) (d ≈ 3.015), σ = 0.35, o = 0.9. For the depth sweep the centre is rescaled along the same ray (c = (0, 0.3, 3.0)·d/3.015) and σ scaled with it (same angular size).

**Observation model.** Image I(p) = (1−α_cam(p))·F(p) + α_cam(p)·0.8.
- Camera alpha (3DGS convention): α_cam = o·exp(−|u_p − u_c|² / (2 s²)), s² = (fx·σ/z_c)² + dil, dil ∈ {0, 0.3} px² (0.3 is the rasterizer's DILATION). Applied only where the occluder is nearer than the floor point.
- Floor value F(p) = a(p)·(ambient + (1/K) Σ_k I0·max(cosθ_k,0)/ℓ_k² · T_k(p)), ambient 0.15, I0 = 6, K light samples (K = 1 for radius 0; else centre + 8 on a disc of radius R_l perpendicular to the light direction).
- **Shadow term (model B):** T_k = 1 − o·exp(−ρ_k² / (2σ²)), ρ_k = distance from the occluder centre to the segment from floor point p to light sample k (max-response alpha, as in ray-traced 3DGS). **No-shadow model (A):** T_k = 1.
- Light: fixed in world coordinates at L = c_true + 4.0·(cos e·(sinφ, 0, −cosφ) + (0, −sin e, 0)). φ = 0 puts the light on the camera side (shadow falls behind the occluder, hidden from the camera); φ = 90° lateral; φ = 180° behind the occluder (shadow towards the camera).
- Pixel noise: i.i.d. Gaussian, std ν ∈ {0.005, 0.02, 0.05}; Fisher F = JᵀJ/ν² (J from torch autodiff, cross-checked against central finite differences).

**Parameters (dimensionless).** θ = (az, el, log d, log σ, log o). Exact null direction in model A (dil = 0): e_logd + e_logσ.

**Nuisance modes** (marginalised with the Schur complement, flat priors): `known` (light, albedo, I0 known); `albedo` (unknown log a0, gx, gz: albedo exp(la0 + gx·x + gz·(z−4))); `light` (unknown light centre position (3) and log gain); `both`.

**Baselines / comparison.** Model A (no shadow) vs model B at identical configurations. Context: a monocular depth network typically has ~0.1 relative depth error, so std(log d) ≤ 0.10 is the bar for shadow information to add anything.

**Metrics.** (i) λ_min/λ_max of the (marginal) occluder Fisher; (ii) marginal std of log d = sqrt([F⁻¹]_{logd,logd}) (∞ if λ_min/λ_max < 1e-10); (iii) alignment (|cos|) of the least-informed eigenvector with (e_logd+e_logσ)/√2.

**Sweep (dil = 0.3, all modes).** φ ∈ {0,15,30,45,60,90,120,150,180}°; elevation e ∈ {20,35,50,65,80}°; R_l ∈ {0,0.1,0.3,0.6} m; albedo ∈ {0.6, 0.2}; depth d ∈ {2, 3, 5} (rescaled as above); ν ∈ {0.005,0.02,0.05}. **Reference configuration:** φ = 60°, e = 50°, R_l = 0.1, a = 0.6, d = 3, ν = 0.02, mode known.

**Favorable regime:** φ ∈ {60, 90, 120}°, e ∈ {35, 50, 65}°, R_l ≤ 0.1, ν ≤ 0.02, a = 0.6, mode `known`.

**Success criteria (numeric).**
- **S1 (null exactness):** model A, dil = 0, mode known, reference light: λ_min/λ_max ≤ 1e-9 and eigenvector alignment ≥ 0.999.
- **S2 (shadow breaks the null):** model B, dil = 0.3, mode known, reference configuration: λ_min/λ_max ≥ 1e-8 and std(log d) ≤ 0.10.
- **S3 (breadth):** ≥ 50% of favorable-regime cells (dil = 0.3, all depths) satisfy the S2 conditions.
- **S4 (robustness, secondary, reported not gating):** S2 conditions in the reference configuration for modes `albedo`, `light`, `both`.
- **Gate:** RQ3 PASS = S1 ∧ S2 ∧ S3 (PASS-ROBUST additionally needs S4 for `light`). S1 or S2 failing ⇒ drop idea A, or restrict to the regimes where S2 holds and report. Failure regimes (light near camera axis φ ≤ 15°, overhead/large soft light, dark floor, unknown albedo, unknown light, high noise) are explored and reported; they are **not** required to succeed.

**Statistical plan.** Deterministic Fisher analysis, no sampling; report the fraction of cells passing per regime. Finite-difference vs autodiff agreement checked in tests (relative Jacobian error < 1e-5).

**Circularity audit.** The forward model is the same model used to define the information (inverse crime by construction): this shows *local identifiability under the assumed model*, not accuracy on real photos. Real photos have soft multi-source indoor light, interreflections, and unknown albedo; these are modelled only through the nuisance modes and the soft-light sweep.

**Stage B (stretch):** out of scope unless shadows can be rendered into the 12-case benchmark photos meaningfully. the benchmark photos are rendered from splat worlds, which store appearance as colour and have no separately modelled cast shadows, so detection of "shadow-consistency" there would be circular. Skipped; reason recorded in results/WP3.md.

**Compute and cost budget:** CPU only (OMP_NUM_THREADS=4), no paid API, no network.

**Stopping rule / decision gate:** as in Gate above.

## Results (fill after the run)

See results/WP3.md.

## Amendments

(The hash in results/wp3_prereg_hash.txt is of the text above this section; amendments were added after the runs.)

1. **2026-10-02, wrong premise corrected (not a result-driven change).** The text says a pixel-space dilation of 0.3 px² makes the null "weakly non-null". It does not: dilation is in pixel space, so the joint scaling (d, σ) → (λd, λσ) still leaves the image exactly unchanged (this is the global similarity ambiguity). Only moving along the ray at *fixed* size is weakly visible (about 1–3% of lateral information). S1 therefore also holds with dil = 0.3 (ratio 5e-18); S1 as pre-registered (dil = 0) is unaffected. The unit test was corrected accordingly.
2. **Depth-sweep parameter.** "d" in the sweep is the z-coordinate scale of the centre ((0, 0.3, 3.0)·z/3, with σ scaled), not |c|. The reference z = 3.0 is exactly the pre-registered true centre.
3. **Schema bug fixed before analysis.** The first sweep stored the floor albedo under the key `albedo`, which collided with the nuisance-mode name `albedo`; regime filters were empty. The key was renamed (`floor_albedo`) and the sweep re-run unchanged. No criterion or threshold was altered.
4. **Exploratory additions, NOT pre-registered** (reported separately in results/WP3.md, not part of the gate): (a) unknown ambient light as an extra nuisance; (b) unknown albedo *texture* modelled as a bilinear grid of log-albedo nodes at spatial scales 4/2/1/0.5 m (flat prior); (c) wrong-light bias: first-order least-squares bias of log d when the estimator's light is displaced by 0.05–1 m; (d) a post-hoc check that the visible-shadow pixel count explains where the shadow term helps (Spearman −0.74 vs std(log d)).
5. **Plots were generated but not visually inspected** (image reads outside the working directory are blocked in this environment).

### Editorial change (2026-10-06)
Reworded 2 descriptive sentence(s) about the public example worlds or the stand-in generator for a neutral, accurate tone. No hypothesis, baseline, metric, success criterion or analysis was changed. The file's hash was re-recorded in `results/wp3_prereg_hash.txt` with this date.

Editorial change (2026-10-06, header only): replaced internal tooling wording in the author line. No hypothesis, criterion or analysis changed.
