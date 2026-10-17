import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Plus, Play, Pause, RotateCcw, Square, ArrowRight } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import Skeleton from "../../components/ui/Skeleton";
import FormField, { inputClass } from "../../components/ui/FormField";
import {
  adminListElections,
  createElection,
  electionAction,
} from "../../services/adminElectionService";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "../../contexts/ToastContext";

const statusTone = {
  draft: "neutral",
  scheduled: "brass",
  live: "verified",
  paused: "brass",
  closed: "neutral",
};

const nextActions = {
  draft: [{ action: "start", label: "Start", icon: Play }],
  scheduled: [{ action: "start", label: "Start", icon: Play }],
  live: [
    { action: "pause", label: "Pause", icon: Pause },
    { action: "close", label: "Close", icon: Square },
  ],
  paused: [
    { action: "resume", label: "Resume", icon: RotateCcw },
    { action: "close", label: "Close", icon: Square },
  ],
  closed: [],
};

export default function ElectionManagement() {
  const { user } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [elections, setElections] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [busyId, setBusyId] = useState(null);

  const isSuperAdmin = user?.role === "super_admin";

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();

  const load = async () => {
    setLoading(true);
    try {
      setElections(await adminListElections());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onCreate = async (values) => {
    try {
      await createElection({
        title: values.title,
        description: values.description,
        start_date: new Date(values.start_date).toISOString(),
        end_date: new Date(values.end_date).toISOString(),
      });
      toast("Election created.", "success");
      setModalOpen(false);
      reset();
      load();
    } catch (err) {
      toast(err.response?.data?.message || "Could not create election.", "error");
    }
  };

  const PAST_TENSE = { start: "started", pause: "paused", resume: "resumed", close: "closed" };

const runAction = async (electionId, action) => {
    setBusyId(electionId);
    try {
      await electionAction(electionId, action);
      toast(`Election ${PAST_TENSE[action]}.`, "success");
      load();
    } catch (err) {
      toast(err.response?.data?.message || `Could not ${action} election.`, "error");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <AdminLayout>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-2xl text-ink_text">Elections & Candidates</h1>
        {isSuperAdmin && (
          <Button onClick={() => setModalOpen(true)}>
            <Plus size={16} /> New election
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : elections.length === 0 ? (
        <p className="text-sm text-muted">
          {isSuperAdmin
            ? "No elections yet — create one to get started."
            : "No elections have been assigned to you yet — ask a Super Admin to assign one."}
        </p>
      ) : (
        <div className="space-y-3">
          {elections.map((e) => (
            <Card key={e.id} className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-ink_text">{e.title}</p>
                    <Badge tone={statusTone[e.status]}>{e.status}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-muted">
                    {e.candidate_count} candidates · {e.eligible_voter_count} eligible voters
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {nextActions[e.status]?.map(({ action, label, icon: Icon }) => (
                    <Button
                      key={action}
                      size="sm"
                      variant="outline"
                      disabled={busyId === e.id}
                      onClick={() => runAction(e.id, action)}
                    >
                      <Icon size={14} /> {label}
                    </Button>
                  ))}
                  <Button as={Link} to={`/admin/elections/${e.id}`} size="sm">
                    Manage <ArrowRight size={14} />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Create election">
        <form onSubmit={handleSubmit(onCreate)}>
          <FormField label="Title" error={errors.title?.message}>
            <input className={inputClass} {...register("title", { required: "Title is required" })} />
          </FormField>
          <FormField label="Description">
            <textarea className={inputClass} rows={3} {...register("description")} />
          </FormField>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Start date" error={errors.start_date?.message}>
              <input
                type="datetime-local"
                className={inputClass}
                {...register("start_date", { required: "Required" })}
              />
            </FormField>
            <FormField label="End date" error={errors.end_date?.message}>
              <input
                type="datetime-local"
                className={inputClass}
                {...register("end_date", { required: "Required" })}
              />
            </FormField>
          </div>
          <Button type="submit" className="mt-2 w-full" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create election"}
          </Button>
        </form>
      </Modal>
    </AdminLayout>
  );
}
