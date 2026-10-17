from datetime import datetime, timezone

from app.extensions import db
from app.models.voter import Voter
from app.models.session import Session
from app.models.face_embedding import FaceEmbedding
from app.models.enums import SessionUserType
from app.services.election_service import ElectionError  # reused generic error class
from app.services.audit_service import log_action


def get_voter_or_404(voter_id) -> Voter:
    voter = Voter.query.get(voter_id)
    if not voter:
        raise ElectionError("Voter not found.", 404)
    return voter


def list_voters(
    is_verified: bool | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
):
    query = Voter.query
    if is_verified is not None:
        query = query.filter(Voter.is_verified == is_verified)
    if is_active is not None:
        query = query.filter(Voter.is_active == is_active)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Voter.name.ilike(like), Voter.email.ilike(like), Voter.voter_id.ilike(like))
        )
    return query.order_by(Voter.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)


def verify_voter(voter: Voter, actor_type, actor_id, note: str | None = None) -> Voter:
    """Admin approval step — a self-registered voter cannot be assigned
    to any election's eligible_voters or cast a vote until this happens."""
    if voter.is_verified:
        raise ElectionError("Voter is already verified.", 409)

    voter.is_verified = True
    db.session.commit()

    log_action(
        actor_type, "voter.verified", actor_id=actor_id,
        details={"voter_id": str(voter.id), "note": note},
    )
    return voter


def suspend_voter(voter: Voter, actor_type, actor_id, reason: str) -> Voter:
    """Deactivates a voter — e.g. following a confirmed fraud finding.
    Does not delete the record (audit trail must be preserved)."""
    voter.is_active = False
    db.session.commit()

    log_action(
        actor_type, "voter.suspended", actor_id=actor_id,
        details={"voter_id": str(voter.id), "reason": reason},
    )
    return voter


def reactivate_voter(voter: Voter, actor_type, actor_id) -> Voter:
    voter.is_active = True
    voter.failed_login_attempts = 0
    voter.account_locked_until = None
    db.session.commit()

    log_action(
        actor_type, "voter.reactivated", actor_id=actor_id,
        details={"voter_id": str(voter.id)},
    )
    return voter


def revoke_all_sessions(voter: Voter, actor_type, actor_id) -> int:
    """
    Force-logs-out a voter everywhere by revoking every active session.

    Real-world use: an admin responding to a lost/stolen device report,
    or clearing a voter's stuck "multiple sessions" fraud flag after
    confirming it was a legitimate mistake (e.g. forgot to log out on
    an old device) rather than actual fraud.

    Dev/test use: repeatedly logging in the same test voter during
    development accumulates sessions, which correctly trips the
    multi-session fraud rule (see app/fraud/rules.py) — this clears
    that out without needing to create a brand new voter every time.
    """
    active_sessions = Session.query.filter_by(
        voter_id=voter.id, user_type=SessionUserType.VOTER, is_active=True
    ).all()

    now = datetime.now(timezone.utc)
    count = 0
    for session in active_sessions:
        session.is_active = False
        session.revoked_at = now
        count += 1
    db.session.commit()

    log_action(
        actor_type, "voter.sessions_revoked", actor_id=actor_id,
        details={"voter_id": str(voter.id), "revoked_count": count},
    )
    return count


def reset_biometrics(voter: Voter, actor_type, actor_id) -> dict:
    """
    Deletes the voter's stored face embedding and clears
    has_face_registered, so they can register a fresh face from
    scratch.

    Real-world use: face embedding quality was poor and needs redoing
    — an admin can reset the biometric enrollment without touching
    their vote history, sessions, or verification status.

    Dev/test use: repeated test runs accumulate a stale face
    registration tied to a reused test voter; this clears it without
    needing a brand-new voter each time.
    """
    removed = {"face": False}

    face_embedding = FaceEmbedding.query.filter_by(voter_id=voter.id).first()
    if face_embedding:
        db.session.delete(face_embedding)
        removed["face"] = True

    voter.has_face_registered = False
    db.session.commit()

    log_action(
        actor_type, "voter.biometrics_reset", actor_id=actor_id,
        details={"voter_id": str(voter.id), **removed},
    )
    return removed
