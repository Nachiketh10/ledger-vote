import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2, XCircle, ShieldCheck, Link2, ArrowLeft,
} from "lucide-react";
import VoterLayout from "../../layouts/VoterLayout";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Skeleton from "../../components/ui/Skeleton";
import FaceCapture from "../../components/webcam/FaceCapture";
import { getElection, listCandidates } from "../../services/electionService";
import { getVoteStatus, castVote } from "../../services/voteService";
import { useToast } from "../../contexts/ToastContext";

const STEPS = ["candidate", "verify", "confirm", "result"];

export default function VotingFlow() {
  const { electionId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [election, setElection] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [voteStatus, setVoteStatus] = useState(null);

  const [step, setStep] = useState("candidate");
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null); // { success, block_index, transaction_id, message }

  useEffect(() => {
    (async () => {
      try {
        const [e, c, vs] = await Promise.all([
          getElection(electionId),
          listCandidates(electionId),
          getVoteStatus(electionId),
        ]);
        setElection(e);
        setCandidates(c);
        setVoteStatus(vs);
      } catch {
        toast("Could not load this election.", "error");
        navigate("/voter");
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [electionId]);

  const handleFaceCapture = async (frames) => {
    if (frames.length < 2) {
      toast("Capture failed — please try again.", "error");
      return;
    }
    await submitVote(frames);
  };

  const submitVote = async (faceFrames) => {
    setSubmitting(true);
    setStep("confirm");
    try {
      const payload = { candidate_id: selectedCandidate.id, face_images: faceFrames };
      const data = await castVote(electionId, payload);
      setResult({ success: true, ...data });
    } catch (err) {
      setResult({ success: false, message: err.response?.data?.message || "Vote could not be recorded." });
    } finally {
      setSubmitting(false);
      setStep("result");
    }
  };

  if (loading) {
    return (
      <VoterLayout>
        <Skeleton className="h-64 w-full max-w-lg" />
      </VoterLayout>
    );
  }

  if (voteStatus && !voteStatus.can_vote_now && step === "candidate") {
    return (
      <VoterLayout>
        <Card className="mx-auto max-w-md p-8 text-center">
          <XCircle size={32} className="mx-auto mb-3 text-alert" />
          <p className="text-sm text-ink_text">
            {voteStatus.has_voted
              ? "You've already cast your vote in this election."
              : "You are not currently able to vote in this election."}
          </p>
          <Button className="mt-6" onClick={() => navigate("/voter")}>
            Back to elections
          </Button>
        </Card>
      </VoterLayout>
    );
  }

  return (
    <VoterLayout>
      <div className="mx-auto max-w-lg">
        <Link to="/voter" className="mb-4 flex items-center gap-1.5 text-sm text-muted hover:text-ink_text">
          <ArrowLeft size={14} /> Back to elections
        </Link>
        <h1 className="mb-1 font-display text-2xl text-ink_text">{election.title}</h1>
        <p className="mb-8 text-sm text-muted">{election.description}</p>

        <StepIndicator step={step} />

        <AnimatePresence mode="wait">
          {step === "candidate" && (
            <StepCard key="candidate">
              <h2 className="mb-4 text-sm font-semibold text-ink_text">Select a candidate</h2>
              <div className="space-y-2.5">
                {candidates.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCandidate(c)}
                    className={`w-full rounded-md border p-4 text-left transition-colors ${
                      selectedCandidate?.id === c.id
                        ? "border-seal bg-seal/5"
                        : "border-line hover:border-seal/50"
                    }`}
                  >
                    <p className="font-medium text-ink_text">{c.name}</p>
                    {c.party && <p className="text-sm text-muted">{c.party}</p>}
                  </button>
                ))}
              </div>
              <Button
                className="mt-6 w-full"
                disabled={!selectedCandidate}
                onClick={() => setStep("verify")}
              >
                Continue
              </Button>
            </StepCard>
          )}

          {step === "verify" && (
            <StepCard key="verify">
              <h2 className="mb-4 text-sm font-semibold text-ink_text">
                Blink and turn your head during capture
              </h2>
              <FaceCapture
                seconds={3}
                fps={4}
                prompt="Blink and turn your head now!"
                buttonLabel="Start verification"
                onComplete={handleFaceCapture}
              />
            </StepCard>
          )}

          {step === "confirm" && (
            <StepCard key="confirm">
              <div className="flex flex-col items-center gap-4 py-8 text-center">
                <ShieldCheck size={36} className="animate-pulse-verify text-seal" />
                <p className="text-sm text-muted">
                  Verifying identity, checking for fraud, and recording your vote to the
                  blockchain...
                </p>
              </div>
            </StepCard>
          )}

          {step === "result" && result && (
            <StepCard key="result">
              {result.success ? (
                <div className="flex flex-col items-center gap-3 py-6 text-center">
                  <CheckCircle2 size={40} className="text-verified" />
                  <p className="font-medium text-ink_text">{result.message}</p>
                  <div className="mt-2 w-full rounded-md bg-ink/5 p-4 text-left font-hash text-xs text-muted dark:bg-white/5">
                    <p className="mb-1 flex items-center gap-1.5">
                      <Link2 size={12} /> Block #{result.block_index}
                    </p>
                    <p className="break-all">Transaction ID: {result.transaction_id}</p>
                  </div>
                  <Button className="mt-4" onClick={() => navigate("/voter")}>
                    Back to elections
                  </Button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3 py-6 text-center">
                  <XCircle size={40} className="text-alert" />
                  <p className="text-sm text-ink_text">{result.message}</p>
                  <Button
                    className="mt-4"
                    variant="outline"
                    onClick={() => {
                      setResult(null);
                      setStep("verify");
                    }}
                  >
                    Try again
                  </Button>
                </div>
              )}
            </StepCard>
          )}
        </AnimatePresence>
      </div>
    </VoterLayout>
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

function StepCard({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="p-6">{children}</Card>
    </motion.div>
  );
}
