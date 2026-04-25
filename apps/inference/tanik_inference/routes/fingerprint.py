from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile, status

from .. import fingerprint_engine, storage
from ..config import settings
from ..errors import APIError, ErrorCode
from ..schemas import (
    FingerPosition,
    FingerprintEnrollResponse,
    FingerprintVerifyResponse,
    Modality,
)
from ..validators import validate_image_bytes

router = APIRouter(prefix="/fingerprint", tags=["fingerprint"])


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.post(
    "/enroll",
    response_model=FingerprintEnrollResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll(
    request: Request,
    image: UploadFile = File(...),
    display_name: Optional[str] = Form(default=None, max_length=64),
    finger_position: FingerPosition = Form(default=FingerPosition.RIGHT_INDEX),
) -> FingerprintEnrollResponse:
    data = await image.read()
    validate_image_bytes(data)

    template_bytes, error_message = await fingerprint_engine.encode(data)
    if template_bytes is None:
        raise APIError(
            500,
            ErrorCode.PIPELINE_FAILURE,
            f"Fingerprint pipeline failed: {error_message}",
            details={"stage": "encode"},
        )

    row = storage.create_subject(
        template_bytes=template_bytes,
        modality=fingerprint_engine.name,
        template_version=fingerprint_engine.template_version(),
        display_name=display_name,
        metadata={"finger_position": finger_position.value},
    )
    return FingerprintEnrollResponse(
        request_id=_request_id(request),
        subject_id=row.subject_id,
        display_name=row.display_name,
        finger_position=finger_position,
        enrolled_at=row.enrolled_at,
        modality=Modality.FINGERPRINT,
        template_version=row.template_version,
    )


@router.post("/verify", response_model=FingerprintVerifyResponse)
async def verify(
    request: Request,
    image: UploadFile = File(...),
    subject_id: str = Form(...),
    finger_position: Optional[FingerPosition] = Form(default=None),
) -> FingerprintVerifyResponse:
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
            details={"stage": "encode"},
        )

    score = await fingerprint_engine.match(probe_bytes, subject_row.template_bytes)
    return FingerprintVerifyResponse(
        request_id=_request_id(request),
        subject_id=subject_id,
        modality=Modality.FINGERPRINT,
        matched=score >= settings.fingerprint_match_threshold,
        similarity_score=score,
        threshold=settings.fingerprint_match_threshold,
        decision_at=datetime.now(timezone.utc),
    )
