"""Unit tests for the pure normalisation + fusion functions.

The route-level integration tests in test_unified_verify.py exercise these
through the API; this file pins the math directly so a regression in the
normalisation curve is caught even if the route happens to compensate.
"""

import pytest

from tanik_inference import fusion


# ---- iris ----

def test_iris_floor_maps_to_one():
    assert fusion.normalise_iris(0.0, floor=0.0, threshold=0.37, ceil=0.5) == 1.0


def test_iris_at_threshold_maps_to_half():
    assert fusion.normalise_iris(0.37, floor=0.0, threshold=0.37, ceil=0.5) == pytest.approx(0.5)


def test_iris_at_ceil_maps_to_zero():
    assert fusion.normalise_iris(0.5, floor=0.0, threshold=0.37, ceil=0.5) == 0.0


def test_iris_above_ceil_clamps_to_zero():
    assert fusion.normalise_iris(0.9, floor=0.0, threshold=0.37, ceil=0.5) == 0.0


def test_iris_below_floor_clamps_to_one():
    assert fusion.normalise_iris(-0.1, floor=0.0, threshold=0.37, ceil=0.5) == 1.0


def test_iris_strictly_monotonic_decreasing():
    """Higher HD must produce a lower or equal normalised score."""
    floor, threshold, ceil = 0.0, 0.37, 0.5
    samples = [floor + i * (ceil - floor) / 50 for i in range(51)]
    scores = [fusion.normalise_iris(hd, floor=floor, threshold=threshold, ceil=ceil) for hd in samples]
    for a, b in zip(scores, scores[1:]):
        assert a >= b


def test_iris_invalid_knobs_raise():
    with pytest.raises(ValueError):
        fusion.normalise_iris(0.2, floor=0.4, threshold=0.3, ceil=0.5)


# ---- fingerprint ----

def test_fingerprint_zero_score_maps_to_zero():
    assert fusion.normalise_fingerprint(0.0, threshold=40.0, ceil=200.0) == 0.0


def test_fingerprint_at_threshold_maps_to_half():
    assert fusion.normalise_fingerprint(40.0, threshold=40.0, ceil=200.0) == pytest.approx(0.5)


def test_fingerprint_at_ceil_maps_to_one():
    assert fusion.normalise_fingerprint(200.0, threshold=40.0, ceil=200.0) == 1.0


def test_fingerprint_above_ceil_clamps_to_one():
    assert fusion.normalise_fingerprint(500.0, threshold=40.0, ceil=200.0) == 1.0


def test_fingerprint_negative_score_clamps_to_zero():
    assert fusion.normalise_fingerprint(-10.0, threshold=40.0, ceil=200.0) == 0.0


def test_fingerprint_strictly_monotonic_increasing():
    threshold, ceil = 40.0, 200.0
    samples = [i * (ceil + 50) / 50 for i in range(51)]
    scores = [fusion.normalise_fingerprint(s, threshold=threshold, ceil=ceil) for s in samples]
    for a, b in zip(scores, scores[1:]):
        assert a <= b


# ---- fuse ----

def test_fuse_single_modality_returns_that_modalitys_score():
    out = fusion.fuse({"iris": 0.7}, {"iris": 0.5, "fingerprint": 0.5})
    assert out == pytest.approx(0.7)


def test_fuse_equal_weights_two_modalities():
    out = fusion.fuse(
        {"iris": 0.6, "fingerprint": 0.8},
        {"iris": 0.5, "fingerprint": 0.5},
    )
    assert out == pytest.approx(0.7)


def test_fuse_unequal_weights():
    out = fusion.fuse(
        {"iris": 1.0, "fingerprint": 0.0},
        {"iris": 0.7, "fingerprint": 0.3},
    )
    assert out == pytest.approx(0.7)


def test_fuse_empty_raises():
    with pytest.raises(ValueError):
        fusion.fuse({}, {"iris": 0.5})


def test_fuse_zero_relevant_weight_raises():
    with pytest.raises(ValueError):
        fusion.fuse({"iris": 0.5}, {"iris": 0.0, "fingerprint": 0.5})
