import { useEffect, useState } from "react";
import { ShieldAlert, CheckCircle2 } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Skeleton from "../../components/ui/Skeleton";
import { listFraudLogs, resolveFraudLog } from "../../services/fraudService";
import { useToast } from "../../contexts/ToastContext";

const severityTone = { low: "neutral", medium: "brass", high: "alert", critical: "alert" };

export default function FraudMonitoring() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState("unresolved");
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await listFraudLogs({
        isResolved: filter === "unresolved" ? false : filter === "resolved" ? true : undefined,
      });
      setLogs(data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleResolve = async (id) => {
    setBusyId(id);
    try {
      await resolveFraudLog(id, "Reviewed by admin");
      toast("Marked resolved.", "success");
      load();
    } catch {
      toast("Could not resolve.", "error");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <AdminLayout>
      <h1 className="mb-6 font-display text-2xl text-ink_text">Fraud Monitoring</h1>

      <div className="mb-5 flex gap-2">
        {["unresolved", "resolved", "all"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-medium capitalize transition-colors ${
              filter === f ? "bg-seal text-white" : "bg-ink/5 text-muted hover:text-ink_text dark:bg-white/5"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading ? (
        <Skeleton className="h-40 w-full" />
      ) : logs.length === 0 ? (
        <p className="text-sm text-muted">No fraud logs for this filter.</p>
      ) : (
        <div className="space-y-2">
          {logs.map((log) => (
            <Card key={log.id} className="flex items-start justify-between gap-3 p-4">
              <div className="flex gap-3">
                <ShieldAlert size={18} className="mt-0.5 shrink-0 text-alert" />
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-ink_text">
                      {log.fraud_type.replaceAll("_", " ")}
                    </p>
                    <Badge tone={severityTone[log.severity]}>{log.severity}</Badge>
                    <span className="text-xs text-muted">score {log.fraud_score}</span>
                  </div>
                  <p className="mt-1 text-sm text-muted">{log.description}</p>
                  <p className="mt-1 text-xs text-muted">{new Date(log.created_at).toLocaleString()}</p>
                </div>
              </div>
              {!log.is_resolved && (
                <Button size="sm" variant="outline" disabled={busyId === log.id} onClick={() => handleResolve(log.id)}>
                  <CheckCircle2 size={13} /> Resolve
                </Button>
              )}
            </Card>
          ))}
        </div>
      )}
    </AdminLayout>
  );
}
