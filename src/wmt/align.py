"""
Phase 2 alignment: bring a generated world into the frame of a reference ("truth") reconstruction.

Real Phase 2: reference = COLMAP reconstruction of a real room; the prompt photo is one of its
images, so its camera pose in the reference frame is known. Marble puts that camera at the origin
looking +z (Phase 0/0b), so:
    X_ref = s * R_cam^T X_gen + C_cam            (C_cam = camera centre, R_cam = world->camera rotation)
Only the scale s is unknown a priori. Initialize it from depth ratios along the photo's rays,
then refine (s, R, t) with trimmed similarity ICP using ONLY splats the photo actually constrains —
aligning on filled-in content would let generated geometry bias the frame.
"""
import numpy as np
from scipy.spatial import cKDTree


def umeyama(src, dst):
    """Least-squares similarity (s, R, t) with dst ~ s R src + t (Umeyama 1991)."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    a, b = src - mu_s, dst - mu_d
    cov = b.T @ a / len(src)
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    s = np.trace(np.diag(D) @ S) / a.var(0).sum()
    return s, R, mu_d - s * R @ mu_s


def apply(sim, X):
    s, R, t = sim
    return s * X @ R.T + t


def compose(outer, inner):
    """outer ∘ inner."""
    s2, R2, t2 = outer
    s1, R1, t1 = inner
    return s2 * s1, R2 @ R1, s2 * R2 @ t1 + t2


def init_from_camera(R_cam, C_cam, scale):
    return scale, R_cam.T.astype(np.float64), np.asarray(C_cam, np.float64)


def icp_similarity(src, dst_tree, dst_pts, sim0, iters=15, trim=0.8):
    """Trimmed similarity ICP: each iteration matches src -> nearest dst, keeps the best `trim`
    fraction of pairs (robust to partial overlap), re-solves Umeyama."""
    sim = sim0
    hist = []
    for _ in range(iters):
        X = apply(sim, src)
        d, j = dst_tree.query(X, k=1)
        keep = d <= np.quantile(d, trim)
        hist.append(float(np.median(d)))
        delta = umeyama(X[keep], dst_pts[j[keep]])
        sim = compose(delta, sim)
    d, _ = dst_tree.query(apply(sim, src), k=1)
    hist.append(float(np.median(d)))
    return sim, hist


if __name__ == "__main__":
    # self-test: recover a known similarity from a noisy, partial copy of a point cloud
    rng = np.random.default_rng(0)

    def box_surface(lo, hi, n):
        """n points on the 6 faces of an axis-aligned box (a room or a piece of furniture)."""
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        p = rng.uniform(lo, hi, (n, 3))
        ax = rng.integers(0, 3, n)
        side = rng.random(n) < 0.5
        p[np.arange(n), ax] = np.where(side, lo[ax], hi[ax])
        return p

    # surfaces, not a volume: a uniform volume has a near neighbour everywhere and gives ICP nothing to lock onto
    dst = np.vstack([box_surface((-3, -1.5, -2), (3, 1.2, 5), 30000),
                     box_surface((-2.5, 0.4, 2), (-0.5, 1.2, 4), 6000),
                     box_surface((1.0, -0.5, 3.5), (2.5, 1.2, 4.8), 6000)])
    ang = np.radians(7)
    R_true = np.array([[np.cos(ang), 0, np.sin(ang)], [0, 1, 0], [-np.sin(ang), 0, np.cos(ang)]])
    s_true, t_true = 1.37, np.array([0.2, -0.1, 0.4])
    sub = dst[dst[:, 2] > 0.5]                                               # partial overlap: only the front part
    src = ((sub - t_true) @ R_true) / s_true + rng.normal(0, 0.01, sub.shape)
    # realistic init (see module doc): camera pose known from the reference reconstruction, scale unknown.
    # Perturb it: 15% scale error + 2 deg rotation error (e.g. from pose/FOV estimation)
    e = np.radians(2)
    R_err = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    sim0 = (s_true * 0.85, R_err @ R_true, t_true)
    sim, hist = icp_similarity(src, cKDTree(dst), dst, sim0, iters=100)
    rot_err = np.degrees(np.arccos(np.clip((np.trace(sim[1] @ R_true.T) - 1) / 2, -1, 1)))
    print(f"ICP self-test: scale {sim[0]:.4f} (true {s_true}), rotation error {rot_err:.3f} deg, "
          f"translation error {np.linalg.norm(sim[2] - t_true):.4f}, median residual {hist[0]:.3f} -> {hist[-1]:.4f}")
    assert abs(sim[0] - s_true) < 0.005 * s_true and rot_err < 0.2 and np.linalg.norm(sim[2] - t_true) < 0.02
    print("align.py self-test passed")
