import { UserCheck, ScanFace, ShieldCheck, Link2 } from "lucide-react";
import LedgerNode from "./LedgerNode";

const STEPS = [
  {
    icon: UserCheck,
    title: "You register, and get verified",
    body: "Sign up with your details. An election admin confirms you're a real, eligible voter before you're added to the roll — one person, one account.",
  },
  {
    icon: ScanFace,
    title: "You prove it's really you",
    body: "On voting day, you verify with your face — the same tech your phone already uses to unlock. A photo or a video replay won't work; the system checks that you're actually there, live.",
  },
  {
    icon: ShieldCheck,
    title: "We quietly check for cheating",
    body: "Before your ballot even shows up, the system checks: has this person already voted? Are they logging in from two places at once? Suspicious patterns get blocked automatically.",
  },
  {
    icon: Link2,
    title: "Your vote is sealed, permanently",
    body: "Once cast, your vote is locked into a chain of records, each one linked to the one before it. Change any single vote afterward, and every record after it visibly breaks — there's nowhere to hide a tamper.",
  },
];

export default function HowItWorks() {
  return (
    <>
      <section id="how-it-works" className="mx-auto max-w-5xl px-6 py-20">
        <div className="mb-14 max-w-xl">
          <div className="font-mono text-xs uppercase tracking-widest text-brass">How it works</div>
          <h2 className="mt-3 font-display text-3xl text-ink_text">From sign-up to a sealed vote.</h2>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            Four steps. No blockchain jargon required.
          </p>
        </div>

        <div className="relative space-y-10">
          <div className="absolute left-6 top-6 bottom-6 hidden w-px bg-line md:block" aria-hidden="true" />
          {STEPS.map(({ icon: Icon, title, body }, i) => (
            <div key={title} className="relative flex gap-5 md:gap-6">
              <div className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-seal bg-surface text-seal">
                <Icon size={20} strokeWidth={2} />
              </div>
              <div className="pt-1.5">
                <div className="font-mono text-xs uppercase tracking-widest text-brass">Step {i + 1}</div>
                <h3 className="mt-1 font-display text-lg text-ink_text">{title}</h3>
                <p className="mt-1.5 max-w-lg text-sm leading-relaxed text-muted">{body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
      <LedgerNode />
    </>
  );
}
