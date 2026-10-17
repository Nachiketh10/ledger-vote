import { useEffect, useState } from "react";
import { Search, CheckCircle2, Ban, RotateCcw, LogOut, ScanFace } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Skeleton from "../../components/ui/Skeleton";
import { inputClass } from "../../components/ui/FormField";
import {
  listVoters, verifyVoter, suspendVoter, reactivateVoter,
  revokeVoterSessions, resetVoterBiometrics,
} from "../../services/voterAdminService";
import { useToast } from "../../contexts/ToastContext";

export default function VoterRegistration() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [voters, setVoters] = useState([]);
  const [search, setSearch] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = async (searchValue = search) => {
    setLoading(true);
    try {
      const data = await listVoters({ search: searchValue || undefined });
      setVoters(data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const run = async (voterId, fn, successMsg) => {
    setBusyId(voterId);
    try {
      await fn(voterId);
      toast(successMsg, "success");
      load();
    } catch (err) {
      toast(err.response?.data?.message || "Action failed.", "error");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <AdminLayout>
      <h1 className="mb-6 font-display text-2xl text-ink_text">Voter Registration</h1>

      <div className="mb-5 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            className={`${inputClass} pl-9`}
            placeholder="Search by name, email, or voter ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
        <Button variant="outline" size="sm" onClick={() => load()}>
          Search
        </Button>
      </div>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : voters.length === 0 ? (
        <p className="text-sm text-muted">No voters found.</p>
      ) : (
        <div className="space-y-2">
          {voters.map((v) => (
            <Card key={v.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-medium text-ink_text">{v.name}</p>
                  {v.is_verified ? (
                    <Badge tone="verified">Verified</Badge>
                  ) : (
                    <Badge tone="brass">Pending</Badge>
                  )}
                  {!v.is_active && <Badge tone="alert">Suspended</Badge>}
                </div>
                <p className="truncate text-xs text-muted">
                  {v.email} · <span className="font-hash">{v.voter_id}</span>
                </p>
                <div className="mt-1 flex gap-2 text-xs text-muted">
                  {v.has_face_registered && (
                    <span className="flex items-center gap-1">
                      <ScanFace size={11} /> face
                    </span>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {!v.is_verified && (
                  <Button size="sm" disabled={busyId === v.id} onClick={() => run(v.id, (id) => verifyVoter(id), "Voter verified.")}>
                    <CheckCircle2 size={13} /> Verify
                  </Button>
                )}
                {v.is_active ? (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busyId === v.id}
                    onClick={() => run(v.id, (id) => suspendVoter(id, "Suspended by admin"), "Voter suspended.")}
                  >
                    <Ban size={13} /> Suspend
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busyId === v.id}
                    onClick={() => run(v.id, reactivateVoter, "Voter reactivated.")}
                  >
                    <RotateCcw size={13} /> Reactivate
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busyId === v.id}
                  onClick={() => run(v.id, revokeVoterSessions, "Sessions revoked.")}
                  title="Force-logout all active sessions"
                >
                  <LogOut size={13} /> Revoke sessions
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busyId === v.id}
                  onClick={() => run(v.id, resetVoterBiometrics, "Biometrics reset.")}
                  title="Clear face enrollment"
                >
                  Reset biometrics
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </AdminLayout>
  );
}
