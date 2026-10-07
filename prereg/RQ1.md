# Pre-registration: RQ1 — does a trust policy prevent robot failures in a generated world?

- **Date / author:** 2026-10-02 / WP1 (CPU-only PoC)
- **Research question:** In a generated world, does a trust-aware navigation policy match the safety of the standard "unknown = obstacle" policy while completing more goals or taking shorter paths?
- **Hypothesis (falsifiable):** At least one of {frustum mask, visibility mask, our tiers + depth uncertainty} (a) is non-inferior to `unknown_obstacle` on failure rate (upper 95% CI bound of the paired difference ≤ +0.02), AND (b) beats it on completion rate (lower CI bound > 0) OR on path-length ratio (upper CI bound < 0). A null result is reportable.

## Data
- 12 cached cases `out/cases/*.pkl` from `wmt.benchmark.build_case` (3 truth worlds × yaw {0,90,180,270}; truth = official Marble example worlds, generated world = stand-in generator, NOT Marble). Alignment `sim` (trimmed ICP on seen splats, measurement stage) maps generated splats into the truth frame; the planner works in that frame (this implicitly gives the planner the metric scale; assumption stated, not hidden).
- No train/select/test split is needed: all thresholds below are fixed here, before any policy outcome is computed. Design-informing exploration (floor height, extents, coverage percentiles, splat-per-cell density) was run before this file was written and is logged in `results/wp1_design_exploration.log`. No policy outcome was computed.

## Robot and maps
- 2D disc robot navigating the floor plane, grid x,z in [-6, 6), **cell 0.1 scene units** (120×120), 8-connected moves, no diagonal corner-cutting. Robot radius ≈ 0.1: obstacles are inflated by 1 cell (3×3 Chebyshev). Scene units are not metres.
- **Floor height** `y_f` per world, estimated separately for truth and for the aligned generated world: mode of a 0.05-bin histogram of splat y (y is down) over splats with 0.3 < y < 3.0, |x|,|z| < 5 (truth uses opacity > 0.3).
- **Floor evidence** (per cell): ≥ 1 splat with |y − y_f| ≤ 0.08, then 3×3 binary closing (removes sub-0.3-wide sampling speckle; large holes remain).
- **Obstacle evidence**: ≥ 2 splats with height above floor in [0.15, 1.0] (y in [y_f − 1.0, y_f − 0.15]). Obstacles are then inflated by 1 cell.
- **Truth traversable** = floor evidence and not inflated obstacle. **Collision** = path cell in truth inflated obstacle. **Fall** = path cell with no truth floor evidence and not truth inflated obstacle. A path *fails* if any path cell collides or falls (execution stops at the first). The start cell (origin, where the prompt camera/robot is) is forced free everywhere.

## Start, goals
- Start = origin cell. Goals: truth-traversable cells reachable from the start in truth (Dijkstra) with Euclidean distance ≥ 1.0 from the start.
- Per case, rng seed 1000 + case index (cases ordered world-major as in `TRUTH`, then yaw 0,90,180,270). Stratify by the generated-world state of the goal cell: stratum **seen** = floor evidence from splats with `seen` (R ≥ 0.5) (closed as above); stratum **unseen** = other. Sample up to 20 goals per stratum without replacement; if one stratum has fewer, fill from the other up to 40 total. Target N ≥ 30 per case; if a case has fewer than 30 reachable goals it is reported with its actual N.

## Policies (planning map built from the generated world only; obstacles from ANY generated splat always block)
1. `no_mask`: free = generated floor evidence (any splat) and not inflated generated obstacle.
2. `frustum`: as no_mask, but floor evidence counts only from splats inside the prompt frustum (`in_frustum`).
3. `visibility`: as no_mask, but floor evidence counts only from splats with `coverage` ≥ 0.5 (coverage = Σw; in-frustum median ≈ 3–4, 10th pct 0.05–0.18).
4. `ours`: floor evidence counts only from splats with `seen` (R ≥ 0.5) AND `abs_depth_std` ≤ the 80th percentile of `abs_depth_std` among seen splats of that case.
5. `unknown_obstacle` (standard occupancy-mapping practice, independent of our scores): a cell is free iff (a) it lies inside the horizontal FOV wedge from the camera (half-angle = `hfov_hat`/2 around the camera forward direction (sin yaw, cos yaw)), (b) the 2D line from the start to the cell centre (sampled every 0.05) crosses no uninflated generated-obstacle cell, (c) it has generated floor evidence (any splat), and (d) it is not an inflated generated obstacle. Everything else is unknown → blocked.
6. `oracle` (sanity only): plan on the truth map. Must complete 100% with 0 failures.

Plan = Dijkstra shortest path (Euclidean step cost) on each policy's free map from the start; no path → goal not attempted (counted as not completed, not a failure).

## Metrics (per case, over its goals)
- `fail_rate` (PRIMARY safety) = # goals with a planned path that fails in truth / # all goals. Secondary: failures / # planned.
- `completion` = # goals with a planned path that does not fail / # all goals.
- `path_ratio` = mean over goals completed by BOTH the policy and `unknown_obstacle` of (planned path length / truth-shortest path length). Cases with no such goals are excluded from path-ratio statistics (reported).
- Failure type split (collision vs fall) and by goal stratum reported descriptively.

## Success criterion (numeric)
Statistics: paired bootstrap over the 12 cases (`wmt.stats.paired_bootstrap`, 10000 resamples, seed 0), policy minus `unknown_obstacle`. A policy **passes** iff
- (safety, non-inferiority) upper 95% CI bound of Δfail_rate ≤ +0.02, AND
- (benefit) lower CI bound of Δcompletion > 0 OR upper CI bound of Δpath_ratio < 0.
**Gate:** passes if ≥ 1 of {frustum, visibility, ours} passes. If no policy passes, the honest negative result is "no trust policy beats unknown = obstacle here".

## Statistical plan
Paired bootstrap as above; effect sizes reported with CIs and win counts. 12 cases share 3 truth worlds, so effective independence is lower than 12; this is stated as a limitation, not corrected.

## Planned sanity checks / known-answer tests
Dijkstra on open grid (octile distance) and around a wall; grid construction on a toy scene; oracle policy = 100% completion, 0 failures.

## Circularity audit
- The generated world's invented region is our own box prior (floor + walls), so "imagined floor/walls are wrong" is partly built in.
- The truth world is a public example splat world whose floor surface is sparser in areas the camera did not cover. "Falls" are measured against truth floor evidence, so cells without floor evidence in the truth count as falls even if a real physics floor existed (collider mesh not used). Seen-tier outcomes are the fairer comparison.
- Alignment `sim` uses truth (ICP on seen splats) and gives the planner true scale; real use would need `metric_scale_factor`.

## Compute and cost budget
CPU only, OMP_NUM_THREADS=4, no API use, no cost.

## Stopping rule / decision gate
Run once as specified. No re-tuning of thresholds after seeing outcomes; changes go to Amendments.

## Results
See `results/WP1.md`.

## Amendments

**Run 1 (exactly as pre-registered, hash in `results/wp1_prereg_hash.txt`, line 2)** produced a degenerate outcome (see `results/WP1.md`): every conservative policy completed ~0% of goals, and the oracle completed 100%. Diagnosis (2026-10-03, `/tmp`-style diagnostic over the same cached cases, no thresholds tuned on policy outcomes) found two artifacts of this prereg's design, not properties of trust masks:

- **A1 (floor height).** The mode-of-histogram floor estimator picked a wall/tabletop slab for the *generated* world in 8 of 12 cases (yG 0.32–0.82 vs true 0.77–0.97), leaving zero overlap with the truth floor. Amended: the generated world's floor height = the truth floor height, standing in for the World API's exported `ground_plane_offset` / known sensor height. (Gives the planner the true floor level; stated as a limitation.)
- **A2 (camera blind zone).** The prompt camera looks horizontally, so floor within `y_f / tan(vfov/2)` (≈1.6–2.0 units) of the start is below the frustum and carries no trusted evidence; frustum/visibility/ours then have no path out of the start cell. Amended: for the three trust policies only, cells in the FOV wedge with line of sight and r ≤ that blind radius (vfov from `hfov_hat` at 4:3) count as free (local flat-floor assumption, not an obstacle). `unknown_obstacle` and `no_mask` already use the generated floor in that area and are unchanged.
- **A4 (alignment).** A second diagnostic showed the ICP similarity `sim` has scale 0.44–0.59 for yaw ≠ 0 against ≈0.70 at yaw 0, so the aligned generated floor lies 0.3–0.6 units above the truth floor (G floor cells at the truth floor height: 0–15 in 8 of 12 cases). Amended (exploratory run only): align by the camera rotation and a scale from the known camera height (scale = truth floor height / the generator frame's floor-plane height, the larger of the two largest planar y-groups among invented splats), with the camera at the origin. This removes alignment error and any floor-height error by construction.
- **A3 (robot footprint).** Cells within r ≤ 0.3 of the start are free in every generated-world map (the robot stands there).

The amended analysis (`--amended`) is **exploratory**: the amendments were made after seeing run-1 outcomes, so it cannot confirm the hypothesis. The **gate decision rests on run 1**, which is reported in full. Everything else (seeds, goals, thresholds 0.5 / 80th pct / ±0.02, metrics, bootstrap) is unchanged.

### Editorial change (2026-10-06)
Reworded 1 descriptive sentence(s) about the public example worlds or the stand-in generator for a neutral, accurate tone. No hypothesis, baseline, metric, success criterion or analysis was changed. The file's hash was re-recorded in `results/wp1_prereg_hash.txt` with this date.

Editorial change (2026-10-06, header only): replaced internal tooling wording in the author line. No hypothesis, criterion or analysis changed.
