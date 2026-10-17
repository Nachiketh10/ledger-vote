"""
Importing this package registers every model's table with SQLAlchemy's
metadata. This module MUST be imported before Alembic autogenerate runs,
and before db.create_all() in any bootstrap/seed script — otherwise
tables silently won't be created.
"""

from app.models.admin import Admin, ElectionAdmin
from app.models.voter import Voter
from app.models.candidate import Candidate
from app.models.election import (
    Election,
    election_admin_assignments,
    election_eligible_voters,
)
from app.models.vote import Vote
from app.models.blockchain import Block
from app.models.fraud_log import FraudLog
from app.models.audit_log import AuditLog
from app.models.face_embedding import FaceEmbedding
from app.models.session import Session

__all__ = [
    "Admin",
    "ElectionAdmin",
    "Voter",
    "Candidate",
    "Election",
    "election_admin_assignments",
    "election_eligible_voters",
    "Vote",
    "Block",
    "FraudLog",
    "AuditLog",
    "FaceEmbedding",
    "Session",
]
