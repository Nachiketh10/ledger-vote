import { motion } from "framer-motion";
import { UserCheck, ShieldCheck, Lock, CheckCircle2 } from "lucide-react";

// A simple, plain-language "what happens to your vote" sequence —
// replaces raw SHA-256 hex strings (accurate, but meaningless to a
// layman glancing at the homepage) with the same idea in words anyone
// understands: your identity gets checked, fraud gets ruled out, the
// vote gets locked down, and it's permanently sealed.
const STAGES = [
  { icon: UserCheck, label: "Identity verified" },
  { icon: ShieldCheck, label: "No fraud detected" },
  { icon: Lock, label: "Vote locked & hashed" },
  { icon: CheckCircle2, label: "Sealed in the chain", highlight: true },
];

export default function HashChainVisual({ className = "" }) {
  return (
    <div className={`flex flex-col gap-0 ${className}`}>
      {STAGES.map((stage, i) => (
        <div key={stage.label} className="flex flex-col items-stretch">
          <motion.div
            initial={{ opacity: 0, y: 14, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: i * 0.35, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className={`flex items-center gap-3 rounded-lg border px-4 py-3.5 shadow-sm ${
              stage.highlight ? "border-brass/50 bg-brass/10" : "border-line bg-surface"
            }`}
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: i * 0.35 + 0.2, duration: 0.25 }}
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                stage.highlight ? "bg-brass/20 text-brass" : "bg-verified/10 text-verified"
              }`}
            >
              <stage.icon size={16} strokeWidth={2.25} />
            </motion.div>
            <span className={`text-sm font-medium ${stage.highlight ? "text-brass" : "text-ink_text"}`}>
              {stage.label}
            </span>
          </motion.div>

          {i < STAGES.length - 1 && (
            <motion.div
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ delay: i * 0.35 + 0.45, duration: 0.3 }}
              style={{ transformOrigin: "top" }}
              className="ml-[19px] h-4 w-px bg-line"
              aria-hidden="true"
            />
          )}
        </div>
      ))}
    </div>
  );
}
