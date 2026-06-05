export function Loader({ className = "", label = "Loading" }) {
  return (
    <span
      role="status"
      aria-label={label}
      className={[
        "cortex-processing-text inline-flex h-5 w-5 animate-spin rounded-full border-2 border-cortex-border border-t-cortex-cyan",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      style={{ animationDuration: "1.2s" }}
    />
  );
}