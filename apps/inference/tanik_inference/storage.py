"""Modality-agnostic persistence for biometric templates.

Templates cross this boundary as opaque `bytes`. The engine that produced them
owns serialization; storage records the modality + version so a mismatched
matcher can be detected later.

`metadata_json` is a small free-form blob for modality-specific extras
(iris's `eye_side`, fingerprint's finger position, etc.). Kept as a JSON
string column rather than a real JSON type so we stay portable across SQLite
and Postgres without driver tricks.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from .db import Subject, session_scope


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_subject(
    *,
    template_bytes: bytes,
    modality: str,
    template_version: str,
    display_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Subject:
    subject_id = str(uuid4())
    row = Subject(
        subject_id=subject_id,
        display_name=display_name,
        modality=modality,
        enrolled_at=_now(),
        template_version=template_version,
        template_bytes=template_bytes,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    with session_scope() as s:
        s.add(row)
        s.flush()
        s.refresh(row)
        s.expunge(row)
    return row


def get_subject(subject_id: str) -> Optional[Subject]:
    with session_scope() as s:
        row = s.get(Subject, subject_id)
        if row is None:
            return None
        s.expunge(row)
        return row


def get_template(subject_id: str) -> Optional[bytes]:
    row = get_subject(subject_id)
    if row is None:
        return None
    return row.template_bytes


def get_metadata(subject_row: Subject) -> Dict[str, Any]:
    if not subject_row.metadata_json:
        return {}
    return json.loads(subject_row.metadata_json)
