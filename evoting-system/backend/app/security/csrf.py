"""
CSRF protection utility.

IMPORTANT CONTEXT: this API authenticates with JWTs sent in the
`Authorization` header (see app/config.py: JWT_TOKEN_LOCATION=["headers"]).
That pattern is NOT vulnerable to classic CSRF, because a malicious page
on another origin cannot make the victim's browser attach a custom
Authorization header to a cross-site request (unlike cookies, which
browsers attach automatically). This is a deliberate design choice, not
an oversight.

This module exists for the scenario where a future flow stores a token in
a cookie instead (e.g. an admin "remember me" cookie, or if the frontend
is later changed to httpOnly-cookie auth) — that flow MUST use these
helpers. Every route in this project reachable only via header-JWT does
not need to call these.
"""

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

CSRF_TOKEN_MAX_AGE_SECONDS = 3600  # 1 hour


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="csrf-token")


def generate_csrf_token() -> str:
    return _serializer().dumps("csrf")


def validate_csrf_token(token: str) -> bool:
    if not token:
        return False
    try:
        _serializer().loads(token, max_age=CSRF_TOKEN_MAX_AGE_SECONDS)
        return True
    except (BadSignature, SignatureExpired):
        return False
