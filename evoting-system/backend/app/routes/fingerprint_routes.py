from flask import Blueprint, request

from app.middleware.auth_middleware import voter_required, current_identity
from app.models.voter import Voter
from app.schemas.fingerprint_schema import WebAuthnVerifySchema
from app.fingerprint import webauthn_service
from app.fingerprint.webauthn_service import FingerprintError
from app.utils.responses import success, error

fingerprint_bp = Blueprint("fingerprint", __name__)


def _current_voter() -> Voter | None:
    user_id, _ = current_identity()
    return Voter.query.get(user_id)


@fingerprint_bp.post("/register/options")
@voter_required
def register_options():
    voter = _current_voter()
    if not voter:
        return error("Voter not found.", 404)
    try:
        result = webauthn_service.generate_registration_options_for_voter(voter)
    except FingerprintError as err:
        return error(err.message, err.status)
    return success(result)


@fingerprint_bp.post("/register/verify")
@voter_required
def register_verify():
    voter = _current_voter()
    if not voter:
        return error("Voter not found.", 404)

    schema = WebAuthnVerifySchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    try:
        webauthn_service.verify_registration_for_voter(voter, data["credential"], data["state"])
    except FingerprintError as err:
        return error(err.message, err.status)

    return success(message="Fingerprint registered successfully.", status=201)


@fingerprint_bp.post("/verify/options")
@voter_required
def verify_options():
    voter = _current_voter()
    if not voter:
        return error("Voter not found.", 404)
    try:
        result = webauthn_service.generate_authentication_options_for_voter(voter)
    except FingerprintError as err:
        return error(err.message, err.status)
    return success(result)


@fingerprint_bp.post("/verify/verify")
@voter_required
def verify_verify():
    voter = _current_voter()
    if not voter:
        return error("Voter not found.", 404)

    schema = WebAuthnVerifySchema()
    data = schema.load(request.get_json(force=True, silent=True) or {})

    try:
        webauthn_service.verify_authentication_for_voter(voter, data["credential"], data["state"])
    except FingerprintError as err:
        return error(err.message, err.status)

    return success(message="Fingerprint verified successfully.")
