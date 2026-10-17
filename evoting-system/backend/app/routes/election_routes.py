from flask import Blueprint, request

from app.middleware.auth_middleware import election_admin_required, super_admin_required, current_identity
from app.models.election import Election
from app.models.enums import ActorType
from app.schemas.election_schema import (
    ElectionCreateSchema,
    ElectionUpdateSchema,
    EligibleVoterUpdateSchema,
)
from app.services import election_service
from app.services.election_service import ElectionError
from app.utils.pagination import parse_pagination_args
from app.utils.responses import success, error

election_bp = Blueprint("elections", __name__)

_role_to_actor_type = {
    "super_admin": ActorType.SUPER_ADMIN,
    "election_admin": ActorType.ELECTION_ADMIN,
}


def _public_election(election: Election) -> dict:
    """Safe for any authenticated user (or the public landing page) to see —
    no eligible-voter list, no assigned-admin details."""
    return {
        "id": str(election.id),
        "title": election.title,
        "description": election.description,
        "start_date": election.start_date.isoformat(),
        "end_date": election.end_date.isoformat(),
        "status": election.status.value,
        "candidate_count": len(election.candidates),
    }


def _admin_election(election: Election) -> dict:
    data = _public_election(election)
    data.update(
        {
            "eligible_voter_count": len(election.eligible_voters),
            "assigned_admin_ids": [str(a.id) for a in election.assigned_admins],
            "created_by_id": str(election.created_by_id) if election.created_by_id else None,
            "created_at": election.created_at.isoformat(),
            "updated_at": election.updated_at.isoformat(),
        }
    )
    return data


def _require_manage_permission(election: Election):
    user_id, role = current_identity()
    if not election_service.user_can_manage_election(election, role, user_id):
        return error(
            "You do not have permission to manage this election. "
            "Election Admins may only manage elections assigned to them.",
            403,
        )
    return None


# ---------- Public / any-authenticated reads ----------

@election_bp.get("")
def list_elections():
    """Public. Only non-draft elections are visible outside the admin
    panel — drafts are internal working state."""
    status_filter = request.args.get("status")
    page, per_page = parse_pagination_args(request)

    try:
        pagination = election_service.list_elections(status=status_filter, page=page, per_page=per_page)
    except ElectionError as err:
        return error(err.message, err.status)

    visible = [e for e in pagination.items if e.status.value != "draft"]
    return success(
        {
            "items": [_public_election(e) for e in visible],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
            },
        }
    )


@election_bp.get("/<uuid:election_id>")
def get_election(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    if election.status.value == "draft":
        return error("Election not found.", 404)  # don't leak draft existence publicly

    return success(_public_election(election))


# ---------- Admin management ----------

@election_bp.get("/admin/<uuid:election_id>")
@election_admin_required
def get_election_admin_view(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    forbidden = _require_manage_permission(election)
    if forbidden:
        return forbidden

    return success(_admin_election(election))


@election_bp.get("/admin")
@election_admin_required
def list_elections_admin():
    status_filter = request.args.get("status")
    page, per_page = parse_pagination_args(request)
    user_id, role = current_identity()

    try:
        pagination = election_service.list_elections(status=status_filter, page=page, per_page=per_page)
    except ElectionError as err:
        return error(err.message, err.status)

    visible = [
        e for e in pagination.items
        if election_service.user_can_manage_election(e, role, user_id)
    ]
    return success({"items": [_admin_election(e) for e in visible]})


@election_bp.post("")
@super_admin_required
def create_election():
    schema = ElectionCreateSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    # Only Super Admins can reach this route now, so created_by_id (which
    # exists to auto-assign an Election Admin who creates their own
    # election) is always None here — assignment happens explicitly via
    # POST /<id>/assign-admin instead.
    election = election_service.create_election(data, created_by_id=None)
    return success(_admin_election(election), message="Election created.", status=201)


@election_bp.put("/<uuid:election_id>")
@election_admin_required
def update_election(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    forbidden = _require_manage_permission(election)
    if forbidden:
        return forbidden

    schema = ElectionUpdateSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    user_id, role = current_identity()
    try:
        election = election_service.update_election(election, data, _role_to_actor_type[role], user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_admin_election(election), message="Election updated.")


@election_bp.delete("/<uuid:election_id>")
@election_admin_required
def delete_election(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    forbidden = _require_manage_permission(election)
    if forbidden:
        return forbidden

    user_id, role = current_identity()
    try:
        election_service.delete_election(election, _role_to_actor_type[role], user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(message="Election deleted.")


def _lifecycle_action(election_id, action: str):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    forbidden = _require_manage_permission(election)
    if forbidden:
        return forbidden

    user_id, role = current_identity()
    try:
        election = election_service.apply_action(election, action, _role_to_actor_type[role], user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_admin_election(election), message=f"Election {action}ed." if action != "close" else "Election closed.")


@election_bp.post("/<uuid:election_id>/start")
@election_admin_required
def start_election(election_id):
    return _lifecycle_action(election_id, "start")


@election_bp.post("/<uuid:election_id>/pause")
@election_admin_required
def pause_election(election_id):
    return _lifecycle_action(election_id, "pause")


@election_bp.post("/<uuid:election_id>/resume")
@election_admin_required
def resume_election(election_id):
    return _lifecycle_action(election_id, "resume")


@election_bp.post("/<uuid:election_id>/close")
@election_admin_required
def close_election(election_id):
    return _lifecycle_action(election_id, "close")


@election_bp.put("/<uuid:election_id>/eligible-voters")
@election_admin_required
def set_eligible_voters(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    forbidden = _require_manage_permission(election)
    if forbidden:
        return forbidden

    schema = EligibleVoterUpdateSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    user_id, role = current_identity()
    try:
        election = election_service.set_eligible_voters(
            election, data["voter_ids"], _role_to_actor_type[role], user_id
        )
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_admin_election(election), message="Eligible voters updated.")


# ---------- Election Admin assignment (Super Admin only) ----------

@election_bp.get("/election-admins")
@super_admin_required
def list_election_admins():
    """Populates the assignment picker — every Election Admin account
    that exists, regardless of what they're currently assigned to."""
    admins = election_service.list_election_admins()
    return success(
        [{"id": str(a.id), "name": a.name, "email": a.email} for a in admins]
    )


@election_bp.post("/<uuid:election_id>/assign-admin")
@super_admin_required
def assign_admin(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    data = request.get_json(force=True, silent=True) or {}
    election_admin_id = data.get("election_admin_id")
    if not election_admin_id:
        return error("election_admin_id is required.", 422)

    user_id, _ = current_identity()
    try:
        election = election_service.assign_admin_to_election(election, election_admin_id, user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_admin_election(election), message="Election Admin assigned.")


@election_bp.post("/<uuid:election_id>/unassign-admin")
@super_admin_required
def unassign_admin(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    data = request.get_json(force=True, silent=True) or {}
    election_admin_id = data.get("election_admin_id")
    if not election_admin_id:
        return error("election_admin_id is required.", 422)

    user_id, _ = current_identity()
    try:
        election = election_service.unassign_admin_from_election(election, election_admin_id, user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_admin_election(election), message="Election Admin unassigned.")
