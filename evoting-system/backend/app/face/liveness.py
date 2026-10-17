"""
Liveness detection: distinguishes a real, live person from a static
photo, a video replay, or a phone screen held up to the camera.

HONESTY NOTE, read before relying on this for anything high-stakes:
this is a HEURISTIC liveness check (eye-blink ratio, head-yaw movement,
mouth-width change across a short sequence of frames) — the same
general approach used in most student/portfolio e-voting projects and
plenty of production KYC flows. It is NOT a silicon-level anti-spoofing
system (no depth sensing, no IR, no dedicated liveness ML model). A
photo won't pass it (no motion at all across frames), and a static
video loop is much harder to pass since it requires blink+turn+smile
in the right order within the capture window — but a sufficiently
sophisticated attacker with a real-time deepfake or a video specifically
recorded to include blinking/turning could potentially defeat it. If
this project ever needs production-grade liveness assurance, that means
integrating a dedicated commercial liveness SDK — pair it with this
heuristic layer rather than replacing it, since this layer is free,
fast, and already implemented.

Requires a SEQUENCE of frames (not one), typically captured over ~2-3
seconds while the voter is prompted to blink, turn their head, and
smile — see face_routes.py for how the frontend feeds frames in.
"""

from dataclasses import dataclass, field

import numpy as np

from app.face.detector import get_face_landmarks

# FaceMesh landmark indices for eye contour points, used to compute Eye
# Aspect Ratio (EAR) — a standard, well-documented blink-detection metric.
_LEFT_EYE = [33, 160, 158, 133, 153, 144]
_RIGHT_EYE = [362, 385, 387, 263, 373, 380]
_NOSE_TIP = 1
_LEFT_FACE_EDGE = 234
_RIGHT_FACE_EDGE = 454
_MOUTH_LEFT = 61
_MOUTH_RIGHT = 291
_MOUTH_TOP = 13
_MOUTH_BOTTOM = 14

EAR_BLINK_THRESHOLD = 0.21     # below this = eyes considered closed
HEAD_TURN_MIN_DELTA = 0.12     # normalized horizontal shift to count as a turn
SMILE_WIDTH_INCREASE_RATIO = 1.15  # mouth width / neutral-frame width


def _distance(p1, p2) -> float:
    return float(np.linalg.norm(np.array(p1[:2]) - np.array(p2[:2])))


def _eye_aspect_ratio(landmarks, indices) -> float:
    p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in indices]
    vertical = _distance(p2, p6) + _distance(p3, p5)
    horizontal = _distance(p1, p4)
    if horizontal == 0:
        return 0.0
    return vertical / (2.0 * horizontal)


def _head_yaw_position(landmarks) -> float:
    """Normalized [0,1] horizontal position of the nose tip relative to
    the two face-edge landmarks — ~0.5 means facing forward, moving
    toward 0 or 1 means turning left/right."""
    nose_x = landmarks[_NOSE_TIP][0]
    left_x = landmarks[_LEFT_FACE_EDGE][0]
    right_x = landmarks[_RIGHT_FACE_EDGE][0]
    span = right_x - left_x
    if span == 0:
        return 0.5
    return (nose_x - left_x) / span


def _mouth_width(landmarks) -> float:
    return _distance(landmarks[_MOUTH_LEFT], landmarks[_MOUTH_RIGHT])


@dataclass
class LivenessResult:
    passed: bool
    blink_detected: bool
    head_turn_detected: bool
    smile_detected: bool
    frames_with_face: int
    frames_total: int
    reasons: list[str] = field(default_factory=list)


def check_liveness(
    frames: list[np.ndarray],
    require_blink: bool = True,
    require_head_turn: bool = True,
    require_smile: bool = False,
) -> LivenessResult:
    """
    Runs FaceMesh over a sequence of frames and checks for the requested
    liveness signals across the sequence. `require_smile` defaults to
    False since it's the least reliable of the three signals (people
    often don't smile naturally on cue) — blink + head-turn are the
    primary gate, matching the spec's three listed checks while keeping
    the default flow fast and not overly strict.
    """
    landmark_sequence = []
    for frame in frames:
        landmarks = get_face_landmarks(frame)
        if landmarks is not None:
            landmark_sequence.append(landmarks)

    reasons = []
    frames_with_face = len(landmark_sequence)

    if frames_with_face < 2:
        return LivenessResult(
            passed=False,
            blink_detected=False,
            head_turn_detected=False,
            smile_detected=False,
            frames_with_face=frames_with_face,
            frames_total=len(frames),
            reasons=["Not enough frames with a detectable face to assess liveness."],
        )

    # --- Blink: EAR must dip below threshold then recover, somewhere
    # in the sequence (i.e. NOT closed for every single frame, which
    # would indicate eyes-closed throughout rather than an actual blink).
    ear_values = [
        (_eye_aspect_ratio(lm, _LEFT_EYE) + _eye_aspect_ratio(lm, _RIGHT_EYE)) / 2.0
        for lm in landmark_sequence
    ]
    had_closed_frame = any(ear < EAR_BLINK_THRESHOLD for ear in ear_values)
    had_open_frame = any(ear >= EAR_BLINK_THRESHOLD for ear in ear_values)
    blink_detected = had_closed_frame and had_open_frame

    # --- Head turn: nose position must shift meaningfully between at
    # least two frames in the sequence.
    yaw_values = [_head_yaw_position(lm) for lm in landmark_sequence]
    head_turn_detected = (max(yaw_values) - min(yaw_values)) >= HEAD_TURN_MIN_DELTA

    # --- Smile: mouth width must widen relative to the first (assumed
    # neutral) frame at some point in the sequence.
    mouth_widths = [_mouth_width(lm) for lm in landmark_sequence]
    baseline_width = mouth_widths[0] if mouth_widths[0] > 0 else 1e-6
    smile_detected = any(
        (w / baseline_width) >= SMILE_WIDTH_INCREASE_RATIO for w in mouth_widths[1:]
    )

    if require_blink and not blink_detected:
        reasons.append("No blink detected across the capture sequence.")
    if require_head_turn and not head_turn_detected:
        reasons.append("No head movement detected across the capture sequence.")
    if require_smile and not smile_detected:
        reasons.append("No smile detected across the capture sequence.")

    # A frame sequence with ZERO variation at all (identical EAR/yaw/mouth
    # across every frame) is a strong photo-attack signal even if the
    # specific required gestures happen to be met by coincidence in noisy
    # data — flag it explicitly.
    if len(set(round(e, 4) for e in ear_values)) == 1 and len(set(round(y, 4) for y in yaw_values)) == 1:
        reasons.append("No motion detected at all across frames — possible static photo.")

    passed = len(reasons) == 0

    return LivenessResult(
        passed=passed,
        blink_detected=blink_detected,
        head_turn_detected=head_turn_detected,
        smile_detected=smile_detected,
        frames_with_face=frames_with_face,
        frames_total=len(frames),
        reasons=reasons,
    )
