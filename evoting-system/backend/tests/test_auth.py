"""
Run with: pytest tests/test_auth.py -v
These tests only exercise pure functions (no Flask app/DB needed) so they
work the moment `bcrypt` is installed — a good first sanity check.
"""

from app.services.auth_service import hash_password, verify_password
from app.security.validators import validate_password_strength, validate_phone


def test_hash_and_verify_roundtrip():
    plain = "Str0ng!Passw0rd"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True


def test_verify_rejects_wrong_password():
    hashed = hash_password("Str0ng!Passw0rd")
    assert verify_password("wrong-password", hashed) is False


def test_password_strength_rejects_weak():
    ok, msg = validate_password_strength("weak")
    assert ok is False
    assert msg is not None


def test_password_strength_accepts_strong():
    ok, msg = validate_password_strength("Str0ng!Passw0rd")
    assert ok is True
    assert msg is None


def test_phone_validation():
    assert validate_phone("+919876543210") is True
    assert validate_phone("not-a-phone") is False
    assert validate_phone("") is False
