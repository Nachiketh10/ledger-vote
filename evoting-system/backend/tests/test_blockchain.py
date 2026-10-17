"""
Run with: pytest tests/test_blockchain.py -v

These tests need nothing but the app/blockchain package itself — no
Flask app, no database. That's by design (see block.py/verifier.py
docstrings): the blockchain logic is pure so it can be proven correct
in isolation, independent of everything else in the system.
"""

import copy

from app.blockchain.block import Block, GENESIS_PREVIOUS_HASH
from app.blockchain.verifier import verify_block_sequence


def _build_valid_chain(n: int = 4) -> list[Block]:
    """Builds n blocks, each correctly chained to the previous one,
    exactly the way app/blockchain/chain.py:create_block does it."""
    blocks = []
    previous_hash = GENESIS_PREVIOUS_HASH

    for i in range(n):
        block = Block(
            block_index=i,
            previous_hash=previous_hash,
            election_id="11111111-1111-1111-1111-111111111111",
            candidate_id=f"candidate-{i % 2}",  # alternate between 2 candidates
            encrypted_vote_hash=f"encrypted-vote-hash-{i}",
            vote_id=f"vote-{i}",
        )
        block.mine(difficulty=0)
        blocks.append(block)
        previous_hash = block.current_hash

    return blocks


def test_compute_hash_is_deterministic():
    b1 = Block(
        block_index=0,
        previous_hash=GENESIS_PREVIOUS_HASH,
        election_id="e1",
        candidate_id="c1",
        encrypted_vote_hash="hash1",
        vote_id="v1",
    )
    b2 = copy.deepcopy(b1)
    b2.timestamp = b1.timestamp  # keep timestamp identical for determinism

    assert b1.compute_hash() == b2.compute_hash()


def test_compute_hash_changes_when_any_field_changes():
    base = Block(
        block_index=0,
        previous_hash=GENESIS_PREVIOUS_HASH,
        election_id="e1",
        candidate_id="c1",
        encrypted_vote_hash="hash1",
        vote_id="v1",
    )
    base_hash = base.compute_hash()

    mutated = copy.deepcopy(base)
    mutated.candidate_id = "c2"  # simulate someone changing which candidate the vote was for
    assert mutated.compute_hash() != base_hash


def test_genesis_block_previous_hash_is_sentinel():
    chain = _build_valid_chain(1)
    assert chain[0].previous_hash == GENESIS_PREVIOUS_HASH


def test_valid_chain_passes_verification():
    chain = _build_valid_chain(5)
    is_valid, report = verify_block_sequence(chain)

    assert is_valid is True
    assert len(report) == 5
    assert all(r.valid for r in report)
    assert all(r.issues == [] for r in report)


def test_naive_tamper_is_caught_immediately_on_that_block():
    """
    Scenario: someone edits a block's data directly (e.g. a raw SQL
    UPDATE against Postgres) WITHOUT recomputing current_hash — exactly
    what an attacker who doesn't understand the hashing rule would do.

    Caught immediately: that block's own current_hash no longer matches
    a fresh recomputation of its (now-different) contents. No cascade is
    needed — the block is self-inconsistent on its own.
    """
    chain = _build_valid_chain(5)
    chain[1].candidate_id = "candidate-9-fraudulent-swap"  # hash NOT recomputed

    is_valid, report = verify_block_sequence(chain)
    report_by_index = {r.block_index: r for r in report}

    assert is_valid is False
    assert report_by_index[0].valid is True, "blocks before the tamper are unaffected"
    assert report_by_index[1].valid is False, "the tampered block fails its own self-check"
    assert any("current_hash mismatch" in issue for issue in report_by_index[1].issues)

    # Blocks after it are still correctly linked to block 1's (unchanged)
    # stored hash, so they pass — the tamper was already caught at its source.
    assert report_by_index[2].valid is True
    assert report_by_index[3].valid is True
    assert report_by_index[4].valid is True


def test_covering_tamper_is_caught_at_the_next_blocks_link():
    """
    Scenario: a more careful attacker edits a block's data AND re-mines
    that block so it's internally self-consistent again (hiding the
    naive tamper above).

    That block now passes its own self-check — but the NEXT block's
    previous_hash was fixed at creation time to the OLD hash, so the
    chain LINK breaks at exactly that seam. This is the real security
    property: to truly erase a tamper at block N without detection, an
    attacker has to re-mine every block from N onward, all the way to
    the tip — the same "redo all the work" cost real blockchains rely on.
    """
    chain = _build_valid_chain(5)
    chain[1].candidate_id = "candidate-9-fraudulent-swap"
    chain[1].mine(difficulty=0)  # attacker re-hashes to hide the self-inconsistency

    is_valid, report = verify_block_sequence(chain)
    report_by_index = {r.block_index: r for r in report}

    assert is_valid is False
    assert report_by_index[0].valid is True
    assert report_by_index[1].valid is True, "the tampered block is self-consistent after re-mining"
    assert report_by_index[2].valid is False, "but the link to it is now broken"
    assert any("previous_hash mismatch" in issue for issue in report_by_index[2].issues)

    # Blocks 3+ remain correctly linked to (unmodified) block 2, so only
    # the exact seam is flagged — which is precisely what makes the
    # report useful for pinpointing where a compromise happened.
    assert report_by_index[3].valid is True
    assert report_by_index[4].valid is True


def test_tampering_with_the_last_block_only_invalidates_that_block():
    chain = _build_valid_chain(5)
    chain[4].encrypted_vote_hash = "swapped-vote-hash"

    is_valid, report = verify_block_sequence(chain)
    report_by_index = {r.block_index: r for r in report}

    assert is_valid is False
    assert all(report_by_index[i].valid for i in range(4)), "no earlier/other blocks should be affected"
    assert report_by_index[4].valid is False


def test_out_of_order_input_is_still_verified_in_index_order():
    """verify_block_sequence should sort by block_index itself — callers
    shouldn't have to guarantee ordering."""
    chain = _build_valid_chain(3)
    shuffled = [chain[2], chain[0], chain[1]]

    is_valid, report = verify_block_sequence(shuffled)
    assert is_valid is True
    assert [r.block_index for r in report] == [0, 1, 2]


def test_mining_with_difficulty_produces_leading_zeros():
    block = Block(
        block_index=0,
        previous_hash=GENESIS_PREVIOUS_HASH,
        election_id="e1",
        candidate_id="c1",
        encrypted_vote_hash="hash1",
        vote_id="v1",
    )
    block.mine(difficulty=2)
    assert block.current_hash.startswith("00")
    # And the mined block still passes normal verification:
    is_valid, _ = verify_block_sequence([block])
    assert is_valid is True
