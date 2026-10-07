import numpy as np
import torch

from wmt.wp3_shadow_model import NULL_DIR, ShadowModel, analyze, marginal_fisher

torch.set_num_threads(2)


def test_autodiff_matches_finite_differences():
    m = ShadowModel(dil=0.3)
    th0 = m.theta0()
    J = m.jacobian(shadow=True)
    h = 1e-6
    Jfd = np.zeros_like(J)
    for i in range(len(th0)):
        e = torch.zeros_like(th0)
        e[i] = h
        Jfd[:, i] = ((m.forward(th0 + e) - m.forward(th0 - e)) / (2 * h)).numpy()
    assert np.linalg.norm(J - Jfd) / np.linalg.norm(Jfd) < 1e-5


def test_null_direction_exact_without_shadow():
    m = ShadowModel(dil=0.0)
    th0 = m.theta0()
    for s in (0.2, -0.3):
        th = th0 + s * torch.tensor([0, 0, 1.0, 1.0, 0])
        diff = (m.forward(th, shadow=False) - m.forward(th0, shadow=False)).abs().max().item()
        assert diff < 1e-10
    J = m.jacobian(shadow=False)
    assert np.linalg.norm(J @ NULL_DIR) / np.linalg.norm(J) < 1e-10
    a = analyze(marginal_fisher(J))
    assert a["ratio"] <= 1e-9 and a["align"] >= 0.999


def test_shadow_breaks_the_null_direction():
    m = ShadowModel(dil=0.0)
    J = m.jacobian(shadow=True)
    assert np.linalg.norm(J @ NULL_DIR) / np.linalg.norm(J) > 1e-3
    a = analyze(marginal_fisher(J))
    assert a["ratio"] > 1e-8


def test_null_stays_exact_with_pixel_dilation_but_fixed_size_depth_is_weakly_visible():
    J3 = ShadowModel(dil=0.3).jacobian(shadow=False)
    assert np.linalg.norm(J3 @ NULL_DIR) / np.linalg.norm(J3) < 1e-10  # pixel-space dilation is scale-invariant
    # moving along the ray at FIXED world size is a different direction: weakly but not zero informative
    j_depth = np.linalg.norm(J3[:, 2])
    j_lateral = np.linalg.norm(J3[:, 0])
    assert 0 < j_depth < 0.3 * j_lateral


def test_marginalising_nuisance_never_increases_information():
    m = ShadowModel()
    F_known = marginal_fisher(m.jacobian(True, ()))
    F_nuis = marginal_fisher(m.jacobian(True, ("albedo", "light")))
    assert np.linalg.eigvalsh(F_known - F_nuis).min() > -1e-6 * np.linalg.eigvalsh(F_known).max()
