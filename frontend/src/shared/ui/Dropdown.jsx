"use client";
import React from "react";
import { useRouter } from "next/navigation";

export default function Dropdown({ onClose, onLogout }){
  const router = useRouter();
  return (
    <div className="dropdown-panel cortex-fade-in">
      <div style={{display:'flex',flexDirection:'column',gap:6}}>
        <button type="button" className="btn-ghost" onClick={() => { onClose(); router.push('/profile'); }}>Profile</button>
        <button type="button" className="btn-ghost" onClick={() => { onClose(); router.push('/vault'); }}>Vault</button>
        <button type="button" className="btn-ghost" onClick={() => { onClose(); fetch('/api/auth/export').then(()=>{}).catch(()=>{}); }}>Export .crtx</button>
        <button type="button" className="btn-ghost" onClick={() => { onClose(); router.push('/profile#change-password'); }}>Change Password</button>
        <hr style={{borderColor:'rgba(255,255,255,0.03)'}} />
        <button type="button" className="btn-ghost danger" onClick={async () => { if (!confirm('Delete account? This is irreversible.')) return; await fetch('/api/auth/delete',{method:'POST'}); onLogout(); }}>Delete Account</button>
      </div>
    </div>
  );
}
