from flask import Blueprint, request

from app.middleware.auth_middleware import election_admin_required
from app.models.audit_log import AuditLog
from app.utils.pagination import parse_pagination_args
from app.utils.responses import success, error

audit_bp = Blueprint("audit", __name__)


def _audit_log_dict(log: AuditLog) -> dict:
    return {
        "id": str(log.id),
        "actor_type": log.actor_type.value,
        "actor_id": str(log.actor_id) if log.actor_id else None,
        "action": log.action,
        "details": log.details,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat(),
    }


@audit_bp.get("")
@election_admin_required
def list_audit_logs():
    page, per_page = parse_pagination_args(request, default_per_page=50)
    action = request.args.get("action")

    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return success(
        {
            "items": [_audit_log_dict(a) for a in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
            },
        }
    )
