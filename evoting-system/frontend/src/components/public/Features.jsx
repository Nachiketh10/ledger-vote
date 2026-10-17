import { ScanFace, Link2, ShieldAlert, Eye, Lock } from "lucide-react";
import LedgerNode from "./LedgerNode";

const FEATURES = [
  {
    icon: ScanFace,
    title: "CNN face verification",
    body: "InsightFace-driven embeddings compare your registered face against the one at the ballot box, with MediaPipe rejecting frames showing more than one person.",
  },
  {
    icon: Link2,
    title: "Custom SHA-256 chain",
    body: "Every vote is one block. Each block's hash depends on the one before it. Change history, and the chain tells on itself.",
  },
  {
    icon: Eye,
    title: "Liveness detection",
    body: "Blink and head-turn checks across a live frame sequence — a printed photo or a static video frame simply won't pass.",
  },
  {
    icon: ShieldAlert,
    title: "Real-time fraud scoring",
    body: "Duplicate votes, multiple sessions, multiple devices, and repeated failed attempts are scored and can block a vote before it's cast.",
  },
  {
    icon: Lock,
    title: "Encrypted at rest",
    body: "Face embeddings are AES-encrypted, never stored as raw images. Passwords are bcrypt-hashed. Every admin action is audit-logged.",
  },
];

export default function Features() {
  return (
    <>
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12 max-w-xl">
          <div className="font-mono text-xs uppercase tracking-widest text-brass">02 — Features</div>
          <h2 className="mt-3 font-display text-3xl text-ink_text">
            Six guarantees, working together.
          </h2>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="rounded-lg border border-line bg-surface p-6 transition-shadow hover:shadow-md"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-seal/10 text-seal">
                <Icon size={19} strokeWidth={2} />
              </div>
              <h3 className="font-medium text-ink_text">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>
      <LedgerNode />
    </>
  );
}
