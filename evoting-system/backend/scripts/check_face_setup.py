"""
Standalone sanity check for the face-recognition stack — MediaPipe (face
detection) and InsightFace (embedding generation). Deliberately has NO
dependency on Flask, the database, or the rest of the app: this proves
the two ML libraries actually work on your machine before we wire them
into the real registration/verification flow.

Usage:
    # Test against your webcam (press SPACE to capture, ESC to quit)
    python scripts/check_face_setup.py

    # Test against a photo instead (useful if you don't have a webcam,
    # or want a repeatable test image)
    python scripts/check_face_setup.py --image path\\to\\photo.jpg

What this proves, step by step:
    1. cv2 / mediapipe / insightface / onnxruntime all import correctly
       (catches the exact kind of build/install issue we hit earlier).
    2. MediaPipe can detect a face in a frame.
    3. InsightFace can load its model (downloads ~300MB the first time
       you run this — needs internet access once) and generate a
       512-dimension embedding from the detected face.

If every step prints a green checkmark, the ML stack is solid and
Part 5's real registration/verification endpoints will work the same
way, just wired into the API instead of a standalone script.
"""

import argparse
import sys


def _print_step(ok: bool, label: str, detail: str = ""):
    mark = "[OK]" if ok else "[FAIL]"
    print(f"{mark} {label}" + (f" — {detail}" if detail else ""))


def check_imports():
    print("\n--- Step 1: Checking library imports ---")
    modules = {}
    all_ok = True

    for name in ("cv2", "mediapipe", "numpy"):
        try:
            modules[name] = __import__(name)
            _print_step(True, f"import {name}")
        except ImportError as exc:
            _print_step(False, f"import {name}", str(exc))
            all_ok = False

    try:
        import insightface
        modules["insightface"] = insightface
        _print_step(True, "import insightface")
    except ImportError as exc:
        _print_step(False, "import insightface", str(exc))
        print(
            "    -> If this fails on Windows with a compiler error, you need "
            "Microsoft C++ Build Tools installed (see earlier setup steps)."
        )
        all_ok = False

    try:
        import onnxruntime
        modules["onnxruntime"] = onnxruntime
        _print_step(True, "import onnxruntime")
    except ImportError as exc:
        _print_step(False, "import onnxruntime", str(exc))
        all_ok = False

    if not all_ok:
        print("\nFix the imports above before continuing — nothing else in this "
              "script (or Part 5) will work until these succeed.")
        sys.exit(1)

    return modules


def get_frame(image_path: str | None, cv2, np):
    print("\n--- Step 2: Getting a frame to test with ---")
    if image_path:
        frame = cv2.imread(image_path)
        if frame is None:
            _print_step(False, f"read image at {image_path}", "file not found or unreadable")
            sys.exit(1)
        _print_step(True, f"loaded test image ({frame.shape[1]}x{frame.shape[0]})")
        return frame

    print("No --image given — opening your webcam.")
    print("A window will open. Press SPACE to capture a frame, ESC to cancel.")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        _print_step(False, "open webcam", "no camera found at index 0")
        print("    -> Try --image path\\to\\photo.jpg instead.")
        sys.exit(1)

    captured = None
    while True:
        ok, frame = cap.read()
        if not ok:
            _print_step(False, "read frame from webcam")
            break
        cv2.imshow("Press SPACE to capture, ESC to cancel", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        if key == 32:  # SPACE
            captured = frame
            break
    cap.release()
    cv2.destroyAllWindows()

    if captured is None:
        print("No frame captured — exiting.")
        sys.exit(1)

    _print_step(True, f"captured webcam frame ({captured.shape[1]}x{captured.shape[0]})")
    return captured


def check_mediapipe_detection(frame, mediapipe, cv2):
    print("\n--- Step 3: MediaPipe face detection ---")
    mp_face_detection = mediapipe.solutions.face_detection

    with mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5
    ) as detector:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

    if not results.detections:
        _print_step(False, "detect a face", "no face found in the frame")
        print("    -> Make sure your face is clearly visible and well-lit, then retry.")
        sys.exit(1)

    count = len(results.detections)
    _print_step(True, f"detected {count} face(s)")
    if count > 1:
        print("    -> NOTE: multiple faces detected. In the real voting flow, "
              "this correctly BLOCKS voting and logs a fraud alert (see spec: "
              "'Multiple Faces Detected'). For this test it's just informational.")

    confidence = results.detections[0].score[0]
    print(f"    Top detection confidence: {confidence:.3f}")
    return results


def check_insightface_embedding(frame, insightface, np):
    print("\n--- Step 4: InsightFace embedding generation ---")
    print("Loading InsightFace model (downloads ~300MB on first run — this "
          "needs internet access once, then it's cached locally)...")

    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    _print_step(True, "InsightFace model loaded")

    faces = app.get(frame)
    if not faces:
        _print_step(False, "generate embedding", "InsightFace found no face in the frame")
        sys.exit(1)

    embedding = faces[0].embedding
    _print_step(True, f"generated embedding, shape={embedding.shape}, dtype={embedding.dtype}")

    norm = np.linalg.norm(embedding)
    print(f"    Embedding L2 norm: {norm:.3f} (typically non-zero, finite)")

    if len(faces) > 1:
        print(f"    NOTE: InsightFace also found {len(faces)} faces independently of MediaPipe.")

    return embedding


def main():
    parser = argparse.ArgumentParser(description="Sanity-check the face recognition stack.")
    parser.add_argument("--image", help="Path to a test photo instead of using the webcam.")
    args = parser.parse_args()

    print("=" * 60)
    print("FACE RECOGNITION STACK CHECK")
    print("=" * 60)

    modules = check_imports()
    cv2 = modules["cv2"]
    mediapipe = modules["mediapipe"]
    np = modules["numpy"]
    insightface = modules["insightface"]

    frame = get_frame(args.image, cv2, np)
    check_mediapipe_detection(frame, mediapipe, cv2)
    embedding = check_insightface_embedding(frame, insightface, np)

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED")
    print("=" * 60)
    print(f"Your machine can run MediaPipe detection + InsightFace embeddings "
          f"({embedding.shape[0]}-dimensional vectors). Part 5's real "
          f"registration/verification endpoints will work the same way.")


if __name__ == "__main__":
    main()
