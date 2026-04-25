from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EyeSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class Modality(str, Enum):
    IRIS = "iris"


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
