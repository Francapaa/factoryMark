"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Flame, MapPin, ShieldCheck, Star } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import GoogleSignInButton from "@/components/GoogleSignInButton";

const ease = [0.22, 1, 0.36, 1] as const;

function Rise({
  delay = 0,
  children,
  className,
}: {
  delay?: number;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay, ease }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function LoginCard({
  configured,
  authError = false,
}: {
  configured: boolean;
  authError?: boolean;
}) {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-[#0A0A0B] font-sans">
      {/* Fondo landing: glows + grid */}
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute -top-40 left-1/2 h-[560px] w-[900px] -translate-x-1/2 rounded-full bg-[#FF5C00]/20 blur-[140px] animate-pulse-glow" />
        <div className="absolute top-[38%] -left-40 h-[480px] w-[480px] rounded-full bg-[#FF5C00]/12 blur-[120px]" />
        <div className="absolute -right-40 bottom-[-120px] h-[520px] w-[520px] rounded-full bg-[#FFB25C]/14 blur-[130px]" />
        <div className="absolute inset-0 bg-grid-orange opacity-60" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#0A0A0B] to-transparent" />
      </div>

      {/* Mini navbar */}
      <Rise className="relative z-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#FF5C00] shadow-[0_0_24px_rgba(255,92,0,0.55)]">
              <Flame className="h-5 w-5 text-[#0A0A0B]" strokeWidth={2.5} />
            </span>
            <span className="font-display text-lg font-bold tracking-tight text-white">
              Factory<span className="text-[#FF5C00]">Mark</span>
            </span>
          </Link>
          <Link
            href="/"
            className="font-display flex items-center gap-2 text-sm font-medium text-zinc-400 transition-colors hover:text-[#FFB25C]"
          >
            <ArrowLeft className="h-4 w-4" /> Volver
          </Link>
        </div>
      </Rise>

      {/* Contenido */}
      <main className="relative z-10 mx-auto grid w-full max-w-6xl flex-1 items-center gap-10 px-4 pb-16 pt-8 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:pt-12">
        {/* Copy estilo Hero */}
        <div>
          <Rise delay={0.05}>
            <Badge variant="ember">
              <MapPin className="h-3 w-3" /> Para negocios de barrio
            </Badge>
          </Rise>
          <Rise delay={0.12}>
            <h1 className="font-display mt-6 text-5xl font-bold leading-[0.95] tracking-tight text-white sm:text-6xl">
              Tu competencia habla.
              <br />
              <span className="bg-gradient-to-r from-[#FF5C00] via-[#FF8A3D] to-[#FFD9A3] bg-clip-text text-transparent text-glow-orange">
                Entrá y escuchala.
              </span>
            </h1>
          </Rise>
          <Rise delay={0.2}>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-400">
              Ingresá con tu cuenta de Google para analizar tu zona y generar tu marketing.{" "}
              <span className="font-semibold text-[#FFB25C]">
                Si es tu primera vez, la cuenta se crea sola
              </span>
              : no hay formularios ni contraseñas.
            </p>
          </Rise>
          <Rise delay={0.28}>
            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-zinc-500">
              <span className="flex items-center gap-1.5">
                <Star className="h-4 w-4 fill-[#FF5C00] text-[#FF5C00]" /> 4.6★ en negocios piloto
              </span>
              <span>· 400+ opiniones por zona</span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-400" /> Nada se publica sin tu OK
              </span>
            </div>
          </Rise>

          {/* Mini card flotante, eco del Hero */}
          <Rise delay={0.36} className="mt-8 hidden lg:block">
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="glass-dark inline-block rounded-2xl p-3.5 text-xs"
            >
              <p className="font-display font-semibold uppercase tracking-widest text-[#FFB25C]">
                Hueco detectado
              </p>
              <p className="mt-1 max-w-[260px] font-medium text-white">
                “0/40 opiniones hablan de merienda de tarde”
              </p>
              <p className="mt-1 text-emerald-400">Confianza: alta</p>
            </motion.div>
          </Rise>
        </div>

        {/* Card de login */}
        <Rise delay={0.18}>
          <motion.section
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.18, ease }}
            className="glass-dark noise relative rounded-[2rem] p-8 shadow-[0_8px_60px_rgba(0,0,0,0.5)] sm:p-10"
          >
            <div className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-[#FF5C00]/60 to-transparent" aria-hidden />
            <p className="font-display text-xs font-semibold uppercase tracking-[0.3em] text-[#FFB25C]">
              FactoryMark · Ingreso
            </p>
            <h2 className="font-display mt-3 text-3xl font-bold tracking-tight text-white">
              Tu espía legal de la competencia
            </h2>
            <p className="mt-3 text-[15px] leading-relaxed text-zinc-400">
              Un solo botón, sin contraseñas. Usamos tu nombre y email de Google solo para
              identificar tu cuenta.
            </p>

            <div className="mt-7">
              {!configured && !authError ? (
                <div className="flex flex-col gap-3">
                  <div className="rounded-2xl border border-[#FF5C00]/25 bg-[#FF5C00]/5 p-4 text-sm leading-relaxed text-zinc-300">
                    El login con Google aún no está configurado en este entorno (faltan{" "}
                    <code className="text-[#FFB25C]">NEON_AUTH_BASE_URL</code> y{" "}
                    <code className="text-[#FFB25C]">NEON_AUTH_COOKIE_SECRET</code>). Mientras
                    tanto podés explorar la landing y la demo.
                  </div>
                  <Link href="/#demo">
                    <Button variant="primary" size="lg" className="w-full">
                      Ver la demo
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {authError && (
                    <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm leading-relaxed text-amber-200">
                      Las variables están cargadas pero no pudimos contactar a Neon Auth al
                      verificar tu sesión (ver consola del server:{" "}
                      <code>[login] getSession failed</code>). Podés intentar ingresar igual.
                    </div>
                  )}
                  <GoogleSignInButton />
                </div>
              )}
            </div>

            <div className="mt-6 flex items-center justify-center gap-2 border-t border-white/10 pt-5 text-xs text-zinc-500">
              <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-400" />
              Legal · Human-in-the-loop · Solo pedimos nombre y email
            </div>
          </motion.section>
        </Rise>
      </main>
    </div>
  );
}
