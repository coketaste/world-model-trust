"""Generate the site's own 3D illustration figures from a procedural synthetic room.

The room is built entirely here (no third-party assets): a floor with a rug, four walls with a window and a
shelf, a ceiling, a bed-like block, a sofa-like block, a plant-like cluster. It is rendered with this
repository's tile rasterizer (src/wmt/raster.py). Trust tiers are computed from the prompt camera's
per-splat sensitivity (illumination), exactly as on the Illumination page.

Run:  python scripts/make_figures.py        (about a minute on CPU; writes PNGs to site/assets/figs/)
"""
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from wmt.raster import covariances, intrinsics, look_at, render, yaw_camera  # noqa: E402

OUT = os.path.join(ROOT, "site", "assets", "figs")
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
TIER_IMAGINED, TIER_SEEN, TIER_PARALLAX = "#86b6ef", "#3987e5", "#0d366b"

# Room geometry (OpenCV-style axes: x right, y DOWN, z forward). The prompt camera sits at the origin looking +z,
# 1.2 m above the floor.
X0, X1 = -3.0, 3.0
Y_CEIL, Y_FLOOR = -1.3, 1.2
Z0, Z1 = -2.5, 5.5
SP = 0.042  # splat spacing on surfaces

rng = np.random.default_rng(7)


def _hex(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


class Room:
    def __init__(self):
        self.pts, self.rgb, self.sc, self.tag = [], [], [], []

    def add(self, p, color, scale=SP * 0.8, tag="room"):
        p = np.asarray(p, np.float32).reshape(-1, 3)
        c = np.asarray(color, np.float32)
        c = np.tile(c, (len(p), 1)) if c.ndim == 1 else c
        self.pts.append(p)
        self.rgb.append(np.clip(c, 0, 1))
        self.sc.append(np.full(len(p), scale, np.float32))
        self.tag += [tag] * len(p)

    def plane(self, o, u, v, color_fn, sp=SP, tag="room", scale=None):
        """Rectangle spanned by vectors u, v from origin o, sampled with jitter; color_fn(s,t)->rgb."""
        o, u, v = (np.asarray(a, np.float32) for a in (o, u, v))
        nu, nv = max(2, int(np.linalg.norm(u) / sp)), max(2, int(np.linalg.norm(v) / sp))
        s, t = np.meshgrid((np.arange(nu) + 0.5) / nu, (np.arange(nv) + 0.5) / nv, indexing="ij")
        s = s + rng.uniform(-0.3, 0.3, s.shape) / nu
        t = t + rng.uniform(-0.3, 0.3, t.shape) / nv
        p = o + s[..., None] * u + t[..., None] * v
        cols = color_fn(s.ravel(), t.ravel()) + rng.normal(0, 0.012, (s.size, 3))
        self.add(p.reshape(-1, 3), cols, scale if scale else sp * 0.68, tag)

    def box(self, lo, hi, faces, tag="room", sp=SP):
        """Axis-aligned box; faces = dict(face_name -> color or color_fn). Faces: top,bottom,front(-z),back(+z),left(-x),right(+x)."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi

        def mk(c):
            return c if callable(c) else (lambda s, t, c=c: np.tile(_hex(c) if isinstance(c, str) else np.asarray(c), (len(s), 1)))
        spec = {"top": ((x0, y0, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0)), "bottom": ((x0, y1, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0)),
                "front": ((x0, y0, z0), (x1 - x0, 0, 0), (0, y1 - y0, 0)), "back": ((x0, y0, z1), (x1 - x0, 0, 0), (0, y1 - y0, 0)),
                "left": ((x0, y0, z0), (0, 0, z1 - z0), (0, y1 - y0, 0)), "right": ((x1, y0, z0), (0, 0, z1 - z0), (0, y1 - y0, 0))}
        for name, col in faces.items():
            o, u, v = spec[name]
            if np.linalg.norm(u) < 1e-6 or np.linalg.norm(v) < 1e-6:
                continue
            self.plane(o, u, v, mk(col), sp, tag)

    def scene(self):
        centers = np.vstack(self.pts)
        n = len(centers)
        s = np.concatenate(self.sc)
        q = np.zeros((n, 4), np.float32)
        q[:, 3] = 1
        sc = np.repeat(s[:, None], 3, 1)
        d = dict(centers=centers, rgb=np.vstack(self.rgb), scales=sc, quats=q, opacity=np.full(n, 0.92, np.float32), tag=np.array(self.tag))
        d["cov3d"] = covariances(d["scales"], d["quats"])
        return d


def build_room():
    r = Room()
    # floor: planks along z and a striped rug
    def floor(s, t):
        x, z = X0 + s * (X1 - X0), Z0 + t * (Z1 - Z0)
        plank = (np.floor(x / 0.24) % 2) * 0.05
        base = np.stack([0.74 + plank, 0.58 + plank * 0.8, 0.42 + plank * 0.6], 1)
        in_rug = (np.abs(x - 0.0) < 1.35) & (z > 0.7) & (z < 3.7)
        ring = np.minimum(1.35 - np.abs(x), np.minimum(z - 0.7, 3.7 - z))
        band = (np.floor(ring / 0.22) % 3).astype(int)
        pal = np.array([[0.25, 0.55, 0.58], [0.93, 0.88, 0.76], [0.80, 0.42, 0.32]], np.float32)
        base[in_rug] = pal[band[in_rug]]
        return base
    r.plane((X0, Y_FLOOR, Z0), (X1 - X0, 0, 0), (0, 0, Z1 - Z0), floor, tag="floor")
    # walls and ceiling
    cream = lambda s, t: np.tile([0.93, 0.89, 0.80], (len(s), 1))
    sage = lambda s, t: np.tile([0.72, 0.80, 0.72], (len(s), 1)) + (np.floor(t * 12) % 2)[:, None] * 0.0
    r.plane((X0, Y_CEIL, Z1), (X1 - X0, 0, 0), (0, Y_FLOOR - Y_CEIL, 0), sage, tag="wall")           # back wall
    r.plane((X0, Y_CEIL, Z0), (X1 - X0, 0, 0), (0, Y_FLOOR - Y_CEIL, 0), cream, tag="wall")           # wall behind the camera
    r.plane((X0, Y_CEIL, Z0), (0, 0, Z1 - Z0), (0, Y_FLOOR - Y_CEIL, 0), cream, tag="wall")           # left wall
    # right wall with a window panel
    def right(s, t):
        z, y = Z0 + s * (Z1 - Z0), Y_CEIL + t * (Y_FLOOR - Y_CEIL)
        c = np.tile([0.93, 0.89, 0.80], (len(s), 1))
        win = (z > 1.2) & (z < 3.4) & (y > -0.75) & (y < 0.35)
        c[win] = [0.66, 0.84, 0.95]
        frame = win & ((np.abs(z - 2.3) < 0.04) | (np.abs(y + 0.2) < 0.04))
        edge = ((np.abs(z - 1.2) < 0.06) | (np.abs(z - 3.4) < 0.06) | (np.abs(y + 0.75) < 0.06) | (np.abs(y - 0.35) < 0.06)) & (z > 1.14) & (z < 3.46) & (y > -0.81) & (y < 0.41)
        c[frame | edge] = [0.98, 0.98, 0.96]
        return c
    r.plane((X1, Y_CEIL, Z0), (0, 0, Z1 - Z0), (0, Y_FLOOR - Y_CEIL, 0), right, tag="wall")
    r.plane((X0, Y_CEIL, Z0), (X1 - X0, 0, 0), (0, 0, Z1 - Z0), lambda s, t: np.tile([0.97, 0.95, 0.90], (len(s), 1)), tag="ceiling")
    # sofa-like block (the main occluder), facing the camera
    terra, terra2 = (0.80, 0.44, 0.31), (0.71, 0.36, 0.26)
    r.box((0.4, 0.75, 1.9), (2.4, 1.2, 2.9), dict(top=terra, front=terra2, left=terra2, right=terra2, back=terra2), tag="sofa")
    r.box((0.4, 0.5, 2.7), (2.4, 0.75, 2.9), dict(top=terra, front=terra2, left=terra2, right=terra2, back=terra2), tag="sofa")     # backrest
    r.box((0.4, 0.45, 1.9), (0.62, 0.75, 2.9), dict(top=terra, front=terra2, left=terra2, right=terra2), tag="sofa")                  # arm L
    r.box((2.18, 0.45, 1.9), (2.4, 0.75, 2.9), dict(top=terra, front=terra2, left=terra2, right=terra2), tag="sofa")                  # arm R
    r.box((0.9, 0.62, 2.55), (1.5, 0.75, 2.7), dict(top=(0.95, 0.86, 0.62), front=(0.9, 0.8, 0.55), left=(0.9, 0.8, 0.55), right=(0.9, 0.8, 0.55)), tag="sofa")  # cushion
    # bed-like block against the back wall, left
    wood, blanket = (0.55, 0.38, 0.26), (0.30, 0.62, 0.60)
    stripe = lambda s, t: np.where(((np.floor(s * 7) % 2) == 0)[:, None], np.array([0.30, 0.62, 0.60]), np.array([0.24, 0.52, 0.52]))
    r.box((-2.8, 0.85, 3.4), (-1.0, 1.2, 5.3), dict(front=wood, right=wood, left=wood), tag="bed")
    r.box((-2.8, 0.55, 3.4), (-1.0, 0.85, 5.3), dict(top=stripe, front=blanket, right=blanket, left=blanket), tag="bed")
    r.box((-2.8, 0.05, 5.3), (-1.0, 1.2, 5.45), dict(front=wood, top=wood, right=wood, left=wood), tag="bed")                          # headboard
    r.box((-2.65, 0.45, 4.75), (-1.75, 0.57, 5.25), dict(top=(0.97, 0.95, 0.92), front=(0.93, 0.9, 0.86), right=(0.93, 0.9, 0.86), left=(0.93, 0.9, 0.86)), tag="bed")  # pillows
    # a small chest on the floor, behind the sofa (hidden from the prompt camera)
    r.box((1.0, 0.85, 3.5), (1.7, 1.2, 4.0), dict(top=(0.45, 0.34, 0.26), front=(0.40, 0.30, 0.22), left=(0.40, 0.30, 0.22), right=(0.40, 0.30, 0.22)), tag="chest")
    # shelf on the back wall with books
    for y in (-0.55, -0.1, 0.35):
        r.box((0.2, y, 5.2), (2.4, y + 0.04, 5.5), dict(top=wood, front=wood), tag="shelf")
    for y0 in (-0.55, -0.1, 0.35):
        x = 0.28
        while x < 2.3:
            w = rng.uniform(0.05, 0.11)
            h = rng.uniform(0.22, 0.38)
            col = np.array([[0.80, 0.30, 0.30], [0.28, 0.45, 0.70], [0.90, 0.72, 0.30], [0.35, 0.60, 0.42], [0.60, 0.40, 0.65]])[rng.integers(0, 5)]
            r.box((x, y0 - h + 0.0, 5.3), (x + w, y0, 5.46), dict(front=tuple(col), left=tuple(col * 0.85), right=tuple(col * 0.85), top=tuple(col * 0.9)), tag="shelf", sp=0.03)
            x += w + 0.012
    # plant-like cluster near the right back corner
    r.box((2.35, 0.9, 4.4), (2.75, 1.2, 4.8), dict(top=(0.52, 0.34, 0.24), front=(0.46, 0.29, 0.20), left=(0.46, 0.29, 0.20), right=(0.46, 0.29, 0.20), back=(0.46, 0.29, 0.20)), tag="plant", sp=0.03)
    n_leaf = 2800
    ang, rad = rng.uniform(0, 2 * np.pi, n_leaf), rng.uniform(0, 1, n_leaf) ** 0.6
    pts = np.stack([2.55 + 0.5 * rad * np.cos(ang), 0.85 - 0.7 * rng.uniform(0, 1, n_leaf) ** 0.8, 4.6 + 0.5 * rad * np.sin(ang)], 1)
    greens = np.stack([0.22 + 0.15 * rng.random(n_leaf), 0.50 + 0.25 * rng.random(n_leaf), 0.25 + 0.10 * rng.random(n_leaf)], 1)
    r.add(pts, greens, scale=0.04, tag="plant")
    # framed picture on the left wall
    def art(s, t):
        c = np.tile([0.95, 0.90, 0.78], (len(s), 1))
        c[(np.hypot(s - 0.5, t - 0.5) < 0.28)] = [0.88, 0.55, 0.30]
        c[(t > 0.65) & (np.abs(s - 0.5) < 0.38)] = [0.40, 0.62, 0.78]
        return c
    r.plane((X0 + 0.01, -0.55, 1.3), (0, 0, 1.3), (0, 0.9, 0), art, tag="art")
    return r.scene()


def tiers_from_prompt(scene, W, H, hfov=65.0):
    """Render from the prompt camera and return per-splat sensitivity (illumination) and a seen mask."""
    K = intrinsics(W, H, hfov)
    o = render(scene, *yaw_camera(0), K, W, H)
    return o, K


SEEN_MIN = 0.004  # a splat counts as measured when the prompt photo is sensitive to it (illumination above this)
W, H = 480, 360


def tier_colors(scene, seen, shade):
    """Per-splat colour: tier colour modulated by the splat's own brightness so the scene stays legible."""
    base = np.where(seen[:, None], _hex(TIER_SEEN), _hex(TIER_IMAGINED))
    return np.clip(base * (0.45 + 0.75 * shade[:, None]), 0, 1)


def view(scene, eye, target, hfov, colors=None, w=W, h=H):
    K = intrinsics(w, h, hfov)
    o = render(scene, *look_at(eye, target), K, w, h, colors=colors, bg=0.985)
    return np.clip(o["image"], 0, 1)


def style_ax(ax):
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=8, length=2)


def save_png(fig, name, max_kb=250):
    import io
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi, facecolor=SURFACE)
    im = Image.open(buf).convert("RGB")
    path = os.path.join(OUT, name)
    for colors in (256, 192, 128, 96, 64):
        q = im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        q.save(path, optimize=True)
        if os.path.getsize(path) <= max_kb * 1024:
            break
    print(f"{name}: {os.path.getsize(path) / 1024:.0f} KB ({im.size[0]}x{im.size[1]}, {colors} colours)")


def legend(fig, y=0.02, imagined="Imagined: the photo does not constrain it", seen="Seen: constrained by the photo (depth from the model's prior)"):
    import matplotlib.patches as mp
    h = [mp.Patch(color=TIER_IMAGINED, label=imagined), mp.Patch(color=TIER_SEEN, label=seen)]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, fontsize=9, labelcolor=INK2, bbox_to_anchor=(0.5, y))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    os.makedirs(OUT, exist_ok=True)
    sc = build_room()
    n = len(sc["centers"])
    o, K = tiers_from_prompt(sc, W, H)
    seen = o["illum"] > SEEN_MIN
    print(f"splats {n}; seen {seen.mean():.1%}, imagined {1 - seen.mean():.1%}")
    shade = sc["rgb"].mean(1)

    prompt = np.clip(o["image"], 0, 1)
    eyeB, tgtB = (0.0, -0.35, 5.05), (0.25, 0.45, -0.8)
    imgB = view(sc, eyeB, tgtB, 78)
    imgC = view(sc, eyeB, tgtB, 78, colors=tier_colors(sc, seen, shade))

    # ---- Figure 1: the photo, the same room from the back, and the trust tiers
    fig, ax = plt.subplots(1, 3, figsize=(12.6, 3.75), facecolor=SURFACE)
    titles = ["A. The photo (what the prompt camera saw)", "B. The same room, seen from the back", "C. View B coloured by trust tier"]
    for a, im, t in zip(ax, (prompt, imgB, imgC), titles):
        a.imshow(im)
        a.set_title(t, loc="left", fontsize=10, color=INK)
        a.axis("off")
    legend(fig, 0.0)
    plt.tight_layout(rect=(0, 0.07, 1, 1))
    save_png(fig, "synthetic-room_views.png")
    plt.close(fig)

    # ---- Figure 2: top-down map and a side cross-section through the sofa (shadow zone)
    c = sc["centers"]
    fig, ax = plt.subplots(1, 2, figsize=(12.6, 4.3), facecolor=SURFACE, gridspec_kw=dict(width_ratios=[1, 1.25]))
    a = ax[0]
    keep = c[:, 1] > -0.6   # drop the ceiling and upper walls so the floor plan is visible
    for mask, col, z in ((keep & ~seen, TIER_IMAGINED, 1), (keep & seen, TIER_SEEN, 2)):
        a.scatter(c[mask, 0], c[mask, 2], s=9, marker="s", color=col, linewidths=0, zorder=z, rasterized=True)
    a.add_patch(Rectangle((X0, Z0), X1 - X0, Z1 - Z0, fill=False, ec=INK2, lw=1.0, zorder=4))
    half = np.radians(65 / 2)
    for sgn in (-1, 1):
        a.plot([0, sgn * 7 * np.tan(half)], [0, 7], color=INK, lw=0.9, ls=(0, (4, 3)), zorder=5)
    a.plot([0], [0], marker="^", ms=11, color=INK, zorder=6)
    a.annotate("prompt camera", (0, 0), xytext=(-2.9, -1.2), fontsize=8.5, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
    for lab, (x, z) in (("sofa", (1.4, 2.4)), ("bed", (-1.9, 4.4)), ("chest", (1.35, 3.75)), ("shelf", (1.3, 5.25))):
        a.text(x, z, lab, fontsize=8, color=INK, ha="center", va="center", zorder=7, bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.75))
    a.set_xlim(X0 - 0.2, X1 + 0.2); a.set_ylim(Z0 - 0.2, Z1 + 0.2); a.set_aspect("equal")
    a.set_title("D. Floor plan: seen (dark) and imagined (light)", loc="left", fontsize=10, color=INK)
    a.set_xlabel("x (m, right)", color=MUTED, fontsize=8.5); a.set_ylabel("z (m, forward)", color=MUTED, fontsize=8.5)
    style_ax(a)

    b = ax[1]
    sl = np.abs(c[:, 0] - 1.4) < 0.1
    for mask, col, z in ((sl & ~seen, TIER_IMAGINED, 1), (sl & seen, TIER_SEEN, 2)):
        b.scatter(c[mask, 2], c[mask, 1], s=7, marker="s", color=col, linewidths=0, zorder=z, rasterized=True)
    ztop, ytop = 2.9, 0.5            # top of the sofa backrest as seen from the camera at the origin
    zback = Z1
    yback = ytop * zback / ztop
    b.add_patch(Polygon([(ztop, ytop), (zback, yback), (zback, Y_FLOOR), (ztop, Y_FLOOR)], closed=True, fc="#9ec5f4", alpha=0.28, ec="none", zorder=0))
    b.plot([0, zback], [0, yback], color=INK, lw=0.9, ls=(0, (4, 3)), zorder=5)
    b.plot([0], [0], marker=">", ms=10, color=INK, zorder=6)
    b.annotate("shadow zone: the sofa hides this part of\nthe floor and back wall from the camera", (4.3, 1.0), xytext=(3.0, -0.95), fontsize=8.5, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
    b.text(0.12, 0.28, "camera", fontsize=8.5, color=INK)
    b.text(1.4 + 0.1, 1.07, "", fontsize=1)
    b.set_xlim(-0.4, Z1 + 0.2); b.set_ylim(Y_FLOOR + 0.15, Y_CEIL - 0.15)
    b.set_aspect("equal")
    b.set_title("E. Side slice through the sofa", loc="left", fontsize=10, color=INK)
    b.set_xlabel("z (m, forward)", color=MUTED, fontsize=8.5); b.set_ylabel("height (m, up)", color=MUTED, fontsize=8.5)
    b.set_yticks([Y_CEIL, -0.5, 0.4, Y_FLOOR]); b.set_yticklabels([f"{Y_FLOOR - y:.1f}" for y in (Y_CEIL, -0.5, 0.4, Y_FLOOR)])
    style_ax(b)
    legend(fig, 0.0)
    plt.tight_layout(rect=(0, 0.07, 1, 1))
    save_png(fig, "synthetic-room_map.png")
    plt.close(fig)

    # ---- Figure 3: a high corner view, raw and by tier
    eyeD, tgtD = (-2.7, -0.95, -1.9), (0.5, 0.7, 3.4)
    imgD = view(sc, eyeD, tgtD, 70)
    imgE = view(sc, eyeD, tgtD, 70, colors=tier_colors(sc, seen, shade))
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.5), facecolor=SURFACE)
    for a, im, t in zip(ax, (imgD, imgE), ("F. The room from a high corner", "G. The same view by trust tier")):
        a.imshow(im); a.set_title(t, loc="left", fontsize=10, color=INK); a.axis("off")
    legend(fig, 0.0)
    plt.tight_layout(rect=(0, 0.08, 1, 0.94))
    save_png(fig, "synthetic-room_corner.png")
    plt.close(fig)
    print("seen fraction by object:", {t: round(float(seen[sc['tag'] == t].mean()), 2) for t in np.unique(sc['tag'])})


if __name__ == "__main__":
    main()
