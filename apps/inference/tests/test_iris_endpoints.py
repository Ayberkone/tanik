"""End-to-end tests for /api/v1/iris/enroll and /api/v1/iris/verify.

Exercises the wire format, the contract in docs/api-contract.md, and the
happy + unhappy paths against real iris fixtures (downloaded by conftest).
"""

import io


def _enroll(client, image_bytes: bytes, **form):
    return client.post(
        "/api/v1/iris/enroll",
        files={"image": ("iris.png", io.BytesIO(image_bytes), "image/png")},
        data=form,
    )


def _verify(client, image_bytes: bytes, subject_id: str, **form):
    return client.post(
        "/api/v1/iris/verify",
        files={"image": ("iris.png", io.BytesIO(image_bytes), "image/png")},
        data={"subject_id": subject_id, **form},
    )


def test_enroll_returns_contracted_shape(client, iris_bytes):
    r = _enroll(client, iris_bytes["subject_1_a"], display_name="Alice", eye_side="left")
    assert r.status_code == 201, r.text
    body = r.json()
    # contract fields
    for key in ("request_id", "subject_id", "display_name", "eye_side",
                "enrolled_at", "modality", "template_version"):
        assert key in body, f"missing {key} in {body}"
    assert body["display_name"] == "Alice"
    assert body["eye_side"] == "left"
    assert body["modality"] == "iris"
    assert body["template_version"].startswith("open-iris/")
    # request_id echoed in response header
    assert r.headers.get("x-request-id") == body["request_id"]


def test_verify_same_eye_matches(client, iris_bytes):
    r1 = _enroll(client, iris_bytes["subject_1_a"], display_name="S1")
    sid = r1.json()["subject_id"]
    r2 = _verify(client, iris_bytes["subject_1_b"], sid)
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["matched"] is True
    assert body["modality"] == "iris"
    assert 0.0 <= body["hamming_distance"] < body["threshold"]
    assert body["subject_id"] == sid


def test_verify_different_eye_does_not_match(client, iris_bytes):
    r1 = _enroll(client, iris_bytes["subject_1_a"], display_name="S1")
    sid = r1.json()["subject_id"]
    r2 = _verify(client, iris_bytes["subject_2_a"], sid)
    assert r2.status_code == 200
    body = r2.json()
    assert body["matched"] is False
    assert body["hamming_distance"] >= body["threshold"]


def test_verify_unknown_subject_404(client, iris_bytes):
    r = _verify(client, iris_bytes["subject_1_a"], "00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    body = r.json()
    assert body["error_code"] == "SUBJECT_NOT_FOUND"
    assert body["request_id"]


def test_enroll_rejects_garbage(client):
    r = _enroll(client, b"this is definitely not an image", display_name="Garbage")
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_IMAGE"
    assert body["request_id"]


def test_enroll_rejects_empty_upload(client):
    r = _enroll(client, b"", display_name="Empty")
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_IMAGE"


def test_enroll_propagates_client_request_id(client, iris_bytes):
    r = client.post(
        "/api/v1/iris/enroll",
        files={"image": ("iris.png", io.BytesIO(iris_bytes["subject_1_a"]), "image/png")},
        data={"display_name": "RID", "eye_side": "left"},
        headers={"x-request-id": "fixed-id-for-test"},
    )
    assert r.status_code == 201
    assert r.json()["request_id"] == "fixed-id-for-test"
    assert r.headers.get("x-request-id") == "fixed-id-for-test"


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["iris_engine"].startswith("open-iris/")
