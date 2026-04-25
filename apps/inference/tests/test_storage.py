import os

# Force a temp DB before importing the app modules.
os.environ["TANIK_DB_URL"] = "sqlite:///:memory:"

import cv2  # noqa: E402
import iris  # noqa: E402
import pytest  # noqa: E402

from tanik_inference.db import init_db  # noqa: E402
from tanik_inference.storage import create_subject, get_subject, get_template  # noqa: E402

MMU_FIXTURE = "/tmp/mmu-probe/probe.bmp"


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_db()


@pytest.fixture(scope="module")
def template():
    if not os.path.exists(MMU_FIXTURE):
        pytest.skip(f"missing fixture {MMU_FIXTURE}")
    img = cv2.imread(MMU_FIXTURE, cv2.IMREAD_GRAYSCALE)
    pipe = iris.IRISPipeline()
    out = pipe(iris.IRImage(img_data=img, image_id="probe", eye_side="left"))
    assert out["error"] is None, f"pipeline error: {out['error']}"
    return out["iris_template"]


def test_create_and_fetch_subject(template):
    row = create_subject(template, eye_side="left", display_name="Alice", template_version="open-iris/1.11.1")
    assert row.subject_id
    assert row.display_name == "Alice"
    fetched = get_subject(row.subject_id)
    assert fetched is not None
    assert fetched.display_name == "Alice"


def test_template_round_trip(template):
    row = create_subject(template, eye_side="left", display_name=None, template_version="open-iris/1.11.1")
    back = get_template(row.subject_id)
    assert back is not None
    matcher = iris.HammingDistanceMatcher()
    d = matcher.run(template, back)
    # round-trip must reproduce essentially the same template; allow rotation-search noise
    assert d < 0.05, f"round-tripped template too different: HD={d}"


def test_unknown_subject_returns_none():
    assert get_subject("00000000-0000-0000-0000-000000000000") is None
    assert get_template("00000000-0000-0000-0000-000000000000") is None
