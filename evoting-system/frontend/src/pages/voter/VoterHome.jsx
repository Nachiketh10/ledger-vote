import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarClock, CheckCircle2, ScanFace, Vote as VoteIcon, ArrowRight } from "lucide-react";
import VoterLayout from "../../layouts/VoterLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Skeleton from "../../components/ui/Skeleton";
import { useAuth } from "../../contexts/AuthContext";
import { listPublicElections } from "../../services/electionService";
import { getVoteStatus } from "../../services/voteService";
import { useCountdown } from "../../hooks/useCountdown";

function Countdown({ target }) {
  const { days, hours, minutes } = useCountdown(target);
  return (
    <span className="font-hash text-xs text-muted">
      Starts in {days}d {hours}h {minutes}m
    </span>
  );
}

export default function VoterHome() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [elections, setElections] = useState([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const list = await listPublicElections();
      const withStatus = await Promise.all(
        list.map(async (e) => {
          try {
            const status = await getVoteStatus(e.id);
            return { ...e, ...status };
          } catch {
            return { ...e, is_eligible: false, has_voted: false, can_vote_now: false };
          }
        })
      );
      if (!cancelled) {
        setElections(withStatus);
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const votable = elections.filter((e) => e.can_vote_now);
  const alreadyVoted = elections.filter((e) => e.has_voted);
  const upcoming = elections.filter((e) => e.status === "scheduled" || e.status === "draft");
  const needsBiometrics = user && !user.has_face_registered;

  return (
    <VoterLayout>
      <div className="mb-8">
        <h1 className="font-display text-2xl text-ink_text">Welcome, {user?.name}</h1>
        <p className="mt-1 text-sm text-muted">
          Voter ID: <span className="font-hash">{user?.voter_id}</span>
          {!user?.is_verified && (
            <Badge tone="brass" className="ml-2">
              Pending admin verification
            </Badge>
          )}
        </p>
      </div>

      {needsBiometrics && (
        <Card className="mb-8 border-brass/40 bg-brass/5 p-5">
          <p className="mb-3 text-sm font-medium text-ink_text">
            Register your face to be able to vote:
          </p>
          <div className="flex flex-wrap gap-3">
            <Button as={Link} to="/voter/register-face" size="sm" variant="brass">
              <ScanFace size={15} /> Register Face
            </Button>
          </div>
        </Card>
      )}

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : (
        <div className="space-y-10">
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
              Available to vote
            </h2>
            {votable.length === 0 ? (
              <p className="text-sm text-muted">No elections are open for you to vote in right now.</p>
            ) : (
              <div className="space-y-3">
                {votable.map((e) => (
                  <Card key={e.id} className="flex items-center justify-between p-5">
                    <div>
                      <p className="font-medium text-ink_text">{e.title}</p>
                      <p className="text-sm text-muted">{e.description}</p>
                    </div>
                    <Button as={Link} to={`/voter/elections/${e.id}/vote`} size="sm">
                      <VoteIcon size={15} /> Vote now <ArrowRight size={14} />
                    </Button>
                  </Card>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
              Upcoming elections
            </h2>
            {upcoming.length === 0 ? (
              <p className="text-sm text-muted">No upcoming elections scheduled.</p>
            ) : (
              <div className="space-y-3">
                {upcoming.map((e) => (
                  <Card key={e.id} className="flex items-center justify-between p-5">
                    <div>
                      <p className="font-medium text-ink_text">{e.title}</p>
                      <p className="flex items-center gap-1.5 text-sm text-muted">
                        <CalendarClock size={13} /> <Countdown target={e.start_date} />
                      </p>
                    </div>
                    <Badge tone="neutral">Scheduled</Badge>
                  </Card>
                ))}
              </div>
            )}
          </section>

          {alreadyVoted.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
                Already voted
              </h2>
              <div className="space-y-3">
                {alreadyVoted.map((e) => (
                  <Card key={e.id} className="flex items-center justify-between p-5">
                    <p className="font-medium text-ink_text">{e.title}</p>
                    <Badge tone="verified">
                      <CheckCircle2 size={13} /> Vote recorded
                    </Badge>
                  </Card>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </VoterLayout>
  );
}
