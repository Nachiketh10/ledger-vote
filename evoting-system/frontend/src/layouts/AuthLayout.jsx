import { Link } from "react-router-dom";
import { Link2 } from "lucide-react";
import ThemeToggle from "../components/ui/ThemeToggle";

export default function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="flex min-h-screen flex-col bg-parchment">
      <header className="flex items-center justify-between px-6 py-5">
        <Link to="/" className="flex items-center gap-2 font-display text-lg text-ink_text">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-seal text-white">
            <Link2 size={16} strokeWidth={2.25} />
          </span>
          Ledger&nbsp;Vote
        </Link>
        <ThemeToggle />
      </header>

      <main className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <h1 className="font-display text-2xl text-ink_text">{title}</h1>
            {subtitle && <p className="mt-2 text-sm text-muted">{subtitle}</p>}
          </div>
          <div className="rounded-lg border border-line bg-surface p-8 shadow-sm">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
