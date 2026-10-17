"""
MediaPipe-based face detection and landmark extraction.

Two separate MediaPipe solutions are used for two different jobs:
  - FaceDetection: fast, just "how many faces and where" — used for the
    multiple-face fraud check (spec: if >1 face, block voting immediately).
  - FaceMesh: 468 detailed landmarks per face — used by liveness.py for
    blink/head-movement/smile detection, which needs actual geometry,
    not just a bounding box.
"""

import cv2
import mediapipe as mp

_mp_face_detection = mp.solutions.face_detection
_mp_face_mesh = mp.solutions.face_mesh


def count_faces(frame, min_confidence: float = 0.5) -> int:
    """Fast face count — this is what gates 'multiple faces detected,
    voting blocked' in the voting flow."""
    with _mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=min_confidence
    ) as detector:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)
        return len(results.detections) if results.detections else 0


def detect_single_face_bbox(frame, min_confidence: float = 0.5):
    """
    Returns the bounding box (x, y, w, h) in pixel coordinates of the
    single detected face, or None if zero or more-than-one faces are
    present. Callers that need "exactly one face" (registration,
    verification) should use this rather than count_faces + a separate
    detection call.
    """
    with _mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=min_confidence
    ) as detector:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

    if not results.detections or len(results.detections) != 1:
        return None

    h, w = frame.shape[:2]
    box = results.detections[0].location_data.relative_bounding_box
    x = max(0, int(box.xmin * w))
    y = max(0, int(box.ymin * h))
    bw = int(box.width * w)
    bh = int(box.height * h)
    return (x, y, bw, bh)


def get_face_landmarks(frame, min_confidence: float = 0.5):
    """
    Returns the 468 FaceMesh landmarks (list of (x, y, z) in normalized
    [0,1] coordinates) for the first detected face, or None if no face
    is found. Used by liveness.py — NOT used for the identity embedding
    itself (that's InsightFace's job, in embedder.py).
    """
    with _mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=min_confidence,
    ) as mesh:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mesh.process(rgb)

    if not results.multi_face_landmarks:
        return None

    landmarks = results.multi_face_landmarks[0].landmark
    return [(lm.x, lm.y, lm.z) for lm in landmarks]
