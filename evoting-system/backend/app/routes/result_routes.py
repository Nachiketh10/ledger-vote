from flask import Blueprint, Response

from app.extensions import db
from app.models.election import Election
from app.models.vote import Vote
from app.models.enums import ElectionStatus
from app.blockchain.chain import verify_election_chain
from app.services.export_service import generate_results_pdf, generate_results_excel
from app.utils.responses import success, error

result_bp = Blueprint("results", __name__)


class ResultsUnavailable(Exception):
    def __init__(self, message: str, status: int):
        self.message = message
        self.status = status


def _compute_results(election_id) -> dict:
    """Shared by the JSON endpoint and both export endpoints, so the
    numbers are always computed exactly one way."""
    election = Election.query.get(str(election_id))
    if not election:
        raise ResultsUnavailable("Election not found.", 404)

    if election.status != ElectionStatus.CLOSED:
        raise ResultsUnavailable(
            f"Results are only available after the election closes (current status: {election.status.value}).",
            403,
        )

    tally = (
        db.session.query(Vote.candidate_id, db.func.count(Vote.id))
        .filter(Vote.election_id == election.id)
        .group_by(Vote.candidate_id)
        .all()
    )
    tally_by_id = {str(cid): count for cid, count in tally}
    total_votes = sum(tally_by_id.values())

    candidates_results = []
    for candidate in election.candidates:
        votes = tally_by_id.get(str(candidate.id), 0)
        candidates_results.append(
            {
                "candidate_id": str(candidate.id),
                "name": candidate.name,
                "party": candidate.party,
                "votes": votes,
                "percentage": round((votes / total_votes * 100), 2) if total_votes else 0.0,
            }
        )
    candidates_results.sort(key=lambda c: c["votes"], reverse=True)

    eligible_count = len(election.eligible_voters)
    participation_pct = round((total_votes / eligible_count * 100), 2) if eligible_count else 0.0

    chain_valid, _ = verify_election_chain(election.id)

    return {
        "election_id": str(election.id),
        "title": election.title,
        "total_votes": total_votes,
        "eligible_voter_count": eligible_count,
        "participation_percentage": participation_pct,
        "winner": candidates_results[0] if candidates_results else None,
        "candidates": candidates_results,
        "blockchain_verified": chain_valid,
    }


@result_bp.get("/elections/<uuid:election_id>/results")
def get_results(election_id):
    """
    Public once the election is closed — matches the spec's "Only after
    election closes" rule. Includes blockchain verification status
    alongside the tally, so the result itself is provably untampered,
    not just a raw vote count.
    """
    try:
        return success(_compute_results(election_id))
    except ResultsUnavailable as exc:
        return error(exc.message, exc.status)


@result_bp.get("/elections/<uuid:election_id>/results/export/pdf")
def export_results_pdf(election_id):
    try:
        results = _compute_results(election_id)
    except ResultsUnavailable as exc:
        return error(exc.message, exc.status)

    pdf_bytes = generate_results_pdf(results)
    filename = f"results-{results['title'].replace(' ', '_')}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@result_bp.get("/elections/<uuid:election_id>/results/export/excel")
def export_results_excel(election_id):
    try:
        results = _compute_results(election_id)
    except ResultsUnavailable as exc:
        return error(exc.message, exc.status)

    excel_bytes = generate_results_excel(results)
    filename = f"results-{results['title'].replace(' ', '_')}.xlsx"
    return Response(
        excel_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
