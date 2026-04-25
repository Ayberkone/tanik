from fastapi import APIRouter
from pydantic import BaseModel

from ..config import settings

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    status: str
    iris_engine: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    import iris

    return HealthResponse(
        status="ok",
        iris_engine=f"open-iris/{iris.__version__}",
        version=settings.version,
    )
