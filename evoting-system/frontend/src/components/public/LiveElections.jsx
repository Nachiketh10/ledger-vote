import { useEffect, useState } from "react";
import { listPublicElections } from "../../services/electionService";
import ElectionCard from "./ElectionCard";
import LedgerNode from "./LedgerNode";

export default function LiveElections() {
  const [elections, setElections] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    let cancelled = false;
    listPublicElections()
      .then((items) => {
        if (!cancelled) {
          setElections(items);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const active = elections.filter((e) => e.status === "live" || e.status === "scheduled");

  return (
    <>
      <section id="elections" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-10 flex items-end justify-between">
          <div>
            <div className="font-mono text-xs uppercase tracking-widest text-brass">05 — Elections</div>
            <h2 className="mt-3 font-display text-3xl text-ink_text">Live &amp; upcoming.</h2>
          </div>
        </div>

        {status === "loading" && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-48 animate-pulse rounded-lg border border-line bg-surface" />
            ))}
          </div>
        )}

        {status === "error" && (
          <div className="rounded-lg border border-line bg-surface p-8 text-center text-sm text-muted">
            Couldn't load elections right now. Check back shortly.
          </div>
        )}

        {status === "ready" && active.length === 0 && (
          <div className="rounded-lg border border-dashed border-line p-10 text-center">
            <p className="text-sm text-muted">
              No elections are open right now. Register now so you're ready
              the moment one goes live.
            </p>
          </div>
        )}

        {status === "ready" && active.length > 0 && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {active.map((election) => (
              <ElectionCard key={election.id} election={election} />
            ))}
          </div>
        )}
      </section>
      <LedgerNode label="election: open" />
    </>
  );
}
