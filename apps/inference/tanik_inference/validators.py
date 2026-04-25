from typing import Tuple

import filetype

from .config import settings
from .errors import APIError, ErrorCode

ALLOWED_MIMES: Tuple[str, ...] = ("image/png", "image/jpeg", "image/bmp")


def validate_image_bytes(data: bytes) -> str:
    """Validate uploaded image bytes by magic-byte sniffing.

    Returns the detected MIME on success. Raises APIError otherwise — never
    trust Content-Type from the client.
    """
    if len(data) == 0:
        raise APIError(400, ErrorCode.INVALID_IMAGE, "Uploaded image is empty")

    if len(data) > settings.max_upload_bytes:
        raise APIError(
            413,
            ErrorCode.PAYLOAD_TOO_LARGE,
            f"Upload exceeds {settings.max_upload_bytes} bytes",
        )

    kind = filetype.guess(data)
    if kind is None:
        raise APIError(400, ErrorCode.INVALID_IMAGE, "Could not determine file type from content")

    if kind.mime not in ALLOWED_MIMES:
        raise APIError(
            415,
            ErrorCode.UNSUPPORTED_MEDIA_TYPE,
            f"MIME {kind.mime!r} not allowed; allowed: {', '.join(ALLOWED_MIMES)}",
        )

    return kind.mime
