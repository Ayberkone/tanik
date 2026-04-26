"""Unified, fused verification across iris + fingerprint.

Accepts either or both modalities in a single multipart upload, normalises
each engine-native score to ``[0, 1]`` via ``fusion.py``, and returns one
fused decision plus a per-modality breakdown for client transparency.

The fused decision threshold is server-configured. The current weights and
normalisation knobs are explicit placeholders — see ``docs/fusion.md``. The
response carries ``calibration_status: "placeholder"`` so any caller sees
the caveat in-band; a downstream system that promises measured FAR/FRR
must refuse a placeholder response.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile

from .. import fingerprint_engine, fusion, iris_engine, storage
from ..config import settings
from ..errors import APIError, ErrorCode
from ..schemas import (
    CalibrationStatus,
    EyeSide,
    FingerPosition,
    Modality,
    ModalityResult,
    UnifiedVerifyResponse,
)
from ..validators import validate_image_bytes

router = APIRouter(prefix="/verify", tags=["verify"])

CALIBRATION_REFERENCE = "docs/fusion.md"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.post("", response_model=UnifiedVerifyResponse)
async def verify(
    request: Request,
    iris_image: Optional[UploadFile] = File(default=None),
    iris_subject_id: Optional[str] = Form(default=None),
    iris_eye_side: Optional[EyeSide] = Form(default=None),
    fingerprint_image: Optional[UploadFile] = File(default=None),
    fingerprint_subject_id: Optional[str] = Form(default=None),
    fingerprint_finger_position: Optional[FingerPosition] = Form(default=None),
) -> UnifiedVerifyResponse:
    # Reject half-supplied modalities first — an image without a subject_id
    # (or vice versa) is almost certainly a client bug worth surfacing
    # specifically, before falling through to the generic "no modality" case.
    if (iris_image is None) != (iris_subject_id is None):
        raise APIError(
            400,
            ErrorCode.VALIDATION_ERROR,
            "iris_image and iris_subject_id must be supplied together.",
        )
    if (fingerprint_image is None) != (fingerprint_subject_id is None):
        raise APIError(
            400,
            ErrorCode.VALIDATION_ERROR,
            "fingerprint_image and fingerprint_subject_id must be supplied together.",
        )

    iris_present = iris_image is not None and iris_subject_id is not None
    fp_present = fingerprint_image is not None and fingerprint_subject_id is not None

    if not iris_present and not fp_present:
        raise APIError(
            400,
            ErrorCode.VALIDATION_ERROR,
            "At least one modality must be supplied: provide (iris_image + iris_subject_id) "
            "and/or (fingerprint_image + fingerprint_subject_id).",
        )

    results: list[ModalityResult] = []
    normalised: dict[str, float] = {}

    if iris_present:
        results.append(
            await _run_iris(
                image=iris_image,
                subject_id=iris_subject_id,
                eye_side=iris_eye_side,
                request_id=_request_id(request),
            )
        )
        normalised[Modality.IRIS.value] = results[-1].normalised_score

    if fp_present:
        results.append(
            await _run_fingerprint(
                image=fingerprint_image,
                subject_id=fingerprint_subject_id,
                request_id=_request_id(request),
            )
        )
        normalised[Modality.FINGERPRINT.value] = results[-1].normalised_score

    weights = {
        Modality.IRIS.value: settings.fusion_iris_weight,
        Modality.FINGERPRINT.value: settings.fusion_fingerprint_weight,
    }
    fused = fusion.fuse(normalised, weights)

    # Renormalised weights, surfaced on each ModalityResult — useful when
    # only one modality was supplied (the present modality's weight becomes 1.0).
    relevant_total = sum(weights[m] for m in normalised)
    for r in results:
        r.weight = weights[r.modality.value] / relevant_total

    return UnifiedVerifyResponse(
        request_id=_request_id(request),
        matched=fused >= settings.fusion_decision_threshold,
        fused_score=fused,
        threshold=settings.fusion_decision_threshold,
        modalities=results,
        calibration_status=CalibrationStatus.PLACEHOLDER,
        calibration_reference=CALIBRATION_REFERENCE,
        decision_at=datetime.now(timezone.utc),
    )


async def _run_iris(
    *,
    image: UploadFile,
    subject_id: str,
    eye_side: Optional[EyeSide],
    request_id: str,
) -> ModalityResult:
    data = await image.read()
    validate_image_bytes(data)

    subject_row = storage.get_subject(subject_id)
    if subject_row is None or subject_row.modality != iris_engine.name:
        raise APIError(404, ErrorCode.SUBJECT_NOT_FOUND, f"No iris subject with id {subject_id}")

    enrolled_eye = storage.get_metadata(subject_row).get("eye_side", EyeSide.LEFT.value)
    use_eye = eye_side.value if eye_side else enrolled_eye

    probe_bytes, error_message = await iris_engine.encode(
        data, eye_side=use_eye, image_id=f"verify:{request_id}:iris"
    )
    if probe_bytes is None:
        raise APIError(
            500,
            ErrorCode.PIPELINE_FAILURE,
            f"Iris pipeline failed: {error_message}",
            details={"stage": "encode", "modality": "iris"},
        )

    distance = await iris_engine.match(probe_bytes, subject_row.template_bytes)
    normalised = fusion.normalise_iris(
        distance,
        floor=settings.iris_hd_floor,
        threshold=settings.iris_match_threshold,
        ceil=settings.iris_hd_ceil,
    )
    return ModalityResult(
        modality=Modality.IRIS,
        subject_id=subject_id,
        engine_native_score=distance,
        normalised_score=normalised,
        weight=0.0,  # filled in after we know which modalities are present
    )


async def _run_fingerprint(
    *,
    image: UploadFile,
    subject_id: str,
    request_id: str,
) -> ModalityResult:
    data = await image.read()
    validate_image_bytes(data)

    subject_row = storage.get_subject(subject_id)
    if subject_row is None or subject_row.modality != fingerprint_engine.name:
        raise APIError(
            404, ErrorCode.SUBJECT_NOT_FOUND, f"No fingerprint subject with id {subject_id}"
        )

    probe_bytes, error_message = await fingerprint_engine.encode(data)
    if probe_bytes is None:
        raise APIError(
            500,
            ErrorCode.PIPELINE_FAILURE,
            f"Fingerprint pipeline failed: {error_message}",
            details={"stage": "encode", "modality": "fingerprint"},
        )

    score = await fingerprint_engine.match(probe_bytes, subject_row.template_bytes)
    normalised = fusion.normalise_fingerprint(
        score,
        threshold=settings.fingerprint_match_threshold,
        ceil=settings.fingerprint_score_ceil,
    )
    return ModalityResult(
        modality=Modality.FINGERPRINT,
        subject_id=subject_id,
        engine_native_score=score,
        normalised_score=normalised,
        weight=0.0,
    )
