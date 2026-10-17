import LedgerNode from "./LedgerNode";

export default function About() {
  return (
    <>
      <section id="about" className="mx-auto max-w-6xl px-6 py-20">
        <div className="grid gap-10 md:grid-cols-[0.9fr_1.1fr]">
          <div>
            <div className="font-mono text-xs uppercase tracking-widest text-brass">01 — About</div>
            <h2 className="mt-3 font-display text-3xl text-ink_text">
              An election office you can audit, not just trust.
            </h2>
          </div>
          <div className="space-y-4 text-base leading-relaxed text-muted">
            <p>
              Most e-voting systems ask you to trust a database. This one asks
              you to check the math instead. Every cast vote is hashed and
              linked to the one before it — the same structural guarantee
              that makes any blockchain tamper-evident, purpose-built here
              rather than borrowed from a cryptocurrency network.
            </p>
            <p>
              Underneath the ledger sits a biometric gate: CNN-based face
              matching with liveness detection. A voter proves who they are
              with their own face, not a password that can be phished or
              shared.
            </p>
          </div>
        </div>
      </section>
      <LedgerNode label="chain: verified" />
    </>
  );
}
