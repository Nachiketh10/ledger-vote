from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class Candidate(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "candidates"

    election_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("elections.id", ondelete="CASCADE"), nullable=False
    )

    name = db.Column(db.String(120), nullable=False)
    party = db.Column(db.String(120), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)

    election = db.relationship("Election", back_populates="candidates")
    votes = db.relationship("Vote", back_populates="candidate")

    __table_args__ = (
        db.Index("ix_candidates_election_id", "election_id"),
    )

    def __repr__(self):
        return f"<Candidate {self.name} ({self.party})>"
