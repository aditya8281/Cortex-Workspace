const base =
  "rounded-cortex-lg border border-cortex-border bg-cortex-surface p-cortex-16 text-cortex-text shadow-cortex transition duration-cortex ease-cortex hover:-translate-y-0.5 hover:border-cortex-cyan/20 hover:shadow-cortex-cyan";

export function Card({ className = "", ...props }) {
  return <section className={[base, "cortex-panel-motion", className].filter(Boolean).join(" ")} {...props} />;
}
