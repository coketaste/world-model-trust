import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments", "wp2_ot_alignment"))
from analyze import LEVELS, boot_ratio, case_basin, pooled_basin, wilson  # noqa: E402
from test_wp2_align import _room  # noqa: E402

from wmt.align import apply, icp_similarity  # noqa: E402
from wmt.wp2_align import IDENTITY, perturbation, pose_error, voxel_pick  # noqa: E402


def test_case_basin_requires_all_lower_levels():
    row = [1, 1, 1, 0.8, 1, 1, 1, 1]
    assert case_basin(row) == LEVELS[2]
    assert case_basin([0.8] + [1] * 7) == 0.0
    assert case_basin([1] * 8) == LEVELS[-1]


def test_pooled_basin_and_wilson_and_ratio():
    T = np.array([[1, 1, 1, 0.9, 0.5, 0, 0, 0], [1, 1, 1, 0.9, 0.5, 0, 0, 0]], float)
    assert pooled_basin(T, 0.9) == LEVELS[3]
    lo, hi = wilson(45, 50)
    assert 0.78 < lo < 0.9 < hi < 0.97
    r = boot_ratio([1.0, 1.0, 1.0, 1.0], [0.5, 0.5, 0.5, 0.5])
    assert np.isclose(r["ratio"], 2.0) and r["ratio_lo"] == 2.0


def test_sweep_sanity_icp_improves_tiny_perturbation():
    rng = np.random.default_rng(0)
    tgt = _room(rng, 30000)
    src = tgt[tgt[:, 2] > 1.5]
    src = src[voxel_pick(src, 3000)]
    tree = cKDTree(tgt)
    X0 = apply(perturbation(0.1, np.random.default_rng(1)), src)
    sim, hist = icp_similarity(X0, tree, tgt, IDENTITY, iters=100)
    # planar walls leave sliding directions unconstrained (small residual, wrong pose): test the residual
    assert hist[-1] < 0.5 * hist[0]
    # and the sanity opposite: a huge perturbation should not be trivially fixed by identity
    X1 = apply(perturbation(2.0, np.random.default_rng(1)), src)
    assert pose_error(IDENTITY, X1, src) > 1.0
