"""
Interface stub for a physical USB fingerprint reader (e.g. DigitalPersona,
SecuGen, Suprema). NOT implemented — no specific hardware was specified,
and every vendor ships its own proprietary SDK with its own template
format, so there's nothing generic to build against.

This exists so that swapping WebAuthn for real hardware later is a
contained change: implement HardwareFingerprintAdapter for your specific
reader's SDK, and point face_service-style calling code at it instead of
webauthn_service — the FingerprintTemplate model already has the fields
for this path (auth_method="hardware_sdk", template_data for the vendor's
encrypted template blob) so no schema change would be needed.

To actually wire in a reader:
    1. Install the vendor's Python SDK/bindings.
    2. Implement the three methods below against that SDK's API.
    3. Add a route that calls this adapter instead of webauthn_service
       when auth_method == "hardware_sdk".
"""

from abc import ABC, abstractmethod


class HardwareFingerprintAdapter(ABC):
    @abstractmethod
    def capture_template(self) -> bytes:
        """Capture a fingerprint from the connected reader and return the
        vendor SDK's encrypted template blob."""
        raise NotImplementedError

    @abstractmethod
    def enroll(self, template: bytes) -> bytes:
        """Store/register a captured template, returning whatever
        reference blob should be persisted in FingerprintTemplate.template_data."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, template: bytes, stored_template: bytes) -> tuple[bool, float]:
        """Compare a freshly captured template against a stored one.
        Returns (matched, confidence_score)."""
        raise NotImplementedError


class NotConfiguredHardwareAdapter(HardwareFingerprintAdapter):
    """Default adapter — raises clearly instead of silently no-oping,
    so it's obvious hardware integration hasn't been implemented yet."""

    _MESSAGE = (
        "No physical fingerprint reader SDK is configured. This project "
        "ships with WebAuthn (platform biometrics) as the working "
        "fingerprint auth method — see app/fingerprint/webauthn_service.py. "
        "To use a physical USB reader instead, implement "
        "HardwareFingerprintAdapter for your device's vendor SDK."
    )

    def capture_template(self) -> bytes:
        raise NotImplementedError(self._MESSAGE)

    def enroll(self, template: bytes) -> bytes:
        raise NotImplementedError(self._MESSAGE)

    def verify(self, template: bytes, stored_template: bytes) -> tuple[bool, float]:
        raise NotImplementedError(self._MESSAGE)
