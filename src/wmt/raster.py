"""
Tile-based CPU Gaussian-splat rasterizer that, besides the image, returns the
per-Gaussian "illumination" — the diagonal of the Gauss-Newton Hessian.

Why this exists: evaluating every Gaussian at every pixel (dense O(N x pixels)) is fine for
a few thousand Gaussians but hopeless for a 500k-2M splat world. Tiled splatting gets its
speed from *tiling*:
cull each Gaussian to the 16x16 screen tiles its 3-sigma footprint touches,
sort (tile, depth) pairs once, then each tile only composites its own short
list front-to-back and stops when it goes opaque. This is an independent implementation
of the tile-based splatting method of Kerbl et al. (3D Gaussian Splatting, ACM TOG 2023,
arXiv:2308.04079) in numpy (no CUDA); no code is taken from the authors' reference
implementation.

Camera convention: OpenCV / "marble_raw_opencv" — x right, y DOWN, z FORWARD.
A camera is (R, t, fx, fy, cx, cy) with X_cam = R @ X_world + t.

Illumination. Rendered pixel color is linear in each Gaussian's color:
    I(p) = sum_i w_i(p) c_i,   w_i(p) = alpha_i(p) * T_i(p)
so dI(p)/dc_i = w_i(p) exactly, and the Gauss-Newton Hessian diagonal of the
photometric misfit w.r.t. c_i is
    H_ii = sum_p w_i(p)^2
— the direct analogue of the seismic illumination map diag(J^T J).
"""
import numpy as np

TILE = 16
ALPHA_MIN = 1.0 / 255.0   # same cutoffs as the reference CUDA rasterizer
ALPHA_MAX = 0.99
T_MIN = 1e-4
DILATION = 0.3            # low-pass dilation of the 2D covariance (as in mini_3dgs.py)
NEAR = 0.05


def quat_to_rotmat(q):
    """(N,4) xyzw -> (N,3,3)."""
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    x, y, z, w = q.T
    return np.stack([
        1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
        2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
        2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y),
    ], axis=-1).reshape(-1, 3, 3).astype(np.float32)


def covariances(scales, quats):
    R = quat_to_rotmat(quats)
    RS = R * scales[:, None, :]
    return RS @ RS.transpose(0, 2, 1)


def look_at(eye, target, up=(0, -1, 0)):
    """OpenCV-convention camera at `eye` looking at `target` (up defaults to -y, i.e. world 'up' in y-down)."""
    eye, target, up = (np.asarray(v, np.float32) for v in (eye, target, up))
    z = target - eye
    z /= np.linalg.norm(z)
    x = np.cross(z, up)  # forward=(0,0,1), up=(0,-1,0) -> right=(1,0,0)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)   # -> (0,1,0), i.e. image-down
    R = np.stack([x, y, z])  # rows = camera axes in world coords
    return R, -R @ eye


def yaw_camera(yaw_deg, eye=(0, 0, 0), pitch_deg=0.0):
    """Camera at `eye` rotated by yaw about world y (0 = looking down +z) and pitch (+ = look up)."""
    yaw, pitch = np.radians(yaw_deg), np.radians(pitch_deg)
    fwd = np.array([np.sin(yaw) * np.cos(pitch), -np.sin(pitch), np.cos(yaw) * np.cos(pitch)], np.float32)
    eye = np.asarray(eye, np.float32)
    return look_at(eye, eye + fwd)


def intrinsics(W, H, hfov_deg):
    fx = 0.5 * W / np.tan(np.radians(hfov_deg) / 2)
    return fx, fx, W / 2.0, H / 2.0


def project(centers, cov3d, opacity, R, t, K, W, H):
    """Per-Gaussian screen-space mean, conic (inverse 2D cov) and pixel radius."""
    fx, fy, cx, cy = K
    pc = centers @ R.T + t
    z = pc[:, 2]
    valid = z > NEAR
    zc = np.where(valid, z, 1.0)
    # clamp x/z, y/z to slightly beyond the frustum, as the reference does, so the Jacobian stays sane
    lim_x, lim_y = 1.3 * (0.5 * W / fx), 1.3 * (0.5 * H / fy)
    tx = np.clip(pc[:, 0] / zc, -lim_x, lim_x) * zc
    ty = np.clip(pc[:, 1] / zc, -lim_y, lim_y) * zc

    u = fx * pc[:, 0] / zc + cx
    v = fy * pc[:, 1] / zc + cy

    zeros = np.zeros_like(zc)
    J = np.stack([fx / zc, zeros, -fx * tx / zc ** 2,
                  zeros, fy / zc, -fy * ty / zc ** 2], axis=-1).reshape(-1, 2, 3)
    M = J @ R[None]
    cov2d = M @ cov3d @ M.transpose(0, 2, 1)
    a = cov2d[:, 0, 0] + DILATION
    b = cov2d[:, 0, 1]
    c = cov2d[:, 1, 1] + DILATION
    det = a * c - b * b
    valid &= det > 0
    det = np.where(valid, det, 1.0)
    conic = np.stack([c / det, -b / det, a / det], axis=1)

    mid = 0.5 * (a + c)
    lam_max = mid + np.sqrt(np.maximum(0.1, mid * mid - det))
    radius = np.ceil(3.0 * np.sqrt(lam_max))

    valid &= (u + radius > 0) & (u - radius < W) & (v + radius > 0) & (v - radius < H)
    valid &= opacity > ALPHA_MIN
    return dict(u=u, v=v, depth=z, conic=conic, radius=radius, valid=valid, M=M)


def bin_to_tiles(proj, W, H):
    """Expand each visible Gaussian into one (tile, gaussian) pair per touched tile, sorted by (tile, depth)."""
    tw, th = (W + TILE - 1) // TILE, (H + TILE - 1) // TILE
    idx = np.nonzero(proj["valid"])[0]
    u, v, r = proj["u"][idx], proj["v"][idx], proj["radius"][idx]
    tx0 = np.clip(np.floor((u - r) / TILE), 0, tw - 1).astype(np.int64)
    tx1 = np.clip(np.floor((u + r) / TILE), 0, tw - 1).astype(np.int64)
    ty0 = np.clip(np.floor((v - r) / TILE), 0, th - 1).astype(np.int64)
    ty1 = np.clip(np.floor((v + r) / TILE), 0, th - 1).astype(np.int64)
    nx, ny = tx1 - tx0 + 1, ty1 - ty0 + 1
    counts = nx * ny

    g = np.repeat(idx, counts)
    starts = np.repeat(np.cumsum(counts) - counts, counts)
    k = np.arange(len(g)) - starts
    nx_r = np.repeat(nx, counts)
    tile = (np.repeat(ty0, counts) + k // nx_r) * tw + (np.repeat(tx0, counts) + k % nx_r)

    order = np.lexsort((proj["depth"][g], tile))
    g, tile = g[order], tile[order]
    bounds = np.searchsorted(tile, np.arange(tw * th + 1))
    return g, bounds, tw, th


def render(scene, R, t, K, W, H, colors=None, bg=0.0, chunk=2048, fisher=False):
    """Render one view. Returns image, expected depth, alpha, and per-Gaussian
    sum_p w (coverage) and sum_p w^2 (illumination / Gauss-Newton Hessian diagonal).

    fisher=True also returns the per-Gaussian 3x3 POSITION Fisher information of the
    luminance image, F_i = sum_p (dL(p)/dmu_i)(dL(p)/dmu_i)^T, via a second compositing pass:
        dL/dalpha_i = l_i T_i - B_i / (1 - alpha_i)      (B_i = luminance composited behind i)
        dalpha_i/du_i = alpha_i * Q_i (p - u_i)           (u_i = 2D mean, Q_i = conic)
        du_i/dmu_i = M_i = J_i R                          (perspective Jacobian)
    Ignored (second order): the change of the 2D footprint and of depth order with mu. Under this
    approximation M_i annihilates the ray direction, so one view reports zero information along the
    ray. The full model is not exactly zero (moving along the ray changes the footprint: ~1% of lateral
    information in tests); what is exactly unobservable from one view is the JOINT depth-size direction
    (near-and-small == far-and-large), i.e. the monocular scale ambiguity."""
    centers, opacity = scene["centers"], scene["opacity"]
    colors = scene["rgb"] if colors is None else colors
    # callers rendering many views should precompute scene["cov3d"] once; it is never cached here,
    # so editing scales/quats in place can't silently render stale covariances
    cov3d = scene["cov3d"] if "cov3d" in scene else covariances(scene["scales"], scene["quats"])

    proj = project(centers, cov3d, opacity, R, t, K, W, H)
    g_sorted, bounds, tw, th = bin_to_tiles(proj, W, H)

    N = len(centers)
    C = colors.shape[1]  # any channel count: e.g. rgb and a false-color overlay stacked in one pass
    bg = np.broadcast_to(np.asarray(bg, np.float32), (C,))
    image = np.zeros((H, W, C), np.float32)
    depth = np.zeros((H, W), np.float32)
    depth_med = np.zeros((H, W), np.float32)  # depth where accumulated opacity crosses 0.5 (robust to faint floaters)
    alpha_acc = np.zeros((H, W), np.float32)
    coverage = np.zeros(N, np.float64)
    illum = np.zeros(N, np.float64)
    G = np.zeros((N, 3), np.float64) if fisher else None  # sum_p g g^T in image space: (xx, xy, yy)
    lum = scene["rgb"].mean(1).astype(np.float32) if fisher else None

    u, v, conic, z = proj["u"], proj["v"], proj["conic"], proj["depth"]
    for ty in range(th):
        for tx in range(tw):
            tid = ty * tw + tx
            lo, hi = bounds[tid], bounds[tid + 1]
            x0, y0 = tx * TILE, ty * TILE
            x1, y1 = min(x0 + TILE, W), min(y0 + TILE, H)
            py, px = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5  # pixel centers
            px, py = px.ravel(), py.ravel()
            T = np.ones(px.size, np.float32)
            col = np.zeros((px.size, C), np.float32)
            dep = np.zeros(px.size, np.float32)
            dmed = np.full(px.size, np.inf, np.float32)

            for s in range(lo, hi, chunk):
                gi = g_sorted[s:min(s + chunk, hi)]
                dx = px[None, :] - u[gi, None]
                dy = py[None, :] - v[gi, None]
                cA, cB, cC = conic[gi, 0:1], conic[gi, 1:2], conic[gi, 2:3]
                power = -0.5 * (cA * dx * dx + cC * dy * dy) - cB * dx * dy
                alpha = np.minimum(ALPHA_MAX, opacity[gi, None] * np.exp(np.minimum(power, 0)))
                alpha[(power > 0) | (alpha < ALPHA_MIN)] = 0.0
                # exclusive cumulative product along the depth-sorted axis = transmittance in front of each Gaussian
                one_m = 1.0 - alpha
                Tex = np.cumprod(np.vstack([T[None, :], one_m[:-1]]), axis=0)
                w = alpha * Tex                                   # (k, pixels) blending weights
                w[Tex < T_MIN] = 0.0                              # per-pixel early termination
                col += w.T @ colors[gi]
                dep += w.T @ z[gi]
                cross = (Tex >= 0.5) & (Tex * one_m < 0.5)        # T drops through 0.5 at this Gaussian (at most once per pixel)
                hit = cross.any(0)
                dmed[hit] = z[gi][cross.argmax(0)[hit]]
                np.add.at(coverage, gi, w.sum(1))
                np.add.at(illum, gi, (w * w).sum(1))
                T = Tex[-1] * one_m[-1]
                if T.max() < T_MIN:
                    break

            if fisher and hi > lo:
                Lt = (col + T[:, None] * bg).mean(1) if C == 3 else None
                if Lt is None:  # luminance of the scene colors, composited the same way
                    raise ValueError("fisher=True needs 3-channel colors")
                T2 = np.ones(px.size, np.float32)
                front = np.zeros(px.size, np.float32)
                for s in range(lo, hi, chunk):
                    gi = g_sorted[s:min(s + chunk, hi)]
                    dx = px[None, :] - u[gi, None]
                    dy = py[None, :] - v[gi, None]
                    cA, cB, cC = conic[gi, 0:1], conic[gi, 1:2], conic[gi, 2:3]
                    power = -0.5 * (cA * dx * dx + cC * dy * dy) - cB * dx * dy
                    alpha = np.minimum(ALPHA_MAX, opacity[gi, None] * np.exp(np.minimum(power, 0)))
                    live = (power <= 0) & (alpha >= ALPHA_MIN) & (alpha < ALPHA_MAX)
                    alpha[(power > 0) | (alpha < ALPHA_MIN)] = 0.0
                    one_m = 1.0 - alpha
                    Tex = np.cumprod(np.vstack([T2[None, :], one_m[:-1]]), axis=0)
                    w = alpha * Tex
                    live &= Tex >= T_MIN
                    incl = front[None, :] + np.cumsum(w * lum[gi, None], axis=0)  # luminance composited up to and incl. i
                    dLda = Tex * lum[gi, None] - (Lt[None, :] - incl) / np.maximum(one_m, 1e-3)
                    a_d = np.where(live, dLda * alpha, 0.0)
                    gx = a_d * (cA * dx + cB * dy)
                    gy = a_d * (cB * dx + cC * dy)
                    np.add.at(G, gi, np.stack([(gx * gx).sum(1), (gx * gy).sum(1), (gy * gy).sum(1)], 1))
                    front = incl[-1]
                    T2 = Tex[-1] * one_m[-1]
                    if T2.max() < T_MIN:
                        break

            acc = 1.0 - T
            image[y0:y1, x0:x1] = (col + T[:, None] * bg).reshape(y1 - y0, x1 - x0, C)
            depth[y0:y1, x0:x1] = (dep / np.maximum(acc, 1e-6)).reshape(y1 - y0, x1 - x0)
            alpha_acc[y0:y1, x0:x1] = acc.reshape(y1 - y0, x1 - x0)
            depth_med[y0:y1, x0:x1] = dmed.reshape(y1 - y0, x1 - x0)

    out = dict(image=image, depth=depth, depth_median=depth_med, alpha=alpha_acc, coverage=coverage, illum=illum,
               n_pairs=len(g_sorted), n_visible=int(proj["valid"].sum()))
    if fisher:
        G2 = np.zeros((N, 2, 2))
        G2[:, 0, 0], G2[:, 0, 1], G2[:, 1, 0], G2[:, 1, 1] = G[:, 0], G[:, 1], G[:, 1], G[:, 2]
        M = proj["M"].astype(np.float64)
        out["fisher"] = M.transpose(0, 2, 1) @ G2 @ M  # (N, 3, 3) in world coordinates
    return out


def render_dense_reference(scene, R, t, K, W, H, colors=None, bg=(0.0, 0.0, 0.0)):
    """Brute-force reference: every Gaussian at every pixel, one global depth sort
    (the mini_3dgs.py algorithm). Only for testing on small scenes."""
    centers, opacity = scene["centers"], scene["opacity"]
    colors = scene["rgb"] if colors is None else colors
    cov3d = covariances(scene["scales"], scene["quats"])
    proj = project(centers, cov3d, opacity, R, t, K, W, H)
    idx = np.nonzero(proj["valid"])[0]
    idx = idx[np.argsort(proj["depth"][idx], kind="stable")]
    py, px = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    px, py = px.ravel(), py.ravel()
    dx = px[None] - proj["u"][idx, None]
    dy = py[None] - proj["v"][idx, None]
    cA, cB, cC = (proj["conic"][idx, k:k + 1] for k in range(3))
    power = -0.5 * (cA * dx * dx + cC * dy * dy) - cB * dx * dy
    alpha = np.minimum(ALPHA_MAX, opacity[idx, None] * np.exp(np.minimum(power, 0)))
    alpha[(power > 0) | (alpha < ALPHA_MIN)] = 0.0
    Tex = np.cumprod(np.vstack([np.ones((1, px.size), np.float32), 1 - alpha[:-1]]), axis=0)
    w = alpha * Tex
    w[Tex < T_MIN] = 0.0
    T = Tex[-1] * (1 - alpha[-1])
    image = (w.T @ colors[idx] + T[:, None] * np.asarray(bg, np.float32)).reshape(H, W, 3)
    illum = np.zeros(len(centers))
    illum[idx] = (w * w).sum(1)
    return dict(image=image, illum=illum)


