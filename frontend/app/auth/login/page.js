"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../src/shared/auth/AuthProvider";
import { apiLogin } from "../../../src/shared/auth/cortexApi";
import { Field, TextInput, PasswordInput, Btn, ErrorBanner } from "../../../src/shared/ui/Primitives";

export default function LoginPage(){
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  async function submit(e){
    e?.preventDefault();
    if (!username.trim() || !password) { setError('Username and password required'); return; }
    setLoading(true); setError("");
    try {
      const res = await apiLogin({ username: username.trim(), password });
      await login(res.access_token, res.user);
      router.push('/');
    } catch (err) { setError(err.message || 'Authentication failed'); }
    finally { setLoading(false); }
  }

  return (
    <div style={{minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div className="glass-card cortex-fade-in" style={{width:420,padding:28}}>
        <h1 style={{margin:0,fontSize:20,fontWeight:700}}>Cortex</h1>
        <div className="subtle" style={{marginBottom:14}}>Access your cognitive system</div>
        <form onSubmit={submit} className="grid gap-3">
          <Field>
            <TextInput placeholder="username" value={username} onChange={(e)=>setUsername(e.target.value)} autoFocus />
          </Field>
          <Field>
            <PasswordInput placeholder="password" value={password} onChange={(e)=>setPassword(e.target.value)} />
          </Field>
          <ErrorBanner message={error} />
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <div className="progress-dots"><div className="dot" /><div className="dot" /><div className="dot" /></div>
            <button type="submit" className="btn-ghost" disabled={loading}>{loading? 'Entering…':'Enter Cortex'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
