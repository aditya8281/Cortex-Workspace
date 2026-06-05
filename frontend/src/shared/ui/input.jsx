import { forwardRef } from "react";

const base =
  "w-full rounded-cortex border border-cortex-border bg-cortex-bg-secondary px-cortex-16 py-cortex-12 text-sm text-cortex-text placeholder:text-cortex-text-muted transition duration-cortex ease-cortex focus:border-cortex-cyan/35 focus:outline-none focus:ring-2 focus:ring-cortex-cyan/20 disabled:cursor-not-allowed disabled:opacity-60";

export const Input = forwardRef(function Input(
  { className = "", type = "text", ...props },
  ref
) {
  const classes = [base, className].filter(Boolean).join(" ");
  return <input ref={ref} type={type} className={classes} {...props} />;
});