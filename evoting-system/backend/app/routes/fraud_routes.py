from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth_middleware import election_admin_required, current_identity
from app.models.fraud_log import FraudLog
from app.models.enums import FraudSeverity
from app.utils.pagination import parse_pagination_args
from app.utils.responses import success, error
from datetime import datetime, timezone

fraud_bp = Blueprint("fraud", __name__)


def _fraud_log_dict(log: FraudLog) -> dict:
    return {
        "id": str(log.id),
        "voter_id": str(log.voter_id) if log.voter_id else None,
        "election_id": str(log.election_id) if log.election_id else None,
        "fraud_type": log.fraud_type.value,
        "severity": log.severity.value,
        "fraud_score": log.fraud_score,
        "description": log.description,
        "is_resolved": log.is_resolved,
        "resolution_notes": log.resolution_notes,
        "created_at": log.created_at.isoformat(),
    }


@fraud_bp.get("")
@election_admin_required
def list_fraud_logs():
    page, per_page = parse_pagination_args(request)
    severity = request.args.get("severity")
    is_resolved = request.args.get("is_resolved")

    query = FraudLog.query.order_by(FraudLog.created_at.desc())
    if severity:
        try:
            query = query.filter(FraudLog.severity == FraudSeverity(severity))
        except ValueError:
            return error(f"Invalid severity '{severity}'.", 422)
    if is_resolved is not None:
        query = query.filter(FraudLog.is_resolved == (is_resolved.lower() in ("1", "true", "yes")))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return success(
        {
            "items": [_fraud_log_dict(f) for f in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
            },
        }
    )


@fraud_bp.post("/<uuid:fraud_log_id>/resolve")
@election_admin_required
def resolve_fraud_log(fraud_log_id):
    log = FraudLog.query.get(str(fraud_log_id))
    if not log:
        return error("Fraud log not found.", 404)

    data = request.get_json(force=True, silent=True) or {}
    user_id, _ = current_identity()

    log.is_resolved = True
    log.resolved_by_id = user_id
    log.resolved_at = datetime.now(timezone.utc)
    log.resolution_notes = data.get("notes")
    db.session.commit()

    return success(_fraud_log_dict(log), message="Fraud log marked resolved.")
