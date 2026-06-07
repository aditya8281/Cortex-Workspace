"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../src/shared/auth/AuthProvider";
import { apiRegister } from "../../../src/shared/auth/cortexApi";
import { Field, TextInput, PasswordInput, Btn, ErrorBanner } from "../../../src/shared/ui/Primitives";

function Dots({active=0}){
  return (<div className="progress-dots">{[0,1,2].map(i => <div key={i} className={`dot ${i===active? 'active':''}`} />)}</div>);
}

export default function RegisterPage(){
  const router = useRouter();
  const { login } = useAuth();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ username:'', password:'', confirm_password:'', full_name:'', nickname:'', vault_password:'', vault_password_confirm:'' });

  function setField(k,v){ setForm(f => ({...f,[k]:v})); }

  async function submit(){
    setError("");
    if (step === 0) {
      if (!form.username.trim() || form.password.length < 8) { setError('Provide username and a password (min 8 chars)'); return; }
      if (form.password !== form.confirm_password) { setError('Passwords do not match'); return; }
      setStep(1); return;
    }
    if (step === 1) {
      if (!form.full_name.trim() || !form.nickname.trim()) { setError('Full name and nickname are required'); return; }
      setStep(2);
      return;
    }
    if (step === 2) {
      if (form.vault_password.length < 8) { setError('Vault password min 8 chars'); return; }
      if (form.vault_password !== form.vault_password_confirm) { setError('Vault passwords do not match'); return; }
      setLoading(true);
      try {
        const res = await apiRegister({
          username: form.username.trim(),
          password: form.password,
          confirm_password: form.confirm_password,
          full_name: form.full_name.trim(),
          nickname: form.nickname.trim(),
          vault_password: form.vault_password,
        });
        await login(res.access_token, res.user);
        router.push('/');
      } catch (err) { setError(err.message || 'Registration failed'); }
      finally { setLoading(false); }
    }
  }

  return (
    <div style={{minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div className="glass-card cortex-fade-in" style={{width:520,padding:28}}>
        <h1 style={{margin:0,fontSize:20,fontWeight:700}}>Cortex</h1>
        <div className="subtle" style={{marginBottom:14}}>Access your cognitive system</div>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10}}>
          <Dots active={step} />
          <div className="subtle">Step {step+1} / 3</div>
        </div>
        <form onSubmit={(e)=>{e.preventDefault(); submit();}} className="grid gap-3">
          {step===0 && (
            <>
              <Field><TextInput placeholder="username" value={form.username} onChange={e=>setField('username',e.target.value)} /></Field>
              <Field><PasswordInput placeholder="password" value={form.password} onChange={e=>setField('password',e.target.value)} /></Field>
              <Field><PasswordInput placeholder="confirm password" value={form.confirm_password} onChange={e=>setField('confirm_password',e.target.value)} /></Field>
            </>
          )}
          {step===1 && (
            <>
              <Field><TextInput placeholder="Full name" value={form.full_name} onChange={e=>setField('full_name',e.target.value)} /></Field>
              <Field><TextInput placeholder="Nickname (optional)" value={form.nickname} onChange={e=>setField('nickname',e.target.value)} /></Field>
            </>
          )}
          {step===2 && (
            <>
              <Field><PasswordInput placeholder="Vault password" value={form.vault_password} onChange={e=>setField('vault_password',e.target.value)} /></Field>
              <Field><PasswordInput placeholder="Confirm vault password" value={form.vault_password_confirm} onChange={e=>setField('vault_password_confirm',e.target.value)} /></Field>
            </>
          )}
          <ErrorBanner message={error} />
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <div>
              {step>0 && (<button type="button" className="btn-ghost" onClick={()=>setStep(s=>s-1)}>Back</button>)}
            </div>
            <button type="submit" className="btn-ghost">{step<2? 'Next':'Create Account'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
