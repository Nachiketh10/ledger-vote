from flask import Blueprint, request

from app.middleware.auth_middleware import election_admin_required
from app.blockchain import chain as blockchain_chain
from app.models.blockchain import Block
from app.utils.pagination import parse_pagination_args
from app.utils.responses import success, error

blockchain_bp = Blueprint("blockchain", __name__)


def _block_dict(block: Block) -> dict:
    return {
        "id": str(block.id),
        "block_index": block.block_index,
        "previous_hash": block.previous_hash,
        "current_hash": block.current_hash,
        "timestamp": block.timestamp.isoformat(),
        "nonce": block.nonce,
        "election_id": str(block.election_id),
        "candidate_id": str(block.candidate_id),
        "transaction_id": str(block.transaction_id),
    }


@blockchain_bp.get("")
@election_admin_required
def list_blocks():
    page, per_page = parse_pagination_args(request, default_per_page=25)
    pagination = blockchain_chain.get_all_blocks(page=page, per_page=per_page)
    return success(
        {
            "items": [_block_dict(b) for b in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
            },
        }
    )


@blockchain_bp.get("/verify")
@election_admin_required
def verify_chain():
    chain_valid, report = blockchain_chain.verify_full_chain()
    return success(
        {
            "chain_valid": chain_valid,
            "blocks_checked": len(report),
            "invalid_blocks": [
                {"block_index": r.block_index, "issues": r.issues}
                for r in report
                if not r.valid
            ],
        }
    )


@blockchain_bp.get("/search")
@election_admin_required
def search_blocks():
    tx_id = request.args.get("transaction_id")
    hash_value = request.args.get("hash")
    election_id = request.args.get("election_id")

    if tx_id:
        block = blockchain_chain.get_block_by_transaction_id(tx_id)
        return success(_block_dict(block) if block else None)

    if hash_value:
        block = blockchain_chain.get_block_by_hash(hash_value)
        return success(_block_dict(block) if block else None)

    if election_id:
        blocks = blockchain_chain.get_blocks_for_election(election_id)
        return success([_block_dict(b) for b in blocks])

    return error("Provide one of: transaction_id, hash, election_id.", 422)
