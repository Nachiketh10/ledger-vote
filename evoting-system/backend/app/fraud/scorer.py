"""
Combines individual fraud rules into one overall assessment. Split into
two layers, same pattern as election_lifecycle.py/election_service.py:

- `decide(...)`: pure function, takes already-gathered primitive values,
  returns a FraudAssessment. Fully unit-testable without a DB.
- `assess_voter_for_voting(...)`: DB-facing wrapper that queries the
  actual counts/flags for a real voter and calls decide().
"""

from dataclasses import dataclass, field

from flask import current_app

from app.extensions import db
from app.models.vote import Vote
from app.models.session import Session
from app.models.fraud_log import FraudLog
from app.models.enums import SessionUserType, FraudSeverity
from app.fraud import rules
from app.fraud.rules import FraudSignal


@dataclass
class FraudAssessment:
    score: int
    blocked: bool
    signals: list[FraudSignal] = field(default_factory=list)


def decide(
    *,
    already_voted: bool,
    active_session_count: int,
    distinct_device_count: int,
    failed_attempts: int,
    failed_attempts_threshold: int,
    block_score_threshold: int,
    is_vpn: bool = False,
    max_sessions_allowed: int = 1,
    max_devices_allowed: int = 1,
) -> FraudAssessment:
    signals = [
        s
        for s in (
            rules.check_duplicate_vote(already_voted),
            rules.check_multiple_sessions(active_session_count, max_sessions_allowed),
            rules.check_multiple_devices(distinct_device_count, max_devices_allowed),
            rules.check_excessive_failed_attempts(failed_attempts, failed_attempts_threshold),
            rules.check_vpn(is_vpn),
        )
        if s is not None
    ]

    score = min(100, sum(s.score for s in signals))
    # Any CRITICAL signal blocks outright, regardless of the summed score
    # (e.g. a duplicate vote attempt is disqualifying on its own, even if
    # every other signal is clean).
    has_critical = any(s.severity == FraudSeverity.CRITICAL for s in signals)
    blocked = has_critical or score >= block_score_threshold

    return FraudAssessment(score=score, blocked=blocked, signals=signals)


def assess_voter_for_voting(voter, election_id) -> FraudAssessment:
    already_voted = (
        Vote.query.filter_by(voter_id=voter.id, election_id=election_id).first() is not None
    )

    active_session_count = Session.query.filter_by(
        voter_id=voter.id, user_type=SessionUserType.VOTER, is_active=True
    ).count()

    distinct_device_count = (
        db.session.query(Session.device_fingerprint)
        .filter(
            Session.voter_id == voter.id,
            Session.user_type == SessionUserType.VOTER,
            Session.is_active.is_(True),
            Session.device_fingerprint.isnot(None),
        )
        .distinct()
        .count()
    )

    return decide(
        already_voted=already_voted,
        active_session_count=active_session_count,
        distinct_device_count=distinct_device_count,
        failed_attempts=voter.failed_login_attempts,
        failed_attempts_threshold=current_app.config["MAX_FAILED_AUTH_ATTEMPTS"],
        block_score_threshold=current_app.config["FRAUD_SCORE_BLOCK_THRESHOLD"],
    )


def log_signals(voter, election_id, signals: list[FraudSignal]) -> None:
    if not signals:
        return
    for sig in signals:
        db.session.add(
            FraudLog(
                voter_id=voter.id,
                election_id=election_id,
                fraud_type=sig.fraud_type,
                severity=sig.severity,
                fraud_score=sig.score,
                description=sig.description,
            )
        )
    db.session.commit()
