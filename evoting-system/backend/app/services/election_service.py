"""
Election business logic. Routes stay thin; all rules live here so they
can't be bypassed by hitting the DB/model directly from elsewhere.
"""

from app.extensions import db
from app.models.election import Election
from app.models.admin import ElectionAdmin
from app.models.voter import Voter
from app.models.enums import ElectionStatus, ActorType
from app.services import election_lifecycle
from app.services.audit_service import log_action
from app.utils.errors import AppError


class ElectionError(AppError):
    """Kept as its own name (rather than importing AppError directly
    everywhere) since 'ElectionError' reads clearly at call sites in
    candidate_service/voter_admin_service, which reuse this same class
    for their own not-found/conflict errors."""
    pass


def get_election_or_404(election_id) -> Election:
    election = Election.query.get(election_id)
    if not election:
        raise ElectionError("Election not found.", 404)
    return election


def user_can_manage_election(election: Election, role: str, user_id: str) -> bool:
    """Super Admins can manage any election. Election Admins can only
    manage elections explicitly assigned to them."""
    if role == "super_admin":
        return True
    if role == "election_admin":
        return any(str(admin.id) == str(user_id) for admin in election.assigned_admins)
    return False


def list_election_admins():
    """All Election Admin accounts — used to populate an assignment
    picker for Super Admins. Super-Admin-only concern, enforced at the
    route layer."""
    return ElectionAdmin.query.order_by(ElectionAdmin.name.asc()).all()


def assign_admin_to_election(election: Election, election_admin_id: str, actor_id) -> Election:
    """Super-Admin-only action: attaches an existing Election Admin to
    an election so they can manage it. Idempotent — assigning the same
    admin twice is a no-op, not an error."""
    admin = ElectionAdmin.query.get(election_admin_id)
    if not admin:
        raise ElectionError("Election Admin not found.", 404)

    if admin not in election.assigned_admins:
        election.assigned_admins.append(admin)
        db.session.commit()
        log_action(
            ActorType.SUPER_ADMIN, "election.admin_assigned", actor_id=actor_id,
            details={"election_id": str(election.id), "election_admin_id": str(admin.id)},
        )
    return election


def unassign_admin_from_election(election: Election, election_admin_id: str, actor_id) -> Election:
    admin = ElectionAdmin.query.get(election_admin_id)
    if not admin:
        raise ElectionError("Election Admin not found.", 404)

    if admin in election.assigned_admins:
        election.assigned_admins.remove(admin)
        db.session.commit()
        log_action(
            ActorType.SUPER_ADMIN, "election.admin_unassigned", actor_id=actor_id,
            details={"election_id": str(election.id), "election_admin_id": str(admin.id)},
        )
    return election


def list_elections(status: str | None = None, page: int = 1, per_page: int = 20):
    query = Election.query.order_by(Election.start_date.desc())
    if status:
        try:
            query = query.filter(Election.status == ElectionStatus(status))
        except ValueError:
            raise ElectionError(
                f"Invalid status filter '{status}'. Must be one of: "
                f"{', '.join(s.value for s in ElectionStatus)}.",
                422,
            )
    return query.paginate(page=page, per_page=per_page, error_out=False)


def create_election(data: dict, created_by_id: str | None = None) -> Election:
    election = Election(
        title=data["title"],
        description=data.get("description"),
        start_date=data["start_date"],
        end_date=data["end_date"],
        status=ElectionStatus.DRAFT,
        created_by_id=created_by_id,
    )

    if created_by_id:
        admin = ElectionAdmin.query.get(created_by_id)
        if admin:
            election.assigned_admins.append(admin)

    voter_id_strings = data.get("eligible_voter_ids") or []
    if voter_id_strings:
        voters = Voter.query.filter(Voter.voter_id.in_(voter_id_strings)).all()
        election.eligible_voters.extend(voters)

    db.session.add(election)
    db.session.commit()

    log_action(
        ActorType.ELECTION_ADMIN if created_by_id else ActorType.SUPER_ADMIN,
        "election.created",
        actor_id=created_by_id,
        details={"election_id": str(election.id), "title": election.title},
    )
    return election


def update_election(election: Election, data: dict, actor_type: ActorType, actor_id) -> Election:
    if not election_lifecycle.can_edit_details(election.status):
        raise ElectionError(
            f"Cannot edit an election that is '{election.status.value}'. "
            "Only draft/scheduled elections can be edited.",
            409,
        )

    for field in ("title", "description", "start_date", "end_date"):
        if field in data:
            setattr(election, field, data[field])

    if election.end_date <= election.start_date:
        raise ElectionError("end_date must be after start_date.", 422)

    db.session.commit()
    log_action(actor_type, "election.updated", actor_id=actor_id, details={"election_id": str(election.id)})
    return election


def delete_election(election: Election, actor_type: ActorType, actor_id) -> None:
    if not election_lifecycle.can_delete(election.status):
        raise ElectionError(
            f"Cannot delete an election that is '{election.status.value}'. "
            "Only draft elections can be deleted.",
            409,
        )

    election_id = str(election.id)
    db.session.delete(election)
    db.session.commit()
    log_action(actor_type, "election.deleted", actor_id=actor_id, details={"election_id": election_id})


def apply_action(election: Election, action: str, actor_type: ActorType, actor_id) -> Election:
    """action is one of: start, pause, resume, close."""
    try:
        new_status = election_lifecycle.apply_transition(election.status, action)
    except election_lifecycle.InvalidTransitionError as exc:
        raise ElectionError(str(exc), 409) from exc

    if action == "start" and len(election.candidates) < 2:
        raise ElectionError(
            "Cannot start an election with fewer than 2 candidates.", 409
        )

    election.status = new_status
    db.session.commit()

    log_action(
        actor_type,
        f"election.{action}",
        actor_id=actor_id,
        details={"election_id": str(election.id), "new_status": new_status.value},
    )
    return election


def set_eligible_voters(election: Election, voter_id_strings: list[str], actor_type: ActorType, actor_id) -> Election:
    if election.status == ElectionStatus.CLOSED:
        raise ElectionError("Cannot change eligibility for a closed election.", 409)

    voters = Voter.query.filter(Voter.voter_id.in_(voter_id_strings)).all()
    found_ids = {v.voter_id for v in voters}
    missing = set(voter_id_strings) - found_ids
    if missing:
        raise ElectionError(f"Unknown voter ID(s): {', '.join(sorted(missing))}", 422)

    election.eligible_voters = voters
    db.session.commit()

    log_action(
        actor_type,
        "election.eligibility_updated",
        actor_id=actor_id,
        details={"election_id": str(election.id), "eligible_count": len(voters)},
    )
    return election
