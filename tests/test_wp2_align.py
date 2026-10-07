import numpy as np
from scipy.spatial import cKDTree

from wmt.align import apply
from wmt.wp2_align import (icp_point_to_plane_sim, ot_align, perturbation, pose_error, rodrigues,
                           voxel_pick)


def _room(rng, n=40000):
    """Surfaces of a box room plus two boxes (surface-like data, as ICP/OT expect)."""
    def box(lo, hi, k):
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        p = rng.uniform(lo, hi, (k, 3))
        ax = rng.integers(0, 3, k)
        p[np.arange(k), ax] = np.where(rng.random(k) < 0.5, lo[ax], hi[ax])
        return p
    return np.vstack([box((-3, -1.5, -1), (3, 1.2, 6), n), box((-2.5, 0.4, 2), (-0.5, 1.2, 4), n // 5),
                      box((1.0, -0.5, 3.5), (2.5, 1.2, 4.8), n // 5)])


def test_perturbation_magnitudes():
    rng = np.random.default_rng(0)
    for f in (0.1, 1.0, 2.0):
        m, R, d = perturbation(f, rng)
        assert np.isclose(max(m, 1 / m), 1 + 0.4 * f)
        ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
        assert np.isclose(ang, 30 * f, atol=1e-6)
        assert np.isclose(np.linalg.norm(d), f)
    assert np.allclose(rodrigues(np.zeros(3)), np.eye(3))


def test_voxel_pick_count_and_determinism():
    rng = np.random.default_rng(1)
    P = rng.uniform(0, 1, (50000, 3))
    a, b = voxel_pick(P, 1000), voxel_pick(P, 1000)
    assert np.array_equal(a, b) and 800 < len(a) < 1200


def test_ot_recovers_known_similarity_with_partial_overlap():
    rng = np.random.default_rng(0)
    tgt_full = _room(rng)
    src_ref = tgt_full[tgt_full[:, 2] > 2.5]            # partial overlap: far half only
    src_ref = src_ref[voxel_pick(src_ref, 800)]
    tgt = tgt_full[voxel_pick(tgt_full, 2500)]
    # known-answer: a pure shift. (A 25% scale + 12 deg rotation is NOT recovered by this OT scheme; see results/WP2.md.)
    P = (1.0, np.eye(3), np.array([0.3, -0.2, 0.2]))
    X0 = apply(P, src_ref)
    sim = ot_align(X0, tgt, rho=0.2, stages=10, iters=6)
    assert pose_error(sim, X0, src_ref) < 0.15, "OT should recover a pure shift under partial overlap"


def test_p2plane_recovers_small_perturbation():
    rng = np.random.default_rng(2)
    tgt = _room(rng, 60000)
    from scipy.spatial import cKDTree as T
    tree = T(tgt)
    # crude normals from local PCA of 15 neighbours
    _, idx = tree.query(tgt[::5], k=15)
    nrm = np.zeros((len(tgt[::5]), 3))
    for i, nb in enumerate(idx):
        pts = tgt[nb] - tgt[nb].mean(0)
        nrm[i] = np.linalg.svd(pts, full_matrices=False)[2][-1]
    sub, nsub = tgt[::5], nrm
    src_ref = sub[sub[:, 2] > 1.0][::2]
    P = (1.1, rodrigues(np.array([0.0, 1.0, 0.0]) * np.radians(4)), np.array([0.1, 0.05, -0.1]))
    X0 = apply(P, src_ref)
    sim = icp_point_to_plane_sim(X0, cKDTree(sub), sub, nsub, iters=100)
    assert pose_error(sim, X0, src_ref) < 0.1


def test_sanity_zero_perturbation_is_fixed_point_for_ot():
    rng = np.random.default_rng(3)
    tgt_full = _room(rng)
    tgt = tgt_full[voxel_pick(tgt_full, 2000)]
    src = tgt[voxel_pick(tgt, 600)]
    sim = ot_align(src, tgt, rho=0.2)
    assert pose_error(sim, src, src) < 0.1
