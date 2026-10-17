import { Link } from "react-router-dom";
import { ShieldCheck, ScanFace } from "lucide-react";
import Button from "../ui/Button";
import HashChainVisual from "./HashChainVisual";

export default function Hero() {
  return (
    <section className="bg-ink text-cream">
      <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 md:grid-cols-2 md:items-center md:py-28">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cream/15 px-3 py-1 font-mono text-[11px] uppercase tracking-widest text-cream/60">
            <ShieldCheck size={13} /> Hybrid blockchain e-voting
          </div>

          <h1 className="font-display text-4xl leading-[1.1] text-cream md:text-5xl">
            Your vote becomes a block.
            <br />
            <span className="text-brass">Provable, not just promised.</span>
          </h1>

          <p className="mt-6 max-w-md text-base leading-relaxed text-cream/70">
            Face verification and fraud detection stand between a voter and
            the ballot box. Once cast, every vote is SHA-256 hashed into a
            chain that anyone can independently verify — tamper with one
            block, and the break is visible immediately.
          </p>

          <div className="mt-9 flex flex-wrap gap-3">
            <Button as={Link} to="/register" variant="brass" size="lg">
              <ScanFace size={18} /> Register to vote
            </Button>
            <Button as="a" href="#how-it-works" variant="outline" size="lg" className="border-cream/20 text-cream hover:border-brass hover:text-brass">
              See how it works
            </Button>
          </div>
        </div>

        <div className="relative">
          <HashChainVisual />
        </div>
      </div>
    </section>
  );
}
