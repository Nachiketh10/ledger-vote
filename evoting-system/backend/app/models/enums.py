"""
Centralized enums used across models. Using Python enums backed by
Postgres ENUM types keeps invalid states unrepresentable at the DB layer.
"""

import enum


class ElectionStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    LIVE = "live"
    PAUSED = "paused"
    CLOSED = "closed"


class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ELECTION_ADMIN = "election_admin"


class FraudType(str, enum.Enum):
    MULTIPLE_FACES = "multiple_faces"
    FACE_MISMATCH = "face_mismatch"
    DUPLICATE_FACE_ENROLLMENT = "duplicate_face_enrollment"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    DUPLICATE_VOTE = "duplicate_vote"
    MULTIPLE_SESSIONS = "multiple_sessions"
    MULTIPLE_DEVICES = "multiple_devices"
    EXCESSIVE_FAILED_ATTEMPTS = "excessive_failed_attempts"
    LIVENESS_FAILURE = "liveness_failure"
    VPN_DETECTED = "vpn_detected"
    OTHER = "other"


class FraudSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActorType(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ELECTION_ADMIN = "election_admin"
    VOTER = "voter"
    SYSTEM = "system"


class SessionUserType(str, enum.Enum):
    ADMIN = "admin"
    ELECTION_ADMIN = "election_admin"
    VOTER = "voter"
