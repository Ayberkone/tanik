import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .errors import register_exception_handlers
from .logging import log, setup_logging
from .routes import fingerprint, health, iris, verify

setup_logging(settings.log_level)
init_db()

app = FastAPI(
    title="TANIK Inference",
    version=settings.version,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["x-request-id"] = request_id
    log.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "elapsed_ms": round(elapsed_ms, 1),
            "request_id": request_id,
        },
    )
    return response


register_exception_handlers(app)

app.include_router(health.router, prefix="/api/v1")
app.include_router(iris.router, prefix="/api/v1")
app.include_router(fingerprint.router, prefix="/api/v1")
app.include_router(verify.router, prefix="/api/v1")
