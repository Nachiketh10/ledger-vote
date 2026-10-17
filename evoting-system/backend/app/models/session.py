from sqlalchemy.dialects.postgresql import UUID, ENUM as PGEnum
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import SessionUserType

session_user_type_enum = PGEnum(SessionUserType, name="session_user_type", create_type=True)


class Session(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    One row per issued refresh token. Used to (a) support logout /
    refresh-token revocation and (b) detect multi-device / multi-session
    fraud patterns (see app/fraud/session_guard.py).
    """

    __tablename__ = "sessions"

    voter_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("voters.id", ondelete="CASCADE"), nullable=True
    )
    admin_id = db.Column(UUID(as_uuid=True), nullable=True)  # either Admin or ElectionAdmin id
    user_type = db.Column(session_user_type_enum, nullable=False)

    refresh_token_hash = db.Column(db.String(128), unique=True, nullable=False)  # SHA-256 of the token, never the raw token

    device_fingerprint = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    voter = db.relationship("Voter", back_populates="sessions")

    __table_args__ = (
        db.Index("ix_sessions_voter_active", "voter_id", "is_active"),
    )

    def __repr__(self):
        return f"<Session user_type={self.user_type} active={self.is_active}>"
