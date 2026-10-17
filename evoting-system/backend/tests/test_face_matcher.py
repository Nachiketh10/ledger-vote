"""
Run with: pytest tests/test_face_matcher.py -v
Pure numpy — no MediaPipe/InsightFace/Flask/DB needed, so this runs
identically here and in CI without any of the heavy ML dependencies.
"""

import numpy as np
import pytest

from app.face.matcher import cosine_similarity, is_match, average_embeddings


def test_identical_vectors_have_similarity_one():
    a = np.random.rand(512).astype(np.float32)
    assert cosine_similarity(a, a) == pytest.approx(1.0, abs=1e-5)


def test_orthogonal_vectors_have_similarity_zero():
    a = np.zeros(512, dtype=np.float32)
    a[0] = 1.0
    b = np.zeros(512, dtype=np.float32)
    b[1] = 1.0
    assert cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)


def test_opposite_vectors_have_similarity_negative_one():
    a = np.zeros(512, dtype=np.float32)
    a[0] = 1.0
    assert cosine_similarity(a, -a) == pytest.approx(-1.0, abs=1e-5)


def test_zero_vector_returns_zero_similarity_not_a_crash():
    a = np.zeros(512, dtype=np.float32)
    b = np.random.rand(512).astype(np.float32)
    assert cosine_similarity(a, b) == 0.0


def test_dimension_mismatch_raises():
    with pytest.raises(ValueError):
        cosine_similarity(np.zeros(512), np.zeros(256))


def test_is_match_true_above_threshold():
    a = np.random.rand(512).astype(np.float32)
    matched, sim = is_match(a, a, threshold=0.5)
    assert matched is True
    assert sim > 0.99


def test_is_match_false_below_threshold():
    a = np.zeros(512, dtype=np.float32)
    a[0] = 1.0
    b = np.zeros(512, dtype=np.float32)
    b[1] = 1.0
    matched, sim = is_match(a, b, threshold=0.5)
    assert matched is False


def test_average_of_identical_embeddings_matches_original_direction():
    a = np.random.rand(512).astype(np.float32)
    avg = average_embeddings([a, a, a])
    assert cosine_similarity(avg, a) == pytest.approx(1.0, abs=1e-4)


def test_average_is_l2_normalized():
    vectors = [np.random.rand(512).astype(np.float32) for _ in range(5)]
    avg = average_embeddings(vectors)
    assert np.linalg.norm(avg) == pytest.approx(1.0, abs=1e-5)


def test_average_of_empty_list_raises():
    with pytest.raises(ValueError):
        average_embeddings([])


def test_average_smooths_out_a_single_noisy_sample():
    """
    Registration captures ~20 frames; one bad/noisy sample shouldn't
    dominate the resulting template. Average of many similar vectors
    plus one outlier should still be much closer to the consistent
    vectors than to the outlier.
    """
    base = np.zeros(512, dtype=np.float32)
    base[0] = 1.0
    consistent = [base + np.random.normal(0, 0.01, 512).astype(np.float32) for _ in range(9)]
    outlier = np.random.rand(512).astype(np.float32)

    avg = average_embeddings(consistent + [outlier])
    assert cosine_similarity(avg, base) > cosine_similarity(avg, outlier)
