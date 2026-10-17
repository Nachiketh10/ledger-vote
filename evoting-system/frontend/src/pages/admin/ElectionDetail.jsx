import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { ArrowLeft, Plus, Trash2, UserPlus, ShieldPlus, X } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import Skeleton from "../../components/ui/Skeleton";
import FormField, { inputClass } from "../../components/ui/FormField";
import {
  adminGetElection, addCandidate, deleteCandidate, setEligibleVoters,
  listElectionAdmins, assignElectionAdmin, unassignElectionAdmin,
} from "../../services/adminElectionService";
import { listCandidates } from "../../services/electionService";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "../../contexts/ToastContext";

export default function ElectionDetail() {
  const { electionId } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [election, setElection] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [electionAdmins, setElectionAdmins] = useState([]);
  const [candidateModalOpen, setCandidateModalOpen] = useState(false);
  const [voterModalOpen, setVoterModalOpen] = useState(false);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [voterIdsInput, setVoterIdsInput] = useState("");
  const [pickedAdminId, setPickedAdminId] = useState("");

  const isSuperAdmin = user?.role === "super_admin";

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();

  const load = async () => {
    setLoading(true);
    try {
      const [e, c] = await Promise.all([adminGetElection(electionId), listCandidates(electionId)]);
      setElection(e);
      setCandidates(c);
      if (isSuperAdmin) {
        setElectionAdmins(await listElectionAdmins());
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [electionId]);

  const canEditCandidates = election && (election.status === "draft" || election.status === "scheduled");

  const onAddCandidate = async (values) => {
    try {
      await addCandidate(electionId, values);
      toast("Candidate added.", "success");
      setCandidateModalOpen(false);
      reset();
      load();
    } catch (err) {
      toast(err.response?.data?.message || "Could not add candidate.", "error");
    }
  };

  const onDeleteCandidate = async (candidateId) => {
    try {
      await deleteCandidate(candidateId);
      toast("Candidate removed.", "success");
      load();
    } catch (err) {
      toast(err.response?.data?.message || "Could not remove candidate.", "error");
    }
  };

  const onSetEligible = async () => {
    const ids = voterIdsInput
      .split(/[\n,]/)
      .map((s) => s.trim())
      .filter(Boolean);
    try {
      await setEligibleVoters(electionId, ids);
      toast(`${ids.length} voter(s) marked eligible.`, "success");
      setVoterModalOpen(false);
      setVoterIdsInput("");
      load();
    } catch (err) {
      toast(err.response?.data?.message || "Could not update eligible voters.", "error");
    }
  };

  const onAssignAdmin = async () => {
    if (!pickedAdminId) return;
    try {
      await assignElectionAdmin(electionId, pickedAdminId);
      toast("Election Admin assigned.", "success");
      setAssignModalOpen(false);
      setPickedAdminId("");
      load();
    } catch (err) {
      toast(err.response?.data?.message || "Could not assign Election Admin.", "error");
    }
  };

  const onUnassignAdmin = async (adminId) => {
    try {
      await unassignElectionAdmin(electionId, adminId);
      toast("Election Admin unassigned.", "success");
      load();
    } catch (err) {
      toast(err.response?.data?.message || "Could not unassign Election Admin.", "error");
    }
  };

  if (loading || !election) {
    return (
      <AdminLayout>
        <Skeleton className="h-40 w-full" />
      </AdminLayout>
    );
  }

  const assignedAdmins = electionAdmins.filter((a) => election.assigned_admin_ids?.includes(a.id));
  const unassignedAdmins = electionAdmins.filter((a) => !election.assigned_admin_ids?.includes(a.id));

  return (
    <AdminLayout>
      <Link to="/admin/elections" className="mb-4 flex items-center gap-1.5 text-sm text-muted hover:text-ink_text">
        <ArrowLeft size={14} /> Back to elections
      </Link>

      <div className="mb-8 flex items-center gap-3">
        <h1 className="font-display text-2xl text-ink_text">{election.title}</h1>
        <Badge tone={election.status === "live" ? "verified" : "neutral"}>{election.status}</Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-ink_text">Candidates ({candidates.length})</h2>
            {canEditCandidates && (
              <Button size="sm" onClick={() => setCandidateModalOpen(true)}>
                <Plus size={14} /> Add
              </Button>
            )}
          </div>
          {!canEditCandidates && (
            <p className="mb-3 text-xs text-muted">
              Candidates are locked once the election is no longer a draft/scheduled.
            </p>
          )}
          <div className="space-y-2">
            {candidates.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-md border border-line p-3">
                <div>
                  <p className="text-sm font-medium text-ink_text">{c.name}</p>
                  {c.party && <p className="text-xs text-muted">{c.party}</p>}
                </div>
                {canEditCandidates && (
                  <button onClick={() => onDeleteCandidate(c.id)} className="text-muted hover:text-alert">
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-ink_text">
              Eligible voters ({election.eligible_voter_count})
            </h2>
            <Button size="sm" onClick={() => setVoterModalOpen(true)}>
              <UserPlus size={14} /> Manage
            </Button>
          </div>
          <p className="text-sm text-muted">
            Set which registered, verified voters may vote in this election using their
            voter ID (not internal account ID).
          </p>
        </Card>

        {isSuperAdmin && (
          <Card className="p-6 lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-ink_text">
                Assigned Election Admins ({assignedAdmins.length})
              </h2>
              <Button size="sm" onClick={() => setAssignModalOpen(true)} disabled={unassignedAdmins.length === 0}>
                <ShieldPlus size={14} /> Assign
              </Button>
            </div>
            {assignedAdmins.length === 0 ? (
              <p className="text-sm text-muted">
                No Election Admin is assigned yet — they won't be able to manage this
                election until you assign one.
              </p>
            ) : (
              <div className="space-y-2">
                {assignedAdmins.map((a) => (
                  <div key={a.id} className="flex items-center justify-between rounded-md border border-line p-3">
                    <div>
                      <p className="text-sm font-medium text-ink_text">{a.name}</p>
                      <p className="text-xs text-muted">{a.email}</p>
                    </div>
                    <button onClick={() => onUnassignAdmin(a.id)} className="text-muted hover:text-alert" title="Unassign">
                      <X size={15} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {unassignedAdmins.length === 0 && electionAdmins.length === 0 && (
              <p className="mt-3 text-xs text-muted">
                No Election Admin accounts exist yet — create one with{" "}
                <code className="rounded bg-ink/5 px-1 py-0.5 font-hash dark:bg-white/5">
                  flask create-super-admin
                </code>{" "}
                (Super Admin) or add an "invite Election Admin" flow if you need one
                created from within the app.
              </p>
            )}
          </Card>
        )}
      </div>

      <Modal open={candidateModalOpen} onClose={() => setCandidateModalOpen(false)} title="Add candidate">
        <form onSubmit={handleSubmit(onAddCandidate)}>
          <FormField label="Name" error={errors.name?.message}>
            <input className={inputClass} {...register("name", { required: "Name is required" })} />
          </FormField>
          <FormField label="Party (optional)">
            <input className={inputClass} {...register("party")} />
          </FormField>
          <FormField label="Description (optional)">
            <textarea className={inputClass} rows={2} {...register("description")} />
          </FormField>
          <Button type="submit" className="mt-2 w-full" disabled={isSubmitting}>
            {isSubmitting ? "Adding..." : "Add candidate"}
          </Button>
        </form>
      </Modal>

      <Modal open={voterModalOpen} onClose={() => setVoterModalOpen(false)} title="Set eligible voters">
        <p className="mb-3 text-sm text-muted">
          Paste voter IDs (one per line or comma-separated). This replaces the current
          eligibility list for this election.
        </p>
        <textarea
          className={inputClass}
          rows={6}
          placeholder={"VTV-abc123\nVTV-def456"}
          value={voterIdsInput}
          onChange={(e) => setVoterIdsInput(e.target.value)}
        />
        <Button className="mt-4 w-full" onClick={onSetEligible}>
          Save eligible voters
        </Button>
      </Modal>

      <Modal open={assignModalOpen} onClose={() => setAssignModalOpen(false)} title="Assign an Election Admin">
        <p className="mb-3 text-sm text-muted">
          They'll be able to manage this election's candidates, eligibility, and lifecycle.
        </p>
        <select
          className={inputClass}
          value={pickedAdminId}
          onChange={(e) => setPickedAdminId(e.target.value)}
        >
          <option value="">Select an Election Admin...</option>
          {unassignedAdmins.map((a) => (
            <option key={a.id} value={a.id}>{a.name} ({a.email})</option>
          ))}
        </select>
        <Button className="mt-4 w-full" onClick={onAssignAdmin} disabled={!pickedAdminId}>
          Assign
        </Button>
      </Modal>
    </AdminLayout>
  );
}
