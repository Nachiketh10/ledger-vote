"""
Chain verification logic, kept pure (operates on a list of Block
dataclass objects, no DB access) so it's directly unit-testable and so
the exact same function verifies a freshly-built in-memory chain or one
reloaded from Postgres — there's only one verification code path.

See app/blockchain/chain.py for the DB-facing wrapper that loads rows
and calls verify_block_sequence().
"""

from dataclasses import dataclass

from app.blockchain.block import Block, GENESIS_PREVIOUS_HASH


@dataclass
class BlockVerification:
    block_index: int
    valid: bool
    stored_hash: str
    recomputed_hash: str
    issues: list[str]


def verify_block_sequence(blocks: list[Block]) -> tuple[bool, list[BlockVerification]]:
    """
    Walks the chain in block_index order and checks, for every block:

    1. previous_hash equals the PREVIOUS block's STORED current_hash
       (or the genesis sentinel, for block 0).
    2. current_hash equals a fresh recomputation of the block's own
       fields (catches direct tampering of that block's data).

    What "tampering invalidates the chain" actually means here, precisely
    (two distinct attacker scenarios):

    - Naive tamper: someone edits a block's data (e.g. a raw SQL UPDATE)
      without recomputing current_hash. That block's own check (2) fails
      immediately — it's caught right there, no cascade needed.

    - Covering tamper: the attacker edits the data AND re-mines that one
      block so it's internally self-consistent again. Now check (2)
      passes for that block, but the NEXT block's previous_hash was
      fixed at creation time to the OLD hash — so check (1) fails at
      exactly that seam. Everything after the seam is still correctly
      linked to each other, but chain_valid is still False overall, and
      the report tells you precisely where the break is. To truly erase
      a tamper at block N, an attacker would have to re-mine every block
      from N onward — the same "redo all the work" cost that makes real
      blockchains tamper-evident, not tamper-proof-by-magic.

    Either way, `chain_valid` (the first return value) is False and the
    per-block report pinpoints exactly which block(s) failed and why —
    that's what the Blockchain Explorer surfaces to admins.
    """
    report: list[BlockVerification] = []
    chain_valid = True
    expected_previous_hash = GENESIS_PREVIOUS_HASH

    for block in sorted(blocks, key=lambda b: b.block_index):
        issues: list[str] = []

        if block.previous_hash != expected_previous_hash:
            issues.append(
                f"previous_hash mismatch at block {block.block_index}: "
                f"expected {expected_previous_hash[:12]}..., "
                f"found {block.previous_hash[:12]}..."
            )

        recomputed = block.compute_hash()
        if recomputed != block.current_hash:
            issues.append(
                f"current_hash mismatch at block {block.block_index}: "
                "stored hash does not match a fresh recomputation — "
                "this block's data has been altered after creation."
            )

        is_valid = len(issues) == 0
        if not is_valid:
            chain_valid = False

        report.append(
            BlockVerification(
                block_index=block.block_index,
                valid=is_valid,
                stored_hash=block.current_hash,
                recomputed_hash=recomputed,
                issues=issues,
            )
        )

        # Next block should chain from THIS block's STORED hash, even if
        # that hash turned out to be wrong — that's what makes tampering
        # cascade forward through every subsequent block.
        expected_previous_hash = block.current_hash

    return chain_valid, report
