"""
Run with: pytest tests/test_face_storage.py -v

Uses a minimal standalone Flask app (not the full create_app() factory)
since only app.config["FIELD_ENCRYPTION_KEY"] is needed for this module
— no database connection required.
"""

import numpy as np
import pytest
from cryptography.fernet import Fernet, InvalidToken
from flask import Flask

from app.face.storage import encrypt_embedding, decrypt_embedding, EMBEDDING_DIM


@pytest.fixture
def app_context():
    app = Flask(__name__)
    app.config["FIELD_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
    with app.app_context():
        yield app


def test_roundtrip_preserves_values(app_context):
    original = np.random.rand(EMBEDDING_DIM).astype(np.float32)
    encrypted = encrypt_embedding(original)
    decrypted = decrypt_embedding(encrypted)
    assert np.allclose(original, decrypted, atol=1e-6)


def test_ciphertext_does_not_contain_plaintext_bytes(app_context):
    original = np.random.rand(EMBEDDING_DIM).astype(np.float32)
    encrypted = encrypt_embedding(original)
    assert original.tobytes() not in encrypted


def test_wrong_dimension_rejected(app_context):
    with pytest.raises(ValueError):
        encrypt_embedding(np.random.rand(128).astype(np.float32))


def test_tampered_ciphertext_fails_to_decrypt(app_context):
    original = np.random.rand(EMBEDDING_DIM).astype(np.float32)
    encrypted = bytearray(encrypt_embedding(original))
    encrypted[15] ^= 0xFF  # flip some bits

    with pytest.raises(ValueError):  # app.security.encryption wraps InvalidToken as ValueError
        decrypt_embedding(bytes(encrypted))


def test_different_key_cannot_decrypt(app_context):
    original = np.random.rand(EMBEDDING_DIM).astype(np.float32)
    encrypted = encrypt_embedding(original)

    # Swap in a different key after encrypting — simulates trying to
    # decrypt data with the wrong FIELD_ENCRYPTION_KEY.
    app_context.config["FIELD_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

    with pytest.raises(ValueError):
        decrypt_embedding(encrypted)
