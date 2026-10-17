import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../contexts/ThemeContext";

export default function ThemeToggle({ className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      aria-pressed={isDark}
      className={`relative inline-flex h-8 w-14 items-center rounded-full border border-line
        bg-surface transition-colors ${className}`}
    >
      <span
        className={`absolute left-1 flex h-6 w-6 items-center justify-center rounded-full
          bg-seal text-white transition-transform duration-200 ease-out
          ${isDark ? "translate-x-6" : "translate-x-0"}`}
      >
        {isDark ? <Moon size={13} strokeWidth={2.25} /> : <Sun size={13} strokeWidth={2.25} />}
      </span>
    </button>
  );
}
