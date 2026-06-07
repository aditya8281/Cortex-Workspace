"use client";
import React from "react";
import TopBar from "../src/shared/ui/TopBar";
import { useAuth } from "../src/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function RootCanvas(){
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/auth");
    }
  }, [loading, router, user]);

  if (loading || !user) return null;

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
