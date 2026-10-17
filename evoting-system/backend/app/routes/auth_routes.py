from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError

from app.extensions import limiter
from app.schemas.auth_schema import VoterRegisterSchema, LoginSchema
from app.services import auth_service
from app.services.audit_service import log_action
from app.services.auth_service import AuthError
from app.models.enums import ActorType
from app.middleware.rate_limiter import LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT, REFRESH_RATE_LIMIT
from app.utils.responses import success, error

auth_bp = Blueprint("auth", __name__)

_role_to_actor_type = {
    "super_admin": ActorType.SUPER_ADMIN,
    "election_admin": ActorType.ELECTION_ADMIN,
    "voter": ActorType.VOTER,
}


def _public_user(user, role: str) -> dict:
    base = {"id": str(user.id), "name": user.name, "email": user.email, "role": role}
    if role == "voter":
        base.update(
            {
                "voter_id": user.voter_id,
                "is_verified": user.is_verified,
                "has_face_registered": user.has_face_registered,
            }
        )
    return base


@auth_bp.post("/register")
@limiter.limit(REGISTER_RATE_LIMIT)
def register():
    """Voter self-registration only. Admin/ElectionAdmin accounts are
    created by a Super Admin via the admin management routes (Part 4),
    never through this public endpoint.

    Auto-logs-in the newly created voter (issues tokens immediately,
    same as /login) so the frontend can continue straight into face
    registration without a separate login step."""
    schema = VoterRegisterSchema()
    try:
        data = schema.load(request.get_json(force=True, silent=True) or {})
    except ValidationError as err:
        return error("Validation failed.", 422, errors=err.messages)

    try:
        voter = auth_service.register_voter(data)
    except AuthError as err:
        return error(err.message, err.status)

    tokens = auth_service.issue_tokens(voter, "voter", device_info=request.headers.get("User-Agent"))
    log_action(ActorType.VOTER, "auth.register_success", actor_id=voter.id)

    return success(
        {**tokens, "user": _public_user(voter, "voter")},
        message="Registration successful. Your account is pending admin verification "
        "before you can vote.",
        status=201,
    )


@auth_bp.post("/login")
@limiter.limit(LOGIN_RATE_LIMIT)
def login():
    schema = LoginSchema()
    try:
        data = schema.load(request.get_json(force=True, silent=True) or {})
    except ValidationError as err:
        return error("Validation failed.", 422, errors=err.messages)

    role = data["role"]
    try:
        user = auth_service.authenticate(data["email"], data["password"], role)
    except AuthError as err:
        log_action(
            _role_to_actor_type[role],
            "auth.login_failed",
            details={"email": data["email"], "reason": err.message},
        )
        return error(err.message, err.status)

    tokens = auth_service.issue_tokens(user, role, device_info=request.headers.get("User-Agent"))
    log_action(_role_to_actor_type[role], "auth.login_success", actor_id=user.id)

    return success(
        {**tokens, "user": _public_user(user, role)},
        message="Login successful.",
    )


@auth_bp.post("/refresh")
@limiter.limit(REFRESH_RATE_LIMIT)
@jwt_required(refresh=True)
def refresh():
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    presented_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    user = auth_service.get_user_by_id_and_role(user_id, role)
    if not user:
        return error("Account no longer exists.", 401)

    try:
        tokens = auth_service.refresh_tokens(user, role, presented_token)
    except AuthError as err:
        return error(err.message, err.status)

    log_action(_role_to_actor_type[role], "auth.token_refreshed", actor_id=user.id)
    return success(tokens, message="Token refreshed.")


@auth_bp.post("/logout")
@jwt_required(refresh=True)
def logout():
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    presented_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    auth_service.revoke_session_by_refresh_token(presented_token)

    log_action(_role_to_actor_type.get(role, ActorType.SYSTEM), "auth.logout", actor_id=user_id)
    return success(message="Logged out successfully.")


@auth_bp.get("/me")
@jwt_required()
def me():
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    user = auth_service.get_user_by_id_and_role(user_id, role)
    if not user:
        return error("Account not found.", 404)

    return success(_public_user(user, role))
