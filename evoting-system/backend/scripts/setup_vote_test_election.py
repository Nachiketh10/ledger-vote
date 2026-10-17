"""
Sets up everything needed for a full live vote test that ONLY needs
admin API calls (no webcam) — creates a test election with 2
candidates, registers a throwaway voter, verifies them, marks them
eligible, and starts the election.

Why this is split from the browser test page: face registration needs
a real webcam (getUserMedia), which can't be scripted from plain
Python. This script handles everything that CAN be scripted (all the
admin setup), then hands off to scripts/vote_test.html (served at
/dev/vote-test) for the browser-only parts: face registration and
finally casting the vote itself.

Usage:
    python scripts/setup_vote_test_election.py --admin-email admin@example.com --admin-password "Str0ng!Pass1"
"""

import argparse
import random
import string
import sys

import requests


def _print_step(ok: bool, label: str, detail: str = ""):
    mark = "[OK]" if ok else "[FAIL]"
    print(f"{mark} {label}" + (f" — {detail}" if detail else ""))


def _random_suffix(n=6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def main():
    parser = argparse.ArgumentParser(description="Set up a live vote test election + voter.")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--admin-password", required=True)
    args = parser.parse_args()

    base = args.base_url
    suffix = _random_suffix()

    print("=" * 60)
    print("VOTE TEST SETUP")
    print("=" * 60)

    # --- Admin login ---
    resp = requests.post(
        f"{base}/api/auth/login",
        json={"email": args.admin_email, "password": args.admin_password, "role": "super_admin"},
    )
    if resp.status_code != 200:
        _print_step(False, "admin login", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    admin_token = resp.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    _print_step(True, "logged in as admin")

    # --- Create election ---
    resp = requests.post(
        f"{base}/api/elections",
        json={
            "title": f"Vote Test Election {suffix}",
            "description": "Automated end-to-end vote test.",
            "start_date": "2026-01-01T00:00:00Z",
            "end_date": "2030-01-01T00:00:00Z",
        },
        headers=admin_headers,
    )
    if resp.status_code != 201:
        _print_step(False, "create election", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    election_id = resp.json()["data"]["id"]
    _print_step(True, f"created election {election_id}")

    # --- Add 2 candidates ---
    for name in ("Candidate A", "Candidate B"):
        resp = requests.post(
            f"{base}/api/elections/{election_id}/candidates",
            json={"name": name},
            headers=admin_headers,
        )
        if resp.status_code != 201:
            _print_step(False, f"add candidate {name}", f"{resp.status_code} {resp.text}")
            sys.exit(1)
    _print_step(True, "added 2 candidates")

    # --- Register test voter ---
    voter_email = f"votetest_{suffix}@example.com"
    voter_password = "Str0ng!TestPass1"
    resp = requests.post(
        f"{base}/api/auth/register",
        json={
            "name": "Vote Test Voter",
            "dob": "1995-01-01",
            "gender": "other",
            "phone": "+15555550123",
            "email": voter_email,
            "address": "123 Test St",
            "voter_id": f"VTV-{suffix}",
            "password": voter_password,
        },
    )
    if resp.status_code != 201:
        _print_step(False, "register voter", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    voter_uuid = resp.json()["data"]["id"]
    voter_registration_id = resp.json()["data"]["voter_id"]  # e.g. "VTV-abc123"
    _print_step(True, f"registered voter {voter_email} (voter_id={voter_registration_id})")

    # --- Verify voter (uses the internal UUID) ---
    resp = requests.post(
        f"{base}/api/admin/voters/{voter_uuid}/verify",
        json={"note": "auto-verified by setup script"},
        headers=admin_headers,
    )
    if resp.status_code != 200:
        _print_step(False, "verify voter", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    _print_step(True, "voter verified")

    # --- Make voter eligible (uses the human-readable voter_id, matching
    # what an admin would actually type in — see election_service.set_eligible_voters) ---
    resp = requests.put(
        f"{base}/api/elections/{election_id}/eligible-voters",
        json={"voter_ids": [voter_registration_id]},
        headers=admin_headers,
    )
    if resp.status_code != 200:
        _print_step(False, "set eligible voters", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    _print_step(True, "voter marked eligible")

    # --- Start election ---
    resp = requests.post(f"{base}/api/elections/{election_id}/start", headers=admin_headers)
    if resp.status_code != 200:
        _print_step(False, "start election", f"{resp.status_code} {resp.text}")
        sys.exit(1)
    _print_step(True, "election started (status: live)")

    print("\n" + "=" * 60)
    print("SETUP COMPLETE — now open the browser test page to finish the flow:")
    print("=" * 60)
    print(f"\n  1. Make sure `flask run` is running (it already is, if you got this far).")
    print(f"  2. Open: {base}/dev/vote-test")
    print(f"  3. Enter these details on the page:")
    print(f"       Voter email:    {voter_email}")
    print(f"       Voter password: {voter_password}")
    print(f"       Election ID:    {election_id}")
    print(f"  4. Click through: Login -> Register Face -> Cast Vote")
    print()


if __name__ == "__main__":
    main()
