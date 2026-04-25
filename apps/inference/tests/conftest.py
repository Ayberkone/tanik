"""Shared pytest fixtures.

Iris fixture images are downloaded once from Worldcoin's public S3 (the same
images open-iris uses in its `colab/MatchingEntities.ipynb` demo) into a
git-ignored cache. Three images: two captures of subject 1, one of subject 2.

Forces the test DB to in-memory SQLite *before* any tanik_inference module is
imported, so create_engine() picks up the override.
"""

import os
import urllib.request
from pathlib import Path

import pytest

# Force in-memory DB before tanik_inference imports its config.
os.environ.setdefault("TANIK_DB_URL", "sqlite:///:memory:")

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "_cache"
WLD_BASE = "https://wld-ml-ai-data-public.s3.amazonaws.com/public-iris-images"
IRIS_FIXTURES = {
    "subject_1_a": f"{WLD_BASE}/example_orb_image_1.png",
    "subject_1_b": f"{WLD_BASE}/example_orb_image_2.png",
    "subject_2_a": f"{WLD_BASE}/example_orb_image_3.png",
}


def _fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "tanik-tests/1"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        f.write(r.read())


@pytest.fixture(scope="session")
def iris_fixtures() -> dict[str, Path]:
    """Three iris images, downloaded once per session into a gitignored cache."""
    paths: dict[str, Path] = {}
    for label, url in IRIS_FIXTURES.items():
        p = FIXTURE_DIR / f"{label}.png"
        _fetch(url, p)
        paths[label] = p
    return paths


@pytest.fixture(scope="session")
def iris_bytes(iris_fixtures) -> dict[str, bytes]:
    return {label: p.read_bytes() for label, p in iris_fixtures.items()}


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from tanik_inference.main import app

    return TestClient(app)
