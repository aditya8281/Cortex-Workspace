"use client";
import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../auth/AuthProvider";
import Dropdown from "./Dropdown";

function Avatar({ user }){
  if (!user) return (<div className="avatar-circle avatar-glow">?</div>);
  if (user.profile_photo_url) return <img src={user.profile_photo_url} alt="avatar" className="avatar-circle" />;
  const initial = (user.full_name || user.username || "?")[0]?.toUpperCase();
  return <div className="avatar-circle avatar-glow">{initial}</div>;
}

export default function AvatarButton(){
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <div style={{position:'relative'}}>
      <button aria-haspopup onClick={() => setOpen((s) => !s)} className="p-0 bg-transparent border-0">
        <Avatar user={user} />
      </button>
      {open && (
        <div style={{position:'absolute',right:0,top:'calc(100% + 8px)'}}>
          <Dropdown onClose={() => setOpen(false)} onLogout={logout} />
        </div>
      )}
    </div>
  );
}
