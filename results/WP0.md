# WP0: baseline migration and reproduction

**Date:** 2026-10-02 · **Status:** passed

## What was done
- Migrated `spz_io.py`, `raster.py` and `align.py` from the author's learning repository into `src/wmt/`, unchanged except for imports.
- Added `wmt/stats.py` (AUROC, paired bootstrap), `wmt/synth.py` (stand-in generator and 12-case setup) and `wmt/benchmark.py` (`build_case`).
- Added `scripts/fetch_data.py`: downloads the public example exports and verifies SHA-256 (all 14 files verified). No World Labs assets are committed.
- Tests: `pytest` passes (5 tests: camera convention, tiled vs dense renderer, illumination = Hessian diagonal, position Fisher vs finite differences, ICP known-answer).

## Reproduction of recorded numbers (12 cases, rank-normalised pooling)

| Score | Recorded (4.1) | Migrated code | Difference |
|---|---|---|---|
| ours (1 − R) | 0.8346 | 0.8346 | 0.0000 |
| visibility | 0.8317 | 0.8317 | 0.0000 |
| frustum | 0.7428 | 0.7428 | 0.0000 |

Gate (|difference| ≤ 0.01): **passed**.

Paired bootstrap over the 12 cases (10,000 resamples):

| Comparison | Mean ΔAUROC | 95% CI | Wins |
|---|---|---|---|
| ours vs visibility | +0.0033 | [+0.0011, +0.0055] | 9/12 |
| ours vs frustum | +0.0864 | [+0.0511, +0.1233] | 12/12 |

The CI excludes zero for ours vs visibility, but the effect is about 0.003 AUROC, which is negligible in practice. This matches the earlier review (REVIEW.md M3). The "+0.014 [−0.006, +0.036]" tie reported in the review compared a different, tier-based score (tier then absolute depth std) against visibility; the plain illumination score used here differs from visibility by a negligible, though statistically detectable, amount.

## Circularity of the error labels
The per-splat error labels come from aligning the generated world to the truth with ICP on the splats the illumination score flags as "seen". That favours scores built on seen-ness (illumination, visibility) over the frame test. The earlier study also ran a variant with no ICP (scale initialised from depth ratios only): pooled AUROC illumination 0.812, visibility 0.809, frame test 0.749 (from the author's earlier illumination study, which is not part of this repository; its log entry `auroc_all_no_icp`). The ordering is the same, and the gap to the frame test is about 0.06, a little smaller than with ICP. This repository's migrated code does not recompute that variant.

## Caveats carried over
- The generator is a stand-in (depth network + room-box prior), not Marble.
- "Imagined means wrong" is partly circular because the invented geometry is our own box prior; seen-tier results are the fair test.
- N = 12 cases from 3 truth worlds; per-case cases are not independent across yaws of the same world.

## Reproduce
```
python scripts/fetch_data.py
python -m pytest -q
python experiments/wp0_baseline/reproduce.py
```
