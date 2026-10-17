import uuid

from sqlalchemy.dialects.postgresql import UUID, ENUM as PGEnum
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import ElectionStatus

election_status_enum = PGEnum(
    ElectionStatus, name="election_status", create_type=True
)

# Which ElectionAdmins are allowed to manage which Elections (many-to-many).
election_admin_assignments = db.Table(
    "election_admin_assignments",
    db.Column(
        "election_admin_id",
        UUID(as_uuid=True),
        db.ForeignKey("election_admins.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "election_id",
        UUID(as_uuid=True),
        db.ForeignKey("elections.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Which Voters are eligible to vote in which Elections (many-to-many).
election_eligible_voters = db.Table(
    "election_eligible_voters",
    db.Column(
        "voter_id",
        UUID(as_uuid=True),
        db.ForeignKey("voters.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "election_id",
        UUID(as_uuid=True),
        db.ForeignKey("elections.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Election(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "elections"

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    start_date = db.Column(db.DateTime(timezone=True), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True), nullable=False)

    status = db.Column(
        election_status_enum, nullable=False, default=ElectionStatus.DRAFT
    )

    created_by_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("election_admins.id"), nullable=True
    )

    # Relationships
    candidates = db.relationship(
        "Candidate", back_populates="election", cascade="all, delete-orphan"
    )
    votes = db.relationship("Vote", back_populates="election")
    fraud_logs = db.relationship("FraudLog", back_populates="election")

    eligible_voters = db.relationship(
        "Voter",
        secondary=election_eligible_voters,
        back_populates="eligible_elections",
    )
    assigned_admins = db.relationship(
        "ElectionAdmin",
        secondary=election_admin_assignments,
        back_populates="assigned_elections",
    )

    __table_args__ = (
        db.CheckConstraint("end_date > start_date", name="ck_election_dates_valid"),
        db.Index("ix_elections_status", "status"),
    )

    def __repr__(self):
        return f"<Election {self.title} [{self.status}]>"
