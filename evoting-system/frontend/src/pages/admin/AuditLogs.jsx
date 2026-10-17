import { useEffect, useState } from "react";
import { ScrollText, Search } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Skeleton from "../../components/ui/Skeleton";
import Button from "../../components/ui/Button";
import { inputClass } from "../../components/ui/FormField";
import { listAuditLogs } from "../../services/auditService";

export default function AuditLogs() {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [action, setAction] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await listAuditLogs({ action: action || undefined });
      setLogs(data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AdminLayout>
      <h1 className="mb-6 font-display text-2xl text-ink_text">Audit Logs</h1>

      <div className="mb-5 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            className={`${inputClass} pl-9`}
            placeholder="Filter by action (e.g. vote.cast)"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
        <Button variant="outline" size="sm" onClick={load}>Filter</Button>
      </div>

      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : logs.length === 0 ? (
        <p className="text-sm text-muted">No audit entries found.</p>
      ) : (
        <Card className="divide-y divide-line">
          {logs.map((log) => (
            <div key={log.id} className="flex items-start gap-3 p-4">
              <ScrollText size={15} className="mt-0.5 shrink-0 text-muted" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-hash text-sm text-ink_text">{log.action}</p>
                  <span className="shrink-0 text-xs text-muted">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-muted">
                  {log.actor_type}{log.actor_id ? ` · ${log.actor_id}` : ""}
                </p>
                {log.details && (
                  <pre className="mt-1 overflow-x-auto rounded bg-ink/5 p-2 font-hash text-xs text-muted dark:bg-white/5">
                    {JSON.stringify(log.details, null, 0)}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </Card>
      )}
    </AdminLayout>
  );
}
