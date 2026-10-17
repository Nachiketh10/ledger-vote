import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X, Link2 } from "lucide-react";
import Button from "../ui/Button";
import ThemeToggle from "../ui/ThemeToggle";

const NAV_LINKS = [
  { href: "#about", label: "About" },
  { href: "#security", label: "Security" },
  { href: "#elections", label: "Elections" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#contact", label: "Contact" },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-parchment/85 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2 font-display text-lg text-ink_text">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-seal text-white">
            <Link2 size={16} strokeWidth={2.25} />
          </span>
          Ledger&nbsp;Vote
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-muted transition-colors hover:text-ink_text"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggle />
          <Button as={Link} to="/login" variant="ghost" size="sm">
            Log in
          </Button>
          <Button as={Link} to="/register" variant="primary" size="sm">
            Register to vote
          </Button>
        </div>

        <button
          className="flex h-9 w-9 items-center justify-center rounded-md md:hidden"
          onClick={() => setOpen((o) => !o)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      {open && (
        <div className="border-t border-line bg-parchment px-6 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="text-sm text-muted"
              >
                {link.label}
              </a>
            ))}
            <div className="flex items-center justify-between pt-2">
              <ThemeToggle />
              <div className="flex gap-2">
                <Button as={Link} to="/login" variant="outline" size="sm">
                  Log in
                </Button>
                <Button as={Link} to="/register" variant="primary" size="sm">
                  Register
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
