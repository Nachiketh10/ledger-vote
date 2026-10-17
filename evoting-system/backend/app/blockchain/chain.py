"""
DB-facing blockchain layer. This is the only module that should touch
BlockModel/db.session directly for chain operations — routes and other
services go through these functions, never the model directly, so the
locking/hashing rules can't accidentally be bypassed.
"""

from app.extensions import db
from app.models.blockchain import Block as BlockModel
from app.blockchain.block import Block, GENESIS_PREVIOUS_HASH
from app.blockchain.verifier import verify_block_sequence, BlockVerification


def _model_to_block(row: BlockModel) -> Block:
    return Block(
        block_index=row.block_index,
        previous_hash=row.previous_hash,
        election_id=str(row.election_id),
        candidate_id=str(row.candidate_id),
        encrypted_vote_hash=row.encrypted_vote_hash,
        vote_id=str(row.vote_id),
        timestamp=row.timestamp,
        nonce=row.nonce,
        transaction_id=str(row.transaction_id),
        current_hash=row.current_hash,
    )


def create_block(
    *,
    election_id,
    candidate_id,
    encrypted_vote_hash: str,
    vote_id,
    difficulty: int = 0,
) -> BlockModel:
    """
    Appends exactly one new block to the END of the single, global chain
    (elections interleave in one shared chain, distinguished by their
    election_id field — this matches "every vote becomes one blockchain
    block" rather than one chain per election, which would let an admin
    quietly swap an entire election's chain undetected).

    Concurrency safety: SELECT ... FOR UPDATE on the last row means two
    votes racing to create block N will serialize — the second one waits
    for the first's transaction to commit, then correctly builds on top
    of it as block N+1. Without this lock, two concurrent votes could
    both read "last block = N-1" and both try to write block N, silently
    corrupting the chain.
    """
    last_row = (
        BlockModel.query.order_by(BlockModel.block_index.desc())
        .with_for_update()
        .first()
    )

    next_index = (last_row.block_index + 1) if last_row else 0
    previous_hash = last_row.current_hash if last_row else GENESIS_PREVIOUS_HASH

    block = Block(
        block_index=next_index,
        previous_hash=previous_hash,
        election_id=str(election_id),
        candidate_id=str(candidate_id),
        encrypted_vote_hash=encrypted_vote_hash,
        vote_id=str(vote_id),
    )
    block.mine(difficulty=difficulty)

    row = BlockModel(
        block_index=block.block_index,
        previous_hash=block.previous_hash,
        current_hash=block.current_hash,
        timestamp=block.timestamp,
        nonce=block.nonce,
        election_id=election_id,
        candidate_id=candidate_id,
        encrypted_vote_hash=encrypted_vote_hash,
        transaction_id=block.transaction_id,
        vote_id=vote_id,
    )
    db.session.add(row)
    db.session.commit()
    return row


def get_chain_length() -> int:
    return BlockModel.query.count()


def get_all_blocks(page: int = 1, per_page: int = 50):
    """Newest first, for the Blockchain Explorer list view."""
    return (
        BlockModel.query.order_by(BlockModel.block_index.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def get_blocks_for_election(election_id):
    return (
        BlockModel.query.filter_by(election_id=election_id)
        .order_by(BlockModel.block_index.asc())
        .all()
    )


def get_block_by_hash(current_hash: str) -> BlockModel | None:
    return BlockModel.query.filter_by(current_hash=current_hash).first()


def get_block_by_transaction_id(transaction_id) -> BlockModel | None:
    return BlockModel.query.filter_by(transaction_id=transaction_id).first()


def verify_full_chain() -> tuple[bool, list[BlockVerification]]:
    """Loads every block and runs the pure verifier over the whole chain."""
    rows = BlockModel.query.order_by(BlockModel.block_index.asc()).all()
    blocks = [_model_to_block(row) for row in rows]
    return verify_block_sequence(blocks)


def verify_election_chain(election_id) -> tuple[bool, list[BlockVerification]]:
    """
    Same as verify_full_chain, but the report is filtered down to only
    this election's blocks for display — the underlying check still
    walks the FULL global chain internally (verify_full_chain), because
    an election's blocks are only trustworthy if the whole shared chain
    up to that point is intact.
    """
    chain_valid, full_report = verify_full_chain()
    election_block_indexes = {
        row.block_index
        for row in BlockModel.query.filter_by(election_id=election_id).all()
    }
    filtered = [r for r in full_report if r.block_index in election_block_indexes]
    election_valid = all(r.valid for r in filtered)
    return (chain_valid and election_valid), filtered
