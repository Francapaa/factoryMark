"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

/** PIPELINE: red orbital — 5 nodos (agentes) conectados + satélite. Distinto al hero. */
function Network({ active = 0 }: { active?: number }) {
  const group = useRef<THREE.Group>(null);
  const sat = useRef<THREE.Mesh>(null);

  const nodes = useMemo(
    () =>
      Array.from({ length: 5 }, (_, i) => {
        const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
        return new THREE.Vector3(Math.cos(a) * 2.1, Math.sin(a) * 2.1, 0);
      }),
    []
  );

  const lineGeom = useMemo(() => {
    const pts = [...nodes, nodes[0]];
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, [nodes]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (group.current) group.current.rotation.z = t * 0.12;
    if (sat.current) {
      const a = t * 0.9;
      sat.current.position.set(Math.cos(a) * 2.1, Math.sin(a) * 2.1, 0.35 + Math.sin(t * 2) * 0.12);
    }
  });

  return (
    <group ref={group}>
      <lineLoop geometry={lineGeom}>
        <lineBasicMaterial color="#FF5C00" transparent opacity={0.55} />
      </lineLoop>
      {nodes.map((p, i) => (
        <mesh key={i} position={p}>
          <sphereGeometry args={[i === active ? 0.3 : 0.2, 24, 24]} />
          <meshStandardMaterial
            color={i === active ? "#FFD9A3" : "#FF5C00"}
            emissive="#FF2E00"
            emissiveIntensity={i === active ? 1.1 : 0.45}
            roughness={0.3}
            metalness={0.4}
          />
        </mesh>
      ))}
      <mesh ref={sat}>
        <octahedronGeometry args={[0.14]} />
        <meshBasicMaterial color="#FFF7ED" />
      </mesh>
      {/* anillos orbitales cruzados */}
      <mesh rotation={[Math.PI / 2.4, 0, 0]}>
        <torusGeometry args={[2.9, 0.012, 8, 120]} />
        <meshBasicMaterial color="#FF8A3D" transparent opacity={0.4} />
      </mesh>
      <pointLight position={[0, 0, 4]} intensity={40} color="#FF8A3D" />
      <ambientLight intensity={0.7} />
    </group>
  );
}

export function Pipeline3D({ active = 0 }: { active?: number }) {
  return (
    <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 7], fov: 50 }} gl={{ antialias: true, alpha: true }}>
      <Network active={active} />
    </Canvas>
  );
}
