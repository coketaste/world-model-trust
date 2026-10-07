# Pre-registration: RQ2 — optimal-transport misfit vs ICP for aligning generated geometry to reference geometry

Commit and tag this file **before** running the experiment (`git tag prereg-RQ2`). Later changes go in an "Amendments" section with date and reason.

- **Date / author:** 2026-10-02 / WP2 (for the repository authors)
- **Research question:** Does an optimal-transport (OT) misfit give a wider convergence basin than ICP when aligning a generated (partial, partly hallucinated) world to reference geometry in the presence of scale, rotation and translation error?
- **Hypothesis (falsifiable):** OT-based similarity alignment has a convergence basin at least 1.5x as wide as trimmed ICP's, with equal or better final accuracy. (FWI analogy: cycle skipping; Wasserstein misfits are more convex w.r.t. shifts and dilations, Engquist et al. arXiv 2002.00031; Métivier et al. 2016.)

## Data
- 12 cached synthetic-truth cases from WP0 (`out/cases/*.pkl`; 3 worlds x 4 yaws). Stand-in generator, not Marble.
- **Hold-out by world.** Tuning set = world `warm_traditional_kitchen_interior` (4 cases). **Evaluation set (primary) = the other two worlds** (`rustic_kitchen_with_natural_light`, `elegant_library_with_fireplace`; 8 cases). All hyperparameters are fixed on the tuning set with seeds 0-99; evaluation uses seeds >= 1000. Results on the tuning world are reported separately and never pooled into the primary test.
- Variants (source in the reference frame -> perturbed):
  - **A (primary): seen-only.** Source = voxel-subsampled generated splat centres with `seen == True`, placed in the reference frame by the stored ICP-converged transform `sim`. Target = truth splat centres (opacity > 0.3, ~380k). Partial overlap, no hallucinated content.
  - **B: all generated splats** (seen + invented room-box prior): partial overlap plus hallucinated geometry. Same reference transform.
  - **C: independent check, no ICP reference.** Source = truth points inside +-50 degrees of the case's viewing direction (yaw), plus Gaussian noise sigma = 0.02 scene units; target = full truth; reference transform = identity exactly. This removes the circularity of using an ICP result as ground truth.
- Caveat stated now: in A/B the "reference" is itself an ICP solution, so ICP has a built-in advantage (it converges to its own optimum); OT's final answer can differ slightly. Variant C is the unbiased check; if A and C disagree, C is more trusted.

## Perturbation protocol
- Perturbation P about the world origin (the prompt-camera position, where a generator's scale/rotation uncertainty actually lives): x -> m R (x) + d.
- Level f in {0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0}. At level f: scale multiplier m = (1 + 0.4 f)^(+-1) (random sign), rotation angle 30 deg * f about a random axis, translation 1.0 * f scene units in a random direction. Level f = 1.0 is the proposal's "scale +-40%, rotation 30 deg, translation 1 unit"; f up to 2 avoids censoring a wide basin.
- 5 random draws per case per level; fixed seeds (eval seeds >= 1000).

## Methods (all start from the perturbed source; none sees the reference)
1. **ICP-trimmed** — `wmt.align.icp_similarity`, trim 0.8, 100 iterations (existing code, unchanged).
2. **ICP point-to-plane (similarity)** — Gauss-Newton on 7 DoF (small-angle rotation, translation, log-free scale increment), trim 0.8, 100 iterations, target normals from 20-NN PCA (open3d); own implementation because open3d's point-to-plane is rigid only.
3. **OT (primary method under test)** — unbalanced entropic OT (squared-distance cost, uniform marginals, KL marginal relaxation rho) with epsilon-scaling, alternating with the closed-form weighted-Umeyama (similarity) update from the plan. Source voxel-subsampled to ~1000 points, target to ~2500 points. Epsilon schedule geometric from 1.0 to 0.003 (blur radius ~1.0 to ~0.055 scene units) over 14 stages, 15 log-domain Sinkhorn iterations per stage with warm-started potentials. **Only rho is tuned**, over {0.05, 0.2, 1.0}, on the tuning world (variants A+B pooled, minimising failure at f in {1.0, 1.5}); the schedule is fixed as stated.
4. **OT -> ICP hybrid (secondary)** — OT result followed by 30 iterations of trimmed ICP. Reported but not the method under test.
5. **FPFH+RANSAC global registration (reference, subset)** — open3d, voxel 0.15, FPFH radius 0.75, mutual filter, similarity (with scaling) point-to-point estimator; run on 2 draws per case per level on variant A only. Included because it does not depend on the initial guess; expected to suffer from scale error because FPFH is not scale-invariant.

## Metrics
- **Success** (per run): median over source points of the distance between the recovered position and the reference position <= 0.25 tau, where tau = 0.1 x median truth depth stored in each case (about 0.25 scene units, so tolerance about 0.06 units).
- **Final accuracy** (per run, reference-free): median nearest-neighbour distance from the aligned source to the truth points.
- **Basin of a case** = largest level f such that all 5 draws succeed at every level <= f (0 if level 0.1 already fails). **Pooled basin curve** = success rate per level over all runs.
- **Basin width** summarised as mean per-case basin over the evaluation cases.

## Success criterion (numeric, with CI requirement)
Primary (variant A, evaluation set, OT vs ICP-trimmed): **mean OT basin / mean ICP basin >= 1.5 with the 95% paired-bootstrap CI (cases resampled, 10 000 draws) of the ratio having lower bound > 1.0**, AND among runs where both succeed, **mean final accuracy of OT <= 1.10 x that of ICP-trimmed**. If the ICP basin is 0 for all cases, the ratio is undefined and the criterion is evaluated as "OT basin >= 0.35 and ICP basin = 0".
Variant C is reported as the same test. The hypothesis is called **supported** only if A passes and C does not contradict it (OT basin >= ICP basin in C); **not supported** if A fails; **inconclusive** if A passes but C contradicts.

## Statistical plan
Paired bootstrap over cases (10 000 resamples, seed 0) for basin differences and ratio; Wilson intervals for pooled per-level success rates (runs are not independent within a case, so they are descriptive only).

## Planned sanity checks / known-answer tests
- OT alignment recovers a known similarity on a toy surface cloud with partial overlap (unit test).
- At f -> 0 (tiny perturbation) all methods succeed (basin sweep sanity).
- Perturbation generator: identity at f = 0; scale/rotation/translation magnitudes as stated (unit test).

## Circularity audit
- A/B: reference = ICP result (ICP advantaged on final accuracy relative to the reference; success tolerance is generous to mitigate). C: reference exact.
- Both source and target derive from the same truth world (no domain gap beyond stand-in generation in A/B). Output from a real generator would differ from the stand-in's.
- Voxel subsampling of the OT inputs (1000/2500 points) makes OT's resolution coarser than ICP's (up to 8000 source points and the full target); this disadvantages OT's final accuracy, hence the secondary hybrid.

## Compute and cost budget
CPU only, 4 worker processes with 1 thread each. No paid API use, no network use beyond package installation. If runtime is excessive, the number of draws or the OT subsample size may be reduced as a recorded amendment.

## Stopping rule / decision gate
Gate for WP2 (from PROPOSAL.md): OT basin >= 1.5x ICP's. If the gate fails, report as a negative result and do not pursue OT misfits further for alignment in this project.

## Results (fill after the run)

## Amendments

### Amendment 1 (2026-10-03, BEFORE any evaluation-set run; after toy-cloud diagnostics and timing only)
Reason: toy diagnostics (a synthetic box-room cloud, not any case data) showed (a) with `eps_start` = 1.0 OT cannot even start from a 30-degree rotation about the camera (point displacement up to ~3 scene units), so the schedule start is a hyperparameter that must scale with the perturbation; (b) 1000/2500-point subsamples cost ~10 s per OT run, which is too slow. Changes:
1. `eps_start` is tuned jointly with `rho` on the tuning world, grid rho in {0.05, 0.2, 1.0} x eps_start in {1, 4, 9}; schedule end stays 0.003.
2. OT sizes reduced to source ~600 / target ~1500 points, 10 epsilon stages, 6 Sinkhorn iterations per stage.
3. All methods are scored on a common evaluation point set (the ~6000-point voxel subsample used by the ICP methods); the OT transform is estimated from a ~600-point subset of it.
4. A second, coarse tolerance is added: **coarse success = median error <= 1.0 tau** ("in the right basin"), because the 1500-point target limits OT's final resolution to roughly the point spacing (~0.2 units) irrespective of basin. The pre-registered criterion above (strict, 0.25 tau) stays the primary criterion and the decision gate; coarse and hybrid (OT -> ICP) results are reported alongside and interpreted explicitly.
5. Tuning objective: strict successes + coarse successes summed over the tuning runs (strict alone is resolution-limited), ties broken by coarse successes. Tuning uses variants A and B, levels {1.0, 1.5}, 3 draws, seeds 0..
6. open3d needs `libusb-1.0.so.0`; provided through a symlink to the `libusb-package` wheel and `LD_LIBRARY_PATH` (no sudo).
7. FPFH baseline: without the edge-length checker (it would reject all pairs when scale error is 1.4-1.8x); distance checker only.

### Amendment 2 (2026-10-03, BEFORE any evaluation-set run)
Reason: the first tuning run (levels {1.0, 1.5}, tuning world only) gave 1 coarse success in 432 OT runs, i.e. no discrimination between configurations; a diagnostic on a single tuning case showed OT works at low perturbation levels (error ~0.4-1.5 tau at f <= 0.5, limited by target resolution and a scale bias from entropic blur) but fails at f >= 0.75 for the configurations tried. Changes: tuning levels become {0.2, 0.5, 1.0} (3 draws, seeds 0.., variants A and B, tuning world only), and the grid is widened to rho in {0.05, 0.1, 0.2, 0.5} x eps_start in {0.5, 1, 2, 4}. Selection objective unchanged (strict + coarse successes). The evaluation protocol, levels, success definitions and criteria are unchanged. The first tuning run is kept in results/wp2_tuning_run1.json for transparency.

### Amendment 3 (2026-10-03, implementation only; the first evaluation launch crashed before saving any results)
A degenerate ICP solution (zero source variance -> NaN scale) raised an exception in the KD-tree query and killed the first evaluation launch of variant A; no results were produced or inspected. Fix: a non-finite transform is scored as a failed run (error = infinity); per-case results are cached on disk so a crash cannot lose finished cases. No change to methods, levels, seeds, hyperparameters or criteria.
Update (same day, still before any evaluation result was produced): the relaunch crashed again inside `icp_similarity` itself (NaN scale propagates to the next KD-tree query). Alignment calls are now wrapped so that this `ValueError` scores the run as failed. Cases finished before the crash (variant A, 6 of 8) are reused from the cache; they ran without exceptions and are unaffected.

### Editorial change (2026-10-06)
Reworded 1 descriptive sentence about the stand-in generator for a neutral, accurate tone, and replaced a name placeholder in the header. No hypothesis, baseline, metric, success criterion or analysis was changed. The file's hash was re-recorded in `results/wp2_prereg_hash.txt` with this date.

Editorial change (2026-10-06, header only): replaced internal tooling wording in the author line. No hypothesis, criterion or analysis changed.
