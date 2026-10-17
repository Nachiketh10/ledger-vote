import { Check } from "lucide-react";
import LedgerNode from "./LedgerNode";

const GUARANTEES = [
  "Passwords hashed with bcrypt — never stored, never logged",
  "Face embeddings AES-encrypted at rest, raw images discarded after capture",
  "JWT access tokens expire in 15 minutes; refresh tokens rotate on every use",
  "Rate-limited login and voting endpoints block brute-force attempts",
  "Every admin action — election created, candidate edited, vote cast — is audit-logged",
  "Duplicate-vote protection enforced at the database level, not just the app layer",
];

export default function Security() {
  return (
    <>
      <section id="security" className="bg-ink text-cream">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <div className="grid gap-12 md:grid-cols-2">
            <div>
              <div className="font-mono text-xs uppercase tracking-widest text-brass">03 — Security</div>
              <h2 className="mt-3 font-display text-3xl text-cream">
                Verification, not vibes.
              </h2>
              <p className="mt-4 max-w-md text-sm leading-relaxed text-cream/70">
                Security claims are easy to make and hard to prove. Here's
                exactly what stands between your identity and your ballot.
              </p>
            </div>

            <ul className="space-y-4">
              {GUARANTEES.map((g) => (
                <li key={g} className="flex items-start gap-3 text-sm text-cream/80">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-verified/15 text-verified">
                    <Check size={12} strokeWidth={3} />
                  </span>
                  {g}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
      <LedgerNode label="identity: confirmed" />
    </>
  );
}
