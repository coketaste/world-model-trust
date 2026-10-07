"""
Correctness checks for raster.py (run: pytest).

1. Camera convention: identity camera looks down +z with +y = image-down.
2. Tiled renderer vs. brute-force dense reference (mini_3dgs.py's algorithm):
   images and illumination must agree up to the 3-sigma tile-culling
   approximation (the real CUDA rasterizer makes the same approximation).
3. Illumination really is the Gauss-Newton Hessian diagonal: for a few
   Gaussians, perturb color c_i by eps, finite-difference the rendered image,
   and check sum_p (dI/dc_i)^2 == illum_i.
"""
import numpy as np

from wmt.raster import intrinsics, look_at, render, render_dense_reference, yaw_camera

rng = np.random.default_rng(0)


def random_scene(n):
    q = rng.normal(size=(n, 4)).astype(np.float32)
    return dict(
        centers=np.column_stack([rng.uniform(-1, 1, n), rng.uniform(-0.8, 0.8, n), rng.uniform(2, 5, n)]).astype(np.float32),
        scales=np.exp(rng.uniform(np.log(0.02), np.log(0.25), (n, 3))).astype(np.float32),
        quats=q / np.linalg.norm(q, axis=1, keepdims=True),
        opacity=rng.uniform(0.05, 0.95, n).astype(np.float32),
        rgb=rng.uniform(0, 1, (n, 3)).astype(np.float32),
    )


def test_camera_convention():
    R, t = yaw_camera(0)
    assert np.allclose(R, np.eye(3), atol=1e-6) and np.allclose(t, 0), R
    R, t = look_at((0, 0, 0), (1, 0, 0))  # looking +x: camera right should be world -z... check forward row
    assert np.allclose(R[2], [1, 0, 0], atol=1e-6) and np.allclose(R[1], [0, 1, 0], atol=1e-6)
    W, H = 64, 48
    K = intrinsics(W, H, 60)
    # a single opaque blob straight ahead and slightly "down" (+y) must land below image center
    s = dict(centers=np.array([[0, 0.3, 3]], np.float32), scales=np.full((1, 3), 0.05, np.float32),
             quats=np.array([[0, 0, 0, 1]], np.float32), opacity=np.array([0.9], np.float32),
             rgb=np.ones((1, 3), np.float32))
    img = render(s, *yaw_camera(0), K, W, H)["image"][..., 0]
    yy, xx = np.unravel_index(img.argmax(), img.shape)
    assert yy > H / 2 and abs(xx - W / 2) <= 1, (yy, xx)
    print("camera convention: OK (identity looks +z, +y renders below center)")


def test_tiled_vs_dense():
    W, H = 80, 60
    K = intrinsics(W, H, 70)
    R, t = yaw_camera(5, pitch_deg=3)
    for name, scale_mult, opac in (("large translucent", 1.0, None), ("small opaque", 0.3, 0.95)):
        s = random_scene(400)
        s["scales"] *= scale_mult
        if opac is not None:
            s["opacity"][:] = opac
        a = render(s, R, t, K, W, H)
        b = render_dense_reference(s, R, t, K, W, H)
        img_err = np.abs(a["image"] - b["image"]).max()
        rel_illum = np.abs(a["illum"] - b["illum"]).sum() / b["illum"].sum()
        print(f"tiled vs dense ({name}, coverage {a['alpha'].mean():.2f}): "
              f"max pixel diff {img_err:.2e}, relative illumination L1 diff {rel_illum:.2e}")
        assert img_err < 0.05 and rel_illum < 0.05


def test_illum_is_hessian_diagonal():
    s = random_scene(150)
    W, H = 48, 36
    K = intrinsics(W, H, 70)
    R, t = yaw_camera(0)
    base = render(s, R, t, K, W, H)
    eps = 1e-3
    for i in np.argsort(-base["illum"])[:5]:
        c = s["rgb"].copy()
        c[i, 0] += eps
        pert = render(s, R, t, K, W, H, colors=c)
        dI = (pert["image"][..., 0] - base["image"][..., 0]) / eps
        fd = float((dI.astype(np.float64) ** 2).sum())
        assert abs(fd - base["illum"][i]) / base["illum"][i] < 1e-2, (i, fd, base["illum"][i])
        print(f"  gaussian {i}: finite-diff sum(dI/dc)^2 = {fd:.4f}, illum = {base['illum'][i]:.4f}")
    print("illumination == Gauss-Newton Hessian diagonal: OK")


def test_position_fisher():
    """Lateral entries of the position Fisher matrix vs. finite differences of the luminance image;
    the along-ray entry must be ~0 for one view (it is exactly 0 under the first-order approximation)."""
    s = random_scene(150)
    W, H = 64, 48
    K = intrinsics(W, H, 70)
    R, t = yaw_camera(0)
    base = render(s, R, t, K, W, H, fisher=True)
    L0 = base["image"].mean(-1).astype(np.float64)
    eps = 1e-3
    errs = []
    for i in np.argsort(-base["illum"])[:5]:
        for ax in (0, 1):  # world x and y are lateral for a camera looking down +z
            c = s["centers"].copy()
            c[i, ax] += eps
            s2 = dict(s, centers=c)
            dL = (render(s2, R, t, K, W, H)["image"].mean(-1) - L0) / eps
            fd = float((dL ** 2).sum())
            an = float(base["fisher"][i, ax, ax])
            errs.append(abs(fd - an) / max(fd, 1e-9))
        ray = s["centers"][i] / np.linalg.norm(s["centers"][i])
        along = float(ray @ base["fisher"][i] @ ray)
        assert along < 1e-6 * np.trace(base["fisher"][i]), along
    print(f"position Fisher vs finite differences: median rel. error {np.median(errs):.3f}, max {max(errs):.3f}; "
          f"along-ray information = 0 for one view")
    assert np.median(errs) < 0.1


if __name__ == "__main__":
    test_camera_convention()
    test_tiled_vs_dense()
    test_illum_is_hessian_diagonal()
    test_position_fisher()
    print("all tests passed")
