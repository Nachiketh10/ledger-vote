"""add duplicate_face_enrollment fraud type

Revision ID: a1b2c3d4e5f6
Revises: ce7e5b147160
Create Date: 2026-07-23

Adds a new value to the existing fraud_type Postgres ENUM. Written by
hand rather than via `flask db migrate` autogenerate — SQLAlchemy/
Alembic's autogenerate support for enum VALUE additions (as opposed to
adding/dropping whole columns) is unreliable and can sometimes try to
drop-and-recreate the type, which fails if any row already references
it. A plain ALTER TYPE ... ADD VALUE is the correct, safe operation.

NOTE: PostgreSQL does not allow ALTER TYPE ... ADD VALUE to run inside
the same transaction as other schema changes in older PG versions; if
this fails with "unsafe use of new value" on your PG version, run the
ALTER TYPE statement manually (see backend/migrations/reference_schema.sql
notes) and then stamp this revision with `flask db stamp a1b2c3d4e5f6`.
"""
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "ce7e5b147160"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE fraud_type ADD VALUE IF NOT EXISTS 'duplicate_face_enrollment'")


def downgrade():
    # Postgres does not support removing a value from an ENUM type
    # directly. Downgrading this would require recreating the type
    # without the value and re-pointing every dependent column, which
    # risks data loss if any row uses it — intentionally left as a
    # no-op. If you truly need to reverse this, handle it manually.
    pass
