"use client";
/* eslint-disable react-hooks/purity -- particle seeds are intentionally random, generated once */

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { getSoftDotTexture } from "./softDot";

/** HERO: núcleo de brasa — torus knot + anillo de partículas redondas + jaula. */
function Core() {
  const knot = useRef<THREE.Mesh>(null);
  const cage = useRef<THREE.Mesh>(null);
  const ring = useRef<THREE.Points>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const mx = state.pointer.x;
    const my = state.pointer.y;
    if (knot.current) {
      knot.current.rotation.x = t * 0.35 + my * 0.4;
      knot.current.rotation.y = t * 0.5 + mx * 0.6;
    }
    if (cage.current) {
      cage.current.rotation.x = -t * 0.12;
      cage.current.rotation.y = t * 0.18;
    }
    if (ring.current) {
      ring.current.rotation.z = t * 0.25;
      ring.current.rotation.x = 0.9 + Math.sin(t * 0.4) * 0.1;
    }
  });

  const ringPositions = useMemo(() => {
    const n = 260;
    const arr = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const r = 2.6 + Math.random() * 0.25;
      arr.set([Math.cos(a) * r, Math.sin(a) * r, (Math.random() - 0.5) * 0.5], i * 3);
    }
    return arr;
  }, []);
  const dot = useMemo(() => getSoftDotTexture(), []);

  return (
    <group>
      <mesh ref={knot}>
        <torusKnotGeometry args={[1.05, 0.32, 180, 24]} />
        <meshStandardMaterial color="#FF5C00" emissive="#FF2E00" emissiveIntensity={0.55} roughness={0.25} metalness={0.65} />
      </mesh>
      <mesh ref={cage}>
        <icosahedronGeometry args={[2.05, 1]} />
        <meshBasicMaterial color="#FF8A3D" wireframe transparent opacity={0.28} />
      </mesh>
      <points ref={ring}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[ringPositions, 3]} />
        </bufferGeometry>
        <pointsMaterial
          color="#FFB25C"
          size={0.14}
          map={dot}
          transparent
          opacity={0.9}
          sizeAttenuation
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
      <pointLight position={[4, 3, 4]} intensity={60} color="#FF8A3D" />
      <pointLight position={[-4, -2, 2]} intensity={25} color="#FF2E00" />
      <ambientLight intensity={0.5} />
    </group>
  );
}

export function Hero3D() {
  return (
    <Canvas dpr={[1, 1.6]} camera={{ position: [0, 0, 6.4], fov: 50 }} gl={{ antialias: true, alpha: true }}>
      <Core />
    </Canvas>
  );
}
