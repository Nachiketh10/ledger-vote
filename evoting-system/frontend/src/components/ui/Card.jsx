export default function Card({ children, className = "", as: Component = "div", ...props }) {
  return (
    <Component
      className={`rounded-lg border border-line bg-surface shadow-sm shadow-ink/5 ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
}
