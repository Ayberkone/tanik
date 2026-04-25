import pytest

from tanik_inference.errors import APIError, ErrorCode
from tanik_inference.validators import validate_image_bytes

# Minimal valid PNG: 1x1 pixel
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c63000100000005000100daacf6710000000049454e"
    "44ae426082"
)


def test_rejects_empty():
    with pytest.raises(APIError) as ex:
        validate_image_bytes(b"")
    assert ex.value.error_code == ErrorCode.INVALID_IMAGE


def test_rejects_garbage():
    with pytest.raises(APIError) as ex:
        validate_image_bytes(b"this is not an image" * 10)
    assert ex.value.error_code == ErrorCode.INVALID_IMAGE


def test_accepts_png():
    mime = validate_image_bytes(PNG_BYTES)
    assert mime == "image/png"
