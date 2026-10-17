"""
Run with: pytest tests/test_fraud_scoring.py -v
Pure logic — no Flask/DB needed, since rules.py and scorer.decide() take
plain values rather than querying anything themselves.
"""

import pytest

from app.fraud import rules
from app.fraud.scorer import decide
from app.models.enums import FraudType, FraudSeverity


# ---------------- Individual rules ----------------

def test_no_duplicate_vote_returns_none():
    assert rules.check_duplicate_vote(already_voted=False) is None


def test_duplicate_vote_returns_critical_signal():
    signal = rules.check_duplicate_vote(already_voted=True)
    assert signal is not None
    assert signal.fraud_type == FraudType.DUPLICATE_VOTE
    assert signal.severity == FraudSeverity.CRITICAL
    assert signal.score == 100


def test_single_session_is_fine():
    assert rules.check_multiple_sessions(active_session_count=1, max_allowed=1) is None


def test_multiple_sessions_flagged():
    signal = rules.check_multiple_sessions(active_session_count=3, max_allowed=1)
    assert signal is not None
    assert signal.fraud_type == FraudType.MULTIPLE_SESSIONS


def test_single_device_is_fine():
    assert rules.check_multiple_devices(distinct_device_count=1, max_allowed=1) is None


def test_multiple_devices_flagged():
    signal = rules.check_multiple_devices(distinct_device_count=2, max_allowed=1)
    assert signal is not None
    assert signal.fraud_type == FraudType.MULTIPLE_DEVICES


def test_failed_attempts_below_threshold_is_fine():
    assert rules.check_excessive_failed_attempts(failed_attempts=2, threshold=5) is None


def test_failed_attempts_at_threshold_flagged():
    signal = rules.check_excessive_failed_attempts(failed_attempts=5, threshold=5)
    assert signal is not None
    assert signal.fraud_type == FraudType.EXCESSIVE_FAILED_ATTEMPTS


def test_vpn_false_returns_none():
    assert rules.check_vpn(is_vpn=False) is None


def test_vpn_true_returns_low_severity_signal():
    signal = rules.check_vpn(is_vpn=True)
    assert signal is not None
    assert signal.severity == FraudSeverity.LOW


# ---------------- Scorer: decide() ----------------

def _decide(**overrides):
    defaults = dict(
        already_voted=False,
        active_session_count=1,
        distinct_device_count=1,
        failed_attempts=0,
        failed_attempts_threshold=5,
        block_score_threshold=70,
    )
    defaults.update(overrides)
    return decide(**defaults)


def test_clean_voter_is_not_blocked():
    assessment = _decide()
    assert assessment.blocked is False
    assert assessment.score == 0
    assert assessment.signals == []


def test_duplicate_vote_blocks_even_with_low_score_threshold_headroom():
    """A single CRITICAL signal blocks outright, regardless of whether
    the summed score alone would cross the threshold."""
    assessment = _decide(already_voted=True, block_score_threshold=1000)
    assert assessment.blocked is True
    assert assessment.score == 100


def test_moderate_signals_below_threshold_do_not_block():
    # multi-session (40) alone, threshold 70 -> should not block
    assessment = _decide(active_session_count=2, block_score_threshold=70)
    assert assessment.score == 40
    assert assessment.blocked is False


def test_combined_signals_crossing_threshold_blocks():
    # multi-session (40) + multi-device (40) = 80 >= 70 -> blocked
    assessment = _decide(active_session_count=2, distinct_device_count=2, block_score_threshold=70)
    assert assessment.score == 80
    assert assessment.blocked is True
    assert len(assessment.signals) == 2


def test_score_is_capped_at_100():
    assessment = _decide(
        already_voted=True,  # 100
        active_session_count=5,  # 40
        distinct_device_count=5,  # 40
        failed_attempts=10, failed_attempts_threshold=5,  # 60
    )
    assert assessment.score == 100  # capped, not 240
    assert assessment.blocked is True


def test_failed_attempts_alone_below_block_threshold():
    # excessive failed attempts (60) alone with default block threshold 70 -> not blocked
    assessment = _decide(failed_attempts=6, failed_attempts_threshold=5, block_score_threshold=70)
    assert assessment.score == 60
    assert assessment.blocked is False


def test_failed_attempts_plus_anything_else_crosses_threshold():
    assessment = _decide(
        failed_attempts=6, failed_attempts_threshold=5,  # 60
        active_session_count=2,  # 40
        block_score_threshold=70,
    )
    assert assessment.score == 100  # capped
    assert assessment.blocked is True
