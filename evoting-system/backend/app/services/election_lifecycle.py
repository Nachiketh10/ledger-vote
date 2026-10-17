"""
Election status state machine, kept pure (no DB/Flask imports) so the
transition rules can be unit-tested directly and reused identically by
both the HTTP layer and any future admin tooling/scripts.

Allowed transitions:

    DRAFT -----start----> LIVE
    LIVE  -----pause----> PAUSED
    PAUSED ----resume---> LIVE
    LIVE  -----close----> CLOSED
    PAUSED ----close----> CLOSED

Deliberately NOT allowed:
- Starting a CLOSED or already-LIVE election.
- Pausing anything except a LIVE election.
- Resuming anything except a PAUSED election.
- Any transition at all out of CLOSED — once closed, an election is
  final. Re-opening a closed election would let votes be cast after
  results may already have been viewed, which undermines the integrity
  guarantee the whole system exists for.
"""

from app.models.enums import ElectionStatus


class InvalidTransitionError(Exception):
    def __init__(self, current: ElectionStatus, action: str):
        self.current = current
        self.action = action
        super().__init__(
            f"Cannot '{action}' an election that is currently '{current.value}'."
        )


# Maps action name -> (allowed source statuses, resulting status)
_TRANSITIONS: dict[str, tuple[set[ElectionStatus], ElectionStatus]] = {
    "start": ({ElectionStatus.DRAFT, ElectionStatus.SCHEDULED}, ElectionStatus.LIVE),
    "pause": ({ElectionStatus.LIVE}, ElectionStatus.PAUSED),
    "resume": ({ElectionStatus.PAUSED}, ElectionStatus.LIVE),
    "close": ({ElectionStatus.LIVE, ElectionStatus.PAUSED}, ElectionStatus.CLOSED),
}

# Editing full details (title/description/dates/eligible voters) is only
# safe before an election goes live — once voters may have started
# voting, changing the ballot underneath them is itself a fraud vector.
EDITABLE_STATUSES = {ElectionStatus.DRAFT, ElectionStatus.SCHEDULED}

# Candidates can only be added/removed before the election is live, for
# the same reason.
CANDIDATE_EDITABLE_STATUSES = {ElectionStatus.DRAFT, ElectionStatus.SCHEDULED}

# An election can only be deleted while still a draft — once it has
# gone live (or worse, closed with real votes/blocks attached), deleting
# it would destroy an audit trail that must be permanent.
DELETABLE_STATUSES = {ElectionStatus.DRAFT}


def apply_transition(current_status: ElectionStatus, action: str) -> ElectionStatus:
    """Returns the new status if the transition is legal, else raises
    InvalidTransitionError. Does not mutate anything — caller applies
    the returned status to the actual Election row."""
    if action not in _TRANSITIONS:
        raise ValueError(f"Unknown election action: {action}")

    allowed_sources, new_status = _TRANSITIONS[action]
    if current_status not in allowed_sources:
        raise InvalidTransitionError(current_status, action)

    return new_status


def can_edit_details(status: ElectionStatus) -> bool:
    return status in EDITABLE_STATUSES


def can_edit_candidates(status: ElectionStatus) -> bool:
    return status in CANDIDATE_EDITABLE_STATUSES


def can_delete(status: ElectionStatus) -> bool:
    return status in DELETABLE_STATUSES
