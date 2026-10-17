"""fix duplicate_face_enrollment enum casing

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-23

The previous migration (a1b2c3d4e5f6) added the fraud_type enum value
as lowercase 'duplicate_face_enrollment', matching the (incorrect)
assumption that the DB stores Python Enum .value strings. In fact,
SQLAlchemy's default Enum behavior stores the member's .name — so every
other value in this column is UPPERCASE (e.g. 'DUPLICATE_VOTE',
'MULTIPLE_FACES'), not lowercase. This migration adds the correctly-
cased value the application actually inserts. The old lowercase value
added by the previous migration is harmless, unused clutter — Postgres
doesn't allow removing individual enum values without recreating the
whole type, so it's left in place rather than risk a disruptive rebuild.
"""
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE fraud_type ADD VALUE IF NOT EXISTS 'DUPLICATE_FACE_ENROLLMENT'")


def downgrade():
    # See note in a1b2c3d4e5f6 — Postgres doesn't support removing an
    # enum value directly; intentionally a no-op.
    pass
