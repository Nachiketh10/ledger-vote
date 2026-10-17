"""
Shared model base classes.

Every table uses a UUID primary key (not a sequential int) so that voter
IDs, block IDs, etc. can't be enumerated by guessing — relevant for an
e-voting system where record IDs shouldn't leak ordering/volume info.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
