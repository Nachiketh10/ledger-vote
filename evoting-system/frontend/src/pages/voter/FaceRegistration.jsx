import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ScanFace, CheckCircle2 } from "lucide-react";
import VoterLayout from "../../layouts/VoterLayout";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import FaceCapture from "../../components/webcam/FaceCapture";
import { registerFace } from "../../services/faceService";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "../../contexts/ToastContext";

export default function FaceRegistration() {
  const navigate = useNavigate();
  const toast = useToast();
  const { refreshUser } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleCapture = async (frames) => {
    if (frames.length < 5) {
      toast("Capture didn't collect enough frames — please try again.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await registerFace(frames);
      await refreshUser();
      setSuccess(true);
      toast("Face registered successfully.", "success");
    } catch (err) {
      toast(err.response?.data?.message || "Face registration failed.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <VoterLayout>
      <div className="mx-auto max-w-lg">
        <div className="mb-5 text-center">
          <h1 className="flex items-center justify-center gap-2 font-display text-xl text-ink_text">
            <ScanFace size={20} className="text-seal" /> Register Your Face
          </h1>
        </div>

        <Card className="p-5">
          {success ? (
            <div className="text-center">
              <CheckCircle2 size={36} className="mx-auto mb-3 text-verified" />
              <p className="mb-5 text-sm text-ink_text">
                Your face is registered. You can use it to verify your identity when voting.
              </p>
              <Button onClick={() => navigate("/voter")}>Back to elections</Button>
            </div>
          ) : (
            <FaceCapture
              seconds={4}
              fps={4}
              prompt="Move your head slightly, vary your expression..."
              buttonLabel={submitting ? "Registering..." : "Start capture"}
              onComplete={handleCapture}
            />
          )}
        </Card>
      </div>
    </VoterLayout>
  );
}
