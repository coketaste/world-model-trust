"""Scientific consistency checks of the committed reduced salt volume and mesh."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator

ASSETS = Path(__file__).resolve().parents[1] / "site/assets/salt"


def test_mesh_is_on_salt_boundary_in_physical_coordinates():
    m = json.loads((ASSETS / "metadata.json").read_text())
    v = np.fromfile(ASSETS / "velocity.bin", "<u2").reshape(m["shape"])
    vertices = np.fromfile(ASSETS / "vertices.bin", "<f4").reshape(-1, 3)
    triangles = np.fromfile(ASSETS / "triangles.bin", "<u4").reshape(-1, 3)
    assert len(vertices) == m["mesh"]["vertices"]
    assert triangles.max() < len(vertices)
    assert np.isfinite(vertices).all()
    # Edge vertices must lie on the 0.5 boundary. Lewiner marching cubes also
    # adds a few interior vertices for ambiguous cells; those must be in a
    # mixed cell but need not lie on the trilinear interpolant's exact level.
    # This catches mismatched units, depth signs and transposed axes.
    field = RegularGridInterpolator(m["axes_km"], (v == 4482).astype(float), bounds_error=False, fill_value=None)
    indices = np.column_stack([np.interp(vertices[:, a], m["axes_km"][a], np.arange(m["shape"][a])) for a in range(3)])
    fractional = np.abs(indices - np.rint(indices)) > 5e-5
    edge = fractional.sum(axis=1) == 1
    assert edge.mean() > .99
    np.testing.assert_allclose(field(vertices[edge]), .5, atol=5e-5)
    assert np.all((field(vertices) > 0) & (field(vertices) < 1))
    area2 = np.linalg.norm(np.cross(vertices[triangles[:, 1]] - vertices[triangles[:, 0]],
                                    vertices[triangles[:, 2]] - vertices[triangles[:, 0]]), axis=1)
    assert np.all(area2 > 0)


def test_provenance_crop_and_files():
    m = json.loads((ASSETS / "metadata.json").read_text())
    assert m["source"]["sha256"] == "6ee10663de588d445332ba7cc1c0dc3d6f9c50d1965f797425cebc64f9c71de6"
    assert m["source"]["round_trip_max_relative_error"] < 1e-6
    assert m["axes_km"][2][0] == .3
    assert m["axes_km"][2][-1] == 3.66
    assert m["quantization_max_error_m_s"] <= .5
    for name, info in m["files"].items():
        b = (ASSETS / name).read_bytes()
        assert len(b) == info["bytes"]
        assert hashlib.sha256(b).hexdigest() == info["sha256"]
