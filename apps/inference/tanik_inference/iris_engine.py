"""Async-safe wrapper around the open-iris pipeline.

The pipeline is CPU-bound and synchronous. FastAPI handlers must not block the
event loop on it, so every call goes through `run_in_threadpool`.

We keep one process-wide pipeline instance to amortize the model load.
"""

from typing import Optional, Tuple

import cv2
import iris
import numpy as np
from fastapi.concurrency import run_in_threadpool

_pipeline: Optional[iris.IRISPipeline] = None
_matcher: Optional[iris.HammingDistanceMatcher] = None


def _get_pipeline() -> iris.IRISPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = iris.IRISPipeline()
    return _pipeline


def _get_matcher() -> iris.HammingDistanceMatcher:
    global _matcher
    if _matcher is None:
        _matcher = iris.HammingDistanceMatcher()
    return _matcher


def template_version() -> str:
    return f"open-iris/{iris.__version__}"


def _decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("OpenCV could not decode image bytes")
    return img


def _encode_sync(image_bytes: bytes, eye_side: str, image_id: str) -> Tuple[Optional[iris.IrisTemplate], Optional[str]]:
    img = _decode_image(image_bytes)
    pipe = _get_pipeline()
    out = pipe(iris.IRImage(img_data=img, image_id=image_id, eye_side=eye_side))
    if out.get("error") is not None:
        err = out["error"]
        # iris pipeline error objects have .error_type / .message-ish attributes; coerce safely
        return None, getattr(err, "message", str(err))
    return out["iris_template"], None


async def encode(image_bytes: bytes, eye_side: str, image_id: str) -> Tuple[Optional[iris.IrisTemplate], Optional[str]]:
    return await run_in_threadpool(_encode_sync, image_bytes, eye_side, image_id)


def _match_sync(probe: iris.IrisTemplate, gallery: iris.IrisTemplate) -> float:
    return _get_matcher().run(probe, gallery)


async def match(probe: iris.IrisTemplate, gallery: iris.IrisTemplate) -> float:
    return await run_in_threadpool(_match_sync, probe, gallery)
