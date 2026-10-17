from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class FingerprintTemplate(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    Stores a WebAuthn credential (public key only — the actual fingerprint
    data never leaves the voter's device/authenticator, by design of the
    WebAuthn standard). See app/fingerprint/webauthn_service.py.

    hardware_adapter.py provides an alternate path for a physical USB
    fingerprint reader; if used, `template_data` holds that vendor SDK's
    encrypted minutiae template instead of a WebAuthn public key.
    """

    __tablename__ = "fingerprint_templates"

    voter_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("voters.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )

    auth_method = db.Column(db.String(20), nullable=False, default="webauthn")  # webauthn | hardware_sdk

    # WebAuthn fields
    credential_id = db.Column(db.String(500), unique=True, nullable=True)
    public_key = db.Column(db.Text, nullable=True)
    sign_count = db.Column(db.Integer, default=0, nullable=False)

    # Hardware SDK fallback field (vendor-encrypted template blob)
    template_data = db.Column(db.LargeBinary, nullable=True)

    device_info = db.Column(db.String(255), nullable=True)

    voter = db.relationship("Voter", back_populates="fingerprint_template")

    def __repr__(self):
        return f"<FingerprintTemplate voter={self.voter_id} method={self.auth_method}>"
