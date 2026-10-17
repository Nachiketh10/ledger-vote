"""
Pure blockchain domain object. Deliberately has ZERO Flask/SQLAlchemy
imports — a Block is just data + a hashing rule, and keeping it pure
means it can be unit-tested with plain pytest (no app context, no DB)
and reused identically whether it's being freshly created or loaded
back from Postgres for verification.

app/models/blockchain.py (the DB row) and this class are deliberately
separate: the DB model is storage, this class is the actual blockchain
logic (hashing, chaining, tamper detection).
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Sentinel previous_hash for block_index 0 (there is no real previous
# block). 64 hex chars, matching the length of a real SHA-256 digest, so
# the column type/length constraints stay uniform for every row.
GENESIS_PREVIOUS_HASH = "0" * 64


@dataclass
class Block:
    block_index: int
    previous_hash: str
    election_id: str
    candidate_id: str
    encrypted_vote_hash: str
    vote_id: str

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    nonce: int = 0
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Populated by .mine() for a freshly created block, or passed in
    # directly when reconstructing a Block from a stored DB row (in
    # which case compute_hash() is used to check it, not set it).
    current_hash: str = ""

    def _canonical_payload(self) -> dict:
        """
        Every field that determines this block's identity, in a fixed,
        order-independent (sort_keys=True) representation. current_hash
        is deliberately EXCLUDED — it's the output of hashing this
        payload, not an input to it (including it would be circular).
        """
        return {
            "block_index": self.block_index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "nonce": self.nonce,
            "election_id": str(self.election_id),
            "candidate_id": str(self.candidate_id),
            "encrypted_vote_hash": self.encrypted_vote_hash,
            "transaction_id": str(self.transaction_id),
            "vote_id": str(self.vote_id),
        }

    def compute_hash(self) -> str:
        """Pure recomputation from current field values. Comparing this
        against self.current_hash is exactly how tampering is detected —
        if anyone changes any field after the block was sealed, this
        will no longer match the stored hash."""
        payload = json.dumps(self._canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def mine(self, difficulty: int = 0) -> str:
        """
        Seals the block by computing (and storing) its hash.

        difficulty > 0 adds simple proof-of-work: increments `nonce`
        until the hash has `difficulty` leading zero hex digits. This is
        OFF by default (difficulty=0 → instant, single-pass hashing)
        because a live voting system needs sub-second block creation,
        not mining delay. Positive difficulty is left available if you
        want to demonstrate classic PoW for the project writeup.
        """
        target_prefix = "0" * difficulty
        self.nonce = 0
        computed = self.compute_hash()
        while difficulty > 0 and not computed.startswith(target_prefix):
            self.nonce += 1
            computed = self.compute_hash()
        self.current_hash = computed
        return self.current_hash

    def to_dict(self) -> dict:
        d = self._canonical_payload()
        d["current_hash"] = self.current_hash
        return d
