"""remove fingerprint auth entirely

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-26

Fingerprint (WebAuthn) authentication has been removed from the
project — face recognition is now the sole biometric verification
method. This drops the fingerprint_templates table and the
voters.has_fingerprint_registered column.

Downgrade recreates the table structure (for completeness/safety) but
obviously cannot restore any WebAuthn credential data that existed —
if you actually need to roll back, restore from a DB backup instead of
relying on this downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("fingerprint_templates")
    op.drop_column("voters", "has_fingerprint_registered")


def downgrade():
    op.add_column(
        "voters",
        sa.Column("has_fingerprint_registered", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "fingerprint_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("voter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("voters.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("auth_method", sa.String(20), nullable=False, server_default="webauthn"),
        sa.Column("credential_id", sa.String(500), unique=True, nullable=True),
        sa.Column("public_key", sa.Text(), nullable=True),
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("template_data", sa.LargeBinary(), nullable=True),
        sa.Column("device_info", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
