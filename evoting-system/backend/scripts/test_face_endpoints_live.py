"""
Live end-to-end test of the face registration/verification API — hits
your actual running Flask server (default http://127.0.0.1:5000),
creates a throwaway test voter, captures real webcam frames, and drives
the full register -> verify flow exactly the way the real frontend will.

Prerequisites:
    - `flask run` already running in another terminal
    - your webcam available

Usage:
    python scripts/test_face_endpoints_live.py
    python scripts/test_face_endpoints_live.py --base-url http://127.0.0.1:5000
"""

import argparse
import base64
import random
import string
import sys
import time
from datetime import date

import cv2
import requests


def _print_step(ok: bool, label: str, detail: str = ""):
    mark = "[OK]" if ok else "[FAIL]"
    print(f"{mark} {label}" + (f" — {detail}" if detail else ""))


def _random_suffix(n=6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def register_test_voter(base_url: str) -> dict:
    print("\n--- Creating a throwaway test voter ---")
    suffix = _random_suffix()
    payload = {
        "name": "Face Test Voter",
        "dob": "1995-01-01",
        "gender": "other",
        "phone": "+15555550123",
        "email": f"facetest_{suffix}@example.com",
        "address": "123 Test St",
        "voter_id": f"FTV-{suffix}",
        "password": "Str0ng!TestPass1",
    }
    resp = requests.post(f"{base_url}/api/auth/register", json=payload)
    if resp.status_code != 201:
        _print_step(False, "register test voter", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    _print_step(True, f"registered test voter {payload['email']}")
    return payload


def login_test_voter(base_url: str, payload: dict) -> str:
    print("\n--- Logging in as the test voter ---")
    resp = requests.post(
        f"{base_url}/api/auth/login",
        json={"email": payload["email"], "password": payload["password"], "role": "voter"},
    )
    if resp.status_code != 200:
        _print_step(False, "login", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    token = resp.json()["data"]["access_token"]
    _print_step(True, "logged in, got access token")
    return token


def _frame_to_base64_jpeg(frame) -> str:
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        raise RuntimeError("Failed to encode frame as JPEG.")
    return base64.b64encode(buffer).decode("ascii")


def capture_frames(prompt: str, duration_seconds: float, interval_seconds: float) -> list:
    print(f"\n--- Capturing frames: {prompt} ---")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        _print_step(False, "open webcam")
        sys.exit(1)

    frames = []
    start = time.time()
    last_capture = 0.0

    while time.time() - start < duration_seconds:
        ok, frame = cap.read()
        if not ok:
            continue

        display = frame.copy()
        remaining = duration_seconds - (time.time() - start)
        cv2.putText(
            display, prompt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )
        cv2.putText(
            display, f"{remaining:.1f}s left, {len(frames)} captured",
            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )
        cv2.imshow("Face capture (ESC to abort)", display)

        now = time.time()
        if now - last_capture >= interval_seconds:
            frames.append(frame)
            last_capture = now

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    _print_step(len(frames) > 0, f"captured {len(frames)} frames")
    return frames


def call_register_face(base_url: str, token: str, frames: list):
    print("\n--- Calling POST /api/face/register ---")
    images = [_frame_to_base64_jpeg(f) for f in frames]
    resp = requests.post(
        f"{base_url}/api/face/register",
        json={"images": images},
        headers={"Authorization": f"Bearer {token}"},
    )
    ok = resp.status_code == 201
    _print_step(ok, "register face", f"{resp.status_code} {resp.text}")
    if not ok:
        sys.exit(1)


def call_verify_face(base_url: str, token: str, frames: list, expect_success: bool = True):
    print(f"\n--- Calling POST /api/face/verify (expecting {'SUCCESS' if expect_success else 'REJECTION'}) ---")
    images = [_frame_to_base64_jpeg(f) for f in frames]
    resp = requests.post(
        f"{base_url}/api/face/verify",
        json={"images": images},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()
    matched_expectation = (resp.status_code == 200) == expect_success
    _print_step(matched_expectation, "verify face", f"{resp.status_code} {data}")
    return resp.status_code, data


def main():
    parser = argparse.ArgumentParser(description="Live end-to-end test of face register/verify endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    args = parser.parse_args()

    print("=" * 60)
    print("LIVE FACE API END-TO-END TEST")
    print("=" * 60)
    print("This hits your REAL running server and writes REAL rows to your Neon DB")
    print("(a throwaway test voter — safe to leave, or delete later).")

    payload = register_test_voter(args.base_url)
    token = login_test_voter(args.base_url, payload)

    reg_frames = capture_frames(
        "REGISTRATION: look at camera, move slightly", duration_seconds=6.0, interval_seconds=0.3
    )
    if len(reg_frames) < 10:
        print(f"\nOnly captured {len(reg_frames)} frames — need at least 10. Try again with better lighting.")
        sys.exit(1)

    call_register_face(args.base_url, token, reg_frames)

    input("\nPress Enter, then look at the camera and BLINK + TURN YOUR HEAD during capture...")
    verify_frames_same_person = capture_frames(
        "VERIFY: blink and turn your head", duration_seconds=3.0, interval_seconds=0.2
    )
    status, data = call_verify_face(args.base_url, token, verify_frames_same_person, expect_success=True)

    print("\n" + "=" * 60)
    if status == 200:
        similarity = data.get("data", {}).get("similarity")
        print(f"END-TO-END TEST PASSED — same-person verification succeeded (similarity={similarity})")
    else:
        print("END-TO-END TEST: verification did not succeed on the first try.")
        print("This can legitimately happen if liveness wasn't detected (try blinking/turning more")
        print("deliberately) or lighting changed between captures. Re-run to confirm.")
    print("=" * 60)


if __name__ == "__main__":
    main()
