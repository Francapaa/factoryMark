"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { authClient } from "@/lib/auth/client";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M23.5 12.3c0-.9-.1-1.5-.3-2.3H12v4.5h6.5c0 1.1-.7 2.7-2.1 3.8l-.1.1 3 2.4.2.1c1.9-1.8 3-4.4 3-8.6z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.2 0 5.9-1.1 7.9-2.9l-3.8-2.9c-1 .7-2.4 1.2-4.1 1.2-3.1 0-5.8-2.1-6.8-5l-.1.1-3.1 2.4-.1.1C3.9 21.3 7.7 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.2 14.4c-.2-.7-.4-1.5-.4-2.4s.1-1.7.4-2.4l-.1-.1-3.1-2.4-.1.1C.7 9.2 0 10.5 0 12s.7 2.8 1.9 4.1l3.3-1.7z"
      />
      <path
        fill="#EA4335"
        d="M12 4.6c1.8 0 3 .8 3.7 1.4l3.3-3.2C17.9 1.1 15.2 0 12 0 7.7 0 3.9 2.7 1.9 6.6l3.3 2.9c1-2.9 3.7-4.9 6.8-4.9z"
      />
    </svg>
  );
}

export default function GoogleSignInButton({ disabled = false }: { disabled?: boolean }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setLoading(true);
    setError(null);
    try {
      // URLs absolutas: el servicio managed redirige a callbackURL (existentes)
      // y a newUserCallbackURL (primer ingreso). Relativas defaultean a `/`
      // dejando el verifier colgado.
      // Existente → /dashboard (si nunca terminó onboarding, el BusinessGate
      // lo devuelve a /onboarding). Primer ingreso → /onboarding.
      const origin = window.location.origin;
      const res = await authClient.signIn.social({
        provider: "google",
        callbackURL: `${origin}/dashboard`,
        newUserCallbackURL: `${origin}/onboarding`,
      });
      if (res?.error) {
        setError("No se pudo iniciar sesión con Google. Probá de nuevo.");
        setLoading(false);
      }
      // Éxito: el SDK redirige solo (OAuth). Si estás registrado o no,
      // Google es el mismo botón: la cuenta se crea en el primer ingreso.
    } catch {
      setError("No se pudo iniciar sesión con Google. Probá de nuevo.");
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <motion.button
        type="button"
        onClick={onClick}
        disabled={disabled || loading}
        whileHover={{ y: -2 }}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.2 }}
        className="font-display flex w-full items-center justify-center gap-3 rounded-full bg-[#FFF7ED] px-5 py-4 text-base font-semibold text-[#0A0A0B] shadow-[0_0_32px_rgba(255,92,0,0.35)] transition-colors hover:bg-white hover:shadow-[0_0_48px_rgba(255,92,0,0.55)] disabled:opacity-50"
      >
        <GoogleIcon />
        {loading ? "Conectando con Google…" : "Continuar con Google"}
      </motion.button>
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
