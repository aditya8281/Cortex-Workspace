"use client";
import React, { useState } from "react";
import { useAuth } from "../auth/AuthProvider";
import { apiGetProfilePhotoUrl } from "../auth/cortexApi";
import Dropdown from "./Dropdown";

function Avatar({ user }){
  if (!user) return (<div className="avatar-circle avatar-glow">?</div>);
  if (user.profile_photo) return <img src={apiGetProfilePhotoUrl()} alt="avatar" className="avatar-circle" />;
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
