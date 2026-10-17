import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, ArrowRight, ArrowLeft } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { registerFace } from "../../services/faceService";
import AuthLayout from "../../layouts/AuthLayout";
import FormField, { inputClass } from "../../components/ui/FormField";
import PasswordInput from "../../components/ui/PasswordInput";
import Button from "../../components/ui/Button";
import FaceCapture from "../../components/webcam/FaceCapture";
import { useToast } from "../../contexts/ToastContext";

const STEPS = ["details", "face", "done"];

const STEP_META = {
  details: { title: "Register to vote", subtitle: "Your details, then your face — one flow." },
  face: { title: "Register your face", subtitle: null },
  done: { title: "You're all set", subtitle: null },
};

export default function RegisterPage() {
  const { register: registerAccount, refreshUser } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [step, setStep] = useState("details");
  const [serverError, setServerError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [faceDone, setFaceDone] = useState(false);

  const {
    register: registerField,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const onCreateAccount = async (data) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      await registerAccount(data);
      setStep("face");
    } catch (err) {
      const messages = err.response?.data?.errors;
      const flatMessage = messages
        ? Object.values(messages).flat().join(" ")
        : err.response?.data?.message ?? "Registration failed. Please check your details.";
      setServerError(flatMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFaceCapture = async (frames) => {
    if (frames.length < 5) {
      toast("Capture didn't collect enough frames — please try again.", "error");
      return;
    }
    try {
      await registerFace(frames);
      await refreshUser();
      setFaceDone(true);
      toast("Face registered.", "success");
    } catch (err) {
      toast(err.response?.data?.message || "Face registration failed.", "error");
    }
  };

  const meta = STEP_META[step];

  return (
    <AuthLayout title={meta.title} subtitle={meta.subtitle}>
      <StepIndicator step={step} />

      <AnimatePresence mode="wait">
        {step === "details" && (
          <StepWrap key="details">
            {serverError && (
              <div className="mb-4 rounded-md border border-alert/30 bg-alert/5 px-3.5 py-2.5 text-sm text-alert">
                {serverError}
              </div>
            )}
            <form onSubmit={handleSubmit(onCreateAccount)} noValidate>
              <FormField label="Full name" error={errors.name?.message}>
                <input className={inputClass} {...registerField("name", { required: "Full name is required." })} />
              </FormField>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Date of birth" error={errors.dob?.message}>
                  <input type="date" className={inputClass} {...registerField("dob", { required: "Required." })} />
                </FormField>
                <FormField label="Gender" error={errors.gender?.message}>
                  <select className={inputClass} {...registerField("gender")}>
                    <option value="">Prefer not to say</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </FormField>
              </div>

              <FormField label="Voter ID" error={errors.voter_id?.message}>
                <input
                  className={inputClass}
                  placeholder="Your official registration ID"
                  {...registerField("voter_id", { required: "Voter ID is required." })}
                />
              </FormField>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Email" error={errors.email?.message}>
                  <input type="email" className={inputClass} {...registerField("email", { required: "Required." })} />
                </FormField>
                <FormField label="Phone" error={errors.phone?.message}>
                  <input className={inputClass} {...registerField("phone", { required: "Required." })} />
                </FormField>
              </div>

              <FormField label="Address" error={errors.address?.message}>
                <input className={inputClass} {...registerField("address")} />
              </FormField>

              <FormField label="Password" error={errors.password?.message}>
                <PasswordInput
                  placeholder="At least 8 characters, mixed case, a number and symbol"
                  {...registerField("password", { required: "Password is required." })}
                />
              </FormField>

              <Button type="submit" variant="primary" size="md" className="mt-2 w-full" disabled={isSubmitting}>
                {isSubmitting ? "Creating account…" : "Continue to face registration"} <ArrowRight size={15} />
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-muted">
              Already registered?{" "}
              <Link to="/login" className="font-medium text-seal hover:underline">
                Log in
              </Link>
            </p>
          </StepWrap>
        )}

        {step === "face" && (
          <StepWrap key="face">
            <p className="mb-4 text-center text-sm text-muted">
              Move your head slightly and vary your expression during capture.
            </p>
            <FaceCapture
              seconds={4}
              fps={4}
              prompt="Move your head slightly, vary your expression..."
              buttonLabel="Start capture"
              onComplete={handleFaceCapture}
            />
            <NavRow
              onNext={() => setStep("done")}
              nextLabel="Continue"
              nextDisabled={!faceDone}
            />
          </StepWrap>
        )}

        {step === "done" && (
          <StepWrap key="done">
            <div className="text-center">
              <CheckCircle2 size={40} className="mx-auto mb-3 text-verified" />
              <p className="text-sm text-muted">
                Your account and face are registered. An election admin will verify
                your details before you're added to any ballot.
              </p>
              <Button className="mt-6 w-full" onClick={() => navigate("/voter")}>
                Go to my elections
              </Button>
            </div>
          </StepWrap>
        )}
      </AnimatePresence>
    </AuthLayout>
  );
}

function NavRow({ onBack, onNext, nextLabel = "Continue", nextDisabled = false }) {
  return (
    <div className="mt-5 flex items-center justify-between">
      {onBack ? (
        <button
          onClick={onBack}
          className="flex items-center gap-1 text-sm text-muted hover:text-ink_text"
        >
          <ArrowLeft size={14} /> Back
        </button>
      ) : (
        <span />
      )}
      <Button onClick={onNext} disabled={nextDisabled} size="sm">
        {nextLabel} <ArrowRight size={14} />
      </Button>
    </div>
  );
}

function StepIndicator({ step }) {
  const idx = STEPS.indexOf(step);
  return (
    <div className="mb-6 flex gap-1.5">
      {STEPS.map((s, i) => (
        <div
          key={s}
          className={`h-1 flex-1 rounded-full ${i <= idx ? "bg-seal" : "bg-ink/10 dark:bg-white/10"}`}
        />
      ))}
    </div>
  );
}

function StepWrap({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
    >
      {children}
    </motion.div>
  );
}
