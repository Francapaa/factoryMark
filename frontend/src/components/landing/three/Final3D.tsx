"use client";
/* eslint-disable react-hooks/purity -- particle seeds are intentionally random, generated once */

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { getSoftDotTexture } from "./softDot";

/** CIERRE: brasas redondas ascendentes — todas suben (+Y), solo varía la velocidad. */
function Embers({ count = 380 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null);
  const { positions, speeds } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const speeds = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      positions.set([(Math.random() - 0.5) * 10, (Math.random() - 0.5) * 6, (Math.random() - 0.5) * 4], i * 3);
      speeds[i] = 0.3 + Math.random() * 1.3;
    }
    return { positions, speeds };
  }, [count]);
  const dot = useMemo(() => getSoftDotTexture(), []);

  useFrame((state, delta) => {
    const pts = ref.current;
    if (!pts) return;
    const t = state.clock.elapsedTime;
    const pos = pts.geometry.attributes.position as THREE.BufferAttribute;
    const arr = pos.array as Float32Array;
    for (let i = 0; i < count; i++) {
      const ix = i * 3;
      arr[ix + 1] += speeds[i] * delta * 1.2;
      // Oscilación lateral acotada (integral de seno): la dirección neta sigue siendo +Y.
      arr[ix] += Math.sin(t * 1.2 + i) * delta * 0.22;
      if (arr[ix + 1] > 3.4) {
        arr[ix + 1] = -3.4;
        arr[ix] = (Math.random() - 0.5) * 10;
      }
    }
    pos.needsUpdate = true;
    const m = pts.material as THREE.PointsMaterial;
    m.opacity = 0.6 + Math.sin(t * 2) * 0.12;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        color="#FF8A3D"
        size={0.2}
        map={dot}
        transparent
        opacity={0.7}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

export function Final3D() {
  return (
    <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 8], fov: 55 }} gl={{ antialias: true, alpha: true }}>
      <Embers />
      <ambientLight intensity={0.6} />
      <pointLight position={[0, 2, 4]} intensity={30} color="#FF5C00" />
    </Canvas>
  );
}
