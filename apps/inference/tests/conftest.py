"""Shared pytest fixtures.

Iris fixture images are downloaded once from Worldcoin's public S3 (the same
images open-iris uses in its `colab/MatchingEntities.ipynb` demo) into a
git-ignored cache. Three images: two captures of subject 1, one of subject 2.

Fingerprint fixture images are downloaded once from `usnistgov/minex` (NIST
MINEX III validation imagery, U.S. public domain). Six images covering
distinct fingers across two subjects. Source `.gray` files are raw 8-bit
grayscale; we transcode to PNG in-memory so SourceAFIS's standard
`FingerprintImage(byte[])` constructor can ingest them. Dimensions match
the values declared in `minexiii_validation_data.h`.

Forces the test DB to in-memory SQLite *before* any tanik_inference module is
imported, so create_engine() picks up the override.
"""

import io
import os
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Force in-memory DB before tanik_inference imports its config.
os.environ.setdefault("TANIK_DB_URL", "sqlite:///:memory:")

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "_cache"
WLD_BASE = "https://wld-ml-ai-data-public.s3.amazonaws.com/public-iris-images"
IRIS_FIXTURES = {
    "subject_1_a": f"{WLD_BASE}/example_orb_image_1.png",
    "subject_1_b": f"{WLD_BASE}/example_orb_image_2.png",
    "subject_2_a": f"{WLD_BASE}/example_orb_image_3.png",
}

MINEX_BASE = (
    "https://raw.githubusercontent.com/usnistgov/minex/master/minexiii/validation/"
    "validation_imagery_raw"
)
# (filename, width, height) — dimensions copied from minexiii_validation_data.h.
# Subject a001: right index / right middle / right ring (all distinct fingers).
# Subject a002: right index / right middle / left index (all distinct fingers).
FINGERPRINT_FIXTURES = {
    "subject_a001_right_index":  ("a001_02.gray", 329, 503),
    "subject_a001_right_middle": ("a001_03.gray", 332, 533),
    "subject_a001_right_ring":   ("a001_04.gray", 292, 495),
    "subject_a002_right_index":  ("a002_02.gray", 341, 519),
    "subject_a002_right_middle": ("a002_03.gray", 337, 555),
    "subject_a002_left_index":   ("a002_07.gray", 355, 535),
}


def _fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "tanik-tests/1"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        f.write(r.read())


def _gray_to_png_bytes(raw_path: Path, width: int, height: int) -> bytes:
    raw = raw_path.read_bytes()
    expected = width * height
    if len(raw) != expected:
        raise RuntimeError(
            f"{raw_path.name}: expected {expected} raw bytes ({width}x{height}), got {len(raw)}"
        )
    arr = np.frombuffer(raw, dtype=np.uint8).reshape(height, width)
    buf = io.BytesIO()
    Image.fromarray(arr, mode="L").save(buf, format="PNG")
    return buf.getvalue()


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
def fingerprint_bytes() -> dict[str, bytes]:
    """Six MINEX fingerprint images, downloaded + transcoded to PNG once.

    The `.gray` files are raw 8-bit grayscale, so we re-encode them as PNG
    in memory before handing them to the SourceAFIS image decoder.
    """
    out: dict[str, bytes] = {}
    for label, (filename, width, height) in FINGERPRINT_FIXTURES.items():
        raw_path = FIXTURE_DIR / "fingerprints" / filename
        _fetch(f"{MINEX_BASE}/{filename}", raw_path)
        out[label] = _gray_to_png_bytes(raw_path, width, height)
    return out


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from tanik_inference.main import app

    return TestClient(app)
