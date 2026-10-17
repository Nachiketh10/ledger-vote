"""
InsightFace-based embedding generation. The model (buffalo_l, ~300MB) is
loaded ONCE per process and cached at module level — re-loading it per
request would make every single API call take several seconds.

Separate from detector.py deliberately: MediaPipe answers "how many
faces / where" (fast, used for fraud gating), InsightFace answers "whose
face is this" (the actual biometric identity, via a 512-d embedding).
"""

import numpy as np

_face_analysis_app = None


class NoFaceDetectedError(Exception):
    pass


class MultipleFacesDetectedError(Exception):
    pass


def _get_app():
    """Lazy singleton — the model only loads on first actual use (e.g.
    not at Flask app startup, which would slow down every `flask run`
    and every test run that never touches face recognition)."""
    global _face_analysis_app
    if _face_analysis_app is None:
        from insightface.app import FaceAnalysis

        _face_analysis_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_analysis_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_analysis_app


def generate_embedding(frame: np.ndarray) -> np.ndarray:
    """
    Runs InsightFace on a single frame and returns its 512-d embedding.
    Raises if zero or more than one face is found — callers are expected
    to have already gated on exactly-one-face via detector.py before
    calling this (this check is a second, independent safety net, not
    a replacement for that gate).
    """
    app = _get_app()
    faces = app.get(frame)

    if not faces:
        raise NoFaceDetectedError("InsightFace did not detect a face in the frame.")
    if len(faces) > 1:
        raise MultipleFacesDetectedError(
            f"InsightFace detected {len(faces)} faces in a frame expected to contain one."
        )

    return faces[0].embedding.astype(np.float32)


def generate_embeddings_batch(frames: list[np.ndarray]) -> list[np.ndarray]:
    """
    Used at registration time (spec: capture 20 images). Frames that
    fail (no face / multiple faces / any InsightFace error) are simply
    skipped rather than aborting the whole batch — a single bad frame
    (motion blur, blink at the wrong moment) shouldn't fail an entire
    20-frame registration. The caller decides the minimum acceptable
    count of successful samples (see face_service.py).
    """
    embeddings = []
    for frame in frames:
        try:
            embeddings.append(generate_embedding(frame))
        except Exception:
            # A single bad frame (blink, motion blur, brief occlusion)
            # shouldn't abort the whole registration batch — just skip it.
            continue
    return embeddings
