from sqlalchemy.dialects.postgresql import UUID, ENUM as PGEnum
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import FraudType, FraudSeverity

fraud_type_enum = PGEnum(FraudType, name="fraud_type", create_type=True)
fraud_severity_enum = PGEnum(FraudSeverity, name="fraud_severity", create_type=True)


class FraudLog(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "fraud_logs"

    voter_id = db.Column(UUID(as_uuid=True), db.ForeignKey("voters.id"), nullable=True)
    election_id = db.Column(UUID(as_uuid=True), db.ForeignKey("elections.id"), nullable=True)

    fraud_type = db.Column(fraud_type_enum, nullable=False)
    severity = db.Column(fraud_severity_enum, nullable=False, default=FraudSeverity.MEDIUM)
    fraud_score = db.Column(db.Integer, nullable=False, default=0)  # 0-100

    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    device_fingerprint = db.Column(db.String(255), nullable=True)

    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    resolved_by_id = db.Column(UUID(as_uuid=True), nullable=True)  # admin id, resolved outside FK to allow either admin type
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    voter = db.relationship("Voter", back_populates="fraud_logs")
    election = db.relationship("Election", back_populates="fraud_logs")

    __table_args__ = (
        db.Index("ix_fraud_logs_voter_id", "voter_id"),
        db.Index("ix_fraud_logs_severity", "severity"),
    )

    def __repr__(self):
        return f"<FraudLog {self.fraud_type} score={self.fraud_score}>"
