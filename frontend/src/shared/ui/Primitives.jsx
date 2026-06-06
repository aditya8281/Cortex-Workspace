"use client";
import React from "react";
import "./CortexStyles.css";

export function Btn({ children, className = "", ...props }) {
  return (
    <button className={`btn-ghost ${className}`} {...props}>{children}</button>
  );
}

export function Field({ label, children }) {
  return (
    <div className="grid gap-1">
      {label && <label className="subtle text-[13px]">{label}</label>}
      {children}
    </div>
  );
}

export function TextInput(props){
  return <input {...props} className="px-3 py-2 rounded-[8px] bg-transparent border border-white/3 text-sm outline-none" />;
}

export function PasswordInput(props){
  return <input type="password" {...props} className="px-3 py-2 rounded-[8px] bg-transparent border border-white/3 text-sm outline-none" />;
}

export function ErrorBanner({ message }){
  if (!message) return null;
  return (<div style={{boxShadow:'0 0 20px rgba(255,80,80,0.08)'}} className="rounded px-3 py-2 text-sm text-[#ff9b9b]">{message}</div>);
}

export function SuccessBanner({ message }){
  if (!message) return null;
  return (<div className="rounded px-3 py-2 text-sm text-cortex-cyan">{message}</div>);
}

export default null;
