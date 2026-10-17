"""
Application configuration.

All secrets/URLs are read from environment variables — never hardcoded.
Copy .env.example to .env and fill in real values before running.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _require(key: str, default: str | None = None) -> str:
    """Fetch an env var, raising a clear error if missing and no default given."""
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(
            f"Missing required environment variable: {key}. "
            f"Check your .env file against .env.example."
        )
    return value


class BaseConfig:
    # --- Core ---
    SECRET_KEY = _require("SECRET_KEY", "dev-secret-change-me")
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = False
    TESTING = False

    # --- Database (Neon PostgreSQL) ---
    # Neon connection strings look like:
    # postgresql://user:password@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require
    SQLALCHEMY_DATABASE_URI = _require("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # avoids stale-connection errors on serverless Postgres
        "pool_recycle": 280,     # Neon idles/recycles connections; recycle before it does
        "pool_size": 5,
        "max_overflow": 10,
    }

    # --- JWT ---
    JWT_SECRET_KEY = _require("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # --- CORS ---
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per hour"

    # --- Encryption (AES key for face embeddings / PII at rest) ---
    # Must be a urlsafe base64-encoded 32-byte key. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    FIELD_ENCRYPTION_KEY = _require("FIELD_ENCRYPTION_KEY", None)

    # --- File uploads ---
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    # --- Face recognition ---
    FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.55"))
    FACE_REGISTRATION_SAMPLE_COUNT = int(os.getenv("FACE_REGISTRATION_SAMPLE_COUNT", "20"))

    # --- Fraud detection ---
    MAX_FAILED_AUTH_ATTEMPTS = int(os.getenv("MAX_FAILED_AUTH_ATTEMPTS", "5"))
    FRAUD_SCORE_BLOCK_THRESHOLD = int(os.getenv("FRAUD_SCORE_BLOCK_THRESHOLD", "70"))



class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    # In production, refuse to boot on default/dev secrets.
    if os.getenv("SECRET_KEY") in (None, "dev-secret-change-me"):
        raise RuntimeError("Refusing to start: SECRET_KEY must be set in production.")
    if os.getenv("JWT_SECRET_KEY") in (None, "dev-jwt-secret-change-me"):
        raise RuntimeError("Refusing to start: JWT_SECRET_KEY must be set in production.")


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", BaseConfig.SQLALCHEMY_DATABASE_URI)


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
