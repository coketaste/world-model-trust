#!/usr/bin/env python3
"""Build a traceable SEG/EAGE viewer volume, salt mesh, and static previews.

Usage (optional dependencies: pip install -e '.[salt]'):
  python scripts/build_salt_assets.py --source data/seg-eage/SEG-EAGE-Salt-Model.h5 --kind emsig-interior
  python scripts/build_salt_assets.py --source data/seg-eage/SALTF.ZIP --kind original

Original inputs may be SALTF.ZIP or the uncompressed big-endian Saltf@@.
No synthetic geometry is generated. No source archive is extracted to disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EMSIG_SHA = "6ee10663de588d445332ba7cc1c0dc3d6f9c50d1965f797425cebc64f9c71de6"
EMSIG_URL = "https://raw.githubusercontent.com/emsig/data/2021-05-21/emg3d/models/SEG-EAGE-Salt-Model.h5"
RECIPE = "https://github.com/emsig/emg3d-gallery/blob/89997efe7ee5a7fceba1b9b559e5fac3fd9c0bef/examples/models/SEG-EAGE_3D_salt_model.py"
ORIGINAL_URL = "https://s3.amazonaws.com/open.source.geoscience/open_data/seg_eage_models_cd/Salt_Model_3D.tar.gz"


def sha(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def load_volume(source, kind):
    """Return XYZ velocity samples in m/s and original depth sample indices."""
    digest = sha(source)
    if kind == "original":
        if zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as z:
                names = [n for n in z.namelist() if Path(n).name.lower() == "saltf@@"]
                if len(names) != 1:
                    raise ValueError("Expected one Saltf@@ member in SALTF.ZIP")
                raw = z.read(names[0])
            flat = np.frombuffer(raw, dtype=">f4")
        else:
            flat = np.fromfile(source, dtype=">f4")
        if flat.size != 676 * 676 * 210:
            raise ValueError("Original grid must contain 676 × 676 × 210 float32 samples")
        v = flat.reshape((676, 676, 210), order="F").astype(np.float32)
        depths = np.arange(210)
        info = {"kind": "original", "url": ORIGINAL_URL, "label": "Original velocity grid", "crop_reason": None}
    else:
        import h5py

        if digest != EMSIG_SHA:
            raise ValueError("EMsig checksum mismatch; cannot assume this derivative's transform or crop")
        with h5py.File(source) as f:
            assert f["model/property_x"].shape == (676, 676, 211)
            assert np.array_equal(f["model/grid/origin"][:], [0, 0, -4200])
            assert all(np.all(f[f"model/grid/h{a}"][:] == 20) for a in "xyz")
            # Published code stores original sample j at HDF5 index 209-j.
            # indices 26..194 retain rho=(v/1700)^3.88. All other depths
            # were overwritten with air, water or basement and are EXCLUDED.
            rho = f["model/property_x"][:, :, 26:195][:, :, ::-1]
        recovered = 1700 * np.power(rho, 1 / 3.88)
        v = recovered.astype(np.float32)
        # Reversal must recover float32 velocities, not merely plausible values.
        relative_error = float(np.max(np.abs((v.astype(float) / 1700) ** 3.88 / rho - 1)))
        if relative_error > 1e-6:
            raise ValueError("Inverse-transform round trip failed")
        depths = np.arange(15, 184)
        info = {"kind": "emsig-interior", "url": EMSIG_URL, "recipe": RECIPE,
                "label": "Recoverable interior from the EMsig derivative",
                "crop_reason": "The derivative overwrites water/air and deep basement; only original depth samples 15–183 (0.30–3.66 km) are retained.",
                "inverse_transform": "v = 1700 * rho ** (1 / 3.88); reversed stored depth axis",
                "round_trip_max_relative_error": relative_error}
    if not np.isfinite(v).all() or v.min() < 1400 or v.max() > 7000:
        raise ValueError("Invalid velocity range or encoding")
    if np.count_nonzero(np.isclose(v, 4482, atol=0.01, rtol=0)) < 1000:
        raise ValueError("Expected salt velocity 4482 m/s is absent")
    return v, depths, {**info, "file": source.name, "sha256": digest}


def sample_indices(n, step):
    return np.unique(np.r_[np.arange(0, n, step), n - 1]).astype(int)


def build(source, kind, output):
    from skimage.measure import marching_cubes

    v, depths, provenance = load_volume(source, kind)
    indices = [sample_indices(v.shape[0], 4), sample_indices(v.shape[1], 4), sample_indices(v.shape[2], 2)]
    sampled = v[np.ix_(*indices)]
    axes = [indices[0] * .02, indices[1] * .02, depths[indices[2]] * .02]
    salt = np.isclose(sampled, 4482, atol=.01, rtol=0)
    vertices, faces, _, _ = marching_cubes(salt.astype(np.float32), level=.5, allow_degenerate=False)
    for i in range(3):
        vertices[:, i] = np.interp(vertices[:, i], np.arange(len(axes[i])), axes[i])
    output.mkdir(parents=True, exist_ok=True)
    # C ordering: Z varies fastest. Coordinates remain X,Y,depth, in km.
    quantized = np.rint(sampled).astype("<u2")
    quantized.tofile(output / "velocity.bin")
    vertices.astype("<f4").tofile(output / "vertices.bin")
    faces.astype("<u4").tofile(output / "triangles.bin")
    meta = {
        "schema": 1, "name": "SEG/EAGE 3D Salt Model", "source": provenance,
        "original_shape": [676, 676, 210], "original_spacing_m": [20, 20, 20],
        "shape": list(sampled.shape), "axes_km": [a.tolist() for a in axes],
        "coordinate_convention": "X, Y, depth positive down; original sample index times 20 m; no vertical exaggeration",
        "velocity_encoding": "uint16 little-endian, XYZ C-order (Z fastest), m/s",
        "velocity_range_m_s": [float(sampled.min()), float(sampled.max())],
        "salt_velocity_m_s": 4482, "salt_tolerance_m_s": .01,
        "sampling": "Nearest original sample every 4 points in X/Y, every 2 in depth, plus final endpoint; no averaging or smoothing",
        "mesh": {"vertices": len(vertices), "triangles": len(faces), "extraction": "Marching cubes at 0.5 on salt-membership mask; open at crop boundaries; no smoothing"},
        "quantization_max_error_m_s": float(np.max(np.abs(sampled - quantized))),
        "attribution": "SEG/EAGE 3-D Modeling committee; Aminzadeh, Brac & Kunz (1997). EMsig derivative: Dieter Werthmüller.",
        "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
    }
    meta["files"] = {n: {"bytes": (output/n).stat().st_size, "sha256": sha(output/n)} for n in ["velocity.bin", "vertices.bin", "triangles.bin"]}
    make_previews(sampled, axes, vertices, faces, output, provenance["kind"])
    (output / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({"shape": meta["shape"], "mesh": meta["mesh"], "files": meta["files"], "source": provenance}, indent=2))


def make_previews(v, axes, vertices, faces, output, kind):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(10, 6), facecolor="#101e2c")
    ax = fig.add_subplot(projection="3d", facecolor="#101e2c")
    poly = Poly3DCollection(vertices[faces], facecolors="#efaa62", shade=True,
                            lightsource=matplotlib.colors.LightSource(azdeg=310, altdeg=40))
    ax.add_collection3d(poly)
    ax.set(xlim=(axes[0][0], axes[0][-1]), ylim=(axes[1][0], axes[1][-1]), zlim=(axes[2][-1], axes[2][0]),
           xlabel="X (km)", ylabel="Y (km)", zlabel="Depth (km)")
    ax.set_box_aspect([np.ptp(a) for a in axes]); ax.view_init(elev=24, azim=-58)
    ax.tick_params(colors="#cbd5df", labelsize=8)
    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.label.set_color("#cbd5df"); axis.set_pane_color((.06, .12, .18, 1))
    label = "Interior crop" if kind == "emsig-interior" else "Original grid"
    fig.text(.07, .92, "SEG/EAGE 3D salt body", color="white", fontsize=19)
    fig.text(.07, .86, f"{label} · {axes[2][0]:.2f}–{axes[2][-1]:.2f} km depth · no vertical exaggeration", color="#cbd5df", fontsize=11)
    fig.text(.07, .05, "SEG/EAGE (1997) · CC BY 4.0 · derived visualisation", color="#cbd5df", fontsize=9)
    fig.savefig(output / "preview.png", dpi=140, bbox_inches="tight"); plt.close(fig)
    fig, axs = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    positions = [len(a)//2 for a in axes]
    for i, ax in enumerate(axs):
        other = [a for a in range(3) if a != i]
        a, b = other
        section = np.take(v, positions[i], axis=i).T
        im = ax.pcolormesh(axes[a], axes[b], section, cmap="viridis", vmin=1500, vmax=4500, shading="nearest")
        ax.set_title(f"{'XYD'[i]} = {axes[i][positions[i]]:.2f} km")
        ax.set_xlabel(f"{'XYD'[a]} (km)"); ax.set_ylabel(f"{'XYD'[b]} (km)"); ax.set_aspect("equal")
        if b == 2: ax.invert_yaxis()
    fig.colorbar(im, ax=axs, label="P-wave velocity (m/s)", shrink=.6)
    fig.savefig(output / "sections.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--kind", choices=["original", "emsig-interior"], required=True)
    p.add_argument("--output", type=Path, default=ROOT / "site/assets/salt")
    a = p.parse_args()
    build(a.source, a.kind, a.output)
