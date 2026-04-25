"""SourceAFIS / JPype binding tests against real MINEX fingerprint fixtures.

Three things are exercised end-to-end:
    1. JVM starts, the vendored JAR loads, the documented Java classes are
       reachable, and the version string matches what we ship.
    2. A real fingerprint image extracts a non-empty template (the binding
       is correct *and* SourceAFIS can find minutiae in NIST-quality input).
    3. Same-image self-match returns a score well above the FMR=0.01%
       threshold of 40 documented by SourceAFIS, while a pair of distinct
       fingers (across two MINEX subjects) returns a score at or near 0.

Skipped automatically when JPype is not installed OR no JVM is on PATH —
local dev on a Mac without Java should not break the test run. Docker (CI +
prod) installs OpenJDK 17 in the runtime image and JPype1 from PyPI.

Tests target the synchronous `_encode_sync` / `_match_sync` helpers directly
to avoid pulling pytest-asyncio into the dev deps; the async wrappers are
thin `run_in_threadpool` shims.
"""

from __future__ import annotations

import importlib.util
import shutil

import pytest

_skip_reason = None
if importlib.util.find_spec("jpype") is None:
    _skip_reason = "JPype1 not installed; SourceAFIS binding cannot run."
elif shutil.which("java") is None:
    _skip_reason = "No JVM on PATH; SourceAFIS binding cannot run."

pytestmark = pytest.mark.skipif(_skip_reason is not None, reason=_skip_reason or "")

# SourceAFIS's documented FMR=0.01% baseline. Scores above this are matches;
# scores below are non-matches. See https://sourceafis.machinezoo.com/threshold
SOURCEAFIS_THRESHOLD = 40.0


def test_template_version_string():
    from tanik_inference import fingerprint_engine

    assert fingerprint_engine.template_version() == "sourceafis/3.18.1"


def test_real_fingerprint_extracts_template(fingerprint_bytes):
    from tanik_inference import fingerprint_engine

    template, error = fingerprint_engine._encode_sync(
        fingerprint_bytes["subject_a001_right_index"]
    )
    assert error is None, f"unexpected extraction error: {error}"
    assert isinstance(template, bytes) and len(template) > 0


def test_self_match_scores_above_threshold(fingerprint_bytes):
    """Identical input must produce a score well above SourceAFIS's documented
    FMR=0.01% threshold (40). Self-match scores are typically in the hundreds.
    """
    from tanik_inference import fingerprint_engine

    template, error = fingerprint_engine._encode_sync(
        fingerprint_bytes["subject_a001_right_index"]
    )
    assert error is None and template is not None

    score = fingerprint_engine._match_sync(template, template)
    assert score > SOURCEAFIS_THRESHOLD, (
        f"self-match score {score} below threshold {SOURCEAFIS_THRESHOLD}; "
        "extraction or matcher binding is broken"
    )


@pytest.mark.parametrize(
    "probe_label,gallery_label",
    [
        ("subject_a001_right_index", "subject_a002_right_index"),
        ("subject_a001_right_middle", "subject_a002_right_middle"),
        ("subject_a001_right_ring", "subject_a002_left_index"),
    ],
)
def test_different_fingers_score_below_threshold(fingerprint_bytes, probe_label, gallery_label):
    """Distinct fingers across distinct subjects must score below the
    FMR=0.01% threshold. SourceAFIS typically returns 0 for clearly
    unrelated minutiae.
    """
    from tanik_inference import fingerprint_engine

    probe, probe_err = fingerprint_engine._encode_sync(fingerprint_bytes[probe_label])
    gallery, gallery_err = fingerprint_engine._encode_sync(fingerprint_bytes[gallery_label])
    assert probe_err is None and gallery_err is None
    assert probe is not None and gallery is not None

    score = fingerprint_engine._match_sync(probe, gallery)
    assert score < SOURCEAFIS_THRESHOLD, (
        f"different fingers ({probe_label} vs {gallery_label}) scored {score}, "
        f"above threshold {SOURCEAFIS_THRESHOLD}; matcher is over-matching"
    )
