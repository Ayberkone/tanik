from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile, status

from .. import iris_engine, storage
from ..config import settings
from ..errors import APIError, ErrorCode
from ..schemas import EnrollResponse, EyeSide, Modality, VerifyResponse
from ..validators import validate_image_bytes

router = APIRouter(prefix="/iris", tags=["iris"])


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.post(
    "/enroll",
    response_model=EnrollResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll(
    request: Request,
    image: UploadFile = File(...),
    display_name: Optional[str] = Form(default=None, max_length=64),
    eye_side: EyeSide = Form(default=EyeSide.LEFT),
) -> EnrollResponse:
    data = await image.read()
    validate_image_bytes(data)

    template_bytes, error_message = await iris_engine.encode(
        data, eye_side=eye_side.value, image_id=f"enroll:{_request_id(request)}"
    )
    if template_bytes is None:
        raise APIError(
            500,
            ErrorCode.PIPELINE_FAILURE,
            f"Iris pipeline failed: {error_message}",
            details={"stage": "encode"},
        )

    row = storage.create_subject(
        template_bytes=template_bytes,
        modality=iris_engine.name,
        template_version=iris_engine.template_version(),
        display_name=display_name,
        metadata={"eye_side": eye_side.value},
    )
    return EnrollResponse(
        request_id=_request_id(request),
        subject_id=row.subject_id,
        display_name=row.display_name,
        eye_side=eye_side,
        enrolled_at=row.enrolled_at,
        modality=Modality.IRIS,
        template_version=row.template_version,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    request: Request,
    image: UploadFile = File(...),
    subject_id: str = Form(...),
    eye_side: Optional[EyeSide] = Form(default=None),
) -> VerifyResponse:
    data = await image.read()
    validate_image_bytes(data)

    subject_row = storage.get_subject(subject_id)
    if subject_row is None or subject_row.modality != iris_engine.name:
        raise APIError(404, ErrorCode.SUBJECT_NOT_FOUND, f"No iris subject with id {subject_id}")

    enrolled_eye = storage.get_metadata(subject_row).get("eye_side", EyeSide.LEFT.value)
    use_eye = (eye_side.value if eye_side else enrolled_eye)

    probe_bytes, error_message = await iris_engine.encode(
        data, eye_side=use_eye, image_id=f"verify:{_request_id(request)}"
    )
    if probe_bytes is None:
        raise APIError(
            500,
            ErrorCode.PIPELINE_FAILURE,
            f"Iris pipeline failed: {error_message}",
            details={"stage": "encode"},
        )

    distance = await iris_engine.match(probe_bytes, subject_row.template_bytes)
    return VerifyResponse(
        request_id=_request_id(request),
        subject_id=subject_id,
        modality=Modality.IRIS,
        matched=distance < settings.iris_match_threshold,
        hamming_distance=distance,
        threshold=settings.iris_match_threshold,
        decision_at=datetime.now(timezone.utc),
    )
