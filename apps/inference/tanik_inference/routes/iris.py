from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse

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

    template, error_message = await iris_engine.encode(
        data, eye_side=eye_side.value, image_id=f"enroll:{_request_id(request)}"
    )
    if template is None:
        raise APIError(
            500,
            ErrorCode.PIPELINE_FAILURE,
            f"Iris pipeline failed: {error_message}",
            details={"stage": "encode"},
        )

    row = storage.create_subject(
        template=template,
        eye_side=eye_side.value,
        display_name=display_name,
        template_version=iris_engine.template_version(),
    )
    return EnrollResponse(
        request_id=_request_id(request),
        subject_id=row.subject_id,
        display_name=row.display_name,
        eye_side=EyeSide(row.eye_side),
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

    gallery = storage.get_template(subject_id)
    if gallery is None:
        raise APIError(404, ErrorCode.SUBJECT_NOT_FOUND, f"No subject with id {subject_id}")

    subject_row = storage.get_subject(subject_id)
    use_eye = (eye_side or EyeSide(subject_row.eye_side)).value

    probe, error_message = await iris_engine.encode(
        data, eye_side=use_eye, image_id=f"verify:{_request_id(request)}"
    )
    if probe is None:
        raise APIError(
            500,
            ErrorCode.PIPELINE_FAILURE,
            f"Iris pipeline failed: {error_message}",
            details={"stage": "encode"},
        )

    distance = await iris_engine.match(probe, gallery)
    return VerifyResponse(
        request_id=_request_id(request),
        subject_id=subject_id,
        modality=Modality.IRIS,
        matched=distance < settings.iris_match_threshold,
        hamming_distance=distance,
        threshold=settings.iris_match_threshold,
        decision_at=datetime.now(timezone.utc),
    )
