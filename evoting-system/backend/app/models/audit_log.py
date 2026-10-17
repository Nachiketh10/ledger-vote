from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PGEnum
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin
from app.models.base import utcnow
from app.models.enums import ActorType

actor_type_enum = PGEnum(ActorType, name="actor_type", create_type=True)


class AuditLog(UUIDPrimaryKeyMixin, db.Model):
    """
    Append-only trail of security-relevant actions. No updated_at —
    audit rows are never edited, only ever inserted.
    """

    __tablename__ = "audit_logs"

    actor_type = db.Column(actor_type_enum, nullable=False)
    actor_id = db.Column(UUID(as_uuid=True), nullable=True)  # nullable for ActorType.SYSTEM

    action = db.Column(db.String(100), nullable=False)  # e.g. "election.created", "vote.cast"
    details = db.Column(JSONB, nullable=True)            # arbitrary structured context

    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        db.Index("ix_audit_logs_action", "action"),
        db.Index("ix_audit_logs_actor", "actor_type", "actor_id"),
        db.Index("ix_audit_logs_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.actor_type}:{self.actor_id}>"
