"""Build one synthetic-truth case: photo -> stand-in world -> confidence scores -> alignment -> error."""
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from .align import apply, icp_similarity, init_from_camera
from .raster import intrinsics, render, yaw_camera
from .synth import (H, HFOV_TRUE, LAMBDA, REF_W, TAU_REL, W, depth_with_tta, generate, load_truth,
                    render_photo)


def _ncc(a, b, m):
    a, b = a[m], b[m]
    return float(((a - a.mean()) * (b - b.mean())).mean() / (a.std() * b.std() + 1e-8))


def fov_fit(G, photo):
    w, h = W // 2, H // 2
    target = np.asarray(Image.fromarray(photo).resize((w, h), Image.BILINEAR), np.float32).mean(-1) / 255
    cands = np.arange(50, 80.1, 2.5)
    scores = []
    for f in cands:
        o = render(G, *yaw_camera(0), intrinsics(w, h, f), w, h)
        scores.append(_ncc(o["image"].mean(-1), target, o["alpha"] > 0.5))
    return float(cands[int(np.argmax(scores))])


def build_case(world, yaw, truth=None, icp_iters=100):
    """Everything WP1-3 need for one (truth world, yaw) case. `truth` may be passed to avoid reloading."""
    T = truth if truth is not None else load_truth(world)
    tp = T["centers"][T["opacity"] > 0.3]
    ttree = cKDTree(tp)
    photo, Dt, (R_cam, _) = render_photo(T, yaw)
    D, tta = depth_with_tta(photo)
    G, from_photo = generate(photo, D)
    N = len(G["centers"])

    hfov_hat = fov_fit(G, photo)
    Kh = intrinsics(W, H, hfov_hat)
    o = render(G, *yaw_camera(0), Kh, W, H, fisher=True)
    Hd = o["illum"] * (REF_W / W) ** 2
    Rres = Hd / (Hd + LAMBDA)
    seen = Rres >= 0.5
    c = G["centers"]
    zc = np.maximum(c[:, 2], 1e-6)
    u_px = Kh[0] * c[:, 0] / zc + Kh[2]
    v_px = Kh[1] * c[:, 1] / zc + Kh[3]
    in_frustum = (c[:, 2] > 0.05) & (u_px >= 0) & (u_px < W) & (v_px >= 0) & (v_px < H)
    tta_s = np.full(N, np.nan, np.float32)
    tta_s[in_frustum] = tta[v_px[in_frustum].astype(int), u_px[in_frustum].astype(int)]
    dist = np.linalg.norm(c, axis=1)
    abs_depth_std = np.nan_to_num(tta_s, nan=1.0) * dist

    ok = (Dt > 0) & np.isfinite(Dt) & (D > 0)
    s0 = float(np.median(Dt[ok] / D[ok]))
    sim0 = init_from_camera(R_cam, np.zeros(3), s0)
    sim, hist = icp_similarity(c[seen].astype(np.float64), ttree, tp.astype(np.float64), sim0, iters=icp_iters)
    err = ttree.query(apply(sim, c.astype(np.float64)), k=1)[0]
    tau = TAU_REL * float(np.median(Dt[ok]))
    return dict(world=world, yaw=yaw, photo=photo, truth_depth=Dt, depth_pred=D, tta=tta, G=G,
                from_photo=from_photo, seen=seen, R=Rres, illum=Hd, coverage=o["coverage"],
                in_frustum=in_frustum, tta_splat=tta_s, abs_depth_std=abs_depth_std, dist=dist,
                sim=sim, err=err, tau=tau, bad=err > tau, hfov_hat=hfov_hat, truth_pts=tp)
