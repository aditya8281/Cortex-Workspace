"use client";

import { useCallback, useState } from "react";

export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function useField(initial = "") {
  const [value, setValue] = useState(initial);
  const onChange = useCallback((e) => setValue(e.target.value), []);
  return [value, onChange, setValue];
}

export function Field({ label, hint, error, children, id }) {
  return (
    <div className="grid gap-[6px]">
      <label
        htmlFor={id}
        className="font-mono text-[10px] uppercase tracking-[0.16em] text-cortex-text-muted"
      >
        {label}
      </label>
      {children}
      {hint && !error && (
        <p className="text-[11px] text-cortex-text-muted leading-4">{hint}</p>
      )}
      {error && (
        <p role="alert" className="text-[11px] text-cortex-error leading-4">{error}</p>
      )}
    </div>
  );
}

export function TextInput({ id, type = "text", placeholder, value, onChange, autoComplete, disabled, inputRef, className = "" }) {
  return (
    <input
      id={id}
      ref={inputRef}
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      autoComplete={autoComplete}
      disabled={disabled}
      className={cn(
        "w-full rounded-[6px] border border-cortex-border bg-cortex-bg-secondary px-4 py-[10px]",
        "text-sm text-cortex-text placeholder:text-cortex-text-muted",
        "transition-all duration-150 ease-out",
        "focus:border-cortex-cyan/40 focus:outline-none focus:ring-2 focus:ring-cortex-cyan/15",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
    />
  );
}

export function Textarea({ id, value, onChange, placeholder, rows = 3, disabled }) {
  return (
    <textarea
      id={id} value={value} onChange={onChange} placeholder={placeholder}
      rows={rows} disabled={disabled}
      className="w-full resize-none rounded-[6px] border border-cortex-border bg-cortex-bg-secondary px-4 py-[10px] text-sm text-cortex-text placeholder:text-cortex-text-muted transition-all duration-150 focus:border-cortex-cyan/40 focus:outline-none focus:ring-2 focus:ring-cortex-cyan/15 disabled:opacity-50"
    />
  );
}

export function PasswordInput({ id, value, onChange, placeholder, autoComplete, disabled, inputRef }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <TextInput
        id={id}
        ref={inputRef}
        type={show ? "text" : "password"}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        disabled={disabled}
        className="pr-12"
      />
      <button
        type="button"
        onClick={() => setShow((s) => !s)}
        aria-label={show ? "Hide password" : "Show password"}
        className="absolute right-3 top-1/2 -translate-y-1/2 font-mono text-[10px] uppercase tracking-[0.12em] text-cortex-text-muted transition-colors hover:text-cortex-cyan"
      >
        {show ? "hide" : "show"}
      </button>
    </div>
  );
}

export function Btn({ children, variant = "primary", size = "md", className = "", loading = false, ...props }) {
  const base = "inline-flex items-center justify-center gap-2 rounded-[6px] border font-medium tracking-wide transition-all duration-150 ease-out focus:outline-none focus-visible:ring-2 focus-visible:ring-cortex-cyan/40 disabled:cursor-not-allowed disabled:opacity-50 select-none";
  const variants = {
    primary: "border-cortex-cyan/35 bg-cortex-cyan/10 text-cortex-text hover:bg-cortex-cyan/18 hover:border-cortex-cyan/50",
    ghost: "border-transparent bg-transparent text-cortex-text-muted hover:border-cortex-border hover:text-cortex-text",
    danger: "border-cortex-error/40 bg-transparent text-cortex-error hover:bg-cortex-error/10",
    outline: "border-cortex-border bg-transparent text-cortex-text hover:border-cortex-cyan/30 hover:bg-cortex-surface",
  };
  const sizes = { sm: "h-8 px-3 text-xs", md: "h-10 px-5 text-sm", lg: "h-11 px-6 text-sm" };
  return (
    <button
      className={cn(base, variants[variant] || variants.primary, sizes[size] || sizes.md, className)}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <>
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-cortex-cyan/30 border-t-cortex-cyan" />
          <span>Processing…</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div role="alert" className="rounded-[6px] border border-cortex-error/35 bg-cortex-error/8 px-4 py-3 font-mono text-[12px] text-cortex-error">
      {message}
    </div>
  );
}

export function SuccessBanner({ message }) {
  if (!message) return null;
  return (
    <div role="status" className="rounded-[6px] border border-cortex-green/30 bg-cortex-green/8 px-4 py-3 font-mono text-[12px] text-cortex-green">
      ✓ {message}
    </div>
  );
}

export function SectionDivider({ label }) {
  return (
    <div className="flex items-center gap-3 py-1">
      <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-cortex-text-muted">{label}</span>
      <div className="h-px flex-1 bg-cortex-border/50" />
    </div>
  );
}

const STEP_LABELS = ["Account", "Profile", "Vault", "Storage", "Review"];
export function StepIndicator({ current, total }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={cn(
              "h-[3px] rounded-full transition-all duration-300",
              i < current
                ? "w-8 bg-cortex-cyan"
                : i === current
                ? "w-12 bg-cortex-cyan/70 animate-cortex-glow-pulse"
                : "w-6 bg-cortex-border"
            )}
          />
        </div>
      ))}
      <span className="ml-2 font-mono text-[10px] uppercase tracking-[0.14em] text-cortex-text-muted">
        {STEP_LABELS[current]} · {current + 1}/{total}
      </span>
    </div>
  );
}

export function Panel({ children, className = "" }) {
  return (
    <div
      className={cn(
        "w-full rounded-[10px] border border-cortex-border bg-cortex-surface/70 backdrop-blur-xl",
        "shadow-[0_2px_40px_rgba(0,0,0,0.35)]",
        className
      )}
    >
      {children}
    </div>
  );
}

export default {};
