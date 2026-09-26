"use client";
/* eslint-disable react-hooks/purity -- particle seeds are intentionally random, generated once */

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { getSoftDotTexture } from "./softDot";

/** CASOS: cristales ámbar flotando + polvo dorado con glow que asciende parejo. */
function Crystals() {
  const group = useRef<THREE.Group>(null);
  const dustRef = useRef<THREE.Points>(null);

  const seeds = useMemo(
    () =>
      Array.from({ length: 7 }, () => ({
        pos: [(Math.random() - 0.5) * 5.4, (Math.random() - 0.5) * 3.4, (Math.random() - 0.5) * 2] as const,
        scale: 0.28 + Math.random() * 0.5,
        speed: 0.4 + Math.random() * 0.9,
        phase: Math.random() * Math.PI * 2,
      })),
    []
  );

  const dustCount = 160;
  const { dust, dustSpeed, dustBaseX, dustPhase } = useMemo(() => {
    const dust = new Float32Array(dustCount * 3);
    const dustSpeed = new Float32Array(dustCount);
    const dustBaseX = new Float32Array(dustCount);
    const dustPhase = new Float32Array(dustCount);
    for (let i = 0; i < dustCount; i++) {
      const x = (Math.random() - 0.5) * 8;
      const y = (Math.random() - 0.5) * 5;
      dust.set([x, y, (Math.random() - 0.5) * 3], i * 3);
      dustBaseX[i] = x;
      dustSpeed[i] = 0.15 + Math.random() * 0.35;
      dustPhase[i] = Math.random() * Math.PI * 2;
    }
    return { dust, dustSpeed, dustBaseX, dustPhase };
  }, []);
  const dot = useMemo(() => getSoftDotTexture(), []);

  useFrame((state, delta) => {
    const t = state.clock.elapsedTime;
    if (group.current) {
      group.current.children.forEach((child, i) => {
        if (i >= seeds.length) return;
        const s = seeds[i];
        child.position.y = s.pos[1] + Math.sin(t * s.speed + s.phase) * 0.35;
        child.rotation.x = t * s.speed * 0.5 + s.phase;
        child.rotation.y = t * s.speed * 0.7;
      });
      group.current.rotation.y = Math.sin(t * 0.15) * 0.25 + state.pointer.x * 0.25;
      group.current.rotation.x = state.pointer.y * 0.12;
    }
    // Polvo dorado: todo asciende en la misma dirección (+Y), sin excepción.
    const pts = dustRef.current;
    if (pts) {
      const pos = pts.geometry.attributes.position as THREE.BufferAttribute;
      const arr = pos.array as Float32Array;
      for (let i = 0; i < dustCount; i++) {
        const ix = i * 3;
        arr[ix] = dustBaseX[i] + Math.sin(t * 0.7 + dustPhase[i]) * 0.18;
        arr[ix + 1] += dustSpeed[i] * delta;
        if (arr[ix + 1] > 2.8) arr[ix + 1] = -2.8;
      }
      pos.needsUpdate = true;
    }
  });

  return (
    <group ref={group}>
      {seeds.map((s, i) => (
        <mesh key={i} position={[s.pos[0], s.pos[1], s.pos[2]]} scale={s.scale}>
          <octahedronGeometry args={[1, 0]} />
          <meshStandardMaterial
            color={i % 2 === 0 ? "#F59E0B" : "#B45309"}
            emissive="#FBBF24"
            emissiveIntensity={0.35}
            roughness={0.15}
            metalness={0.55}
            transparent
            opacity={0.92}
          />
        </mesh>
      ))}
      <points ref={dustRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[dust, 3]} />
        </bufferGeometry>
        <pointsMaterial
          color="#D97706"
          size={0.16}
          map={dot}
          transparent
          opacity={0.5}
          sizeAttenuation
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
      <directionalLight position={[4, 5, 4]} intensity={2.2} color="#FFF7ED" />
      <pointLight position={[-3, 1, 3]} intensity={30} color="#F59E0B" />
      <ambientLight intensity={0.9} />
    </group>
  );
}

export function Cases3D() {
  return (
    <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 7.5], fov: 50 }} gl={{ antialias: true, alpha: true }}>
      <Crystals />
    </Canvas>
  );
}
