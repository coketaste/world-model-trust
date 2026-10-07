# results/

Write-ups, raw outputs and plots for each experiment. The web pages read these files through `scripts/build_site_data.py`.

| File(s) | What it is |
|---|---|
| `WP0.md`, `wp0_reproduce.json` | Illumination: reproduction of the baseline on the migrated code. |
| `WP1.md`, `wp1_results_run1_as_preregistered.json`, `wp1_results_amended.json`, `wp1_design_exploration.log` | Robots: the run as originally specified, the exploratory amended run, and the design diagnostics. |
| `WP1-sensitivity.md`, `wp1_sensitivity_*.json` | Post-hoc check that giving the baseline the same relaxation changes nothing. |
| `WP2.md`, `wp2_runs_{A,B,C}.json`, `wp2_analysis.json`, `wp2_basin_{A,B,C}.png`, `wp2_tuning*.json` | Alignment: the first evaluation, its analysis and plots, and the tuning runs (the first tuning run is kept for transparency). |
| `WP2-sensitivity.md`, `wp2_sensitivity_runs.json`, `wp2_sensitivity_analysis.json` | Post-hoc matched-compute rerun. |
| `WP3.md`, `wp3_stageA.json`, `wp3_summary.json`, `wp3_stress.json`, `wp3_*.png` | Shadows: the Fisher-information sweep, summary, stress tests and plots. |
| `wp*_prereg_hash.txt`, `wp*_sensitivity_hash.txt` | SHA-256 and timestamp of each pre-specification, recorded locally before the run. They were not committed beforehand, so they are self-attested. |

Naming: `WP0` to `WP3` are the internal work-package labels (illumination, robots, alignment, shadows); the web pages use plain experiment names. Some JSON files contain bare `Infinity` or `NaN` tokens (Python's default), which are not valid JSON for other tools; the site builder maps them to `null`.

Not committed (git-ignored, regenerable): `out/` (cached cases), per-job caches of the WP2 runs, `data/` (downloaded example exports).
