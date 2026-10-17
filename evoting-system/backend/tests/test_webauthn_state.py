"""
Run with: pytest tests/test_webauthn_state.py -v

Tests the stateless challenge sign/verify round-trip that
app/fingerprint/webauthn_service.py relies on. This is the one part of
the WebAuthn module that's testable without an actual browser ceremony
— generate_registration_options_for_voter/verify_registration_for_voter
etc. genuinely need a real authenticator and can't be unit tested here
(see scripts/webauthn_test.html for that).

Uses a minimal standalone Flask app (only SECRET_KEY + the WebAuthn TTL
setting are needed) rather than the full create_app() factory, since no
database is involved in this layer.
"""

import time

import pytest
from flask import Flask

from app.fingerprint.webauthn_service import _sign_state, _unsign_state, FingerprintError


@pytest.fixture
def app_context():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key-not-for-production"
    app.config["WEBAUTHN_CHALLENGE_TTL_SECONDS"] = 1  # short, so expiry is testable quickly
    with app.app_context():
        yield app


def test_roundtrip_recovers_original_challenge(app_context):
    challenge = b"\x01\x02\x03random-challenge-bytes\xff\xfe"
    voter_id = "11111111-1111-1111-1111-111111111111"

    state = _sign_state(voter_id, challenge, "register")
    recovered = _unsign_state(state, voter_id, "register")

    assert recovered == challenge


def test_wrong_voter_id_is_rejected(app_context):
    challenge = b"some-challenge"
    state = _sign_state("voter-a", challenge, "register")

    with pytest.raises(FingerprintError) as exc_info:
        _unsign_state(state, "voter-b", "register")
    assert exc_info.value.status == 403


def test_wrong_purpose_is_rejected(app_context):
    """A state token signed for registration must not be usable for
    authentication, and vice versa — the salt binds it to one purpose."""
    challenge = b"some-challenge"
    state = _sign_state("voter-a", challenge, "register")

    with pytest.raises(FingerprintError):
        _unsign_state(state, "voter-a", "authenticate")


def test_tampered_state_is_rejected(app_context):
    challenge = b"some-challenge"
    state = _sign_state("voter-a", challenge, "register")
    tampered = state[:-1] + ("A" if state[-1] != "A" else "B")

    with pytest.raises(FingerprintError):
        _unsign_state(tampered, "voter-a", "register")


def test_expired_state_is_rejected(app_context):
    """
    Note on timing: itsdangerous timestamps have 1-second integer
    granularity, so a small TTL needs a sleep comfortably larger than
    it to reliably trigger expiry (sleeping only slightly longer than
    the TTL can land on a rounding boundary and flake). 3s sleep vs 1s
    TTL gives a safe margin.
    """
    challenge = b"some-challenge"
    state = _sign_state("voter-a", challenge, "register")

    time.sleep(3.0)  # TTL is set to 1 second in the fixture

    with pytest.raises(FingerprintError) as exc_info:
        _unsign_state(state, "voter-a", "register")
    assert exc_info.value.status == 400


def test_different_challenges_produce_different_states(app_context):
    state1 = _sign_state("voter-a", b"challenge-one", "register")
    state2 = _sign_state("voter-a", b"challenge-two", "register")
    assert state1 != state2
