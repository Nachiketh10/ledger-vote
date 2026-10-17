from flask import Blueprint, request

from app.middleware.auth_middleware import election_admin_required, current_identity
from app.models.candidate import Candidate
from app.models.enums import ActorType
from app.schemas.candidate_schema import CandidateCreateSchema, CandidateUpdateSchema
from app.services import election_service, candidate_service
from app.services.election_service import ElectionError
from app.utils.responses import success, error

candidate_bp = Blueprint("candidates", __name__)

_role_to_actor_type = {
    "super_admin": ActorType.SUPER_ADMIN,
    "election_admin": ActorType.ELECTION_ADMIN,
}


def _public_candidate(candidate: Candidate) -> dict:
    return {
        "id": str(candidate.id),
        "election_id": str(candidate.election_id),
        "name": candidate.name,
        "party": candidate.party,
        "photo_url": candidate.photo_url,
        "description": candidate.description,
    }


@candidate_bp.get("/elections/<uuid:election_id>/candidates")
def list_candidates(election_id):
    """Public — voters need to see candidates to vote, and the landing
    page may show them too."""
    try:
        election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    candidates = candidate_service.list_candidates(str(election_id))
    return success([_public_candidate(c) for c in candidates])


@candidate_bp.post("/elections/<uuid:election_id>/candidates")
@election_admin_required
def add_candidate(election_id):
    try:
        election = election_service.get_election_or_404(str(election_id))
    except ElectionError as err:
        return error(err.message, err.status)

    user_id, role = current_identity()
    if not election_service.user_can_manage_election(election, role, user_id):
        return error("You do not have permission to manage this election.", 403)

    schema = CandidateCreateSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    try:
        candidate = candidate_service.add_candidate(election, data, _role_to_actor_type[role], user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_public_candidate(candidate), message="Candidate added.", status=201)


@candidate_bp.put("/candidates/<uuid:candidate_id>")
@election_admin_required
def update_candidate(candidate_id):
    try:
        candidate = candidate_service.get_candidate_or_404(str(candidate_id))
    except ElectionError as err:
        return error(err.message, err.status)

    user_id, role = current_identity()
    if not election_service.user_can_manage_election(candidate.election, role, user_id):
        return error("You do not have permission to manage this election.", 403)

    schema = CandidateUpdateSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    try:
        candidate = candidate_service.update_candidate(candidate, data, _role_to_actor_type[role], user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(_public_candidate(candidate), message="Candidate updated.")


@candidate_bp.delete("/candidates/<uuid:candidate_id>")
@election_admin_required
def delete_candidate(candidate_id):
    try:
        candidate = candidate_service.get_candidate_or_404(str(candidate_id))
    except ElectionError as err:
        return error(err.message, err.status)

    user_id, role = current_identity()
    if not election_service.user_can_manage_election(candidate.election, role, user_id):
        return error("You do not have permission to manage this election.", 403)

    try:
        candidate_service.delete_candidate(candidate, _role_to_actor_type[role], user_id)
    except ElectionError as err:
        return error(err.message, err.status)

    return success(message="Candidate deleted.")
