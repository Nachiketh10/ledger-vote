import { Link, useNavigate } from "react-router-dom";
import { Link2, LogOut, User } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import ThemeToggle from "../components/ui/ThemeToggle";

export default function VoterLayout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-parchment">
      <header className="flex items-center justify-between border-b border-line bg-surface px-6 py-4">
        <Link to="/voter" className="flex items-center gap-2 font-display text-lg text-ink_text">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-seal text-white">
            <Link2 size={16} strokeWidth={2.25} />
          </span>
          Ledger&nbsp;Vote
        </Link>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link
            to="/voter/profile"
            className="hidden items-center gap-1.5 text-sm text-muted hover:text-ink_text sm:flex"
          >
            <User size={15} /> {user?.name}
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm text-muted hover:text-alert"
          >
            <LogOut size={15} /> Log out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-6 py-10">{children}</main>
    </div>
  );
}
