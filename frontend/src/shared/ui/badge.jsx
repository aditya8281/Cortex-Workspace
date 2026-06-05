const base =
  "inline-flex items-center rounded-cortex-pill border px-cortex-12 py-1 text-xs font-medium uppercase tracking-[0.12em]";

const variants = {
  neutral: "border-cortex-border text-cortex-text-muted",
  cyan: "border-cortex-cyan/30 text-cortex-cyan shadow-cortex-cyan",
  green: "border-cortex-green/30 text-cortex-green shadow-cortex-green",
  warning: "border-cortex-warning/30 text-cortex-warning",
  error: "border-cortex-error/30 text-cortex-error",
};

export function Badge({ variant = "neutral", className = "", ...props }) {
  return <span className={[base, variants[variant] || variants.neutral, className].filter(Boolean).join(" ")} {...props} />;
}