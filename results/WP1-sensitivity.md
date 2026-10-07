# WP1 sensitivity analysis (post-hoc, exploratory): is the amended RQ1 comparison asymmetric?

**Status:** POST-HOC and EXPLORATORY. It does not replace `results/WP1.md` or the pre-registered result (`prereg/RQ1.md`). It was triggered by an internal check of this project's own work, which noted that the free blind zone went to the trust policies but not to the baseline, and that only 95 of 480 goals are in regions the photo saw. Written 2026-10-05 before any sensitivity run; the SHA-256 of this plan section is in `results/wp1_sensitivity_hash.txt`.

## 1. Plan (written and hashed BEFORE running)

### 1.1 The issue
In the amended exploratory run (`run.py --amended`), amendment A2 (treat floor inside the camera's blind zone, along clear lines of sight, as free) is added to the three trust policies (`frustum`, `visibility`, `ours`) but **not** to the baseline `unknown_obstacle` (UO). Amendment A3 (free robot-footprint disc of radius 0.3) is applied to every non-oracle policy, UO included, so A3 is already symmetric. A1 (truth floor height for the generated map) and A4 (alignment by camera height and rotation) apply to all generated-map policies equally. So the only asymmetry is A2.

### 1.2 What is varied (same 12 cases, same goals, same seeds 1000+index; only the per-policy free maps change)
- **S0** as amended: exact reproduction of `results/wp1_results_amended.json` (check: per-policy means and Delta CIs must match to 1e-9; if not, the sensitivity code is wrong).
- **S1** symmetric A2: UO also receives A2 (and A3, which it already has). The blind-zone radius and line-of-sight rule are identical to those of the trust policies.
- **S1b** symmetric the other way: nobody receives A2 (trust policies lose it); A3 stays. This brings back the "blind zone traps conservative policies" artifact for everyone and tests whether the artifact, not trust, drove run 1.
- **S2** (prompt camera pitched down so the floor near the start is in frame): **will not be run.** The cached cases (`out/cases/*.pkl`) come from level prompt photos; a pitched prompt camera would change the photo, the depth lift, the room-box prior and the confidence maps, i.e. require regenerating all 12 cases with a new generator geometry, which `wmt.synth` / `wmt.benchmark` do not support (the generator assumes a level camera at the origin). Emulating it by shrinking the blind radius would invent floor evidence the generated world does not contain. S1 (no penalty for the blind zone for anyone) is the closest cheap bound.
- **S3** stratified breakdown: for each of S0, S1, S1b, completion and failure restricted to goals in seen regions and in unseen regions, with the number of cases and goals contributing to each stratum.

### 1.3 Metrics and statistics
Per policy: completion, failure rate, planned rate, path ratio over goals completed by both the policy and UO (as in `run.py`). Differences versus UO: paired bootstrap over cases (`wmt.stats.paired_bootstrap`, 10,000 resamples, seed 0; exact mean, lower and upper bounds are reported without rounding). Three trust policies are compared and the gate uses `any()` over them, which inflates false positives; so a Bonferroni-adjusted interval (98.33% percentile interval from the same resampling scheme) is also reported next to the 95% one. The 12 cases come from 3 truth worlds (4 yaws each) and are not independent; intervals are indicative only. Path-ratio comparisons rest on very few cases (n_common). Only goals that exist in a stratum contribute (the seen stratum exists in 5 of 12 cases, 95 of 480 goals).

### 1.4 Hypothesis and how to read outcomes (stated in advance)
- **Hypothesis H1:** giving UO the same blind-zone relaxation removes most of the amended-run gap between UO and the trust policies, so Delta completion and Delta failure versus UO for `frustum`, `visibility`, `ours` stay close to zero with intervals that include zero.
- **H2:** under S1b (no relaxation for anyone) all conservative policies, UO included, are again largely trapped at the start, and differences vs UO are again near zero because they share the same limitation.
- **Reading:** the gate rule of `prereg/RQ1.md` is applied unchanged as a descriptive check (safety non-inferiority: upper bound of Delta failure <= 0.02; benefit: lower bound of Delta completion > 0 or upper bound of Delta path ratio < 0).
- **What would change the conclusion:** (a) if under S1 some trust policy has a Delta completion lower bound above 0 and a Delta failure upper bound <= 0.02, the statement "trust policies are indistinguishable from unknown = obstacle" would be revised to "better than UO under symmetric treatment (exploratory, post-hoc)"; (b) if under S1 UO is clearly better than a trust policy (Delta completion upper bound below 0), the amended result would be reported as having been biased in favour of the trust policies; (c) otherwise the exploratory conclusion stands (no trust policy beats UO) and the asymmetry is simply disclosed.

### 1.5 Fixed non-goals
No new policies, no new goals, no parameter tuning, no change to the original files. The original pre-registered and amended results stay as reported in `results/WP1.md`.

## 2. Results (appended after the run; the plan above is unchanged)

### Plain-language conclusion
Giving the "unknown = obstacle" baseline the same blind-zone relaxation as the trust policies changes nothing, because that baseline already reached the blind zone through the generator's own floor. So the amended comparison was not tilted toward the trust policies. With the baseline treated identically, none of the three trust policies (frustum, visibility, ours) differs from it in a way these data can detect: completion differs by 0.000 to -0.008 and failure by +0.002 to +0.004, with every interval including zero. The trust policies only match the baseline once the blind zone is given back to them; without that they complete nothing. The benchmark stays underpowered (the baseline completes goals in only 3 of 12 cases), so this is "no detectable difference", not proof that trust maps are useless.

Code: `experiments/wp1_robot_benchmark/run_sensitivity.py` (a copy of the amended `run_case` with a switch for who receives A2; `run.summarize` and `wmt.stats.paired_bootstrap` are reused). Raw output: `results/wp1_sensitivity_{S0,S1,S1b,summary}.json` (the JSON files contain bare `NaN` where a quantity is undefined, as in the other result files). The run takes about 30 seconds on CPU.

### 2.1 Reproduction check and the main finding
- **S0 reproduces the existing amended results exactly** (maximum absolute difference in per-policy means and Delta intervals: 0.0).
- **S1 is identical to S0 in every number.** The reason is structural, checked directly: in all 12 cases the blind-zone region that A2 adds (102–249 cells per case) is **already inside UO's free map** (0 cells added in 12 of 12 cases; UO's map has 114–442 cells). UO builds its map from *all* generated floor evidence inside the camera wedge, which includes the generator's own room-box prior floor, so it already reaches the blind zone. The trust masks (frustum, visibility, ours) restrict floor evidence to what the photo supports, which removes the near floor; A2 gives that back. So A2 was not a hidden advantage for the trust policies: it only restores to them a reach that UO already had. A3 was already applied to UO.
- Consequence: the asymmetry flagged by the internal check exists in the code but has no effect on any reported number for UO.

### 2.2 Per-policy means (12 cases, 480 goals)

| Policy | Completion S0 = S1 | Failure S0 = S1 | Completion S1b | Failure S1b |
|---|---|---|---|---|
| no_mask | 0.2521 | 0.0813 | 0.2521 | 0.0813 |
| frustum | 0.1708 | 0.0500 | 0.0000 | 0.0000 |
| visibility | 0.1792 | 0.0500 | 0.0000 | 0.0000 |
| ours | 0.1708 | 0.0479 | 0.0000 | 0.0000 |
| unknown_obstacle | 0.1792 | 0.0458 | 0.1792 | 0.0458 |
| oracle | 1.0000 | 0.0000 | 1.0000 | 0.0000 |

UO completes at least one goal in 3 of 12 cases. Path ratio over goals completed by both a policy and UO exists in 3 cases only (values 1.0000–1.0018).

### 2.3 Difference versus UO, S0 = S1 (paired bootstrap over 12 cases; exact bounds; Bonferroni = 98.33% interval for three comparisons)

| Policy | Delta completion [95%] | Bonferroni | Delta failure [95%] | Bonferroni | Delta path ratio (n = 3) |
|---|---|---|---|---|---|
| frustum | -0.008333 [-0.025000, 0.000000] | [-0.033333, 0.000000] | +0.004167 [0.000000, +0.012500] | [0.000000, +0.016667] | -0.000943 [-0.002828, 0.000000] |
| visibility | 0.000000 [0.000000, 0.000000] | [0.000000, 0.000000] | +0.004167 [0.000000, +0.012500] | [0.000000, +0.016667] | 0.000000 [0.000000, 0.000000] |
| ours | -0.008333 [-0.025000, 0.000000] | [-0.033333, 0.000000] | +0.002083 [0.000000, +0.006250] | [0.000000, +0.008333] | -0.000943 [-0.002828, 0.000000] |
| no_mask (reference) | +0.072917 [+0.027083, +0.131250] | [+0.022917, +0.143750] | +0.035417 [+0.008333, +0.070833] | [+0.004844, +0.081250] | -0.001774 [-0.002828, 0.000000] |

Gate rule applied descriptively: for frustum, visibility and ours, safety non-inferiority holds (upper bound of Delta failure <= 0.02, also after Bonferroni) but benefit does not (no lower bound of Delta completion above 0, no path-ratio improvement), so none passes. `no_mask` is faster to completion but fails the safety bound. Several bounds are exactly 0 because most per-case differences are 0 (only 3 of 12 cases have any UO completion); read these as degenerate resampling distributions, not as precision.

### 2.4 S1b (nobody gets A2)
The three trust policies complete nothing (completion 0.0000, failure 0.0000, no planned goals) while UO still completes 0.1792. Delta completion versus UO is -0.179167 [-0.375000, 0.000000] (Bonferroni [-0.431250, 0.000000]) for all three; Delta failure -0.045833 [-0.131250, 0.000000]. This is the blind-zone trap of the pre-registered run, now shown to hit the trust policies only because their masks remove the near floor, not because UO is smarter.

### 2.5 S3: seen-goals and unseen-goals strata
Seen goals exist in 5 of 12 cases (95 goals); unseen goals in 12 cases (385 goals).

| Variant | Stratum (cases, goals) | frustum | visibility | ours | unknown_obstacle | no_mask |
|---|---|---|---|---|---|---|
| S0 = S1 | seen (5, 95): completion / failure | 0.50 / 0.19 | 0.54 / 0.19 | 0.50 / 0.18 | 0.54 / 0.17 | 0.54 / 0.217 |
| S0 = S1 | unseen (12, 385) | 0.133 / 0.015 | 0.133 / 0.015 | 0.133 / 0.015 | 0.133 / 0.015 | 0.225 / 0.055 |
| S1b | seen (5, 95) | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.54 / 0.17 | 0.54 / 0.217 |
| S1b | unseen (12, 385) | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.133 / 0.015 | 0.225 / 0.055 |

Under S0 = S1 the unseen stratum shows no difference between any trust policy and UO (identical to the reported precision). In the seen stratum the trust policies are at or slightly below UO on completion (frustum and ours -0.04 [-0.12, 0.00]; visibility 0.00) and slightly above on failure (+0.01 to +0.02, upper bound <= 0.06). Over 5 cases these intervals are too wide to rule out differences of several percentage points either way. Under S1b the seen-stratum Delta completion is -0.54 [-0.91, -0.17] for all three, the only interval that excludes zero in this analysis.

### 2.6 S2 (pitched prompt camera)
Not run, for the reason given in the plan (the cached cases come from level prompt photos and the generator assumes a level camera; shrinking the blind radius by hand would invent floor evidence). S1 is the closest cheap bound: if the blind zone were free for everyone, the comparison is S0 = S1.

### 2.7 Reading against the plan (stated in advance)
- **H1 (symmetric relaxation removes the gap):** not testable as phrased, because the relaxation changes nothing for UO. The trust policies already sit at UO's level in S0 (Delta completion between -0.008 and 0.000; Delta failure +0.002 to +0.004).
- **H2 (nobody relaxed: all trapped, differences near zero):** wrong in detail. UO is not trapped, because it already reaches the blind zone through the generator's prior floor; only the trust policies are. So UO is better than the trust policies in S1b.
- **What would change the conclusion:** (a) not met (no trust policy beats UO under any variant); (b) not met under the symmetric comparison S1 (= S0); it is met in S1b, which is the pre-registered-run artifact and not a fair comparison; (c) holds: **no trust policy beats unknown = obstacle in this exploratory benchmark; the asymmetry in A2 does not bias the amended comparison.**

### 2.8 Caveats that still apply
- Exploratory and post-hoc; it does not rescue or overturn the pre-registered outcome (gate not passed).
- Multiplicity: three trust policies are compared and the gate uses `any()`; Bonferroni intervals are shown and do not change any reading.
- 12 cases from 3 truth worlds (4 yaws each) are not independent; bootstrap over cases ignores that clustering. Path-ratio statistics rest on 3 cases; the seen stratum on 5 cases.
- The amended maps use the truth floor height for every generated-map policy (A1) and a camera-height-based alignment (A4), which a real generated world would not provide, and UO's reach is partly inherited from the stand-in generator's room-box prior (a circularity: "unknown" is partly filled by our own prior).
- The benchmark remains underpowered: UO completes goals in only 3 of 12 cases, so most differences are exactly 0.
