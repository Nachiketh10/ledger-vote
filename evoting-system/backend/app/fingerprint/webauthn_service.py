"""
WebAuthn (platform biometrics — Windows Hello, Touch ID, Android
fingerprint) registration and authentication.

HONESTY NOTE: unlike face recognition (Part 5), I cannot execute a real
WebAuthn ceremony in this environment — it fundamentally requires a
browser calling navigator.credentials.create()/get() against a real
platform authenticator, which no sandbox or script can simulate. This
module is written carefully against the documented `webauthn` (py_webauthn
v2.x) API, but it is the one piece of this project most likely to need a
small adjustment once you actually exercise it. Use the standalone test
page (scripts/webauthn_test.html) to verify it in isolation before it's
wired into the React frontend in Part 8 — the same "prove it in isolation
first" approach used for the face recognition stack.

Stateless challenge handling: WebAuthn requires the server to remember
the random challenge it issued and check the browser's response against
it. Rather than server-side sessions (which would break the stateless
JWT architecture used everywhere else in this app), the challenge is
signed and time-limited with itsdangerous and handed back to the client
as an opaque "state" string, which the client returns unmodified on the
verify call. The signature means the client can't forge or tamper with
it, and the server never has to store anything in between.
"""

import base64

from flask import current_app
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired

from app.extensions import db
from app.models.fingerprint_template import FingerprintTemplate
from app.models.voter import Voter
from app.utils.errors import AppError


class FingerprintError(AppError):
    pass


def _b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _b64u_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded)


def _sign_state(voter_id, challenge: bytes, purpose: str) -> str:
    signer = TimestampSigner(current_app.config["SECRET_KEY"], salt=f"webauthn-{purpose}")
    payload = f"{_b64u_encode(challenge)}:{voter_id}"
    return signer.sign(payload.encode()).decode()


def _unsign_state(state: str, voter_id, purpose: str) -> bytes:
    signer = TimestampSigner(current_app.config["SECRET_KEY"], salt=f"webauthn-{purpose}")
    max_age = current_app.config["WEBAUTHN_CHALLENGE_TTL_SECONDS"]
    try:
        payload = signer.unsign(state.encode(), max_age=max_age).decode()
    except SignatureExpired as exc:
        raise FingerprintError("This registration/verification attempt has expired. Please try again.", 400) from exc
    except BadSignature as exc:
        raise FingerprintError("Invalid state token.", 400) from exc

    challenge_b64u, bound_voter_id = payload.rsplit(":", 1)
    if bound_voter_id != str(voter_id):
        raise FingerprintError("This challenge does not belong to the current user.", 403)
    return _b64u_decode(challenge_b64u)


# ---------------- Registration ----------------

def generate_registration_options_for_voter(voter: Voter) -> dict:
    from webauthn import generate_registration_options, options_to_json
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        UserVerificationRequirement,
        ResidentKeyRequirement,
    )

    existing = FingerprintTemplate.query.filter_by(voter_id=voter.id).first()
    if existing and existing.auth_method == "webauthn":
        raise FingerprintError(
            "A fingerprint credential is already registered for this voter. "
            "Delete the existing registration before registering a new one.",
            409,
        )

    options = generate_registration_options(
        rp_id=current_app.config["WEBAUTHN_RP_ID"],
        rp_name=current_app.config["WEBAUTHN_RP_NAME"],
        user_id=str(voter.id).encode(),
        user_name=voter.email,
        user_display_name=voter.name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.REQUIRED,
            resident_key=ResidentKeyRequirement.PREFERRED,
        ),
    )

    state = _sign_state(voter.id, options.challenge, "register")
    return {"options": options_to_json(options), "state": state}


def verify_registration_for_voter(voter: Voter, credential_json: str, state: str) -> FingerprintTemplate:
    from webauthn import verify_registration_response
    from webauthn.helpers.exceptions import InvalidRegistrationResponse

    challenge = _unsign_state(state, voter.id, "register")

    try:
        verification = verify_registration_response(
            credential=credential_json,
            expected_challenge=challenge,
            expected_origin=current_app.config["WEBAUTHN_ORIGIN"],
            expected_rp_id=current_app.config["WEBAUTHN_RP_ID"],
            require_user_verification=True,
        )
    except InvalidRegistrationResponse as exc:
        raise FingerprintError(f"Fingerprint registration failed verification: {exc}", 400) from exc

    existing = FingerprintTemplate.query.filter_by(voter_id=voter.id).first()
    if existing:
        row = existing
    else:
        row = FingerprintTemplate(voter_id=voter.id)
        db.session.add(row)

    row.auth_method = "webauthn"
    row.credential_id = _b64u_encode(verification.credential_id)
    row.public_key = _b64u_encode(verification.credential_public_key)
    row.sign_count = verification.sign_count

    voter.has_fingerprint_registered = True
    db.session.commit()
    return row


# ---------------- Authentication (verification at vote time) ----------------

def generate_authentication_options_for_voter(voter: Voter) -> dict:
    from webauthn import generate_authentication_options, options_to_json
    from webauthn.helpers.structs import PublicKeyCredentialDescriptor, UserVerificationRequirement

    template = FingerprintTemplate.query.filter_by(voter_id=voter.id).first()
    if not template or template.auth_method != "webauthn" or not template.credential_id:
        raise FingerprintError("No fingerprint registered for this voter. Registration is required first.", 409)

    options = generate_authentication_options(
        rp_id=current_app.config["WEBAUTHN_RP_ID"],
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=_b64u_decode(template.credential_id))
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    state = _sign_state(voter.id, options.challenge, "authenticate")
    return {"options": options_to_json(options), "state": state}


def verify_authentication_for_voter(voter: Voter, credential_json: str, state: str) -> bool:
    from webauthn import verify_authentication_response
    from webauthn.helpers.exceptions import InvalidAuthenticationResponse

    template = FingerprintTemplate.query.filter_by(voter_id=voter.id).first()
    if not template or template.auth_method != "webauthn":
        raise FingerprintError("No fingerprint registered for this voter.", 409)

    challenge = _unsign_state(state, voter.id, "authenticate")

    try:
        verification = verify_authentication_response(
            credential=credential_json,
            expected_challenge=challenge,
            expected_rp_id=current_app.config["WEBAUTHN_RP_ID"],
            expected_origin=current_app.config["WEBAUTHN_ORIGIN"],
            credential_public_key=_b64u_decode(template.public_key),
            credential_current_sign_count=template.sign_count,
            require_user_verification=True,
        )
    except InvalidAuthenticationResponse as exc:
        raise FingerprintError(f"Fingerprint verification failed: {exc}", 401) from exc

    # Anti-replay: the authenticator's sign_count must have increased
    # (some authenticators, mostly platform ones like Touch ID, always
    # report 0 and never increment it — that's a known, accepted quirk of
    # the WebAuthn spec itself, not a bug here, so 0->0 is allowed).
    if verification.new_sign_count != 0 and verification.new_sign_count <= template.sign_count:
        raise FingerprintError(
            "Fingerprint verification rejected: authenticator sign count did not "
            "increase, which can indicate a cloned/replayed credential.",
            401,
        )

    template.sign_count = verification.new_sign_count
    db.session.commit()
    return True
