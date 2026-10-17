from app.extensions import db
from app.models.candidate import Candidate
from app.models.election import Election
from app.services import election_lifecycle
from app.services.election_service import ElectionError
from app.services.audit_service import log_action


def get_candidate_or_404(candidate_id) -> Candidate:
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        raise ElectionError("Candidate not found.", 404)
    return candidate


def list_candidates(election_id):
    return Candidate.query.filter_by(election_id=election_id).order_by(Candidate.name.asc()).all()


def add_candidate(election: Election, data: dict, actor_type, actor_id) -> Candidate:
    if not election_lifecycle.can_edit_candidates(election.status):
        raise ElectionError(
            f"Cannot add candidates to an election that is '{election.status.value}'. "
            "Candidates can only be added while the election is still a draft.",
            409,
        )

    candidate = Candidate(
        election_id=election.id,
        name=data["name"],
        party=data.get("party"),
        photo_url=data.get("photo_url"),
        description=data.get("description"),
    )
    db.session.add(candidate)
    db.session.commit()

    log_action(
        actor_type,
        "candidate.added",
        actor_id=actor_id,
        details={"election_id": str(election.id), "candidate_id": str(candidate.id), "name": candidate.name},
    )
    return candidate


def update_candidate(candidate: Candidate, data: dict, actor_type, actor_id) -> Candidate:
    election = candidate.election
    if not election_lifecycle.can_edit_candidates(election.status):
        raise ElectionError(
            f"Cannot edit candidates once the election is '{election.status.value}'.", 409
        )

    for field in ("name", "party", "photo_url", "description"):
        if field in data:
            setattr(candidate, field, data[field])

    db.session.commit()
    log_action(
        actor_type, "candidate.updated", actor_id=actor_id,
        details={"candidate_id": str(candidate.id)},
    )
    return candidate


def delete_candidate(candidate: Candidate, actor_type, actor_id) -> None:
    election = candidate.election
    if not election_lifecycle.can_edit_candidates(election.status):
        raise ElectionError(
            f"Cannot remove candidates once the election is '{election.status.value}'.", 409
        )

    candidate_id = str(candidate.id)
    db.session.delete(candidate)
    db.session.commit()
    log_action(
        actor_type, "candidate.deleted", actor_id=actor_id,
        details={"candidate_id": candidate_id},
    )
