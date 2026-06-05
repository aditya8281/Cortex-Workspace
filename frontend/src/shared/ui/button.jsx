const base =
  "inline-flex items-center justify-center gap-cortex-8 rounded-cortex border border-cortex-border px-cortex-16 py-cortex-8 text-sm font-medium tracking-wide text-cortex-text transition duration-cortex ease-cortex hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-cortex-cyan/40 disabled:cursor-not-allowed disabled:opacity-60";

const variants = {
  primary: "border-cortex-cyan/30 bg-cortex-cyan/10 shadow-cortex-cyan hover:bg-cortex-cyan/15",
  secondary: "bg-transparent hover:border-cortex-cyan/20 hover:bg-cortex-surface",
  danger: "border-cortex-error/45 bg-transparent text-cortex-error hover:bg-cortex-error/10",
};

const sizes = {
  sm: "h-8 px-cortex-12 text-xs",
  md: "h-10 px-cortex-16 text-sm",
  lg: "h-12 px-cortex-24 text-sm",
};

export function Button({
  as: Component = "button",
  variant = "secondary",
  size = "md",
  className = "",
  type = "button",
  ...props
}) {
  const classes = [base, variants[variant] || variants.secondary, sizes[size] || sizes.md, className]
    .filter(Boolean)
    .join(" ");

  return <Component type={Component === "button" ? type : undefined} className={classes} {...props} />;
}
