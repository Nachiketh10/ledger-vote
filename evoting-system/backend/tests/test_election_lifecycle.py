"""
Run with: pytest tests/test_election_lifecycle.py -v
Pure logic, no DB/Flask app needed.
"""

import pytest

from app.models.enums import ElectionStatus
from app.services.election_lifecycle import (
    apply_transition,
    InvalidTransitionError,
    can_edit_details,
    can_edit_candidates,
    can_delete,
)


def test_start_from_draft_succeeds():
    assert apply_transition(ElectionStatus.DRAFT, "start") == ElectionStatus.LIVE


def test_pause_from_live_succeeds():
    assert apply_transition(ElectionStatus.LIVE, "pause") == ElectionStatus.PAUSED


def test_resume_from_paused_succeeds():
    assert apply_transition(ElectionStatus.PAUSED, "resume") == ElectionStatus.LIVE


def test_close_from_live_succeeds():
    assert apply_transition(ElectionStatus.LIVE, "close") == ElectionStatus.CLOSED


def test_close_from_paused_succeeds():
    assert apply_transition(ElectionStatus.PAUSED, "close") == ElectionStatus.CLOSED


def test_cannot_start_an_already_live_election():
    with pytest.raises(InvalidTransitionError):
        apply_transition(ElectionStatus.LIVE, "start")


def test_cannot_pause_a_draft_election():
    with pytest.raises(InvalidTransitionError):
        apply_transition(ElectionStatus.DRAFT, "pause")


def test_cannot_resume_a_live_election():
    with pytest.raises(InvalidTransitionError):
        apply_transition(ElectionStatus.LIVE, "resume")


def test_nothing_is_legal_out_of_closed():
    for action in ("start", "pause", "resume", "close"):
        with pytest.raises(InvalidTransitionError):
            apply_transition(ElectionStatus.CLOSED, action)


def test_can_edit_details_only_before_live():
    assert can_edit_details(ElectionStatus.DRAFT) is True
    assert can_edit_details(ElectionStatus.SCHEDULED) is True
    assert can_edit_details(ElectionStatus.LIVE) is False
    assert can_edit_details(ElectionStatus.PAUSED) is False
    assert can_edit_details(ElectionStatus.CLOSED) is False


def test_can_edit_candidates_only_before_live():
    assert can_edit_candidates(ElectionStatus.DRAFT) is True
    assert can_edit_candidates(ElectionStatus.LIVE) is False


def test_can_delete_only_while_draft():
    assert can_delete(ElectionStatus.DRAFT) is True
    assert can_delete(ElectionStatus.SCHEDULED) is False
    assert can_delete(ElectionStatus.LIVE) is False
    assert can_delete(ElectionStatus.CLOSED) is False
