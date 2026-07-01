import { type ReactNode } from "react";
import { NeuralParticles } from "@/shared/layout/NeuralParticles";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-dvh items-center justify-center bg-bg-base px-4 overflow-hidden">
      <NeuralParticles />
      <div className="relative z-10 w-full max-w-sm">{children}</div>
    </div>
  );
}
