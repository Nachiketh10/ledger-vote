const tones = {
  verified: "bg-verified/10 text-verified border-verified/30",
  brass: "bg-brass/10 text-brass border-brass/30",
  alert: "bg-alert/10 text-alert border-alert/30",
  neutral: "bg-ink/5 text-muted border-line dark:bg-white/5",
};

export default function Badge({ tone = "neutral", children, className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1
        text-xs font-medium tracking-wide ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
