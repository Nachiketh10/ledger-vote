import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Vote, Users, ShieldAlert, Link2, ScrollText,
  BarChart3, Settings as SettingsIcon, LogOut, Menu, X,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import ThemeToggle from "../components/ui/ThemeToggle";

const navItems = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/elections", label: "Elections & Candidates", icon: Vote },
  { to: "/admin/voters", label: "Voter Registration", icon: Users },
  { to: "/admin/fraud", label: "Fraud Monitoring", icon: ShieldAlert },
  { to: "/admin/blockchain", label: "Blockchain Explorer", icon: Link2 },
  { to: "/admin/audit", label: "Audit Logs", icon: ScrollText },
  { to: "/admin/results", label: "Results", icon: BarChart3 },
  { to: "/admin/settings", label: "Settings", icon: SettingsIcon },
];

export default function AdminLayout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const SidebarContent = () => (
    <>
      <div className="flex items-center gap-2 px-5 py-5 font-display text-lg text-ink_text">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-seal text-white">
          <Link2 size={16} strokeWidth={2.25} />
        </span>
        Ledger&nbsp;Vote
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-seal/10 text-seal"
                  : "text-muted hover:bg-ink/5 hover:text-ink_text dark:hover:bg-white/5"
              }`
            }
          >
            <Icon size={17} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-line px-5 py-4">
        <p className="truncate text-sm font-medium text-ink_text">{user?.name}</p>
        <p className="truncate text-xs text-muted">{user?.role === "super_admin" ? "Super Admin" : "Election Admin"}</p>
        <button
          onClick={handleLogout}
          className="mt-3 flex items-center gap-2 text-sm text-muted hover:text-alert"
        >
          <LogOut size={15} /> Log out
        </button>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen bg-parchment">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-col border-r border-line bg-surface md:flex">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-ink/40" onClick={() => setMobileOpen(false)} />
          <aside className="relative z-50 flex w-64 flex-col bg-surface">
            <SidebarContent />
          </aside>
        </div>
      )}

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-line bg-surface px-5 py-3 md:justify-end">
          <button className="md:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu size={20} className="text-ink_text" />
          </button>
          <ThemeToggle />
        </header>
        <main className="flex-1 p-5 md:p-8">{children}</main>
      </div>
    </div>
  );
}
