import { Link2 } from "lucide-react";

export default function Footer() {
  return (
    <footer id="contact" className="bg-ink text-cream">
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid gap-12 md:grid-cols-[1.3fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-2 font-display text-lg">
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-brass text-white">
                <Link2 size={16} strokeWidth={2.25} />
              </span>
              Ledger Vote
            </div>
            <p className="mt-4 max-w-sm text-sm text-cream/60">
              Every vote becomes a block. Every block is provable. Built with a custom
              SHA-256 chain, CNN face verification, and platform biometric authentication.
            </p>
          </div>

          <div>
            <div className="font-mono text-xs uppercase tracking-widest text-cream/50">Platform</div>
            <ul className="mt-4 space-y-2 text-sm text-cream/70">
              <li><a href="#security" className="hover:text-cream">Security model</a></li>
              <li><a href="#how-it-works" className="hover:text-cream">How voting works</a></li>
              <li><a href="#elections" className="hover:text-cream">Live elections</a></li>
            </ul>
          </div>

          <div>
            <div className="font-mono text-xs uppercase tracking-widest text-cream/50">Contact</div>
            <ul className="mt-4 space-y-2 text-sm text-cream/70">
              <li>election-office@example.edu</li>
              <li>Student Government Office, Room 214</li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-2 border-t border-cream/10 pt-6 text-xs text-cream/40 md:flex-row md:items-center md:justify-between">
          <span>&copy; {new Date().getFullYear()} Ledger Vote. A student engineering project.</span>
          <span className="font-hash">chain-integrity: verified</span>
        </div>
      </div>
    </footer>
  );
}
