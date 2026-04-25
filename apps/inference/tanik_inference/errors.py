from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(str, Enum):
    INVALID_IMAGE = "INVALID_IMAGE"
    SUBJECT_NOT_FOUND = "SUBJECT_NOT_FOUND"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PIPELINE_FAILURE = "PIPELINE_FAILURE"
    PAD_FAILURE = "PAD_FAILURE"


class ErrorBody(BaseModel):
    request_id: str
    error_code: ErrorCode
    message: str
    details: Optional[Any] = None


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[Any] = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def _api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorBody(
                request_id=_request_id(request),
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
            ).dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorBody(
                request_id=_request_id(request),
                error_code=ErrorCode.VALIDATION_ERROR,
                message="Request body or form fields failed validation",
                details=exc.errors(),
            ).dict(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Map unsupported media type / payload too large that Starlette may raise itself
        code_map = {
            413: ErrorCode.PAYLOAD_TOO_LARGE,
            415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
            404: ErrorCode.SUBJECT_NOT_FOUND if "subject" in str(exc.detail).lower() else ErrorCode.VALIDATION_ERROR,
        }
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorBody(
                request_id=_request_id(request),
                error_code=code_map.get(exc.status_code, ErrorCode.VALIDATION_ERROR),
                message=str(exc.detail),
            ).dict(),
        )
