"""End-to-end tests for /api/v1/fingerprint/enroll and /verify.

Same shape as test_iris_endpoints.py: exercises the wire format, the
contract in docs/api-contract.md, and happy + unhappy paths against real
MINEX fingerprint fixtures.

Skipped wholesale when JPype + JVM are unavailable — the fingerprint
pipeline can't run without them. Local Mac dev without Java skips cleanly;
Docker / CI install both and run the suite.
"""

import importlib.util
import io
import shutil

import pytest

_skip_reason = None
if importlib.util.find_spec("jpype") is None:
    _skip_reason = "JPype1 not installed; fingerprint endpoints cannot run."
elif shutil.which("java") is None:
    _skip_reason = "No JVM on PATH; fingerprint endpoints cannot run."

pytestmark = pytest.mark.skipif(_skip_reason is not None, reason=_skip_reason or "")

SOURCEAFIS_THRESHOLD = 40.0


def _enroll(client, image_bytes: bytes, **form):
    return client.post(
        "/api/v1/fingerprint/enroll",
        files={"image": ("fingerprint.png", io.BytesIO(image_bytes), "image/png")},
        data=form,
    )


def _verify(client, image_bytes: bytes, subject_id: str, **form):
    return client.post(
        "/api/v1/fingerprint/verify",
        files={"image": ("fingerprint.png", io.BytesIO(image_bytes), "image/png")},
        data={"subject_id": subject_id, **form},
    )


def test_enroll_returns_contracted_shape(client, fingerprint_bytes):
    r = _enroll(
        client,
        fingerprint_bytes["subject_a001_right_index"],
        display_name="Alice",
        finger_position="right_index",
    )
    assert r.status_code == 201, r.text
    body = r.json()
    for key in (
        "request_id", "subject_id", "display_name", "finger_position",
        "enrolled_at", "modality", "template_version",
    ):
        assert key in body, f"missing {key} in {body}"
    assert body["display_name"] == "Alice"
    assert body["finger_position"] == "right_index"
    assert body["modality"] == "fingerprint"
    assert body["template_version"].startswith("sourceafis/")
    assert r.headers.get("x-request-id") == body["request_id"]


def test_verify_self_match_succeeds(client, fingerprint_bytes):
    """Enrolling and verifying the same fingerprint must match with a
    similarity score above SourceAFIS's documented FMR=0.01% threshold (40).
    """
    r1 = _enroll(client, fingerprint_bytes["subject_a001_right_index"], display_name="S1")
    sid = r1.json()["subject_id"]
    r2 = _verify(client, fingerprint_bytes["subject_a001_right_index"], sid)
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["matched"] is True
    assert body["modality"] == "fingerprint"
    assert body["similarity_score"] > SOURCEAFIS_THRESHOLD
    assert body["threshold"] == SOURCEAFIS_THRESHOLD
    assert body["subject_id"] == sid


def test_verify_different_finger_does_not_match(client, fingerprint_bytes):
    r1 = _enroll(client, fingerprint_bytes["subject_a001_right_index"], display_name="S1")
    sid = r1.json()["subject_id"]
    r2 = _verify(client, fingerprint_bytes["subject_a002_right_index"], sid)
    assert r2.status_code == 200
    body = r2.json()
    assert body["matched"] is False
    assert body["similarity_score"] < SOURCEAFIS_THRESHOLD


def test_verify_unknown_subject_404(client, fingerprint_bytes):
    r = _verify(
        client,
        fingerprint_bytes["subject_a001_right_index"],
        "00000000-0000-0000-0000-000000000000",
    )
    assert r.status_code == 404
    body = r.json()
    assert body["error_code"] == "SUBJECT_NOT_FOUND"
    assert body["request_id"]


def test_verify_iris_subject_id_against_fingerprint_endpoint_404(client, iris_bytes, fingerprint_bytes):
    """Cross-modality lookup must return 404 even though the subject_id is
    valid — modality mismatch is treated as not-found from the fingerprint
    endpoint's perspective. Prevents accidental cross-engine matching.
    """
    enroll = client.post(
        "/api/v1/iris/enroll",
        files={"image": ("iris.png", io.BytesIO(iris_bytes["subject_1_a"]), "image/png")},
        data={"display_name": "iris-subject", "eye_side": "left"},
    )
    assert enroll.status_code == 201
    iris_sid = enroll.json()["subject_id"]
    r = _verify(client, fingerprint_bytes["subject_a001_right_index"], iris_sid)
    assert r.status_code == 404
    assert r.json()["error_code"] == "SUBJECT_NOT_FOUND"


def test_enroll_rejects_garbage(client):
    r = _enroll(client, b"this is definitely not an image", display_name="Garbage")
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_IMAGE"
    assert body["request_id"]


def test_enroll_default_finger_position(client, fingerprint_bytes):
    """When no finger_position is supplied, the API must default to
    right_index (the contract default).
    """
    r = _enroll(client, fingerprint_bytes["subject_a001_right_index"])
    assert r.status_code == 201
    assert r.json()["finger_position"] == "right_index"
