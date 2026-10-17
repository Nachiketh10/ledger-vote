from flask import request

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.enums import ActorType


def log_action(
    actor_type: ActorType,
    action: str,
    actor_id=None,
    details: dict | None = None,
) -> None:
    """
    Writes one audit log row. Called from services after (not before) the
    action succeeds/fails is determined, so `action` strings should be
    specific, e.g. "auth.login_success", "auth.login_failed",
    "voter.registered", "election.created".

    Never raises — an audit-logging failure must not break the primary
    request. Errors are logged and swallowed.
    """
    try:
        entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            details=details or {},
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
        # Intentionally not re-raised — audit logging is best-effort and
        # must never be the reason a legitimate request fails.
        import logging
        logging.getLogger(__name__).exception("Failed to write audit log for action=%s", action)
