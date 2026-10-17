"""
The actual /vote endpoint's business logic. This is where every
previous part comes together:

    Select Election -> Fraud Pre-Check -> Face Verification ->
    Candidate List -> Vote Confirmation -> Hash Vote ->
    Blockchain Block -> Store Block

Face recognition is the sole biometric verification method (fingerprint/
WebAuthn support was removed from the project).

(Fraud pre-check is run FIRST here, before face verification, rather
than strictly last as a literal flow-diagram reading might suggest —
deliberately: there's no point running expensive face verification for
a voter who's already voted or is mid multi-session fraud. Multi-face
and face-mismatch fraud are still detected exactly during face
verification, not moved.)
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.election import Election
from app.models.vote import Vote
from app.models.enums import ElectionStatus, ActorType, FraudType, FraudSeverity
from app.services.audit_service import log_action
from app.services import face_service
from app.services.face_service import FaceError
from app.fraud import scorer
from app.blockchain import chain as blockchain_chain
from app.utils.errors import AppError


class VoteError(AppError):
    pass


@dataclass
class VoteResult:
    success: bool
    message: str
    block_index: int | None = None
    transaction_id: str | None = None


def _log_single_fraud_signal(voter, election_id, fraud_type: FraudType, severity: FraudSeverity, description: str):
    from app.models.fraud_log import FraudLog

    db.session.add(
        FraudLog(
            voter_id=voter.id,
            election_id=election_id,
            fraud_type=fraud_type,
            severity=severity,
            fraud_score=100 if severity == FraudSeverity.CRITICAL else 70,
            description=description,
        )
    )
    db.session.commit()
    log_action(
        ActorType.SYSTEM,
        f"fraud.{fraud_type.value}",
        details={"voter_id": str(voter.id), "election_id": str(election_id)},
    )


def get_vote_status(voter, election_id) -> dict:
    election = Election.query.get(election_id)
    if not election:
        raise VoteError("Election not found.", 404)

    has_voted = Vote.query.filter_by(voter_id=voter.id, election_id=election_id).first() is not None
    is_eligible = election in voter.eligible_elections

    return {
        "election_status": election.status.value,
        "is_eligible": is_eligible,
        "has_voted": has_voted,
        "can_vote_now": (
            election.status == ElectionStatus.LIVE
            and is_eligible
            and not has_voted
            and voter.is_verified
            and voter.is_active
            and voter.has_face_registered
        ),
    }


def cast_vote(voter, election_id, candidate_id, face_frames: list) -> VoteResult:
    election = Election.query.get(election_id)
    if not election:
        raise VoteError("Election not found.", 404)

    if election.status != ElectionStatus.LIVE:
        raise VoteError(
            f"Voting is not currently open for this election (status: {election.status.value}).", 409
        )
    if not voter.is_verified:
        raise VoteError("Your voter registration has not yet been verified by an election admin.", 403)
    if not voter.is_active:
        raise VoteError("Your voter account is suspended.", 403)
    if election not in voter.eligible_elections:
        raise VoteError("You are not on the eligible-voter list for this election.", 403)

    candidate = next((c for c in election.candidates if str(c.id) == str(candidate_id)), None)
    if not candidate:
        raise VoteError("Candidate not found in this election.", 404)

    # --- 1. Fraud pre-check: duplicate vote, multi-session, multi-device, failed attempts ---
    assessment = scorer.assess_voter_for_voting(voter, election.id)
    if assessment.signals:
        scorer.log_signals(voter, election.id, assessment.signals)
    if assessment.blocked:
        reasons = "; ".join(s.description for s in assessment.signals)
        log_action(
            ActorType.SYSTEM, "vote.blocked_fraud",
            details={"voter_id": str(voter.id), "election_id": str(election.id), "score": assessment.score},
        )
        raise VoteError(f"Voting blocked due to suspicious activity: {reasons}", 403)

    # --- 2. Face verification (multiple-faces / mismatch / liveness handled + logged inside) ---
    if not voter.has_face_registered:
        raise VoteError("Face registration is required before voting.", 409)
    try:
        face_outcome = face_service.verify_face(voter, face_frames, election_id=election.id)
    except FaceError as exc:
        raise VoteError(f"Face verification error: {exc.message}", exc.status)
    if not face_outcome.success:
        raise VoteError(f"Face verification failed: {face_outcome.reason}", 401)

    # --- 3. All checks passed: hash the vote, record it, mine a block ---
    now = datetime.now(timezone.utc)
    nonce = secrets.token_hex(16)
    # NOTE ON NAMING: this is a SHA-256 HASH, not reversible encryption —
    # "encrypted_vote_hash" is the spec's own field name, kept for
    # consistency with the DB schema (see app/models/vote.py / blockchain.py).
    # Its purpose is tamper-evidence for the blockchain block content, not
    # concealing the candidate choice — candidate_id is already stored in
    # cleartext on the Vote row itself (see the anonymity tradeoff note in
    # app/models/vote.py).
    vote_hash = hashlib.sha256(
        f"{voter.id}:{candidate.id}:{election.id}:{now.isoformat()}:{nonce}".encode()
    ).hexdigest()

    vote = Vote(
        election_id=election.id,
        candidate_id=candidate.id,
        voter_id=voter.id,
        encrypted_vote_hash=vote_hash,
        cast_at=now,
    )
    db.session.add(vote)
    try:
        db.session.flush()  # makes the vote row visible (in-transaction) for the block's FK
    except IntegrityError:
        db.session.rollback()
        # Race condition: two near-simultaneous requests both passed the
        # pre-check above before either committed. The DB's UNIQUE
        # constraint is the final, authoritative guard against a double
        # vote — this is the safety net, not the primary check.
        _log_single_fraud_signal(
            voter, election.id, FraudType.DUPLICATE_VOTE, FraudSeverity.CRITICAL,
            "Duplicate vote blocked by database constraint (race condition on concurrent submission).",
        )
        raise VoteError("You have already voted in this election.", 409)

    block = blockchain_chain.create_block(
        election_id=election.id,
        candidate_id=candidate.id,
        encrypted_vote_hash=vote_hash,
        vote_id=vote.id,
    )
    db.session.commit()

    log_action(
        ActorType.VOTER, "vote.cast", actor_id=voter.id,
        details={
            "election_id": str(election.id),
            "block_index": block.block_index,
            "transaction_id": str(block.transaction_id),
        },
    )

    return VoteResult(
        success=True,
        message="Vote successfully recorded.",
        block_index=block.block_index,
        transaction_id=str(block.transaction_id),
    )
