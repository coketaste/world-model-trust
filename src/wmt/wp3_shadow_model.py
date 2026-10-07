"""WP3 forward model: one Gaussian occluder, a Lambertian floor, a point/area light, a pinhole camera.

Observation = the photo. Model A ignores the occluder's shadow (floor brightness independent of it);
model B includes it. Parameters theta = (az, el, log d, log sigma, log opacity) [+ nuisance]. In model A with
zero pixel dilation, (log d, log sigma) -> (+s, +s) leaves the image unchanged (exact null direction).
"""
import math

import numpy as np
import torch

torch.set_default_dtype(torch.float64)

W, H, HFOV = 96, 72, 60.0
FLOOR_Y, AMBIENT, I0, BG, OCC_COLOR = 1.5, 0.15, 6.0, 0.5, 0.8
C0, SIGMA0, OPAC0, LIGHT_DIST = (0.0, 0.3, 3.0), 0.35, 0.9, 4.0
N_OCC = 5
NULL_DIR = np.array([0, 0, 1, 1, 0]) / math.sqrt(2)


class ShadowModel:
    def __init__(self, phi_deg=60.0, elev_deg=50.0, light_radius=0.1, albedo=0.6, depth=3.0, dil=0.3):
        self.dil, self.albedo = dil, albedo
        scale = depth / C0[2]
        self.c_true = np.array(C0) * scale
        self.sigma_true = SIGMA0 * scale
        phi, e = math.radians(phi_deg), math.radians(elev_deg)
        ell0 = math.cos(e) * np.array([math.sin(phi), 0, -math.cos(phi)]) + np.array([0, -math.sin(e), 0])
        self.L_true = self.c_true + LIGHT_DIST * ell0
        e1 = np.cross(ell0, [0, 1, 0])
        e1 = e1 / np.linalg.norm(e1) if np.linalg.norm(e1) > 1e-6 else np.array([1.0, 0, 0])
        e2 = np.cross(ell0, e1)
        if light_radius > 0:
            ang = np.arange(8) * math.pi / 4
            off = np.vstack([np.zeros(3), light_radius * (np.outer(np.cos(ang), e1) + np.outer(np.sin(ang), e2))])
        else:
            off = np.zeros((1, 3))
        self.offsets = torch.tensor(off)

        self.fx = 0.5 * W / math.tan(math.radians(HFOV) / 2)
        ys, xs = np.mgrid[0:H, 0:W]
        u, v = xs.ravel() + 0.5, ys.ravel() + 0.5
        d = np.stack([(u - W / 2) / self.fx, (v - H / 2) / self.fx, np.ones_like(u)], 1)
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        hit = d[:, 1] > 0.02
        tf = np.where(hit, FLOOR_Y / np.maximum(d[:, 1], 1e-9), 1e9)
        hit &= tf < 15
        tf = np.where(hit, tf, 1e9)
        self.u, self.v, self.rays = torch.tensor(u), torch.tensor(v), torch.tensor(d)
        self.hit, self.tf = torch.tensor(hit), torch.tensor(tf)
        self.p = torch.tensor(np.where(hit[:, None], d * tf[:, None], 0.0))

    def theta0(self, nuis=()):
        c = self.c_true
        dist = float(np.linalg.norm(c))
        th = [0.0, math.asin(c[1] / dist), math.log(dist), math.log(self.sigma_true), math.log(OPAC0)]
        if "albedo" in nuis:
            th += [math.log(self.albedo), 0.0, 0.0]
        if "light" in nuis:
            th += list(self.L_true) + [0.0]
        if "ambient" in nuis:
            th += [0.0]
        return torch.tensor(th)

    def forward(self, theta, shadow=True, nuis=()):
        F, a_cam = self.parts(theta, shadow, nuis)
        return (1 - a_cam) * F + a_cam * OCC_COLOR

    def parts(self, theta, shadow=True, nuis=()):
        """(floor value F per pixel, camera alpha per pixel). nuis may contain albedo, light, ambient (in that order)."""
        az, el, ld, ls, lo = theta[0], theta[1], theta[2], theta[3], theta[4]
        k = N_OCC
        d, sig, o = torch.exp(ld), torch.exp(ls), torch.exp(lo)
        c = d * torch.stack([torch.sin(az) * torch.cos(el), torch.sin(el), torch.cos(az) * torch.cos(el)])
        if "albedo" in nuis:
            alb = torch.exp(theta[k] + theta[k + 1] * self.p[:, 0] + theta[k + 2] * (self.p[:, 2] - 4.0))
            k += 3
        else:
            alb = self.albedo
        if "light" in nuis:
            L, gain = theta[k:k + 3], torch.exp(theta[k + 3])
            k += 4
        else:
            L, gain = torch.tensor(self.L_true), 1.0
        amb = AMBIENT * torch.exp(theta[k]) if "ambient" in nuis else AMBIENT

        zc = c[2]
        uc, vc = self.fx * c[0] / zc + W / 2, self.fx * c[1] / zc + H / 2
        s2 = (self.fx * sig / zc) ** 2 + self.dil
        a_cam = o * torch.exp(-((self.u - uc) ** 2 + (self.v - vc) ** 2) / (2 * s2))
        near = ((~self.hit) | ((self.rays @ c) < self.tf)) & (zc > 0.05)
        a_cam = torch.where(near, a_cam, torch.zeros_like(a_cam))

        S = L[None, :] + self.offsets
        vec = S[:, None, :] - self.p[None]
        ell = torch.linalg.norm(vec, dim=-1)
        u_hat = vec / ell[..., None]
        irr = I0 * gain * (-u_hat[..., 1]).clamp(min=0) / ell ** 2
        if shadow:
            t0 = torch.minimum(((c[None, None, :] - self.p[None]) * u_hat).sum(-1).clamp(min=0), ell)
            rho2 = ((c[None, None, :] - (self.p[None] + t0[..., None] * u_hat)) ** 2).sum(-1)
            irr = irr * (1 - o * torch.exp(-rho2 / (2 * sig ** 2)))
        F = torch.where(self.hit, alb * (amb + irr.mean(0)), torch.full_like(self.tf, BG))
        return F, a_cam

    def jacobian(self, shadow=True, nuis=(), theta=None):
        th = self.theta0(nuis) if theta is None else theta
        return torch.func.jacfwd(lambda t: self.forward(t, shadow, nuis))(th).numpy()


def marginal_fisher(J, noise=1.0, n_occ=N_OCC):
    """Occluder Fisher information with nuisance parameters marginalised (Schur complement, flat priors)."""
    F = J.T @ J / noise ** 2
    if J.shape[1] == n_occ:
        return F
    Fon, Fnn = F[:n_occ, n_occ:], F[n_occ:, n_occ:]
    return F[:n_occ, :n_occ] - Fon @ np.linalg.pinv(Fnn, rcond=1e-12) @ Fon.T


def analyze(Fm, noise=1.0):
    """Eigen-spectrum, null-direction alignment and marginal std of log d, log sigma (std scales with noise)."""
    Fm = 0.5 * (Fm + Fm.T)
    w, V = np.linalg.eigh(Fm)
    ratio = float(max(w[0], 0) / w[-1])
    ok = ratio >= 1e-10
    cov = np.linalg.inv(Fm) if ok else None
    return dict(eig=w.tolist(), ratio=ratio, align=float(abs(V[:, 0] @ NULL_DIR)),
                std_logd=float(noise * math.sqrt(cov[2, 2])) if ok else float("inf"),
                std_logsig=float(noise * math.sqrt(cov[3, 3])) if ok else float("inf"))
