"use client";
import React from "react";
import TopBar from "../src/shared/ui/TopBar";
import { useAuth } from "../src/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";

export default function RootCanvas(){
  const { user, loading } = useAuth();
  const router = useRouter();
  if (loading) return null;
  if (!user) { router.push('/auth/login'); return null; }

  return (
    <div style={{minHeight:'100vh',display:'flex',flexDirection:'column'}}>
      <TopBar />
      <main style={{flex:1,display:'flex',alignItems:'center',justifyContent:'center'}}>
        <div className="cortex-fade-in" style={{textAlign:'center',opacity:0.9}}>
          <h2 style={{fontSize:22,margin:0,fontWeight:700}}>Empty Cortex Brain Canvas</h2>
          <p className="subtle" style={{marginTop:8}}>Begin by opening your identity controls.</p>
        </div>
      </main>
    </div>
  );
}
"use client";

// Minimal blank dashboard canvas (post-auth). Intentionally small — placeholder for future modules.
export default function Page() {
  return (
    <main className="min-h-[60vh] w-full bg-transparent">
      {/* Intentionally empty authenticated canvas. Avatar is in header (top-right). */}
    </main>
  );
}
