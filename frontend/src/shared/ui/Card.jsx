/**
 * Card — Simple container with subtle border and background.
 */
export default function Card({ className = "", children, ...props }) {
  return (
    <div
      className={[
        "rounded-lg bg-bg-card border border-border shadow-card",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
