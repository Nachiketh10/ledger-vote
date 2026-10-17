"""
Face embedding comparison. Pure numpy — no MediaPipe/InsightFace import
here, so this is directly unit-testable with plain vectors.
"""

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64).flatten()
    b = np.asarray(b, dtype=np.float64).flatten()

    if a.shape != b.shape:
        raise ValueError(f"Embedding dimension mismatch: {a.shape} vs {b.shape}")

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def is_match(embedding: np.ndarray, stored_embedding: np.ndarray, threshold: float) -> tuple[bool, float]:
    """Returns (matched, similarity_score). threshold typically ~0.5-0.6
    for InsightFace ArcFace embeddings (cosine similarity, not distance)."""
    similarity = cosine_similarity(embedding, stored_embedding)
    return similarity >= threshold, similarity


def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    Combines multiple registration-time samples (e.g. 20 captured
    frames) into a single template embedding.

    Each embedding is L2-normalized to unit length BEFORE averaging.
    This matters: raw InsightFace embeddings are NOT unit-norm (a real
    one typically has norm ~20-30) and that magnitude can vary between
    frames (lighting, angle, etc.). Averaging raw vectors would let
    whichever frame happens to have the largest magnitude dominate the
    template, even if it's just one noisy frame out of twenty. Only the
    DIRECTION of each embedding is the actual identity signal — so we
    normalize first, average the unit vectors, then re-normalize the
    result. This is the standard, robust way to build an enrollment
    template from multiple samples.
    """
    if not embeddings:
        raise ValueError("Cannot average an empty list of embeddings.")

    unit_vectors = []
    for e in embeddings:
        v = np.asarray(e, dtype=np.float64).flatten()
        norm = np.linalg.norm(v)
        if norm > 0:
            unit_vectors.append(v / norm)

    if not unit_vectors:
        raise ValueError("All provided embeddings had zero norm — invalid input.")

    mean = np.mean(unit_vectors, axis=0)
    norm = np.linalg.norm(mean)
    if norm == 0:
        raise ValueError("Averaged embedding has zero norm — invalid input embeddings.")

    return (mean / norm).astype(np.float32)
