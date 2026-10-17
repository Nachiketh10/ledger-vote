"""
Bridges a numpy embedding vector and the generic AES (Fernet) layer in
app/security/encryption.py. Kept separate from that module because the
serialization format (fixed-dtype float32 bytes) is domain-specific to
face embeddings, not a general-purpose concern.
"""

import numpy as np

from app.security.encryption import encrypt_bytes, decrypt_bytes

EMBEDDING_DTYPE = np.float32
EMBEDDING_DIM = 512  # InsightFace buffalo_l ArcFace embedding size


def encrypt_embedding(embedding: np.ndarray) -> bytes:
    arr = np.asarray(embedding, dtype=EMBEDDING_DTYPE)
    if arr.shape != (EMBEDDING_DIM,):
        raise ValueError(f"Expected a {EMBEDDING_DIM}-d embedding, got shape {arr.shape}.")
    return encrypt_bytes(arr.tobytes())


def decrypt_embedding(encrypted: bytes) -> np.ndarray:
    raw = decrypt_bytes(encrypted)
    arr = np.frombuffer(raw, dtype=EMBEDDING_DTYPE)
    if arr.shape != (EMBEDDING_DIM,):
        raise ValueError(
            f"Decrypted embedding has unexpected shape {arr.shape} "
            f"(expected {EMBEDDING_DIM},) — data may be corrupted."
        )
    return arr
