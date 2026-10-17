import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Fingerprint, CheckCircle2, AlertTriangle } from "lucide-react";
import VoterLayout from "../../layouts/VoterLayout";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { registerFingerprint } from "../../services/fingerprintService";
import { isWebAuthnSupported } from "../../utils/webauthn";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "../../contexts/ToastContext";

export default function FingerprintRegistration() {
  const navigate = useNavigate();
  const toast = useToast();
  const { refreshUser } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const supported = isWebAuthnSupported();

  const handleRegister = async () => {
    setSubmitting(true);
    try {
      await registerFingerprint();
      await refreshUser();
      setSuccess(true);
      toast("Fingerprint registered successfully.", "success");
    } catch (err) {
      const message =
        err.name === "NotAllowedError"
          ? "The prompt was cancelled or timed out. Please try again."
          : err.response?.data?.message || err.message || "Fingerprint registration failed.";
      toast(message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <VoterLayout>
      <div className="mx-auto max-w-lg">
        <div className="mb-8 text-center">
          <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-seal/10 text-seal">
            <Fingerprint size={22} />
          </span>
          <h1 className="font-display text-2xl text-ink_text">Register Your Fingerprint</h1>
          <p className="mt-2 text-sm text-muted">
            Uses your device's built-in biometrics (Windows Hello, Touch ID, or Android
            fingerprint) via the WebAuthn standard — your actual fingerprint data never
            leaves your device.
          </p>
        </div>

        <Card className="p-8 text-center">
          {!supported ? (
            <div className="flex flex-col items-center gap-3 text-alert">
              <AlertTriangle size={32} />
              <p className="text-sm">
                Your browser doesn't support WebAuthn. Try Chrome, Edge, or Safari on a
                device with a fingerprint sensor, Windows Hello, or Face ID/Touch ID.
              </p>
            </div>
          ) : success ? (
            <div>
              <CheckCircle2 size={40} className="mx-auto mb-3 text-verified" />
              <p className="mb-6 text-sm text-ink_text">
                Your fingerprint is registered. You can use it to verify your identity
                when voting.
              </p>
              <Button onClick={() => navigate("/voter")}>Back to elections</Button>
            </div>
          ) : (
            <>
              <p className="mb-6 text-sm text-muted">
                Click below, then follow your device's prompt (fingerprint sensor,
                Windows Hello, or Face ID).
              </p>
              <Button onClick={handleRegister} disabled={submitting}>
                {submitting ? "Waiting for biometric..." : "Register fingerprint"}
              </Button>
            </>
          )}
        </Card>
      </div>
    </VoterLayout>
  );
}
