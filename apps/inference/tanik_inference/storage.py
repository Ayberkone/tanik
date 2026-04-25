"""Persistence layer for iris templates.

Templates are serialized via `iris.IrisTemplate.serialize()` (a JSON-friendly
dict the upstream library knows how to round-trip) and stored in a single
text column. Raw images never reach this module.
"""

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import iris

from .db import Subject, session_scope


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize(template: iris.IrisTemplate) -> str:
    return json.dumps(template.serialize())


def _deserialize(blob: str) -> iris.IrisTemplate:
    return iris.IrisTemplate.deserialize(json.loads(blob))


def create_subject(
    template: iris.IrisTemplate,
    eye_side: str,
    display_name: Optional[str],
    template_version: str,
) -> Subject:
    subject_id = str(uuid4())
    row = Subject(
        subject_id=subject_id,
        display_name=display_name,
        eye_side=eye_side,
        enrolled_at=_now(),
        template_version=template_version,
        template_json=_serialize(template),
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


def get_template(subject_id: str) -> Optional[iris.IrisTemplate]:
    row = get_subject(subject_id)
    if row is None:
        return None
    return _deserialize(row.template_json)
