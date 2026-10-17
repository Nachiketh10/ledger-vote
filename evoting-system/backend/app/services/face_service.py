"""
Orchestrates the full face registration and verification flows. Routes
stay thin (decode request -> call this -> serialize response); all the
actual rules live here.
"""

from dataclasses import dataclass

from flask import current_app

from app.extensions import db
from app.models.face_embedding import FaceEmbedding
from app.models.voter import Voter
from app.models.fraud_log import FraudLog
from app.models.enums import FraudType, FraudSeverity, ActorType
from app.services.audit_service import log_action
from app.utils.errors import AppError
from app.face import detector, embedder, liveness
from app.face.storage import encrypt_embedding, decrypt_embedding
from app.face.matcher import average_embeddings, is_match


class FaceError(AppError):
    pass


@dataclass
class VerifyFaceOutcome:
    success: bool
    reason: str
    similarity: float | None = None


def _log_fraud(voter: Voter, fraud_type: FraudType, severity: FraudSeverity, description: str, election_id=None):
    db.session.add(
        FraudLog(
            voter_id=voter.id,
            election_id=election_id,
            fraud_type=fraud_type,
            severity=severity,
            fraud_score=100 if severity == FraudSeverity.CRITICAL else 70,
            description=description,
        )
    )
    db.session.commit()
    log_action(
        ActorType.SYSTEM,
        f"fraud.{fraud_type.value}",
        details={"voter_id": str(voter.id), "election_id": str(election_id) if election_id else None},
    )


def register_face(voter: Voter, frames: list) -> FaceEmbedding:
    """
    frames: list of decoded OpenCV BGR ndarrays (already run through
    image_utils.decode_base64_image by the route).

    Only frames containing EXACTLY one face are used — frames with zero
    or multiple faces are silently skipped (a user shifting position
    mid-capture is normal; a full batch of bad frames is not).
    """
    expected = current_app.config["FACE_REGISTRATION_SAMPLE_COUNT"]
    min_required = max(5, expected // 2)  # tolerate some bad frames, but not too many

    single_face_frames = [f for f in frames if detector.detect_single_face_bbox(f) is not None]

    if len(single_face_frames) < min_required:
        raise FaceError(
            f"Only {len(single_face_frames)} of {len(frames)} captured frames had a "
            f"clearly detectable single face (need at least {min_required}). "
            "Please retry registration with better lighting and one person in frame.",
            422,
        )

    embeddings = embedder.generate_embeddings_batch(single_face_frames)
    if len(embeddings) < min_required:
        raise FaceError(
            f"Only generated {len(embeddings)} usable face embeddings (need at least "
            f"{min_required}). Please retry registration.",
            422,
        )

    template = average_embeddings(embeddings)

    duplicate_voter_id = _find_duplicate_face_owner(template, exclude_voter_id=voter.id)
    if duplicate_voter_id is not None:
        db.session.add(
            FraudLog(
                voter_id=voter.id,
                fraud_type=FraudType.DUPLICATE_FACE_ENROLLMENT,
                severity=FraudSeverity.CRITICAL,
                fraud_score=100,
                description=(
                    "Face registration rejected: this face matches the face already "
                    f"registered to a different voter account ({duplicate_voter_id})."
                ),
            )
        )
        db.session.commit()
        log_action(
            ActorType.SYSTEM, "fraud.duplicate_face_enrollment",
            details={"attempted_by_voter_id": str(voter.id), "matches_voter_id": str(duplicate_voter_id)},
        )
        raise FaceError(
            "This face is already registered to a different voter account. "
            "Each person may only register one voter account. If you believe this "
            "is an error, contact an election administrator.",
            409,
        )

    encrypted = encrypt_embedding(template)

    existing = FaceEmbedding.query.filter_by(voter_id=voter.id).first()
    if existing:
        existing.encrypted_embedding = encrypted
        existing.sample_count = len(embeddings)
        row = existing
    else:
        row = FaceEmbedding(
            voter_id=voter.id,
            encrypted_embedding=encrypted,
            embedding_model="insightface-buffalo_l",
            sample_count=len(embeddings),
        )
        db.session.add(row)

    voter.has_face_registered = True
    db.session.commit()

    log_action(
        ActorType.VOTER,
        "face.registered",
        actor_id=voter.id,
        details={"sample_count": len(embeddings)},
    )
    return row


def _find_duplicate_face_owner(template, exclude_voter_id):
    """
    Scans every OTHER voter's stored face embedding and returns the
    voter_id of the first match above threshold, or None. This is what
    was MISSING before: registration only checked "does this look like
    a face" (MediaPipe/InsightFace can detect a face), never "is this
    face already enrolled under someone else's account" — so the same
    person could register multiple voter identities with the same face.

    Scaling note: this is an O(n) linear scan across all registered
    embeddings, decrypting and comparing each one. Registration is a
    rare, one-time event per voter (unlike per-vote verification, which
    only compares against the ONE stored embedding it already knows),
    so this is fine at the scale of a single election's voter roll. A
    system with millions of registered voters would need approximate
    nearest-neighbor indexing (e.g. pgvector) instead of a full scan —
    flagged here rather than silently left as a hidden bottleneck.
    """
    threshold = current_app.config["FACE_MATCH_THRESHOLD"]
    other_rows = FaceEmbedding.query.filter(FaceEmbedding.voter_id != exclude_voter_id).all()

    for row in other_rows:
        try:
            stored = decrypt_embedding(row.encrypted_embedding)
        except ValueError:
            continue  # corrupted/undecryptable row shouldn't crash registration for someone else
        matched, _ = is_match(template, stored, threshold)
        if matched:
            return row.voter_id
    return None


def verify_face(voter: Voter, frames: list, election_id=None) -> VerifyFaceOutcome:
    """
    frames: a SEQUENCE of decoded frames captured over ~2-3 seconds
    (needed for liveness — see face/liveness.py). Must be called with
    the voter's face_embedding already registered.

    Order of checks matters and mirrors the spec's flow exactly:
      1. Multiple faces in ANY frame -> immediate block + fraud log.
      2. No registered face template -> hard error (shouldn't happen if
         has_face_registered is checked before allowing voting to start).
      3. Liveness check across the sequence.
      4. Identity match against the stored template.
    """
    if not voter.face_embedding:
        raise FaceError("No face registered for this voter. Face registration is required first.", 409)

    # --- 1. Multiple-face gate (checked on every frame, not just one) ---
    for frame in frames:
        count = detector.count_faces(frame)
        if count > 1:
            _log_fraud(
                voter, FraudType.MULTIPLE_FACES, FraudSeverity.CRITICAL,
                f"{count} faces detected during verification capture — voting blocked.",
                election_id=election_id,
            )
            return VerifyFaceOutcome(success=False, reason="Multiple faces detected. Voting blocked.")

    # --- 2. Liveness ---
    liveness_result = liveness.check_liveness(frames)
    if not liveness_result.passed:
        _log_fraud(
            voter, FraudType.LIVENESS_FAILURE, FraudSeverity.HIGH,
            "; ".join(liveness_result.reasons) or "Liveness check failed.",
            election_id=election_id,
        )
        return VerifyFaceOutcome(
            success=False,
            reason="Liveness check failed: " + "; ".join(liveness_result.reasons),
        )

    # --- 3. Identity match — use the first single-face frame available ---
    candidate_frame = next((f for f in frames if detector.detect_single_face_bbox(f) is not None), None)
    if candidate_frame is None:
        return VerifyFaceOutcome(success=False, reason="No clear single-face frame available for verification.")

    try:
        live_embedding = embedder.generate_embedding(candidate_frame)
    except Exception as exc:
        return VerifyFaceOutcome(success=False, reason=f"Could not generate embedding: {exc}")

    stored_embedding = decrypt_embedding(voter.face_embedding.encrypted_embedding)
    threshold = current_app.config["FACE_MATCH_THRESHOLD"]
    matched, similarity = is_match(live_embedding, stored_embedding, threshold)

    if not matched:
        _log_fraud(
            voter, FraudType.FACE_MISMATCH, FraudSeverity.HIGH,
            f"Face verification failed: similarity {similarity:.3f} below threshold {threshold}.",
            election_id=election_id,
        )
        return VerifyFaceOutcome(success=False, reason="Face does not match registered identity.", similarity=similarity)

    log_action(
        ActorType.VOTER, "face.verified", actor_id=voter.id,
        details={"election_id": str(election_id) if election_id else None, "similarity": round(similarity, 4)},
    )
    return VerifyFaceOutcome(success=True, reason="Face verified.", similarity=similarity)
