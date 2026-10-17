import Badge from "../ui/Badge";
import { useCountdown } from "../../hooks/useCountdown";

const STATUS_TONE = {
  live: "verified",
  scheduled: "brass",
  closed: "neutral",
};

function CountdownUnit({ value, label }) {
  return (
    <div className="text-center">
      <div className="font-hash text-xl text-ink_text">{String(value).padStart(2, "0")}</div>
      <div className="text-[10px] uppercase tracking-widest text-muted">{label}</div>
    </div>
  );
}

export default function ElectionCard({ election }) {
  const targetDate = election.status === "live" ? election.end_date : election.start_date;
  const { days, hours, minutes, seconds } = useCountdown(targetDate);
  const label = election.status === "live" ? "Voting closes in" : "Voting opens in";

  return (
    <div className="rounded-lg border border-line bg-surface p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium text-ink_text">{election.title}</h3>
          {election.description && (
            <p className="mt-1 text-sm text-muted line-clamp-2">{election.description}</p>
          )}
        </div>
        <Badge tone={STATUS_TONE[election.status] ?? "neutral"}>{election.status}</Badge>
      </div>

      {election.status !== "closed" && (
        <div className="mt-5 border-t border-line pt-4">
          <div className="mb-2 text-xs text-muted">{label}</div>
          <div className="flex gap-4">
            <CountdownUnit value={days} label="Days" />
            <CountdownUnit value={hours} label="Hrs" />
            <CountdownUnit value={minutes} label="Min" />
            <CountdownUnit value={seconds} label="Sec" />
          </div>
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-xs text-muted">
        <span>{election.candidate_count} candidates</span>
      </div>
    </div>
  );
}
