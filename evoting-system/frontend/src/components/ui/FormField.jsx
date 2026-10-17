export default function FormField({ label, error, children, className = "" }) {
  return (
    <div className={`mb-4 ${className}`}>
      <label className="mb-1.5 block text-sm font-medium text-ink_text">{label}</label>
      {children}
      {error && <p className="mt-1.5 text-xs text-alert">{error}</p>}
    </div>
  );
}

export const inputClass =
  "w-full rounded-md border border-line bg-parchment px-3.5 py-2.5 text-sm text-ink_text " +
  "placeholder:text-muted/60 focus:border-seal outline-none transition-colors";
