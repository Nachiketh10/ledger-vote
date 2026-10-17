import { forwardRef, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { inputClass } from "./FormField";

/**
 * Drop-in replacement for a plain password <input> — same props/ref
 * forwarding pattern react-hook-form's register() expects, but with an
 * eye icon to toggle visibility so people can check what they typed
 * before submitting.
 */
const PasswordInput = forwardRef(function PasswordInput({ className = "", ...props }, ref) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative">
      <input
        ref={ref}
        type={visible ? "text" : "password"}
        className={`${inputClass} pr-10 ${className}`}
        {...props}
      />
      <button
        type="button"
        tabIndex={-1}
        onClick={() => setVisible((v) => !v)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink_text"
        aria-label={visible ? "Hide password" : "Show password"}
      >
        {visible ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
});

export default PasswordInput;
