from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.models.election import election_eligible_voters


class Voter(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "voters"

    voter_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # government/registration ID

    name = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    address = db.Column(db.Text, nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)  # bcrypt

    is_verified = db.Column(db.Boolean, default=False, nullable=False)  # admin-approved registration
    is_active = db.Column(db.Boolean, default=True, nullable=False)     # can be suspended for fraud

    has_face_registered = db.Column(db.Boolean, default=False, nullable=False)

    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    account_locked_until = db.Column(db.DateTime(timezone=True), nullable=True)

    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    eligible_elections = db.relationship(
        "Election", secondary=election_eligible_voters, back_populates="eligible_voters"
    )
    votes = db.relationship("Vote", back_populates="voter")
    face_embedding = db.relationship(
        "FaceEmbedding", back_populates="voter", uselist=False, cascade="all, delete-orphan"
    )
    fraud_logs = db.relationship("FraudLog", back_populates="voter")
    sessions = db.relationship("Session", back_populates="voter", cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("ix_voters_locked_until", "account_locked_until"),
    )

    def __repr__(self):
        return f"<Voter {self.voter_id}>"
