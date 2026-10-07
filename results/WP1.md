# WP1 / RQ1 results: do trust policies prevent robot failures in a generated world?

**Gate decision: NOT PASSED (pre-registered run), and the benchmark as designed is underpowered, so the result is inconclusive rather than a clean negative.** 2026-10-03. CPU-only PoC. Prereg: `prereg/RQ1.md` (hash in `results/wp1_prereg_hash.txt`). Code: `src/wmt/wp1_nav.py`, `experiments/wp1_robot_benchmark/run.py`, `tests/test_wp1_nav.py`.

## What was done
12 cached synthetic-truth cases (3 Marble example worlds × 4 yaws; the "generated" world is the **stand-in** generator, not Marble). A 2D disc robot (cell 0.1 scene units, 1-cell obstacle inflation) starts at the prompt camera and plans, per policy, on a floor-plane map built only from the generated splats; the path is then executed in the truth map and counted as a failure on collision (truth obstacle) or fall (truth cell with no floor). 40 goals per case (20 "seen" + 20 "unseen" where available; 480 goals total), seed 1000+case index. Policies: no_mask, frustum, visibility (coverage ≥ 0.5), ours (R ≥ 0.5 and abs-depth-std ≤ 80th pct), unknown_obstacle (FOV wedge + line of sight + generated floor), and an oracle (plans on truth; sanity check).
Sanity: oracle = 100% completion, 0 failures in all 12 cases. Unit tests pass (`pytest`: Dijkstra octile/detour/no corner-cutting, grid construction, execution, wedge, blind radius).

*Post-hoc check (internal check): see `results/WP1-sensitivity.md`. Giving the baseline the same blind-zone relaxation changes nothing (identical results in all 12 cases), so that amendment did not tilt the comparison; the conclusion that no trust policy beats "unknown = obstacle" here is unchanged.*

## Run 1: exactly as pre-registered (primary; gate decision)
Means over 12 cases (per-goal rates): 

| policy | fail rate | completion | planned |
|---|---|---|---|
| no_mask | 0.033 | 0.152 | 0.185 |
| frustum | 0.000 | 0.000 | 0.000 |
| visibility | 0.000 | 0.000 | 0.000 |
| ours | 0.000 | 0.000 | 0.000 |
| unknown_obstacle | 0.000 | 0.137 | 0.137 |
| oracle | 0.000 | 1.000 | 1.000 |

Paired bootstrap vs unknown_obstacle (95% CI, n=12):
- frustum / visibility / ours: Δfail 0.000 [0.000, 0.000]; Δcompletion −0.137 [−0.340, 0.000]. Safe, but they complete nothing, so **benefit fails**. Gate: not passed for all three.
- no_mask: Δfail +0.033 [0.000, +0.096] (upper bound > +0.02, not non-inferior); Δcompletion +0.015 [+0.002, +0.033].
- Only 4/12 cases had any generated-policy completion; unknown_obstacle completed anything in 2/12.

**Why it is degenerate.** Two design artifacts, not findings about trust: (a) the floor-height estimator (mode of y) picked a wall/tabletop slab for the generated world in 8/12 cases (0.32–0.82 vs true 0.77–0.97); (b) the camera looks level, so the floor within ≈1.6–2.0 units of the start is below the frustum and has no trusted evidence, which traps every conservative policy at the start cell.

## Amendments and the exploratory run (A1–A4, see `prereg/RQ1.md`)
Made **after** seeing run 1, so this run cannot confirm the hypothesis. A1: generated floor height = truth (stand-in for the API's `ground_plane_offset`). A2: for the 3 trust policies, floor inside the blind zone counts as free. A3: robot footprint (r ≤ 0.3) free. A4: a second diagnostic showed the ICP similarity has scale 0.44–0.59 for yaw ≠ 0 vs ≈0.70 at yaw 0, putting the aligned generated floor 0.3–0.6 above the truth floor, so alignment now uses the camera rotation and camera-height scale. Only the final A1–A4 results are saved (`results/wp1_results_amended.json`); an earlier A1–A3 run was overwritten (its means: frustum/visibility/ours fail 0.048/0.029/0.027, completion 0.185 each; same qualitative picture).

| policy (A1–A4) | fail rate | completion | Δfail vs UO [95% CI] | Δcompletion vs UO [95% CI] |
|---|---|---|---|---|
| no_mask | 0.081 | 0.252 | +0.035 [+0.008, +0.071] | +0.073 [+0.027, +0.131] |
| frustum | 0.050 | 0.171 | +0.004 [0.000, +0.013] | −0.008 [−0.025, 0.000] |
| visibility | 0.050 | 0.179 | +0.004 [0.000, +0.013] | 0.000 [0.000, 0.000] |
| ours | 0.048 | 0.171 | +0.002 [0.000, +0.006] | −0.008 [−0.025, 0.000] |
| unknown_obstacle | 0.046 | 0.179 | n/a | n/a |
| oracle | 0.000 | 1.000 | n/a | n/a |

Path ratio (goals completed by both): ≈1.00 for every policy (n = 3 cases with common goals); no shorter paths. Gate (exploratory): **not passed** — safety is non-inferior for the three trust policies, but none beats unknown_obstacle on completion or path length. Falls = 0 everywhere; all failures are collisions with truth obstacles (including 0.47–0.68 failure rate in the yaw-0 library case, where generated obstacles are mislocated).

What the exploratory run suggests (not confirmed): masks buy safety (no_mask +3.5 pp failures vs UO, CI excludes 0) at a small completion cost; ours/visibility/frustum are indistinguishable from unknown_obstacle on this data. This matches the earlier finding that the illumination score ties plain visibility.

## Circularity audit
- The generated world's invented region is **our own box prior**, so "unseen/invented geometry is unreliable" is partly built in. This does not favour any policy specifically but limits what unseen-goal results mean.
- The truth world is a public example world whose exported surfaces are less complete in areas the camera did not cover, so a path there could be counted as a fall. Falls were measured against splat-derived floor evidence, not a collider mesh. Falls were still 0, so this failure mode was **not exercised** here.
- Truth "free" space is small and cluttered (538 / 587 / 1270 free cells per world; obstacle evidence covers more cells than floor), and 40 goals per case are drawn from it.
- A1 and A4 hand the planner the true floor height/scale (stand-ins for `ground_plane_offset` / `metric_scale_factor`); real use would not.
- 12 cases share 3 truth worlds; effective sample size is smaller than 12 and the CIs are optimistic. Many bootstrap CIs are degenerate because most cases have zero completions.

## Conclusion (honest)
Negative on the pre-registered gate, with a caveat that matters more than the verdict: **this PoC has almost no statistical power.** In the primary run 8/12 cases give every generated-world policy 0% completion; in the exploratory run unknown_obstacle completes goals in only 3/12 cases. Reasons are properties of the setup (level-gaze camera blind zone, narrow cluttered truth space, a box-prior generator that rarely overlaps the truth's free space, and an ICP alignment that fails for wall-facing views), not evidence that trust maps are useless. Supported: unmasked planning is less safe; trust masks are conservative. Not supported: any benefit of ours/visibility/frustum over unknown = obstacle.

**If WP1 is revisited:** use a pitched-down camera or multiple photos (no blind zone), larger/open truth scenes (e.g. the house/lane worlds, not the cluttered kitchens), a stand-in generator that actually reproduces truth in the seen area, an alignment that does not depend on ICP on wall views, and consider collider meshes as the truth for falls. Re-pre-register before running.
