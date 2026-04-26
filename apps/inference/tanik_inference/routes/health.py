from fastapi import APIRouter
from pydantic import BaseModel

from .. import fingerprint_engine
from ..config import settings

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    status: str
    iris_engine: str
    fingerprint_engine: str
    calibration_status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    import iris

    return HealthResponse(
        status="ok",
        iris_engine=f"open-iris/{iris.__version__}",
        fingerprint_engine=fingerprint_engine.template_version(),
        calibration_status="placeholder",
        version=settings.version,
    )
