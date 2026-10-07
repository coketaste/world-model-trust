import json
import pathlib

import numpy as np
import pytest

from wmt.stats import auroc, paired_bootstrap

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_auroc_perfect_and_reversed():
    score = np.array([0.1, 0.2, 0.8, 0.9])
    bad = np.array([False, False, True, True])
    assert auroc(score, bad) == 1.0
    assert auroc(-score, bad) == 0.0


def test_auroc_ties_count_half():
    # all scores equal: every bad/good pair is a tie, so AUROC must be exactly 0.5
    assert auroc(np.ones(6), np.array([True, True, True, False, False, False])) == 0.5


def test_auroc_hand_computed_with_one_tie():
    # bad scores {3, 2}, good scores {2, 1}: pairs (3>2)=1, (3>1)=1, (2=2)=0.5, (2>1)=1 -> 3.5/4
    score = np.array([3.0, 2.0, 2.0, 1.0])
    bad = np.array([True, True, False, False])
    assert auroc(score, bad) == pytest.approx(0.875)


def test_auroc_undefined_without_both_classes():
    assert np.isnan(auroc(np.arange(4.0), np.zeros(4, bool)))
    assert np.isnan(auroc(np.arange(4.0), np.ones(4, bool)))


def test_bootstrap_constant_difference_has_degenerate_interval():
    r = paired_bootstrap([0.6] * 5, [0.5] * 5, n_boot=2000)
    assert r["mean"] == pytest.approx(0.1)
    assert r["lo"] == pytest.approx(0.1) and r["hi"] == pytest.approx(0.1)
    assert r["wins"] == 5 and r["n"] == 5 and r["excludes_zero"]


def test_bootstrap_interval_brackets_mean_and_uses_percentiles():
    a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    r = paired_bootstrap(a, np.zeros(5), n_boot=20000, seed=1)
    assert r["mean"] == pytest.approx(3.0)
    # the resampled means of [1..5] are multiples of 0.2; their 2.5% and 97.5% points are 1.8 and 4.2,
    # whereas a 90% interval (5% and 95%) would be [2.0, 4.0]; these ranges pin the 95% percentiles
    r = paired_bootstrap(a, np.zeros(5), n_boot=200000, seed=1)
    assert 1.7 <= r["lo"] <= 1.9 and 4.1 <= r["hi"] <= 4.3


def test_bootstrap_symmetric_data_does_not_exclude_zero():
    d = np.array([-1.0, 1.0, -0.5, 0.5, 0.2, -0.2])
    assert not paired_bootstrap(d, np.zeros(len(d)), n_boot=5000)["excludes_zero"]


def test_bootstrap_is_reproducible_for_a_seed():
    a, b = np.linspace(0, 1, 9), np.linspace(0.1, 0.8, 9)
    assert paired_bootstrap(a, b, seed=3) == paired_bootstrap(a, b, seed=3)


def test_wp0_recorded_intervals_match_recomputation():
    d = json.loads((ROOT / "results" / "wp0_reproduce.json").read_text())
    cases = d["per_case"]
    got = paired_bootstrap([c["auroc_ours"] for c in cases], [c["auroc_visibility"] for c in cases])
    rec = d["bootstrap"]["ours_vs_visibility"]
    assert got["mean"] == pytest.approx(rec["mean"]) and got["lo"] == pytest.approx(rec["lo"]) and got["hi"] == pytest.approx(rec["hi"])
    assert got["wins"] == rec["wins"]


def test_bootstrap_wins_count_only_strictly_positive_differences():
    r = paired_bootstrap([0.6, 0.5, 0.4], [0.5, 0.5, 0.5], n_boot=1000)
    assert r["wins"] == 1 and r["n"] == 3
