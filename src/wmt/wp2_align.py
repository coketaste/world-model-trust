"""WP2: alignment methods and perturbation protocol for the OT-vs-ICP basin study.

Similarity convention (same as wmt.align): x' = s R x + t, sim = (s, R, t).
"""
import numpy as np
from scipy.spatial import cKDTree

from .align import apply, compose, icp_similarity

IDENTITY = (1.0, np.eye(3), np.zeros(3))


# ---------------------------------------------------------------- utilities
def rodrigues(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3)
    k = w / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def voxel_pick(P, n_target, seed=0):
    """Roughly n_target points, one per occupied voxel (uniform coverage); deterministic."""
    P = np.asarray(P)
    if len(P) <= n_target:
        return np.arange(len(P))
    ext = np.ptp(P, 0)
    size = (np.prod(np.maximum(ext, 1e-6)) / n_target) ** (1 / 3) * 0.5
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(P))
    for _ in range(12):
        key = np.floor(P[order] / size).astype(np.int64)
        _, first = np.unique(key, axis=0, return_index=True)
        n = len(first)
        if 0.9 * n_target <= n <= 1.1 * n_target:
            break
        size *= (n / n_target) ** (1 / 2.2)
    return order[first]


def perturbation(level, rng):
    """Random similarity about the origin: scale (1+0.4 f)^+-1, rotation 30 deg*f, translation 1.0*f."""
    m = (1 + 0.4 * level) ** rng.choice([-1, 1])
    ax = rng.normal(size=3)
    ax /= np.linalg.norm(ax)
    R = rodrigues(ax * np.radians(30.0) * level)
    d = rng.normal(size=3)
    d = d / np.linalg.norm(d) * 1.0 * level
    return (float(m), R, d)


def pose_error(sim_est, X0, X_ref):
    """Median distance between the aligned perturbed source and its reference positions."""
    return float(np.median(np.linalg.norm(apply(sim_est, X0) - X_ref, axis=1)))


# ---------------------------------------------------------------- point-to-plane similarity ICP
def icp_point_to_plane_sim(src, tree, tgt_pts, tgt_nrm, iters=100, trim=0.8):
    """Gauss-Newton similarity ICP with a point-to-plane residual (7 DoF)."""
    sim = (1.0, np.eye(3), np.zeros(3))
    X = src.astype(np.float64).copy()
    for _ in range(iters):
        d, j = tree.query(X, k=1)
        keep = d <= np.quantile(d, trim)
        xk, y, n = X[keep], tgt_pts[j[keep]], tgt_nrm[j[keep]]
        r = ((xk - y) * n).sum(1)
        A = np.column_stack([np.cross(xk, n), n, (xk * n).sum(1)])
        delta, *_ = np.linalg.lstsq(A, -r, rcond=None)
        w, t, ds = delta[:3], delta[3:6], float(np.clip(delta[6], -0.3, 0.3))
        nw = np.linalg.norm(w)
        if nw > 0.4:
            w = w * 0.4 / nw
        Rw = rodrigues(w)
        step = (1.0 + ds, Rw, t)
        X = apply(step, X)
        sim = compose(step, sim)
        if np.linalg.norm(w) < 1e-7 and np.linalg.norm(t) < 1e-8 and abs(ds) < 1e-8:
            break
    return sim


# ---------------------------------------------------------------- unbalanced OT alignment
def _weighted_umeyama(X, Y, plan):
    """Minimise sum_ij plan_ij |s R x_i + t - y_j|^2 over similarities (closed form)."""
    M = plan.sum()
    if M < 1e-9:
        return None
    wx, wy = plan.sum(1), plan.sum(0)
    mux, muy = (wx @ X) / M, (wy @ Y) / M
    Xc, Yc = X - mux, Y - muy
    cov = Yc.T @ (plan.T @ Xc) / M
    var = (wx * (Xc ** 2).sum(1)).sum() / M
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    s = float(np.trace(np.diag(D) @ S) / max(var, 1e-12))
    return s, R, muy - s * R @ mux


def ot_align(src, tgt, rho=0.2, eps_start=1.0, eps_end=0.003, stages=14, iters=15, scale_step=None):
    """Unbalanced entropic-OT registration (similarity) with epsilon scaling.

    Alternates (a) log-domain unbalanced Sinkhorn (squared-distance cost, uniform marginals,
    KL marginal relaxation rho) with warm-started potentials, and (b) the closed-form weighted
    similarity update from the plan. `scale_step=(lo, hi)` optionally clips the per-stage scale update.
    """
    import torch
    torch.set_num_threads(1)
    n, m = len(src), len(tgt)
    Y = torch.as_tensor(tgt, dtype=torch.float32)
    loga = float(-np.log(n))
    logb = float(-np.log(m))
    f = torch.zeros(n)
    g = torch.zeros(m)
    sim = (1.0, np.eye(3), np.zeros(3))
    for eps in np.geomspace(eps_start, eps_end, stages):
        X = torch.as_tensor(apply(sim, src), dtype=torch.float32)
        C = torch.cdist(X, Y) ** 2
        tau = rho / (rho + eps)
        for _ in range(iters):
            f = -tau * eps * torch.logsumexp(logb + (g[None, :] - C) / eps, dim=1)
            g = -tau * eps * torch.logsumexp(loga + (f[:, None] - C) / eps, dim=0)
        plan = torch.exp(loga + logb + (f[:, None] + g[None, :] - C) / eps).double().numpy()
        delta = _weighted_umeyama(X.double().numpy(), Y.double().numpy(), plan)
        if delta is None:
            continue
        s, R, t = delta
        if scale_step is not None:
            s = float(np.clip(s, *scale_step))
            # re-solve translation for the clipped scale
            M = plan.sum()
            mux = (plan.sum(1) @ X.double().numpy()) / M
            muy = (plan.sum(0) @ Y.double().numpy()) / M
            t = muy - s * R @ mux
        sim = compose((s, R, t), sim)
    return sim
