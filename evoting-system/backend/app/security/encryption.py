"""
Field-level encryption for sensitive data at rest (face embeddings, and
anything else that shouldn't sit in the DB as plaintext even though the
DB connection itself is already TLS + access-controlled).

Uses Fernet (AES-128-CBC + HMAC) from the `cryptography` package —
authenticated encryption, so tampering is detected, not just hidden.
"""

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _get_fernet() -> Fernet:
    key = current_app.config["FIELD_ENCRYPTION_KEY"]
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_bytes(data: bytes) -> bytes:
    return _get_fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return _get_fernet().decrypt(token)
    except InvalidToken as exc:
        raise ValueError("Decryption failed: data is invalid or was tampered with.") from exc


def encrypt_str(text: str) -> bytes:
    return encrypt_bytes(text.encode("utf-8"))


def decrypt_str(token: bytes) -> str:
    return decrypt_bytes(token).decode("utf-8")
