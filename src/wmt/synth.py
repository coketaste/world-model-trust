"""Synthetic-truth benchmark: a stand-in single-image world generator and the 12-case setup.

Truth world  = a public example 3D world (500k splats), known everywhere.
Prompt photo = rendered from the truth at the origin (yaw in YAWS, HFOV 65 deg).
Generator    = a STAND-IN generator (NOT Marble): Depth Anything V2 metric-indoor lifts pixels to
               splats (seen part); a room-box prior fills in the rest. Convention: prompt
               camera at the origin looking +z.
CIRCULARITY: "filled in => wrong" is partly built in because the filled-in geometry is our crude
prior. Seen-tier results (errors from a real depth network) are the fair test.
"""
import os

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from .raster import covariances, intrinsics, render, yaw_camera
from .spz_io import read_spz

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.environ.setdefault("HF_HOME", os.path.join(DATA, "hf"))

TRUTH = ["rustic_kitchen_with_natural_light", "warm_traditional_kitchen_interior", "elegant_library_with_fireplace"]
YAWS = (0, 90, 180, 270)
W, H = 384, 288
HFOV_TRUE, HFOV_GEN = 65.0, 60.0
STRIDE = 2
LAMBDA, REF_W = (0.02 / 0.25) ** 2, 1024
TAU_REL = 0.10

_pipe = None


def _depth_pipe():
    global _pipe
    if _pipe is None:
        from transformers import pipeline
        _pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf", device="cpu")
    return _pipe


def predict_depth(img):
    d = np.asarray(_depth_pipe()(img)["predicted_depth"], np.float32)
    if d.shape != (img.height, img.width):
        d = np.asarray(Image.fromarray(d, mode="F").resize((img.width, img.height), Image.BILINEAR))
    return d


def depth_with_tta(photo):
    """Depth + relative test-time-augmentation std (original / h-flip / 1.5x upscale)."""
    im = Image.fromarray(photo)
    d0 = predict_depth(im)
    d1 = predict_depth(im.transpose(Image.FLIP_LEFT_RIGHT))[:, ::-1]
    big = im.resize((int(W * 1.5), int(H * 1.5)), Image.BICUBIC)
    d2 = np.asarray(Image.fromarray(predict_depth(big), mode="F").resize((W, H), Image.BILINEAR))
    st = np.stack([d0, d1, d2])
    return d0, st.std(0) / np.maximum(st.mean(0), 1e-3)


def generate(photo, D, hfov_gen=HFOV_GEN):
    """Stand-in single-image world generator. Returns (scene, from_photo mask)."""
    fx, fy, cx, cy = intrinsics(W, H, hfov_gen)
    ys, xs = np.mgrid[STRIDE // 2:H:STRIDE, STRIDE // 2:W:STRIDE]
    ys, xs = ys.ravel(), xs.ravel()
    d = D[ys, xs]
    P = np.column_stack([(xs + 0.5 - cx) / fx * d, (ys + 0.5 - cy) / fy * d, d]).astype(np.float32)
    rgb = photo[ys, xs].astype(np.float32) / 255
    sc = (d * STRIDE / fx * 0.6).astype(np.float32)

    X, Y, Z = P.T
    y_floor = np.percentile(Y, 98)
    y_ceil = min(np.percentile(Y, 2), y_floor - 2.4)
    x_lo, x_hi = np.percentile(X, 2), np.percentile(X, 98)
    z_far, z_back = np.percentile(Z, 98), -1.0
    step = 0.08

    def grid(a0, a1, b0, b1):
        a, b = np.meshgrid(np.arange(a0, a1, step), np.arange(b0, b1, step))
        return a.ravel(), b.ravel()

    def med_color(mask, default):
        return np.median(rgb[mask], 0) if mask.sum() > 20 else np.asarray(default, np.float32)

    faces = []
    gx, gz = grid(x_lo, x_hi, z_back, z_far)
    faces.append((np.column_stack([gx, np.full_like(gx, y_floor), gz]), med_color(Y > y_floor - 0.15, (0.5, 0.45, 0.4))))
    faces.append((np.column_stack([gx, np.full_like(gx, y_ceil), gz]), med_color(Y < y_ceil + 0.2, (0.85, 0.85, 0.85))))
    gy, gz = grid(y_ceil, y_floor, z_back, z_far)
    faces.append((np.column_stack([np.full_like(gy, x_lo), gy, gz]), med_color(np.abs(X - x_lo) < 0.2, (0.7, 0.68, 0.64))))
    faces.append((np.column_stack([np.full_like(gy, x_hi), gy, gz]), med_color(np.abs(X - x_hi) < 0.2, (0.7, 0.68, 0.64))))
    gx, gy = grid(x_lo, x_hi, y_ceil, y_floor)
    faces.append((np.column_stack([gx, gy, np.full_like(gx, z_far)]), med_color(np.abs(Z - z_far) < 0.3, (0.7, 0.68, 0.64))))
    faces.append((np.column_stack([gx, gy, np.full_like(gx, z_back)]), med_color(np.ones(len(Z), bool), (0.7, 0.68, 0.64))))
    F = np.vstack([f for f, _ in faces]).astype(np.float32)
    Fc = np.vstack([np.tile(c, (len(f), 1)) for f, c in faces]).astype(np.float32)
    keep = cKDTree(P).query(F, k=1)[0] > 0.15
    F, Fc = F[keep], Fc[keep]

    n_l, n_f = len(P), len(F)
    q = np.zeros((n_l + n_f, 4), np.float32)
    q[:, 3] = 1
    scene = dict(centers=np.vstack([P, F]), rgb=np.vstack([rgb, Fc]),
                 scales=np.concatenate([np.repeat(sc[:, None], 3, 1), np.full((n_f, 3), 0.045, np.float32)]),
                 quats=q, opacity=np.full(n_l + n_f, 0.95, np.float32))
    scene["cov3d"] = covariances(scene["scales"], scene["quats"])
    return scene, np.concatenate([np.ones(n_l, bool), np.zeros(n_f, bool)])


def load_truth(world):
    T = read_spz(os.path.join(DATA, "marble_examples", f"{world}_500k.spz"))
    T["cov3d"] = covariances(T["scales"], T["quats"])
    return T


def render_photo(T, yaw):
    """Prompt photo (uint8), its truth depth (median), and the camera, rendered from the truth world."""
    R_cam, t_cam = yaw_camera(yaw)
    tr = render(T, R_cam, t_cam, intrinsics(W, H, HFOV_TRUE), W, H)
    return (tr["image"].clip(0, 1) * 255).astype(np.uint8), tr["depth_median"], (R_cam, t_cam)
