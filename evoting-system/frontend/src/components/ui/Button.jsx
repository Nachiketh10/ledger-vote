import { forwardRef } from "react";

const variants = {
  primary:
    "bg-seal text-white hover:bg-seal/90 active:bg-seal/80 shadow-sm shadow-seal/20",
  brass:
    "bg-brass text-white hover:bg-brass/90 active:bg-brass/80 shadow-sm shadow-brass/20",
  outline:
    "border border-line text-ink_text hover:border-seal hover:text-seal bg-transparent",
  ghost:
    "text-ink_text hover:bg-ink/5 dark:hover:bg-white/5 bg-transparent",
};

const sizes = {
  sm: "px-3.5 py-1.5 text-sm",
  md: "px-5 py-2.5 text-sm",
  lg: "px-7 py-3.5 text-base",
};

const Button = forwardRef(
  ({ variant = "primary", size = "md", className = "", as: Component = "button", ...props }, ref) => {
    return (
      <Component
        ref={ref}
        className={`inline-flex items-center justify-center gap-2 rounded-md font-medium
          transition-colors duration-150 disabled:opacity-50 disabled:pointer-events-none
          ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export default Button;
