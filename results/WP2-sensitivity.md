# WP2 sensitivity: does the OT-vs-ICP result survive a matched compute budget? (POST-HOC, exploratory)

**Status:** post-hoc sensitivity analysis. It does **not** replace `results/WP2.md`, whose pre-registered result stands as reported. It exists because an internal check of this project's own work found that (i) OT received 10 similarity updates against 100 for ICP, (ii) a scratch rerun with more OT stages raised OT's strict success markedly, and (iii) yaw 180 and 270 of every world shared perturbation seeds, because the seed was derived from `sum(ord(c))` of the case name.

## 1. Plan (written and hashed BEFORE any run; see `results/wp2_sensitivity_hash.txt`)

**Question.** If optimal transport is given a compute budget comparable to ICP's, is its convergence basin still narrower than ICP's, and by how much does the gap shrink?

**Hypothesis (stated as a prediction, not a gate).** The sign of the original result survives (OT basin <= ICP basin) but the gap shrinks materially at matched budget. The original gate (OT basin >= 1.5x ICP, CI lower bound > 1) is *not* expected to be met.

**Data and protocol (identical to `prereg/RQ2.md` except where listed).**
- The same 8 evaluation cases (rustic kitchen and elegant library, 4 yaws each), variants **A** (seen generated splats vs truth, ICP-converged reference) and **C** (noisy truth subset in the viewing cone, exact identity reference). Variant B and FPFH are skipped.
- Perturbation levels f in {0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0}, up to 5 draws per case per level, same perturbation generator, same success definitions (strict: median error <= 0.25 tau; coarse: <= 1.0 tau), basin of a case = largest level such that every draw succeeds at every level <= f.
- **Changed:** perturbation seeds are a collision-free stable hash of (case name including yaw, level, draw). Therefore draws differ from the original evaluation; numbers are comparable only statistically, not draw by draw. All methods see identical draws within this analysis.
- OT hyper-parameters are those selected in the original tuning (rho = 0.05, eps_start = 0.5, eps_end = 0.003, 600/1500 source/target points); they are **not** re-tuned for the larger budgets (a limit: they were tuned at 10 stages).

**Methods.**

| Label | Method | Similarity updates | Sinkhorn iterations per update |
|---|---|---|---|
| icp | trimmed similarity ICP, 100 iterations (existing) | 100 | n/a |
| p2plane | point-to-plane similarity ICP, 100 iterations | 100 | n/a |
| ot10 | OT as evaluated originally (10 stages x 6) | 10 | 6 |
| ot14x15 | OT with the original pre-registered design (14 x 15) | 14 | 15 |
| ot30 | OT, 30 stages x 6 (intermediate budget) | 30 | 6 |
| ot100 | OT, **matched budget**, 100 stages x 6 | 100 | 6 |
| ot10+icp, ot100+icp | OT followed by 30 trimmed-ICP iterations | 10 / 100 (+30) | 6 |

**Outputs.** Pooled success curves per level with Wilson 95% intervals; per-case basin means; mean-basin difference (OT minus ICP) and ratio (OT/ICP) with a case-level paired bootstrap (10,000 resamples, seed 0) reporting exact bounds, with the number of resamples in which the ratio is undefined (ICP basin zero) stated explicitly, never turned into NaN; per-world means; leave-one-world-out basin ratios. Primary reading: variant C, strict tolerance (the cleanest check); variant A and the coarse tolerance are secondary.

**How the result will be read.**
- *Original conclusion survives* if, at matched budget (ot100) in variant C strict, the 95% interval of (OT minus ICP) mean basin has an upper bound below zero.
- *Gap shrinks* is measured as (ICP - OT)/ICP mean basin at ot10 versus ot100; I will report the percentages.
- *Original conclusion reversed* only if ot100 meets the original gate (ratio >= 1.5 with the interval's lower bound > 1) in variant C or A. That would mean the WP2 negative result was largely a compute-budget artefact.
- *Inconclusive* if the interval includes zero (8 cases cannot separate them).

**What would change the conclusion.** A matched-budget OT basin at least equal to ICP's with an interval including zero would change "OT is clearly narrower" to "not distinguishable at 8 cases". Any dependence of the result on re-tuning rho/eps (not done here) is an acknowledged unknown.

**Limits (fixed in advance).** 8 evaluation cases from 2 worlds (4 yaws per world are not independent; world-level resampling is impossible with 2 worlds, so CIs are indicative only); stand-in generator rather than Marble; post-hoc and exploratory; OT hyper-parameters not re-tuned; ICP, point-to-plane ICP were never tuned at all (noted in an internal check); the all-or-nothing basin metric is fragile on an 8-point grid, so success curves are reported first.

**Runtime guard.** Pass 1 runs draws 0-2 for every (case, variant). Pass 2 (draws 3-4) runs only if the projected total stays under about 90 minutes; the number of draws actually used is recorded and applied uniformly to all methods.

## 2. Results
*(appended below as they are produced)*

### 2.0 Run log
- Smoke run passed (2 levels x 1 draw, 16 records in 67 s, about 30 s per task including one-time setup); projected total about 80 minutes for pass 1 (draws 0-2) plus pass 2 (draws 3-4).
- Main run started 2026-10-05T19:07:55Z in the background, 4 workers, one result file per (variant, case, draw set) written incrementally to `results/wp2_sensitivity_job_*.json` (deletable after the merge into `wp2_sensitivity_runs.json`).
- **Deviation from the plan (recorded at 2026-10-05T20:23Z).** The first launch (jobs of 3 draws x 8 levels per case) was stopped after 74 minutes with only 4 of 16 jobs finished (variant A, elegant library, draws 0-2): another process on the machine kept the load average near 20 on 16 cores, so jobs took 18 to 62 minutes instead of about 12. Those 4 files are kept. The relaunch runs **variant C first** (the primary check), one job per (draw, case) in draw-major order, so any prefix is balanced across cases, with a 75-minute budget and an incremental merge. Draws actually completed for all cases are used, uniformly across methods, and are stated with the results. Variant A will be reported only for the cases that have complete coverage (currently the 4 elegant-library cases, draws 0-2).

### 2.1 Coverage actually used
- **Variant C (primary): all 8 evaluation cases x 5 draws x 8 levels** (all 40 jobs finished inside the time budget). Variant C is the exact-reference check and the cleanest of the two.
- **Variant A (secondary): only the 4 elegant-library cases x 3 draws** (4 jobs from the first launch). The rustic-kitchen A cases were not run (see the deviation above), so A is half the evaluation set and should be read as supporting evidence only.
- Perturbation draws use the collision-free hash seed, so they differ from the original evaluation; nothing here is draw-for-draw comparable to `results/WP2.md`. Same similarity-update budget for ICP (100) and `ot100` (100); wall-clock cost was **not** matched or measured separately.
- Full tables are in Appendix A; raw runs in `results/wp2_sensitivity_runs.json`, derived statistics in `results/wp2_sensitivity_analysis.json`.

### 2.2 Headline (variant C, 8 cases, mean per-case basin in level units; 95% case-level paired bootstrap)

| OT budget (similarity updates x Sinkhorn iterations) | strict: OT basin vs ICP 0.156 | OT minus ICP, strict [95% CI] | coarse: OT basin vs ICP 0.250 | OT minus ICP, coarse [95% CI] |
|---|---|---|---|---|
| ot10 (10 x 6, as originally evaluated) | 0.038 | -0.119 [-0.175, -0.050] | 0.113 | -0.138 [-0.212, -0.069] |
| ot14x15 (the pre-registered design) | 0.038 | -0.119 [-0.175, -0.050] | 0.131 | -0.119 [-0.200, -0.044] |
| ot30 (30 x 6) | 0.113 | -0.044 [-0.125, +0.069] | 0.225 | -0.025 [-0.138, +0.081] |
| **ot100 (100 x 6, matched to ICP's 100 updates)** | **0.231** | **+0.075 [-0.125, +0.306]** | **0.388** | **+0.138 [-0.069, +0.344]** |
| ot100 then 30 ICP iterations | 0.388 | +0.231 [+0.031, +0.438] | 0.463 | +0.213 [+0.025, +0.425] |
| (point-to-plane ICP, for scale) | 0.338 | +0.181 [+0.062, +0.319] | 0.350 | +0.100 [+0.019, +0.200] |

Gap to ICP, (ICP - OT) / ICP in mean strict basin: **76% at ot10, 28% at ot30, -48% at ot100** (negative means OT's basin is larger). Coarse: 55%, 10%, -55%.

### 2.3 Reading, against the rules fixed in the plan
- **Does "OT narrower than ICP" survive at matched budget?** **No, not as stated.** The plan's survival rule required the upper bound of (OT minus ICP) at `ot100`, variant C strict, to be below zero. It is +0.306. The ot100 interval includes zero in both tolerances, so by the plan's own wording the matched-budget comparison is **inconclusive** at 8 cases (point estimate: OT's basin larger than ICP's, ratio 1.48 strict [0.23, 3.47] and 1.55 coarse [0.73, 2.37]).
- **Is the original gate (ratio >= 1.5 with the interval's lower bound > 1) met by `ot100`?** No (lower bound 0.23 strict, 0.73 coarse). So the WP2 hypothesis is **not supported either**; what changes is that the earlier, firm negative verdict ("OT is clearly narrower") is not robust. It was largely a compute-budget artefact: the 76% gap at 10 updates becomes about zero by 30-100 updates.
- **The bottleneck is the number of similarity updates, not Sinkhorn iterations.** `ot14x15` (more Sinkhorn work per update, 14 updates) is statistically identical to `ot10`; tripling and 10x-ing the number of updates is what closes the gap. This confirms a concern raised in an internal check.
- **OT-then-ICP at the larger budget (`ot100+icp`) beats plain ICP** (strict ratio 2.48 [1.19, 4.38]) and is indistinguishable from point-to-plane ICP (difference +0.050 [-0.119, +0.237]). That is a hybrid, not the pre-registered OT method, so it does not satisfy the gate for OT itself.
- **A different shape, not a uniformly wider basin.** At the coarse tolerance, `ot100` succeeds more often than ICP at large perturbations (levels 0.5, 0.75, 1.0, 1.5: 0.65, 0.60, 0.47, 0.23 against ICP's 0.53, 0.28, 0.25, 0.00) but less at the smallest (level 0.1: 0.65 against 1.00). At the strict tolerance OT's success plateaus near 0.38 even for tiny perturbations: with 600 source and 1,500 target points its accuracy floor is close to the strict tolerance (about 0.06 scene units), and among runs where both succeed OT's final accuracy is worse (median-distance ratio 1.17 at ot100). Because a case's basin is zero if any draw fails at level 0.1, this floor depresses OT's basin metric; success curves and AUC are more informative than the basin number.
- **Both worlds point the same way** for `ot100` against ICP at the strict tolerance (elegant library 0.275 against 0.188; rustic kitchen 0.188 against 0.125) but not at the coarse one (elegant 0.275 against 0.287; rustic 0.500 against 0.212). With two worlds, nothing here can be tested at world level.
- **Variant A (4 elegant cases, 3 draws), secondary:** strict basins are zero for every OT variant (ICP 0.100; the ICP-derived reference favours ICP, as stated in the plan). At the coarse tolerance `ot100` is on par with ICP (0.212 against 0.200, ratio 1.06, interval [0.00, 1.43]) and `ot10` still has the 50% gap.

### 2.4 What this changes about WP2's claims (for the reader of `results/WP2.md`)
The original result stands as reported for the budget it used. The accurate summary is now: "At 10 similarity updates OT's basin was clearly narrower than ICP's. With a budget matched to ICP's (100 updates) the difference is not distinguishable from zero in either direction at 8 cases, and OT followed by ICP is better than ICP alone. This PoC does not show that OT widens the basin; it also no longer shows that it narrows it." Any page or note that says "OT is narrower than ICP in every variant" should be qualified by this.

### 2.5 Limits
8 cases from 2 worlds (4 yaws per world are not independent; bootstrap is over cases only, so the intervals are indicative); 5 draws per level are not independent within a case; stand-in generator, not Marble; post-hoc and exploratory; **OT hyper-parameters (rho = 0.05, eps_start = 0.5) were tuned at 10 stages and not re-tuned at 100**, so `ot100` may be under- or over-tuned; ICP, point-to-plane ICP and the 30-iteration hybrid refinement were not tuned (noted in an internal check); cost was matched in similarity updates, not in wall-clock; variant A covers half of the evaluation cases; ratio intervals with very small basins are unstable (some show degenerate bounds in Appendix A).

### 2.6 Files
`experiments/wp2_ot_alignment/run_sensitivity.py` (modes: run, run_incremental, merge, analyze, tables), `results/wp2_sensitivity_runs.json`, `results/wp2_sensitivity_analysis.json`, `results/wp2_sensitivity_hash.txt`, and 44 per-job files `results/wp2_sensitivity_job_*.json` (resumable cache, deletable after the merge). The libusb shim used for open3d was recreated at `/tmp/wp2lib` (see `results/WP2.md` section 8).

## Appendix A. Full tables (generated by `run_sensitivity.py tables`)

Coverage used (per variant: draws and cases): {"A": {"draws": [0, 1, 2], "cases": ["elegant_library_with_fireplace_0", "elegant_library_with_fireplace_180", "elegant_library_with_fireplace_270", "elegant_library_with_fireplace_90"]}, "C": {"draws": [0, 1, 2, 3, 4], "cases": ["elegant_library_with_fireplace_0", "elegant_library_with_fireplace_180", "elegant_library_with_fireplace_270", "elegant_library_with_fireplace_90", "rustic_kitchen_with_natural_light_0", "rustic_kitchen_with_natural_light_180", "rustic_kitchen_with_natural_light_270", "rustic_kitchen_with_natural_light_90"]}}

#### Variant C, strict tolerance

Mean per-case basin (level units) and mean success over levels:

| method | mean basin | mean success (AUC) |
|---|---|---|
| icp | 0.156 | 0.356 |
| p2plane | 0.338 | 0.522 |
| ot10 | 0.038 | 0.097 |
| ot14x15 | 0.038 | 0.119 |
| ot30 | 0.113 | 0.178 |
| ot100 | 0.231 | 0.275 |
| ot10+icp | 0.113 | 0.259 |
| ot100+icp | 0.388 | 0.466 |

Pooled success rate per level (Wilson 95% interval):

| method | 0.1 | 0.2 | 0.35 | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| icp | 0.88 (0.74-0.95) | 0.80 (0.65-0.90) | 0.55 (0.40-0.69) | 0.35 (0.22-0.50) | 0.10 (0.04-0.23) | 0.15 (0.07-0.29) | 0.00 (0.00-0.09) | 0.03 (0.00-0.13) |
| p2plane | 0.97 (0.87-1.00) | 0.97 (0.87-1.00) | 0.80 (0.65-0.90) | 0.62 (0.47-0.76) | 0.38 (0.24-0.53) | 0.35 (0.22-0.50) | 0.03 (0.00-0.13) | 0.05 (0.01-0.17) |
| ot10 | 0.35 (0.22-0.50) | 0.33 (0.20-0.48) | 0.07 (0.03-0.20) | 0.03 (0.00-0.13) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) |
| ot14x15 | 0.35 (0.22-0.50) | 0.35 (0.22-0.50) | 0.12 (0.05-0.26) | 0.10 (0.04-0.23) | 0.00 (0.00-0.09) | 0.03 (0.00-0.13) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) |
| ot30 | 0.38 (0.24-0.53) | 0.38 (0.24-0.53) | 0.35 (0.22-0.50) | 0.20 (0.10-0.35) | 0.07 (0.03-0.20) | 0.05 (0.01-0.17) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) |
| ot100 | 0.38 (0.24-0.53) | 0.38 (0.24-0.53) | 0.38 (0.24-0.53) | 0.35 (0.22-0.50) | 0.30 (0.18-0.45) | 0.28 (0.16-0.43) | 0.12 (0.05-0.26) | 0.03 (0.00-0.13) |
| ot10+icp | 0.78 (0.62-0.88) | 0.68 (0.52-0.80) | 0.42 (0.29-0.58) | 0.17 (0.09-0.32) | 0.00 (0.00-0.09) | 0.03 (0.00-0.13) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) |
| ot100+icp | 0.62 (0.47-0.76) | 0.62 (0.47-0.76) | 0.62 (0.47-0.76) | 0.62 (0.47-0.76) | 0.53 (0.37-0.67) | 0.45 (0.31-0.60) | 0.17 (0.09-0.32) | 0.07 (0.03-0.20) |

Paired case-level bootstrap (10,000 resamples; difference = first minus second, in basin level units):

| comparison | basin diff [95% CI] | basin ratio [95% CI] | AUC diff [95% CI] |
|---|---|---|---|
| p2plane vs icp | +0.181 [+0.062, +0.319] | 2.16 [1.35, 3.65] | +0.166 [+0.094, +0.234] |
| ot10 vs icp | -0.119 [-0.175, -0.050] | 0.24 [0.00, 0.51] | -0.259 [-0.362, -0.169] |
| ot14x15 vs icp | -0.119 [-0.175, -0.050] | 0.24 [0.00, 0.51] | -0.237 [-0.350, -0.137] |
| ot30 vs icp | -0.044 [-0.125, +0.069] | 0.72 [0.14, 1.50] | -0.178 [-0.316, -0.047] |
| ot100 vs icp | +0.075 [-0.125, +0.306] | 1.48 [0.23, 3.47] | -0.081 [-0.281, +0.125] |
| ot10+icp vs icp | -0.044 [-0.106, +0.019] | 0.72 [0.38, 1.17] | -0.097 [-0.166, -0.031] |
| ot100+icp vs icp | +0.231 [+0.031, +0.438] | 2.48 [1.19, 4.38] | +0.109 [-0.053, +0.256] |
| ot10 vs p2plane | -0.300 [-0.456, -0.169] | 0.11 [0.00, 0.28] | -0.425 [-0.500, -0.353] |
| ot100 vs p2plane | -0.106 [-0.231, +0.025] | 0.69 [0.15, 1.07] | -0.247 [-0.422, -0.059] |
| ot100+icp vs p2plane | +0.050 [-0.119, +0.237] | 1.15 [0.61, 1.81] | -0.056 [-0.244, +0.116] |

Gap to ICP, (ICP - OT)/ICP in mean basin: ot10 76%, ot14x15 76%, ot30 28%, ot100 -48%, ot100+icp -148%

Per-world mean basin:

| world | icp | p2plane | ot10 | ot14x15 | ot30 | ot100 | ot10+icp | ot100+icp |
|---|---|---|---|---|---|---|---|---|
| elegant_library_with_fireplace | 0.188 | 0.363 | 0.050 | 0.050 | 0.138 | 0.275 | 0.100 | 0.275 |
| rustic_kitchen_with_natural_light | 0.125 | 0.312 | 0.025 | 0.025 | 0.087 | 0.188 | 0.125 | 0.500 |

Final accuracy among runs where both methods succeed strictly (mean of per-run median-distance ratio vs ICP; below 1 is more accurate):

| method | n both succeed | mean accuracy ratio |
|---|---|---|
| ot10 | 31 | 1.292 |
| ot100 | 57 | 1.166 |
| ot100+icp | 93 | 0.993 |
| p2plane | 111 | 0.993 |

#### Variant C, coarse tolerance

Mean per-case basin (level units) and mean success over levels:

| method | mean basin | mean success (AUC) |
|---|---|---|
| icp | 0.250 | 0.469 |
| p2plane | 0.350 | 0.525 |
| ot10 | 0.113 | 0.300 |
| ot14x15 | 0.131 | 0.322 |
| ot30 | 0.225 | 0.419 |
| ot100 | 0.388 | 0.519 |
| ot10+icp | 0.237 | 0.416 |
| ot100+icp | 0.463 | 0.622 |

Pooled success rate per level (Wilson 95% interval):

| method | 0.1 | 0.2 | 0.35 | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| icp | 1.00 (0.91-1.00) | 0.93 (0.80-0.97) | 0.72 (0.57-0.84) | 0.53 (0.37-0.67) | 0.28 (0.16-0.43) | 0.25 (0.14-0.40) | 0.00 (0.00-0.09) | 0.05 (0.01-0.17) |
| p2plane | 1.00 (0.91-1.00) | 0.97 (0.87-1.00) | 0.80 (0.65-0.90) | 0.62 (0.47-0.76) | 0.38 (0.24-0.53) | 0.35 (0.22-0.50) | 0.03 (0.00-0.13) | 0.05 (0.01-0.17) |
| ot10 | 0.88 (0.74-0.95) | 0.80 (0.65-0.90) | 0.53 (0.37-0.67) | 0.17 (0.09-0.32) | 0.00 (0.00-0.09) | 0.03 (0.00-0.13) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) |
| ot14x15 | 0.82 (0.68-0.91) | 0.78 (0.62-0.88) | 0.60 (0.45-0.74) | 0.30 (0.18-0.45) | 0.05 (0.01-0.17) | 0.03 (0.00-0.13) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) |
| ot30 | 0.78 (0.62-0.88) | 0.80 (0.65-0.90) | 0.72 (0.57-0.84) | 0.57 (0.42-0.71) | 0.28 (0.16-0.43) | 0.17 (0.09-0.32) | 0.03 (0.00-0.13) | 0.00 (0.00-0.09) |
| ot100 | 0.65 (0.50-0.78) | 0.75 (0.60-0.86) | 0.72 (0.57-0.84) | 0.65 (0.50-0.78) | 0.60 (0.45-0.74) | 0.47 (0.33-0.63) | 0.23 (0.12-0.38) | 0.07 (0.03-0.20) |
| ot10+icp | 0.97 (0.87-1.00) | 0.95 (0.83-0.99) | 0.80 (0.65-0.90) | 0.42 (0.29-0.58) | 0.12 (0.05-0.26) | 0.05 (0.01-0.17) | 0.00 (0.00-0.09) | 0.00 (0.00-0.09) |
| ot100+icp | 0.88 (0.74-0.95) | 0.90 (0.77-0.96) | 0.88 (0.74-0.95) | 0.72 (0.57-0.84) | 0.70 (0.55-0.82) | 0.55 (0.40-0.69) | 0.28 (0.16-0.43) | 0.07 (0.03-0.20) |

Paired case-level bootstrap (10,000 resamples; difference = first minus second, in basin level units):

| comparison | basin diff [95% CI] | basin ratio [95% CI] | AUC diff [95% CI] |
|---|---|---|---|
| p2plane vs icp | +0.100 [+0.019, +0.200] | 1.40 [1.09, 1.76] | +0.056 [+0.025, +0.087] |
| ot10 vs icp | -0.138 [-0.212, -0.069] | 0.45 [0.21, 0.68] | -0.169 [-0.266, -0.075] |
| ot14x15 vs icp | -0.119 [-0.200, -0.044] | 0.53 [0.23, 0.81] | -0.147 [-0.244, -0.056] |
| ot30 vs icp | -0.025 [-0.138, +0.081] | 0.90 [0.40, 1.30] | -0.050 [-0.178, +0.050] |
| ot100 vs icp | +0.138 [-0.069, +0.344] | 1.55 [0.73, 2.37] | +0.050 [-0.122, +0.187] |
| ot10+icp vs icp | -0.013 [-0.069, +0.044] | 0.95 [0.72, 1.19] | -0.053 [-0.106, -0.006] |
| ot100+icp vs icp | +0.213 [+0.025, +0.425] | 1.85 [1.13, 2.79] | +0.153 [+0.088, +0.213] |
| ot10 vs p2plane | -0.237 [-0.350, -0.137] | 0.32 [0.17, 0.48] | -0.225 [-0.312, -0.137] |
| ot100 vs p2plane | +0.038 [-0.131, +0.225] | 1.11 [0.58, 1.72] | -0.006 [-0.184, +0.138] |
| ot100+icp vs p2plane | +0.113 [-0.056, +0.337] | 1.32 [0.82, 2.14] | +0.097 [+0.025, +0.172] |

Gap to ICP, (ICP - OT)/ICP in mean basin: ot10 55%, ot14x15 48%, ot30 10%, ot100 -55%, ot100+icp -85%

Per-world mean basin:

| world | icp | p2plane | ot10 | ot14x15 | ot30 | ot100 | ot10+icp | ot100+icp |
|---|---|---|---|---|---|---|---|---|
| elegant_library_with_fireplace | 0.287 | 0.388 | 0.125 | 0.125 | 0.212 | 0.275 | 0.250 | 0.363 |
| rustic_kitchen_with_natural_light | 0.212 | 0.312 | 0.100 | 0.138 | 0.237 | 0.500 | 0.225 | 0.562 |

Final accuracy among runs where both methods succeed strictly (mean of per-run median-distance ratio vs ICP; below 1 is more accurate):

| method | n both succeed | mean accuracy ratio |
|---|---|---|
| ot10 | 31 | 1.292 |
| ot100 | 57 | 1.166 |
| ot100+icp | 93 | 0.993 |
| p2plane | 111 | 0.993 |

#### Variant A, strict tolerance

Mean per-case basin (level units) and mean success over levels:

| method | mean basin | mean success (AUC) |
|---|---|---|
| icp | 0.100 | 0.167 |
| p2plane | 0.175 | 0.260 |
| ot10 | 0.000 | 0.021 |
| ot14x15 | 0.000 | 0.021 |
| ot30 | 0.000 | 0.000 |
| ot100 | 0.000 | 0.000 |
| ot10+icp | 0.000 | 0.062 |
| ot100+icp | 0.000 | 0.000 |

Pooled success rate per level (Wilson 95% interval):

| method | 0.1 | 0.2 | 0.35 | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| icp | 0.58 (0.32-0.81) | 0.50 (0.25-0.75) | 0.25 (0.09-0.53) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| p2plane | 0.58 (0.32-0.81) | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.17 (0.05-0.45) | 0.25 (0.09-0.53) | 0.08 (0.01-0.35) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot10 | 0.00 (0.00-0.24) | 0.17 (0.05-0.45) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot14x15 | 0.00 (0.00-0.24) | 0.17 (0.05-0.45) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot30 | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot100 | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot10+icp | 0.08 (0.01-0.35) | 0.42 (0.19-0.68) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot100+icp | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |

Paired case-level bootstrap (10,000 resamples; difference = first minus second, in basin level units):

| comparison | basin diff [95% CI] | basin ratio [95% CI] | AUC diff [95% CI] |
|---|---|---|---|
| p2plane vs icp | +0.075 [+0.000, +0.150] | 1.75 [1.75, 1.75] | +0.094 [-0.021, +0.208] |
| ot10 vs icp | -0.100 [-0.200, +0.000] | 0.00 [0.00, 0.00] | -0.146 [-0.250, -0.042] |
| ot14x15 vs icp | -0.100 [-0.200, +0.000] | 0.00 [0.00, 0.00] | -0.146 [-0.250, -0.042] |
| ot30 vs icp | -0.100 [-0.200, +0.000] | 0.00 [0.00, 0.00] | -0.167 [-0.292, -0.042] |
| ot100 vs icp | -0.100 [-0.200, +0.000] | 0.00 [0.00, 0.00] | -0.167 [-0.292, -0.042] |
| ot10+icp vs icp | -0.100 [-0.200, +0.000] | 0.00 [0.00, 0.00] | -0.104 [-0.177, -0.031] |
| ot100+icp vs icp | -0.100 [-0.200, +0.000] | 0.00 [0.00, 0.00] | -0.167 [-0.292, -0.042] |
| ot10 vs p2plane | -0.175 [-0.350, +0.000] | 0.00 [0.00, 0.00] | -0.240 [-0.458, -0.021] |
| ot100 vs p2plane | -0.175 [-0.350, +0.000] | 0.00 [0.00, 0.00] | -0.260 [-0.500, -0.021] |
| ot100+icp vs p2plane | -0.175 [-0.350, +0.000] | 0.00 [0.00, 0.00] | -0.260 [-0.500, -0.021] |

Gap to ICP, (ICP - OT)/ICP in mean basin: ot10 100%, ot14x15 100%, ot30 100%, ot100 100%, ot100+icp 100%

Per-world mean basin:

| world | icp | p2plane | ot10 | ot14x15 | ot30 | ot100 | ot10+icp | ot100+icp |
|---|---|---|---|---|---|---|---|---|
| elegant_library_with_fireplace | 0.100 | 0.175 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Final accuracy among runs where both methods succeed strictly (mean of per-run median-distance ratio vs ICP; below 1 is more accurate):

| method | n both succeed | mean accuracy ratio |
|---|---|---|
| ot10 | 2 | 1.043 |
| ot100 | 0 | undefined |
| ot100+icp | 0 | undefined |
| p2plane | 15 | 1.011 |

#### Variant A, coarse tolerance

Mean per-case basin (level units) and mean success over levels:

| method | mean basin | mean success (AUC) |
|---|---|---|
| icp | 0.200 | 0.292 |
| p2plane | 0.175 | 0.271 |
| ot10 | 0.100 | 0.177 |
| ot14x15 | 0.100 | 0.187 |
| ot30 | 0.175 | 0.219 |
| ot100 | 0.212 | 0.323 |
| ot10+icp | 0.175 | 0.250 |
| ot100+icp | 0.212 | 0.333 |

Pooled success rate per level (Wilson 95% interval):

| method | 0.1 | 0.2 | 0.35 | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| icp | 0.75 (0.47-0.91) | 0.67 (0.39-0.86) | 0.58 (0.32-0.81) | 0.17 (0.05-0.45) | 0.08 (0.01-0.35) | 0.08 (0.01-0.35) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| p2plane | 0.58 (0.32-0.81) | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.17 (0.05-0.45) | 0.33 (0.14-0.61) | 0.08 (0.01-0.35) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot10 | 0.58 (0.32-0.81) | 0.58 (0.32-0.81) | 0.08 (0.01-0.35) | 0.17 (0.05-0.45) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot14x15 | 0.50 (0.25-0.75) | 0.58 (0.32-0.81) | 0.25 (0.09-0.53) | 0.17 (0.05-0.45) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot30 | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.25 (0.09-0.53) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot100 | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.42 (0.19-0.68) | 0.17 (0.05-0.45) | 0.33 (0.14-0.61) | 0.17 (0.05-0.45) | 0.00 (0.00-0.24) |
| ot10+icp | 0.67 (0.39-0.86) | 0.67 (0.39-0.86) | 0.50 (0.25-0.75) | 0.17 (0.05-0.45) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) | 0.00 (0.00-0.24) |
| ot100+icp | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.50 (0.25-0.75) | 0.42 (0.19-0.68) | 0.25 (0.09-0.53) | 0.33 (0.14-0.61) | 0.17 (0.05-0.45) | 0.00 (0.00-0.24) |

Paired case-level bootstrap (10,000 resamples; difference = first minus second, in basin level units):

| comparison | basin diff [95% CI] | basin ratio [95% CI] | AUC diff [95% CI] |
|---|---|---|---|
| p2plane vs icp | -0.025 [-0.075, +0.000] | 0.88 [0.00, 1.00] | -0.021 [-0.146, +0.062] |
| ot10 vs icp | -0.100 [-0.150, -0.037] | 0.50 [0.00, 0.57] | -0.115 [-0.187, -0.042] |
| ot14x15 vs icp | -0.100 [-0.150, -0.037] | 0.50 [0.00, 0.57] | -0.104 [-0.198, -0.021] |
| ot30 vs icp | -0.025 [-0.075, +0.000] | 0.88 [0.00, 1.00] | -0.073 [-0.219, +0.000] |
| ot100 vs icp | +0.013 [-0.075, +0.113] | 1.06 [0.00, 1.43] | +0.031 [-0.177, +0.208] |
| ot10+icp vs icp | -0.025 [-0.075, +0.000] | 0.88 [0.00, 1.00] | -0.042 [-0.094, +0.000] |
| ot100+icp vs icp | +0.013 [-0.075, +0.113] | 1.06 [0.00, 1.43] | +0.042 [-0.167, +0.229] |
| ot10 vs p2plane | -0.075 [-0.150, +0.000] | 0.57 [0.57, 0.57] | -0.094 [-0.188, +0.000] |
| ot100 vs p2plane | +0.038 [+0.000, +0.113] | 1.21 [1.00, 1.43] | +0.052 [-0.042, +0.146] |
| ot100+icp vs p2plane | +0.038 [+0.000, +0.113] | 1.21 [1.00, 1.43] | +0.062 [-0.042, +0.167] |

Gap to ICP, (ICP - OT)/ICP in mean basin: ot10 50%, ot14x15 50%, ot30 12%, ot100 -6%, ot100+icp -6%

Per-world mean basin:

| world | icp | p2plane | ot10 | ot14x15 | ot30 | ot100 | ot10+icp | ot100+icp |
|---|---|---|---|---|---|---|---|---|
| elegant_library_with_fireplace | 0.200 | 0.175 | 0.100 | 0.100 | 0.175 | 0.212 | 0.175 | 0.212 |

Final accuracy among runs where both methods succeed strictly (mean of per-run median-distance ratio vs ICP; below 1 is more accurate):

| method | n both succeed | mean accuracy ratio |
|---|---|---|
| ot10 | 2 | 1.043 |
| ot100 | 0 | undefined |
| ot100+icp | 0 | undefined |
| p2plane | 15 | 1.011 |

