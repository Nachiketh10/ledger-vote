"""
Individual fraud rules, kept PURE (no DB queries inside) — each function
takes data the caller already gathered and returns a FraudSignal or
None. This mirrors the pattern used for election_lifecycle.py and
blockchain/verifier.py: business rules stay testable in isolation, and
the DB-facing gathering happens one layer up (see app/fraud/scorer.py).

Multiple-faces, face-mismatch, and liveness-failure rules are NOT here
— they're checked and logged directly in app/services/face_service.py,
since they're specific to the face-verification step itself, not a
general voting-time signal. This module covers the remaining rules from
the spec: duplicate vote, multiple sessions, multiple devices, excessive
failed attempts, and VPN detection.
"""

from dataclasses import dataclass

from app.models.enums import FraudType, FraudSeverity


@dataclass
class FraudSignal:
    fraud_type: FraudType
    severity: FraudSeverity
    score: int  # 0-100, contribution to the overall fraud score
    description: str


def check_duplicate_vote(already_voted: bool) -> FraudSignal | None:
    if already_voted:
        return FraudSignal(
            FraudType.DUPLICATE_VOTE,
            FraudSeverity.CRITICAL,
            100,
            "Voter has already cast a vote in this election.",
        )
    return None


def check_multiple_sessions(active_session_count: int, max_allowed: int = 1) -> FraudSignal | None:
    if active_session_count > max_allowed:
        return FraudSignal(
            FraudType.MULTIPLE_SESSIONS,
            FraudSeverity.MEDIUM,
            40,
            f"{active_session_count} active sessions detected for this voter "
            f"(max allowed: {max_allowed}).",
        )
    return None


def check_multiple_devices(distinct_device_count: int, max_allowed: int = 1) -> FraudSignal | None:
    if distinct_device_count > max_allowed:
        return FraudSignal(
            FraudType.MULTIPLE_DEVICES,
            FraudSeverity.MEDIUM,
            40,
            f"{distinct_device_count} distinct devices detected recently for this "
            f"voter (max allowed: {max_allowed}).",
        )
    return None


def check_excessive_failed_attempts(failed_attempts: int, threshold: int) -> FraudSignal | None:
    if failed_attempts >= threshold:
        return FraudSignal(
            FraudType.EXCESSIVE_FAILED_ATTEMPTS,
            FraudSeverity.HIGH,
            60,
            f"{failed_attempts} failed authentication attempts (threshold: {threshold}).",
        )
    return None


def check_vpn(is_vpn: bool) -> FraudSignal | None:
    """
    HONESTY NOTE: `is_vpn` must come from a real IP-intelligence provider
    (e.g. IPQualityScore, ipinfo.io, MaxMind) to mean anything — no such
    provider is wired in here, since that needs an API key and outbound
    network access this project doesn't assume you have configured. This
    function exists so the rule has a defined place to plug into once you
    choose a provider; callers that don't have VPN data should simply not
    call this (or always pass is_vpn=False), which is the current default
    throughout the app. This matches the spec's own listing of VPN
    detection as "(optional)".
    """
    if is_vpn:
        return FraudSignal(
            FraudType.VPN_DETECTED,
            FraudSeverity.LOW,
            20,
            "Request originated from a VPN or proxy IP address.",
        )
    return None
