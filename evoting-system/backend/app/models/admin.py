from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.models.election import election_admin_assignments


class Admin(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """Super Admin — full system control, manages Election Admins."""

    __tablename__ = "admins"

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Admin {self.email}>"


class ElectionAdmin(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """Election Admin — manages the elections assigned to them by a Super Admin."""

    __tablename__ = "election_admins"

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    assigned_elections = db.relationship(
        "Election",
        secondary=election_admin_assignments,
        back_populates="assigned_admins",
    )

    def __repr__(self):
        return f"<ElectionAdmin {self.email}>"
