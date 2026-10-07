"""Metrics and paired-bootstrap helpers shared by all experiments."""
import numpy as np
from scipy.stats import rankdata


def auroc(score, bad):
    """P(score of a random bad item > score of a random good item). Higher score = less trustworthy."""
    bad = np.asarray(bad, bool)
    nb, ng = bad.sum(), (~bad).sum()
    if nb == 0 or ng == 0:
        return float("nan")
    r = rankdata(score)
    return float((r[bad].sum() - nb * (nb + 1) / 2) / (nb * ng))


def paired_bootstrap(a, b, n_boot=10000, seed=0):
    """Mean of (a - b) over cases with a 95% percentile CI, resampling cases. Also returns win count."""
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[np.isfinite(d)]
    rng = np.random.default_rng(seed)
    means = rng.choice(d, (n_boot, len(d)), replace=True).mean(1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return dict(mean=float(d.mean()), lo=float(lo), hi=float(hi), wins=int((d > 0).sum()), n=int(len(d)),
                excludes_zero=bool(lo > 0 or hi < 0))
