import uuid

from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin


class Block(UUIDPrimaryKeyMixin, db.Model):
    """
    One block per vote. block_index is the chain position (0, 1, 2, ...);
    current_hash is derived from previous_hash + block contents, so any
    tampering with a past block invalidates every block after it.

    Deliberately has NO updated_at / mutable timestamp mixin — a block's
    fields must never be edited after creation. Corrections happen by
    appending a new block, never by rewriting history.
    """

    __tablename__ = "blockchain"

    block_index = db.Column(db.Integer, unique=True, nullable=False, index=True)

    previous_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hex = 64 chars
    current_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    nonce = db.Column(db.Integer, nullable=False, default=0)

    election_id = db.Column(UUID(as_uuid=True), db.ForeignKey("elections.id"), nullable=False)
    candidate_id = db.Column(UUID(as_uuid=True), db.ForeignKey("candidates.id"), nullable=False)

    encrypted_vote_hash = db.Column(db.String(128), nullable=False)

    transaction_id = db.Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )

    vote_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("votes.id"), unique=True, nullable=False
    )

    vote = db.relationship("Vote", back_populates="block")

    __table_args__ = (
        db.Index("ix_blockchain_election_id", "election_id"),
    )

    def __repr__(self):
        return f"<Block #{self.block_index} {self.current_hash[:10]}...>"
