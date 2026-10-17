"""
Core authentication business logic. Kept out of routes so it's directly
unit-testable and reusable (e.g. seed scripts can call register_voter
without going through HTTP).
"""

import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db
from app.models.admin import Admin, ElectionAdmin
from app.models.voter import Voter
from app.models.session import Session
from app.models.fraud_log import FraudLog
from app.models.enums import SessionUserType, FraudType, FraudSeverity, ActorType
from app.services.audit_service import log_action

# Maps the role string used everywhere in the API to (Model, SessionUserType)
_ROLE_MAP = {
    "super_admin": (Admin, SessionUserType.ADMIN),
    "election_admin": (ElectionAdmin, SessionUserType.ELECTION_ADMIN),
    "voter": (Voter, SessionUserType.VOTER),
}


from app.utils.errors import AppError


class AuthError(AppError):
    """Raised for any auth failure with a client-safe message."""

    def __init__(self, message: str, status: int = 401):
        super().__init__(message, status)


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _hash_token(token: str) -> str:
    """We never store raw refresh tokens — only their SHA-256 hash, so a DB
    leak alone can't be used to forge sessions."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register_voter(data: dict) -> Voter:
    """
    Self-registration. is_verified starts False — an Election Admin (or
    Super Admin) must approve the voter before they're eligible to vote
    in any election (wired up in Part 4: Voter Registration admin flow).
    """
    if Voter.query.filter_by(email=data["email"]).first():
        raise AuthError("An account with this email already exists.", 409)
    if Voter.query.filter_by(voter_id=data["voter_id"]).first():
        raise AuthError("This Voter ID is already registered.", 409)

    voter = Voter(
        voter_id=data["voter_id"],
        name=data["name"],
        dob=data["dob"],
        gender=data.get("gender"),
        phone=data["phone"],
        email=data["email"],
        address=data.get("address"),
        password_hash=hash_password(data["password"]),
        is_verified=False,
        is_active=True,
    )
    db.session.add(voter)
    db.session.commit()

    log_action(ActorType.VOTER, "voter.registered", actor_id=voter.id, details={"email": voter.email})
    return voter


def _is_locked(user) -> bool:
    if not getattr(user, "account_locked_until", None):
        return False
    return user.account_locked_until > datetime.now(timezone.utc)


def _register_failed_attempt(user, role: str) -> None:
    """Only Voter rows track failed_login_attempts/lockout in this schema
    (Admin/ElectionAdmin are lower-volume, staff-managed accounts). Extend
    similarly for admins if you want the same lockout behavior there."""
    if role != "voter":
        return

    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    max_attempts = current_app.config["MAX_FAILED_AUTH_ATTEMPTS"]

    if user.failed_login_attempts >= max_attempts:
        lock_minutes = 15
        user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
        db.session.add(
            FraudLog(
                voter_id=user.id,
                fraud_type=FraudType.EXCESSIVE_FAILED_ATTEMPTS,
                severity=FraudSeverity.HIGH,
                fraud_score=70,
                description=f"{user.failed_login_attempts} failed login attempts; account locked {lock_minutes}m.",
            )
        )
    db.session.commit()


def authenticate(email: str, password: str, role: str):
    """
    Returns the authenticated user row on success.
    Raises AuthError (401/403/423) on any failure — messages are
    deliberately generic ("Invalid credentials") to avoid confirming
    whether an email exists (prevents user enumeration).
    """
    model, _ = _ROLE_MAP[role]
    user = model.query.filter_by(email=email.lower().strip()).first()

    # Constant-shape response whether or not the user exists, to resist
    # timing/enumeration attacks: always run a bcrypt comparison.
    dummy_hash = "$2b$12$CwTycUXWue0Thq9StjUM0uJ8lWt0aQqL1lQ4Q1w1w1w1w1w1w1w1u"
    password_hash = user.password_hash if user else dummy_hash
    password_ok = verify_password(password, password_hash)

    if not user or not user.is_active:
        raise AuthError("Invalid credentials.", 401)

    if _is_locked(user):
        raise AuthError("Account temporarily locked due to repeated failed attempts.", 423)

    if not password_ok:
        _register_failed_attempt(user, role)
        raise AuthError("Invalid credentials.", 401)

    if role == "voter":
        user.failed_login_attempts = 0
        user.account_locked_until = None

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()
    return user


def issue_tokens(user, role: str, device_info: str | None = None) -> dict:
    identity = str(user.id)
    additional_claims = {"role": role, "email": user.email}

    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=identity, additional_claims=additional_claims)

    _, session_user_type = _ROLE_MAP[role]
    session = Session(
        voter_id=user.id if role == "voter" else None,
        admin_id=user.id if role != "voter" else None,
        user_type=session_user_type,
        refresh_token_hash=_hash_token(refresh_token),
        device_fingerprint=device_info,
        expires_at=datetime.now(timezone.utc) + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
    )
    db.session.add(session)
    db.session.commit()

    return {"access_token": access_token, "refresh_token": refresh_token}


def refresh_tokens(user, role: str, presented_refresh_token: str) -> dict:
    """
    Rotates the refresh token: the old session is revoked and a new one
    issued, so a leaked-then-reused refresh token is detectable (reuse of
    a revoked token indicates compromise — a production system would
    revoke ALL of that user's sessions on detecting this; flagged here as
    the next hardening step rather than silently assumed).
    """
    token_hash = _hash_token(presented_refresh_token)
    session = Session.query.filter_by(refresh_token_hash=token_hash, is_active=True).first()

    if not session or session.expires_at < datetime.now(timezone.utc):
        raise AuthError("Refresh token invalid or expired. Please log in again.", 401)

    session.is_active = False
    session.revoked_at = datetime.now(timezone.utc)
    db.session.commit()

    return issue_tokens(user, role)


def revoke_session_by_refresh_token(presented_refresh_token: str) -> None:
    token_hash = _hash_token(presented_refresh_token)
    session = Session.query.filter_by(refresh_token_hash=token_hash, is_active=True).first()
    if session:
        session.is_active = False
        session.revoked_at = datetime.now(timezone.utc)
        db.session.commit()


def get_user_by_id_and_role(user_id: str, role: str):
    model, _ = _ROLE_MAP.get(role, (None, None))
    if model is None:
        return None
    return model.query.get(user_id)
