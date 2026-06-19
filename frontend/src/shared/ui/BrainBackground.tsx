"use client";

import { useRef, useMemo, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return s / 2147483647;
  };
}

function WireframeBrain({ particleCount }: { particleCount: number }) {
  const meshRef = useRef<THREE.Mesh>(null);

  const particles = useMemo(() => {
    const rand = seededRandom(42);
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const theta = rand() * Math.PI * 2;
      const phi = Math.acos(2 * rand() - 1);
      const r = 1.8 + rand() * 0.8;
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }
    return positions;
  }, [particleCount]);

  const geometry = useMemo(() => {
    const rand = seededRandom(42);
    const geo = new THREE.IcosahedronGeometry(1.3, 2);
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      pos.setY(i, pos.getY(i) * 0.85 + (rand() - 0.5) * 0.1);
      pos.setX(i, pos.getX(i) * (0.9 + rand() * 0.2));
      pos.setZ(i, pos.getZ(i) * (0.9 + rand() * 0.2));
    }
    geo.computeVertexNormals();
    return geo;
  }, []);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.1;
      const scale = 1 + Math.sin(clock.getElapsedTime() * 0.5) * 0.02;
      meshRef.current.scale.setScalar(scale);
    }
  });

  return (
    <group>
      <mesh ref={meshRef} geometry={geometry}>
        <meshBasicMaterial color="#06b6d4" wireframe transparent opacity={0.15} />
      </mesh>
      <points>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[particles, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#06b6d4"
          size={0.02}
          transparent
          opacity={0.4}
          sizeAttenuation
        />
      </points>
    </group>
  );
}

export default function BrainBackground({
  intensity = "medium",
}: {
  intensity?: "low" | "medium" | "high";
}) {
  const [reducedMotion] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });

  if (reducedMotion) {
    return (
      <div className="pointer-events-none fixed inset-0 z-[-1]">
        <div className="h-full w-full bg-gradient-to-b from-[#050508] to-[#030306]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.05),transparent_70%)]" />
      </div>
    );
  }

  const count = intensity === "high" ? 200 : intensity === "medium" ? 100 : 50;

  return (
    <div className="pointer-events-none fixed inset-0 z-[-1]">
      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        frameloop="demand"
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[5, 5, 5]} intensity={0.3} color="#06b6d4" />
        <WireframeBrain particleCount={count} />
      </Canvas>
    </div>
  );
}
