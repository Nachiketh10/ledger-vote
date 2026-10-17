"""
Role-based access guards built on top of Flask-JWT-Extended.

Usage:
    @app.route("/api/admin/elections", methods=["POST"])
    @roles_required("super_admin", "election_admin")
    def create_election():
        ...
"""

from functools import wraps

from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from app.utils.responses import error


def roles_required(*allowed_roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")

            if role not in allowed_roles:
                return error("You do not have permission to perform this action.", 403)

            g.current_user_id = get_jwt_identity()
            g.current_user_role = role
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# Convenience aliases for the most common guard combinations
super_admin_required = roles_required("super_admin")
election_admin_required = roles_required("super_admin", "election_admin")
voter_required = roles_required("voter")
any_authenticated_required = roles_required("super_admin", "election_admin", "voter")


def current_identity() -> tuple[str | None, str | None]:
    """(user_id, role) of the caller, only valid inside a route already
    guarded by one of the decorators above (or verify_jwt_in_request())."""
    return getattr(g, "current_user_id", None), getattr(g, "current_user_role", None)
