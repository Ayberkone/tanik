from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EyeSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class FingerPosition(str, Enum):
    """ISO/IEC 19794-2 finger position labels (lowercase string form).

    The numeric position codes used in the standard map cleanly to these
    identifiers; we expose the labels because they are easier to read in API
    requests and responses and the schema is small enough that an enum is
    safer than a free-form string.
    """

    RIGHT_THUMB = "right_thumb"
    RIGHT_INDEX = "right_index"
    RIGHT_MIDDLE = "right_middle"
    RIGHT_RING = "right_ring"
    RIGHT_LITTLE = "right_little"
    LEFT_THUMB = "left_thumb"
    LEFT_INDEX = "left_index"
    LEFT_MIDDLE = "left_middle"
    LEFT_RING = "left_ring"
    LEFT_LITTLE = "left_little"


class Modality(str, Enum):
    IRIS = "iris"
    FINGERPRINT = "fingerprint"


class EnrollResponse(BaseModel):
    request_id: str
    subject_id: str
    display_name: Optional[str] = None
    eye_side: EyeSide
    enrolled_at: datetime
    modality: Modality = Modality.IRIS
    template_version: str = Field(..., description='e.g. "open-iris/1.11.1"')


class VerifyResponse(BaseModel):
    request_id: str
    subject_id: str
    modality: Modality = Modality.IRIS
    matched: bool
    hamming_distance: float = Field(..., ge=0.0, le=1.0)
    threshold: float = Field(..., ge=0.0, le=1.0)
    decision_at: datetime


class FingerprintEnrollResponse(BaseModel):
    request_id: str
    subject_id: str
    display_name: Optional[str] = None
    finger_position: FingerPosition
    enrolled_at: datetime
    modality: Modality = Modality.FINGERPRINT
    template_version: str = Field(..., description='e.g. "sourceafis/3.18.1"')


class FingerprintVerifyResponse(BaseModel):
    request_id: str
    subject_id: str
    modality: Modality = Modality.FINGERPRINT
    matched: bool
    similarity_score: float = Field(..., ge=0.0, description="SourceAFIS similarity, higher is better, open-ended")
    threshold: float = Field(..., ge=0.0)
    decision_at: datetime
