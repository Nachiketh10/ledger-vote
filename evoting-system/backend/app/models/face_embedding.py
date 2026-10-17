from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class FaceEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    Stores the AES-encrypted InsightFace embedding vector — never a raw
    face image. See app/face/embedder.py (generation) and
    app/face/encryption.py (the AES layer applied before this ever
    reaches the DB).
    """

    __tablename__ = "face_embeddings"

    voter_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("voters.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )

    encrypted_embedding = db.Column(db.LargeBinary, nullable=False)  # AES-encrypted 512-d float vector
    embedding_model = db.Column(db.String(50), nullable=False, default="insightface-buffalo_l")
    sample_count = db.Column(db.Integer, nullable=False, default=0)  # how many capture frames were averaged

    voter = db.relationship("Voter", back_populates="face_embedding")

    def __repr__(self):
        return f"<FaceEmbedding voter={self.voter_id} model={self.embedding_model}>"
