from flask import Blueprint, request

from app.extensions import limiter
from app.middleware.auth_middleware import voter_required, current_identity
from app.middleware.rate_limiter import FACE_VERIFY_RATE_LIMIT
from app.models.voter import Voter
from app.schemas.face_schema import FaceRegisterSchema, FaceVerifySchema
from app.services import face_service
from app.services.face_service import FaceError
from app.face.image_utils import decode_base64_image
from app.utils.responses import success, error

face_bp = Blueprint("face", __name__)


def _decode_frames(image_list: list[str]):
    frames = []
    for i, img_b64 in enumerate(image_list):
        try:
            frames.append(decode_base64_image(img_b64))
        except ValueError as exc:
            raise FaceError(f"Image {i + 1} could not be decoded: {exc}", 422)
    return frames


@face_bp.post("/register")
@voter_required
@limiter.limit(FACE_VERIFY_RATE_LIMIT)
def register_face():
    user_id, _ = current_identity()
    voter = Voter.query.get(user_id)
    if not voter:
        return error("Voter not found.", 404)

    schema = FaceRegisterSchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    try:
        frames = _decode_frames(data["images"])
        face_service.register_face(voter, frames)
    except FaceError as err:
        return error(err.message, err.status)

    return success(message="Face registered successfully.", status=201)


@face_bp.post("/verify")
@voter_required
@limiter.limit(FACE_VERIFY_RATE_LIMIT)
def verify_face():
    user_id, _ = current_identity()
    voter = Voter.query.get(user_id)
    if not voter:
        return error("Voter not found.", 404)

    schema = FaceVerifySchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    try:
        frames = _decode_frames(data["images"])
        outcome = face_service.verify_face(voter, frames, election_id=data.get("election_id"))
    except FaceError as err:
        return error(err.message, err.status)

    if not outcome.success:
        return error(outcome.reason, 401, errors={"similarity": outcome.similarity})

    return success({"similarity": outcome.similarity}, message="Face verified successfully.")
