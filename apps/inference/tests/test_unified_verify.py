"""End-to-end tests for the unified, fused POST /api/v1/verify.

Covers iris-only, fingerprint-only, and both-modality flows; the empty
request and the half-supplied modality cases; cross-modality subject_id
mismatch (must 404 like the per-modality endpoints); and the placeholder
calibration signal in the response.

Skipped wholesale when JPype + JVM are unavailable — the unified endpoint
exercises the fingerprint pipeline in the both-modality and fingerprint-
only paths. Iris-only tests still need the route registered, which it is.
"""

import importlib.util
import io
import shutil

import pytest

_skip_reason = None
if importlib.util.find_spec("jpype") is None:
    _skip_reason = "JPype1 not installed; unified verify cannot exercise fingerprint."
elif shutil.which("java") is None:
    _skip_reason = "No JVM on PATH; unified verify cannot exercise fingerprint."

pytestmark = pytest.mark.skipif(_skip_reason is not None, reason=_skip_reason or "")


def _enroll_iris(client, image_bytes: bytes, **form):
    return client.post(
        "/api/v1/iris/enroll",
        files={"image": ("iris.png", io.BytesIO(image_bytes), "image/png")},
        data=form,
    )


def _enroll_fingerprint(client, image_bytes: bytes, **form):
    return client.post(
        "/api/v1/fingerprint/enroll",
        files={"image": ("fingerprint.png", io.BytesIO(image_bytes), "image/png")},
        data=form,
    )


def _verify(client, *, iris=None, iris_subject_id=None, fp=None, fp_subject_id=None, **extra):
    files = {}
    data = {**extra}
    if iris is not None:
        files["iris_image"] = ("iris.png", io.BytesIO(iris), "image/png")
    if iris_subject_id is not None:
        data["iris_subject_id"] = iris_subject_id
    if fp is not None:
        files["fingerprint_image"] = ("fingerprint.png", io.BytesIO(fp), "image/png")
    if fp_subject_id is not None:
        data["fingerprint_subject_id"] = fp_subject_id
    return client.post("/api/v1/verify", files=files or None, data=data)


def test_iris_only_self_match(client, iris_bytes):
    r = _enroll_iris(client, iris_bytes["subject_1_a"], display_name="A", eye_side="left")
    assert r.status_code == 201
    sid = r.json()["subject_id"]

    v = _verify(client, iris=iris_bytes["subject_1_a"], iris_subject_id=sid)
    assert v.status_code == 200, v.text
    body = v.json()
    assert body["matched"] is True
    assert 0.0 <= body["fused_score"] <= 1.0
    assert body["fused_score"] >= body["threshold"]
    assert body["calibration_status"] == "placeholder"
    assert body["calibration_reference"] == "docs/fusion.md"
    assert len(body["modalities"]) == 1
    only = body["modalities"][0]
    assert only["modality"] == "iris"
    assert only["subject_id"] == sid
    assert only["weight"] == pytest.approx(1.0)
    # When only iris is supplied, the fused score IS the iris normalised score.
    assert body["fused_score"] == pytest.approx(only["normalised_score"])


def test_fingerprint_only_self_match(client, fingerprint_bytes):
    r = _enroll_fingerprint(client, fingerprint_bytes["subject_a001_right_index"], display_name="F1")
    assert r.status_code == 201
    sid = r.json()["subject_id"]

    v = _verify(client, fp=fingerprint_bytes["subject_a001_right_index"], fp_subject_id=sid)
    assert v.status_code == 200, v.text
    body = v.json()
    assert body["matched"] is True
    assert len(body["modalities"]) == 1
    only = body["modalities"][0]
    assert only["modality"] == "fingerprint"
    assert only["weight"] == pytest.approx(1.0)
    assert body["fused_score"] == pytest.approx(only["normalised_score"])


def test_fused_both_modalities_self_match(client, iris_bytes, fingerprint_bytes):
    iris_sid = _enroll_iris(client, iris_bytes["subject_1_a"], display_name="A").json()["subject_id"]
    fp_sid = _enroll_fingerprint(
        client, fingerprint_bytes["subject_a001_right_index"], display_name="A"
    ).json()["subject_id"]

    v = _verify(
        client,
        iris=iris_bytes["subject_1_a"],
        iris_subject_id=iris_sid,
        fp=fingerprint_bytes["subject_a001_right_index"],
        fp_subject_id=fp_sid,
    )
    assert v.status_code == 200, v.text
    body = v.json()
    assert body["matched"] is True
    assert len(body["modalities"]) == 2
    iris_r = next(m for m in body["modalities"] if m["modality"] == "iris")
    fp_r = next(m for m in body["modalities"] if m["modality"] == "fingerprint")
    assert iris_r["weight"] == pytest.approx(0.5)
    assert fp_r["weight"] == pytest.approx(0.5)
    expected = iris_r["normalised_score"] * 0.5 + fp_r["normalised_score"] * 0.5
    assert body["fused_score"] == pytest.approx(expected)


def test_fused_impostor_pair_does_not_match(client, iris_bytes, fingerprint_bytes):
    """An iris and fingerprint that both fail their per-modality checks must
    fuse to a sub-threshold decision. Uses subject 1's iris vs subject 2's
    iris probe, plus a cross-subject fingerprint pair from MINEX.
    """
    iris_sid = _enroll_iris(client, iris_bytes["subject_1_a"], display_name="A").json()["subject_id"]
    fp_sid = _enroll_fingerprint(
        client, fingerprint_bytes["subject_a001_right_index"], display_name="A"
    ).json()["subject_id"]

    v = _verify(
        client,
        iris=iris_bytes["subject_2_a"],
        iris_subject_id=iris_sid,
        fp=fingerprint_bytes["subject_a002_right_index"],
        fp_subject_id=fp_sid,
    )
    assert v.status_code == 200, v.text
    body = v.json()
    assert body["matched"] is False
    assert body["fused_score"] < body["threshold"]


def test_no_modality_supplied_400(client):
    r = client.post("/api/v1/verify")
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert "at least one modality" in body["message"].lower()


def test_iris_image_without_subject_id_400(client, iris_bytes):
    r = client.post(
        "/api/v1/verify",
        files={"iris_image": ("iris.png", io.BytesIO(iris_bytes["subject_1_a"]), "image/png")},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "VALIDATION_ERROR"


def test_iris_subject_id_without_image_400(client):
    r = client.post(
        "/api/v1/verify",
        data={"iris_subject_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "VALIDATION_ERROR"


def test_cross_modality_subject_id_404(client, iris_bytes, fingerprint_bytes):
    """Passing an iris subject_id under fingerprint_subject_id (or vice versa)
    must return 404 SUBJECT_NOT_FOUND, matching the per-modality contract.
    """
    iris_sid = _enroll_iris(client, iris_bytes["subject_1_a"]).json()["subject_id"]
    r = _verify(
        client,
        fp=fingerprint_bytes["subject_a001_right_index"],
        fp_subject_id=iris_sid,
    )
    assert r.status_code == 404
    assert r.json()["error_code"] == "SUBJECT_NOT_FOUND"


def test_calibration_status_placeholder_in_response(client, iris_bytes):
    """Until Phase 3 #43 ships measured weights, every unified response must
    carry calibration_status=placeholder. This is the in-band honesty signal.
    """
    iris_sid = _enroll_iris(client, iris_bytes["subject_1_a"]).json()["subject_id"]
    v = _verify(client, iris=iris_bytes["subject_1_a"], iris_subject_id=iris_sid)
    assert v.status_code == 200
    assert v.json()["calibration_status"] == "placeholder"
