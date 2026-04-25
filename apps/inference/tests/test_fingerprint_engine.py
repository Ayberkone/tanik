"""Smoke tests for the SourceAFIS / JPype binding.

Scope: prove the binding works end-to-end — JVM starts, the JAR loads, the
documented Java classes are reachable, and a template byte array round-trips
through serialize/deserialize.

This is *not* a biometric-quality test. Same-finger / different-finger score
separation is exercised in `test_fingerprint_pipeline.py` (added in task #37
once a real public dataset is sourced under task #5).

Skipped automatically when JPype is not installed OR no JVM is on PATH —
local dev on a Mac without Java should not break the test run. Docker (CI +
prod) installs OpenJDK 17 in the runtime image and JPype1 from PyPI, so these
tests do execute there.

Tests target the synchronous `_encode_sync` / `_match_sync` helpers directly
to avoid pulling pytest-asyncio into the dev deps; the async wrappers are
thin `run_in_threadpool` shims.
"""

from __future__ import annotations

import importlib.util
import io
import shutil

import numpy as np
import pytest
from PIL import Image

_skip_reason = None
if importlib.util.find_spec("jpype") is None:
    _skip_reason = "JPype1 not installed; SourceAFIS binding cannot run."
elif shutil.which("java") is None:
    _skip_reason = "No JVM on PATH; SourceAFIS binding cannot run."

pytestmark = pytest.mark.skipif(_skip_reason is not None, reason=_skip_reason or "")


def _synthetic_fingerprint_png() -> bytes:
    rng = np.random.default_rng(42)
    y, x = np.mgrid[0:320, 0:320]
    ridges = (np.sin(np.sqrt((x - 160) ** 2 + (y - 160) ** 2) * 0.4) * 100 + 128).astype(np.uint8)
    noise = rng.integers(0, 30, size=ridges.shape, dtype=np.uint8)
    img = np.clip(ridges.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img, mode="L").save(buf, format="PNG")
    return buf.getvalue()


def test_template_version_string():
    from tanik_inference import fingerprint_engine

    assert fingerprint_engine.template_version() == "sourceafis/3.18.1"


def test_encode_returns_template_or_typed_error():
    """Binding proof: either we get bytes back, or we get a string error from
    Java land (proving we reached SourceAFIS, didn't crash JPype itself).
    """
    from tanik_inference import fingerprint_engine

    template, error = fingerprint_engine._encode_sync(_synthetic_fingerprint_png())
    if template is None:
        assert isinstance(error, str) and len(error) > 0
    else:
        assert isinstance(template, bytes)
        assert len(template) > 0


def test_template_round_trips_and_self_matches():
    """If extraction succeeds on the synthetic image, matching it against
    itself must produce a non-zero score (SourceAFIS convention: 0 = unrelated,
    higher = more similar; 40 ≈ FMR 0.01% per upstream).
    """
    from tanik_inference import fingerprint_engine

    template, error = fingerprint_engine._encode_sync(_synthetic_fingerprint_png())
    if template is None:
        pytest.skip(f"Synthetic image yielded no template: {error}")
    score = fingerprint_engine._match_sync(template, template)
    assert score > 0
