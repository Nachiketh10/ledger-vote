import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Vote, Users, ShieldAlert, Link2, Radio } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Skeleton from "../../components/ui/Skeleton";
import { adminListElections } from "../../services/adminElectionService";
import { listVoters } from "../../services/voterAdminService";
import { listBlocks } from "../../services/blockchainService";
import { listFraudLogs } from "../../services/fraudService";

function StatCard({ icon: Icon, label, value, loading, to }) {
  const content = (
    <Card className="p-5">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-md bg-seal/10 text-seal">
          <Icon size={18} />
        </span>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
          {loading ? (
            <Skeleton className="mt-1 h-6 w-12" />
          ) : (
            <p className="font-display text-xl text-ink_text">{value}</p>
          )}
        </div>
      </div>
    </Card>
  );
  return to ? <Link to={to}>{content}</Link> : content;
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalElections: 0,
    liveElections: 0,
    registeredVoters: 0,
    blockchainBlocks: 0,
    fraudAlerts: 0,
  });

  useEffect(() => {
    (async () => {
      try {
        const [elections, votersPage, blocksPage, fraudPage] = await Promise.all([
          adminListElections(),
          listVoters({ page: 1 }),
          listBlocks(1),
          listFraudLogs({ page: 1, isResolved: false }),
        ]);
        setStats({
          totalElections: elections.length,
          liveElections: elections.filter((e) => e.status === "live").length,
          registeredVoters: votersPage.pagination.total_items,
          blockchainBlocks: blocksPage.pagination.total_items,
          fraudAlerts: fraudPage.pagination.total_items,
        });
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <AdminLayout>
      <h1 className="mb-6 font-display text-2xl text-ink_text">Dashboard</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard icon={Vote} label="Total Elections" value={stats.totalElections} loading={loading} to="/admin/elections" />
        <StatCard icon={Radio} label="Live Elections" value={stats.liveElections} loading={loading} to="/admin/elections" />
        <StatCard icon={Users} label="Registered Voters" value={stats.registeredVoters} loading={loading} to="/admin/voters" />
        <StatCard icon={Link2} label="Blockchain Blocks" value={stats.blockchainBlocks} loading={loading} to="/admin/blockchain" />
        <StatCard icon={ShieldAlert} label="Unresolved Fraud Alerts" value={stats.fraudAlerts} loading={loading} to="/admin/fraud" />
      </div>
    </AdminLayout>
  );
}
