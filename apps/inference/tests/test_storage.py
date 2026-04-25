"""Modality-agnostic storage tests.

Storage now stores opaque template bytes plus a modality label and a small
metadata blob. We exercise it with a real iris template to keep the test
honest end-to-end (the engine produces bytes; storage round-trips them; the
matcher accepts the round-tripped bytes back).
"""

import pytest

from tanik_inference import iris_engine
from tanik_inference.db import init_db
from tanik_inference.storage import (
    create_subject,
    get_metadata,
    get_subject,
    get_template,
)


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_db()


@pytest.fixture(scope="module")
def iris_template_bytes(iris_bytes):
    template, error = iris_engine._encode_sync(
        iris_bytes["subject_1_a"], eye_side="left", image_id="storage_test"
    )
    assert error is None and template is not None, f"pipeline error: {error}"
    return template


def test_create_and_fetch_subject(iris_template_bytes):
    row = create_subject(
        template_bytes=iris_template_bytes,
        modality="iris",
        template_version=iris_engine.template_version(),
        display_name="Alice",
        metadata={"eye_side": "left"},
    )
    assert row.subject_id
    assert row.display_name == "Alice"
    assert row.modality == "iris"
    fetched = get_subject(row.subject_id)
    assert fetched is not None
    assert fetched.display_name == "Alice"
    assert get_metadata(fetched) == {"eye_side": "left"}


def test_template_round_trip(iris_template_bytes):
    row = create_subject(
        template_bytes=iris_template_bytes,
        modality="iris",
        template_version=iris_engine.template_version(),
    )
    back = get_template(row.subject_id)
    assert back is not None
    distance = iris_engine._match_sync(iris_template_bytes, back)
    # round-trip must reproduce essentially the same template; allow rotation-search noise
    assert distance < 0.05, f"round-tripped template too different: HD={distance}"


def test_unknown_subject_returns_none():
    assert get_subject("00000000-0000-0000-0000-000000000000") is None
    assert get_template("00000000-0000-0000-0000-000000000000") is None


def test_subject_without_metadata_returns_empty_dict(iris_template_bytes):
    row = create_subject(
        template_bytes=iris_template_bytes,
        modality="iris",
        template_version=iris_engine.template_version(),
    )
    fetched = get_subject(row.subject_id)
    assert get_metadata(fetched) == {}
