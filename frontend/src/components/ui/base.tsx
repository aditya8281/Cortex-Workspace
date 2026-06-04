import React, { useState } from "react";
import clsx from "clsx";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const baseStyles = "font-medium rounded transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary: "bg-primary hover:bg-primary-hover text-white",
    secondary: "bg-surface hover:bg-border text-white border border-border",
    danger: "bg-danger hover:bg-red-700 text-white",
    ghost: "hover:bg-surface text-white",
  };

  const sizes = {
    sm: "px-3 py-1 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <button
      className={clsx(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? "Loading..." : children}
    </button>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className, ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && <label className="block text-sm font-medium mb-1 text-white">{label}</label>}
      <input
        className={clsx(
          "w-full px-3 py-2 bg-surface border border-border rounded text-white placeholder-gray-400 focus:outline-none focus:border-primary",
          error && "border-danger",
          className
        )}
        {...props}
      />
      {error && <p className="text-danger text-sm mt-1">{error}</p>}
    </div>
  );
}

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={clsx("bg-surface border border-border rounded-lg p-4", className)}>
      {children}
    </div>
  );
}

export function Badge({ children, variant = "primary" }: { children: React.ReactNode; variant?: string }) {
  const variants: Record<string, string> = {
    primary: "bg-primary text-white",
    secondary: "bg-secondary text-white",
    danger: "bg-danger text-white",
  };
  return (
    <span className={clsx("px-2 py-1 text-xs rounded font-medium", variants[variant as keyof typeof variants])}>
      {children}
    </span>
  );
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center">
      <div className="animate-pulse w-8 h-8 bg-primary rounded-full"></div>
    </div>
  );
}
