/**
 * A thin vertical thread with a node-tick, placed between sections of
 * the landing page. This isn't decoration: the product's core mechanic
 * is "each block links to the one before it" — this divider makes the
 * page's own structure echo that literally, section linked to section.
 */
export default function LedgerNode({ label }) {
  return (
    <div className="relative flex items-center justify-center py-2" aria-hidden="true">
      <div className="h-10 w-px bg-line" />
      <div className="absolute flex h-3 w-3 items-center justify-center rounded-full border-2 border-brass bg-parchment">
        <div className="h-1 w-1 rounded-full bg-brass" />
      </div>
      {label && (
        <span className="absolute left-1/2 ml-4 whitespace-nowrap font-mono text-[10px] uppercase tracking-widest text-muted">
          {label}
        </span>
      )}
    </div>
  );
}
