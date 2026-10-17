from flask import Blueprint, request

from app.extensions import limiter
from app.middleware.auth_middleware import voter_required, current_identity
from app.middleware.rate_limiter import VOTE_RATE_LIMIT
from app.models.voter import Voter
from app.schemas.vote_schema import CastVoteSchema
from app.services import vote_service
from app.services.vote_service import VoteError
from app.face.image_utils import decode_base64_image
from app.utils.responses import success, error

vote_bp = Blueprint("vote", __name__)


def _current_voter() -> Voter | None:
    user_id, _ = current_identity()
    return Voter.query.get(user_id)


@vote_bp.get("/elections/<uuid:election_id>/vote-status")
@voter_required
def vote_status(election_id):
    voter = _current_voter()
    if not voter:
        return error("Voter not found.", 404)

    try:
        status = vote_service.get_vote_status(voter, str(election_id))
    except VoteError as err:
        return error(err.message, err.status)

    return success(status)


@vote_bp.post("/elections/<uuid:election_id>/vote")
@voter_required
@limiter.limit(VOTE_RATE_LIMIT)
def cast_vote(election_id):
    voter = _current_voter()
    if not voter:
        return error("Voter not found.", 404)

    schema = CastVoteSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    try:
        frames = [decode_base64_image(img) for img in data["face_images"]]
    except ValueError as exc:
        return error(f"Could not decode a face image: {exc}", 422)

    try:
        result = vote_service.cast_vote(voter, str(election_id), data["candidate_id"], frames)
    except VoteError as err:
        return error(err.message, err.status)

    return success(
        {"block_index": result.block_index, "transaction_id": result.transaction_id},
        message=result.message,
        status=201,
    )
