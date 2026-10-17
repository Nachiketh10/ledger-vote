import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip,
} from "chart.js";
import { Trophy, ShieldCheck, ShieldX, FileDown, FileSpreadsheet } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Skeleton from "../../components/ui/Skeleton";
import { adminListElections } from "../../services/adminElectionService";
import { getResults } from "../../services/voteService";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

export default function Results() {
  const [elections, setElections] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      const list = await adminListElections("closed");
      setElections(list);
      if (list.length > 0) setSelectedId(list[0].id);
      else setLoading(false);
    })();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    getResults(selectedId)
      .then(setResults)
      .catch((err) => setError(err.response?.data?.message || "Could not load results."))
      .finally(() => setLoading(false));
  }, [selectedId]);

  return (
    <AdminLayout>
      <h1 className="mb-6 font-display text-2xl text-ink_text">Results</h1>

      {elections.length === 0 ? (
        <p className="text-sm text-muted">
          No closed elections yet — results are only available once an election is closed.
        </p>
      ) : (
        <>
          <select
            className="mb-6 max-w-sm rounded-md border border-line bg-parchment px-3.5 py-2.5 text-sm text-ink_text outline-none focus:border-seal"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {elections.map((e) => (
              <option key={e.id} value={e.id}>{e.title}</option>
            ))}
          </select>

          {loading ? (
            <Skeleton className="h-80 w-full" />
          ) : error ? (
            <p className="text-sm text-alert">{error}</p>
          ) : results ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Card className="p-5">
                  <p className="text-xs uppercase tracking-wide text-muted">Total votes</p>
                  <p className="font-display text-2xl text-ink_text">{results.total_votes}</p>
                </Card>
                <Card className="p-5">
                  <p className="text-xs uppercase tracking-wide text-muted">Participation</p>
                  <p className="font-display text-2xl text-ink_text">{results.participation_percentage}%</p>
                </Card>
                <Card className="p-5">
                  <p className="text-xs uppercase tracking-wide text-muted">Blockchain integrity</p>
                  <p className={`flex items-center gap-1.5 font-display text-lg ${results.blockchain_verified ? "text-verified" : "text-alert"}`}>
                    {results.blockchain_verified ? <ShieldCheck size={18} /> : <ShieldX size={18} />}
                    {results.blockchain_verified ? "Verified" : "Tampered"}
                  </p>
                </Card>
              </div>

              {results.winner && (
                <Card className="flex items-center gap-3 border-brass/40 bg-brass/5 p-5">
                  <Trophy size={22} className="text-brass" />
                  <div>
                    <p className="text-sm text-muted">Winner</p>
                    <p className="font-display text-lg text-ink_text">
                      {results.winner.name} — {results.winner.votes} votes ({results.winner.percentage}%)
                    </p>
                  </div>
                </Card>
              )}

              <div className="flex gap-2">
                <Button as="a" href={`/api/elections/${selectedId}/results/export/pdf`} variant="outline" size="sm">
                  <FileDown size={14} /> Export PDF
                </Button>
                <Button as="a" href={`/api/elections/${selectedId}/results/export/excel`} variant="outline" size="sm">
                  <FileSpreadsheet size={14} /> Export Excel
                </Button>
              </div>

              <Card className="p-6">
                <Bar
                  data={{
                    labels: results.candidates.map((c) => c.name),
                    datasets: [
                      {
                        label: "Votes",
                        data: results.candidates.map((c) => c.votes),
                        backgroundColor: "rgb(36 64 107 / 0.75)",
                        borderRadius: 4,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                  }}
                />
              </Card>

              <Card className="divide-y divide-line">
                {results.candidates.map((c) => (
                  <div key={c.candidate_id} className="flex items-center justify-between p-4">
                    <div>
                      <p className="text-sm font-medium text-ink_text">{c.name}</p>
                      {c.party && <p className="text-xs text-muted">{c.party}</p>}
                    </div>
                    <Badge tone="neutral">{c.votes} votes · {c.percentage}%</Badge>
                  </div>
                ))}
              </Card>
            </div>
          ) : null}
        </>
      )}
    </AdminLayout>
  );
}
