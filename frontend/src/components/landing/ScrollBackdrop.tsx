"use client";

import { motion, useScroll, useTransform } from "framer-motion";

/**
 * Fondo global que cambia de color con el scroll:
 * negro → brasa → negro → ÁMBAR CLARO (casos de éxito) → negro cierre.
 */
export function ScrollBackdrop() {
  const { scrollYProgress } = useScroll();

  const background = useTransform(
    scrollYProgress,
    [0, 0.16, 0.34, 0.52, 0.64, 0.78, 0.9, 1],
    [
      "#0A0A0B", // hero
      "#170C05", // problema: brasa
      "#0A0A0B", // pipeline
      "#1A0E04", // demo: marrón quemado
      "#F59E0B", // casos: entra ámbar
      "#FDE9C8", // casos: ámbar claro pleno
      "#140B06", // testimonios: vuelta a brasa
      "#0A0A0B", // cierre negro
    ]
  );

  const glowOpacity = useTransform(scrollYProgress, [0, 0.5, 1], [0.7, 0.35, 0.7]);

  return (
    <>
      <motion.div className="fixed inset-0 -z-20" style={{ background }} aria-hidden />
      <motion.div
        className="fixed inset-0 -z-10 pointer-events-none"
        style={{ opacity: glowOpacity }}
        aria-hidden
      >
        <div className="absolute -top-40 left-1/2 h-[560px] w-[900px] -translate-x-1/2 rounded-full bg-[#FF5C00]/20 blur-[140px]" />
        <div className="absolute top-[38%] -left-40 h-[480px] w-[480px] rounded-full bg-[#FF5C00]/12 blur-[120px]" />
        <div className="absolute top-[62%] -right-40 h-[520px] w-[520px] rounded-full bg-[#FFB25C]/14 blur-[130px]" />
        <div className="absolute inset-0 bg-grid-orange opacity-60" />
      </motion.div>
    </>
  );
}
