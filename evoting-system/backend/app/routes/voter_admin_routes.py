from flask import Blueprint, request

from app.middleware.auth_middleware import election_admin_required, current_identity
from app.models.voter import Voter
from app.models.enums import ActorType
from app.schemas.voter_schema import VoterVerifyActionSchema, VoterSuspendActionSchema
from app.services import voter_admin_service
from app.services.election_service import ElectionError
from app.utils.pagination import parse_pagination_args
from app.utils.responses import success, error

voter_admin_bp = Blueprint("voter_admin", __name__)

_role_to_actor_type = {
    "super_admin": ActorType.SUPER_ADMIN,
    "election_admin": ActorType.ELECTION_ADMIN,
}


def _admin_voter_view(voter: Voter) -> dict:
    return {
        "id": str(voter.id),
        "voter_id": voter.voter_id,
        "name": voter.name,
        "email": voter.email,
        "phone": voter.phone,
        "dob": voter.dob.isoformat(),
        "gender": voter.gender,
        "address": voter.address,
        "is_verified": voter.is_verified,
        "is_active": voter.is_active,
        "has_face_registered": voter.has_face_registered,
        "failed_login_attempts": voter.failed_login_attempts,
        "account_locked_until": voter.account_locked_until.isoformat() if voter.account_locked_until else None,
        "created_at": voter.created_at.isoformat(),
        "last_login_at": voter.last_login_at.isoformat() if voter.last_login_at else None,
    }


@voter_admin_bp.get("")
@election_admin_required
def list_voters():
    page, per_page = parse_pagination_args(request)
    is_verified = request.args.get("is_verified")
    is_active = request.args.get("is_active")
    search = request.args.get("search")

    def _parse_bool(v):
        if v is None:
            return None
        return v.lower() in ("1", "true", "yes")

    pagination = voter_admin_service.list_voters(
        is_verified=_parse_bool(is_verified),
        is_active=_parse_bool(is_active),
        search=search,
        page=page,
        per_page=per_page,
    )
    return success(
        {
            "items": [_admin_voter_view(v) for v in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
            },
        }
    )


@voter_admin_bp.get("/<uuid:voter_id>")
@election_admin_required
def get_voter(voter_id):
    try:
        voter = voter_admin_service.get_voter_or_404(str(voter_id))
    except ElectionError as err:
        return error(err.message, err.status)
    return success(_admin_voter_view(voter))


@voter_admin_bp.post("/<uuid:voter_id>/verify")
@election_admin_required
def verify_voter(voter_id):
    try:
        voter = voter_admin_service.get_voter_or_404(str(voter_id))
    except ElectionError as err:
        return error(err.message, err.status)

    schema = VoterVerifyActionSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    user_id, role = current_identity()
    try:
        voter = voter_admin_service.verify_voter(
            voter, _role_to_actor_type[role], user_id, note=data.get("note")
        )
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_admin_voter_view(voter), message="Voter verified and eligible to be added to elections.")


@voter_admin_bp.post("/<uuid:voter_id>/suspend")
@election_admin_required
def suspend_voter(voter_id):
    try:
        voter = voter_admin_service.get_voter_or_404(str(voter_id))
    except ElectionError as err:
        return error(err.message, err.status)

    schema = VoterSuspendActionSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    user_id, role = current_identity()
    voter = voter_admin_service.suspend_voter(voter, _role_to_actor_type[role], user_id, reason=data["reason"])
    return success(_admin_voter_view(voter), message="Voter suspended.")


@voter_admin_bp.post("/<uuid:voter_id>/reactivate")
@election_admin_required
def reactivate_voter(voter_id):
    try:
        voter = voter_admin_service.get_voter_or_404(str(voter_id))
    except ElectionError as err:
        return error(err.message, err.status)

    user_id, role = current_identity()
    voter = voter_admin_service.reactivate_voter(voter, _role_to_actor_type[role], user_id)
    return success(_admin_voter_view(voter), message="Voter reactivated.")


@voter_admin_bp.post("/<uuid:voter_id>/revoke-sessions")
@election_admin_required
def revoke_voter_sessions(voter_id):
    """
    Force-logs-out a voter from every active session — e.g. to clear a
    'multiple sessions' fraud flag after confirming it was a legitimate
    mistake (forgot to log out elsewhere), or in response to a lost/
    stolen device report.
    """
    try:
        voter = voter_admin_service.get_voter_or_404(str(voter_id))
    except ElectionError as err:
        return error(err.message, err.status)

    user_id, role = current_identity()
    count = voter_admin_service.revoke_all_sessions(voter, _role_to_actor_type[role], user_id)
    return success({"revoked_count": count}, message=f"Revoked {count} active session(s).")


@voter_admin_bp.post("/<uuid:voter_id>/reset-biometrics")
@election_admin_required
def reset_voter_biometrics(voter_id):
    """
    Deletes the voter's stored face embedding so they can re-enroll
    from scratch — e.g. poor-quality original enrollment. Does not
    affect vote history, sessions, or verification status.
    """
    try:
        voter = voter_admin_service.get_voter_or_404(str(voter_id))
    except ElectionError as err:
        return error(err.message, err.status)

    user_id, role = current_identity()
    removed = voter_admin_service.reset_biometrics(voter, _role_to_actor_type[role], user_id)
    return success(removed, message="Biometric enrollment reset. Voter can re-register.")
