"use client";
/* eslint-disable react-hooks/purity -- particle seeds are intentionally random, generated once */

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { getSoftDotTexture } from "./softDot";

function scrollProgress() {
  if (typeof window === "undefined") return 0;
  const max = document.documentElement.scrollHeight - window.innerHeight;
  if (max <= 0) return 0;
  return Math.min(1, Math.max(0, window.scrollY / max));
}

/**
 * Río de brasas: ~1300 partículas redondas con glow que viajan TODAS
 * en la misma dirección (hacia la cámara, +Z). Solo varía la velocidad
 * por partícula; el sway lateral es una oscilación suave que no cambia
 * la dirección neta. El scroll acelera la corriente.
 */
function FlowPoints({ count = 1300 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null);
  const { positions, colors, speeds, baseX, baseY, phase } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const speeds = new Float32Array(count);
    const baseX = new Float32Array(count);
    const baseY = new Float32Array(count);
    const phase = new Float32Array(count);
    const cA = new THREE.Color("#FF5C00");
    const cB = new THREE.Color("#FFD9A3");
    for (let i = 0; i < count; i++) {
      const x = (Math.random() - 0.5) * 26;
      const y = Math.sin(x * 0.45 + Math.random() * 6.28) * 3.2 + (Math.random() - 0.5) * 4;
      const z = (Math.random() - 0.5) * 22 - 4;
      positions.set([x, y, z], i * 3);
      baseX[i] = x;
      baseY[i] = y;
      phase[i] = Math.random() * Math.PI * 2;
      const c = cA.clone().lerp(cB, Math.random());
      colors.set([c.r, c.g, c.b], i * 3);
      speeds[i] = 0.7 + Math.random() * 1.8;
    }
    return { positions, colors, speeds, baseX, baseY, phase };
  }, [count]);
  const dot = useMemo(() => getSoftDotTexture(), []);

  useFrame((state, delta) => {
    const pts = ref.current;
    if (!pts) return;
    const p = scrollProgress();
    const t = state.clock.elapsedTime;
    const pos = pts.geometry.attributes.position as THREE.BufferAttribute;
    const arr = pos.array as Float32Array;
    const flow = delta * (1.1 + p * 6);
    for (let i = 0; i < count; i++) {
      const ix = i * 3;
      // Avance: solo +Z. Sway: oscilación alrededor de la base, sin deriva.
      arr[ix] = baseX[i] + Math.sin(t * 0.6 + phase[i]) * 0.35;
      arr[ix + 1] = baseY[i] + Math.cos(t * 0.5 + phase[i]) * 0.28;
      arr[ix + 2] += speeds[i] * flow;
      if (arr[ix + 2] > 8) arr[ix + 2] = -14;
    }
    pos.needsUpdate = true;
    pts.rotation.y = p * 0.5;
    pts.rotation.x = -0.1 + p * 0.22;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.22}
        map={dot}
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

/**
 * Línea de corriente: se DIBUJA a medida que el usuario scrollea.
 * El progreso del scroll controla cuántos segmentos del tubo están visibles
 * (drawRange) y una cabeza brillante viaja por la curva marcando el avance.
 */
function FlowRibbon() {
  const group = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.Mesh>(null);
  const head = useRef<THREE.Mesh>(null);
  const { curve, geometry } = useMemo(() => {
    const pts = Array.from({ length: 60 }, (_, i) => {
      const x = -13 + (i / 59) * 26;
      return new THREE.Vector3(x, Math.sin(x * 0.45) * 3.2, Math.cos(x * 0.3) * 2 - 3);
    });
    const curve = new THREE.CatmullRomCurve3(pts);
    return { curve, geometry: new THREE.TubeGeometry(curve, 200, 0.05, 8, false) };
  }, []);

  useFrame((state) => {
    const p = scrollProgress();
    const t = state.clock.elapsedTime;
    // Dibujo progresivo: de un tramo corto al tubo completo
    const total = geometry.index?.count ?? 0;
    geometry.setDrawRange(0, Math.max(24, Math.floor(total * (0.06 + p * 0.94))));
    // Cabeza brillante que viaja con el scroll
    if (head.current) {
      const pos = curve.getPointAt(Math.min(0.999, 0.02 + p * 0.97));
      head.current.position.copy(pos);
      head.current.scale.setScalar(0.22 + Math.sin(t * 3) * 0.035);
    }
    if (group.current) group.current.rotation.y = p * 0.35;
    if (meshRef.current) {
      const m = meshRef.current.material as THREE.MeshBasicMaterial;
      m.opacity = 0.28 + Math.sin(t * 1.4) * 0.08 + p * 0.15;
    }
  });

  return (
    <group ref={group}>
      <mesh ref={meshRef} geometry={geometry}>
        <meshBasicMaterial color="#FF5C00" transparent opacity={0.32} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
      <mesh ref={head}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshBasicMaterial color="#FFD9A3" transparent opacity={0.95} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
    </group>
  );
}

export function BackgroundFlow() {
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none" aria-hidden>
      <Canvas
        dpr={[1, 1.5]}
        camera={{ position: [0, 0.6, 9], fov: 60 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <FlowPoints />
        <FlowRibbon />
      </Canvas>
    </div>
  );
}
