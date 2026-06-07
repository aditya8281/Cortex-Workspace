"use client";
import React from "react";
import AvatarButton from "./AvatarButton";

export default function TopBar(){
  return (
    <div style={{height:56}} className="w-full flex items-center justify-end px-6">
      <div className="flex items-center gap-3">
        <AvatarButton />
      </div>
    </div>
  );
}
