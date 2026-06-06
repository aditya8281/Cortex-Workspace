"use client";
import React from "react";

export default function Modal({ open, onClose, children, title }){
  if (!open) return null;
  return (
    <div style={{position:'fixed',inset:0,zIndex:60,display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div style={{position:'absolute',inset:0,backdropFilter:'blur(6px)',background:'rgba(2,4,8,0.45)'}} onClick={onClose} />
      <div className="glass-card cortex-fade-in" style={{zIndex:61,minWidth:320,maxWidth:720,padding:20}}>
        {title && <div style={{fontWeight:700,marginBottom:8}}>{title}</div>}
        {children}
      </div>
    </div>
  );
}
