"""
Reusable input validators. Kept separate from marshmallow schemas so the
same rules can be reused in services (e.g. re-checked server-side even if
a schema is bypassed by a direct service call).
"""

import re

PASSWORD_MIN_LENGTH = 8

_PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """
    Returns (is_valid, error_message). error_message is None when valid.
    Requires: min length, upper, lower, digit, special char.
    Deliberately does NOT reveal which specific rule failed beyond a
    generic message, to avoid giving attackers a policy oracle.
    """
    if not isinstance(password, str) or len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters."

    has_upper = re.search(r"[A-Z]", password)
    has_lower = re.search(r"[a-z]", password)
    has_digit = re.search(r"\d", password)
    has_special = re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\[\]/\\+=;']", password)

    if not all([has_upper, has_lower, has_digit, has_special]):
        return False, (
            "Password must include uppercase, lowercase, a number, "
            "and a special character."
        )
    return True, None


def validate_phone(phone: str) -> bool:
    return bool(phone) and bool(_PHONE_RE.match(phone.strip()))
