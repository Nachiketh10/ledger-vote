from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class Vote(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    A single cast vote.

    NOTE ON ANONYMITY: this schema keeps voter_id on the Vote row so a
    UNIQUE(voter_id, election_id) constraint can enforce "one vote per
    voter per election" at the database level, and so audit/fraud tooling
    can trace a vote back to a voter if a dispute is raised. This is the
    same tradeoff most real-world verifiable e-voting systems make
    (voter-verifiable, not fully anonymous). If you need full anonymity,
    the voter link would need to move into a separate access-controlled
    "eligibility ledger" decoupled from the vote content — flagged here
    rather than silently assumed.
    """

    __tablename__ = "votes"

    election_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("elections.id", ondelete="CASCADE"), nullable=False
    )
    candidate_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("candidates.id"), nullable=False
    )
    voter_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("voters.id"), nullable=False
    )

    encrypted_vote_hash = db.Column(db.String(128), nullable=False)  # SHA-256 hex digest of vote payload
    cast_at = db.Column(db.DateTime(timezone=True), nullable=False)

    election = db.relationship("Election", back_populates="votes")
    candidate = db.relationship("Candidate", back_populates="votes")
    voter = db.relationship("Voter", back_populates="votes")
    block = db.relationship("Block", back_populates="vote", uselist=False)

    __table_args__ = (
        db.UniqueConstraint("voter_id", "election_id", name="uq_one_vote_per_election"),
        db.Index("ix_votes_election_id", "election_id"),
    )

    def __repr__(self):
        return f"<Vote election={self.election_id} voter={self.voter_id}>"
