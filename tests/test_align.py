import numpy as np
from scipy.spatial import cKDTree

from wmt.align import icp_similarity


def _box_surface(rng, lo, hi, n):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    p = rng.uniform(lo, hi, (n, 3))
    ax = rng.integers(0, 3, n)
    side = rng.random(n) < 0.5
    p[np.arange(n), ax] = np.where(side, lo[ax], hi[ax])
    return p


def test_icp_recovers_known_similarity():
    rng = np.random.default_rng(0)
    dst = np.vstack([_box_surface(rng, (-3, -1.5, -2), (3, 1.2, 5), 30000),
                     _box_surface(rng, (-2.5, 0.4, 2), (-0.5, 1.2, 4), 6000),
                     _box_surface(rng, (1.0, -0.5, 3.5), (2.5, 1.2, 4.8), 6000)])
    ang = np.radians(7)
    R_true = np.array([[np.cos(ang), 0, np.sin(ang)], [0, 1, 0], [-np.sin(ang), 0, np.cos(ang)]])
    s_true, t_true = 1.37, np.array([0.2, -0.1, 0.4])
    sub = dst[dst[:, 2] > 0.5]
    src = ((sub - t_true) @ R_true) / s_true + rng.normal(0, 0.01, sub.shape)
    e = np.radians(2)
    R_err = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    sim, _ = icp_similarity(src, cKDTree(dst), dst, (s_true * 0.85, R_err @ R_true, t_true), iters=100)
    rot_err = np.degrees(np.arccos(np.clip((np.trace(sim[1] @ R_true.T) - 1) / 2, -1, 1)))
    assert abs(sim[0] - s_true) < 0.005 * s_true
    assert rot_err < 0.2
    assert np.linalg.norm(sim[2] - t_true) < 0.02
