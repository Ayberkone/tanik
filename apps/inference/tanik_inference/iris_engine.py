"""open-iris pipeline behind the BiometricEngine contract.

The pipeline is CPU-bound and synchronous; FastAPI handlers must not block on
it, so every public call is offloaded via `run_in_threadpool`.

We keep one process-wide pipeline + matcher to amortise model load. Templates
cross the engine boundary as JSON-encoded bytes so the storage layer never
imports `iris.IrisTemplate`.
"""

import json
from typing import Optional, Tuple

import cv2
import iris
import numpy as np
from fastapi.concurrency import run_in_threadpool

name = "iris"

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


def _serialize(template: iris.IrisTemplate) -> bytes:
    return json.dumps(template.serialize()).encode("utf-8")


def _deserialize(blob: bytes) -> iris.IrisTemplate:
    return iris.IrisTemplate.deserialize(json.loads(blob.decode("utf-8")))


def _encode_sync(image_bytes: bytes, eye_side: str, image_id: str) -> Tuple[Optional[bytes], Optional[str]]:
    img = _decode_image(image_bytes)
    pipe = _get_pipeline()
    out = pipe(iris.IRImage(img_data=img, image_id=image_id, eye_side=eye_side))
    if out.get("error") is not None:
        err = out["error"]
        return None, getattr(err, "message", str(err))
    return _serialize(out["iris_template"]), None


async def encode(
    image_bytes: bytes,
    *,
    eye_side: str = "left",
    image_id: str = "iris",
) -> Tuple[Optional[bytes], Optional[str]]:
    return await run_in_threadpool(_encode_sync, image_bytes, eye_side, image_id)


def _match_sync(probe: bytes, gallery: bytes) -> float:
    return _get_matcher().run(_deserialize(probe), _deserialize(gallery))


async def match(probe: bytes, gallery: bytes) -> float:
    return await run_in_threadpool(_match_sync, probe, gallery)
