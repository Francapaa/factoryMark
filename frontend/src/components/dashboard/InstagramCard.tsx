"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AuthRequiredError, apiFetch } from "@/lib/api";
import type { IGProfile, IGStatus } from "@/types/dashboard";
import { ErrorState } from "./SectionCard";

/** Glifo estilo Instagram en SVG propio (lucide deprecó los brand icons). */
function InstagramGlyph({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
    </svg>
  );
}

export type IGState =
  | { status: "loading" }
  | { status: "desconectado" }
  | { status: "conectado"; profile: IGProfile }
  | { status: "expirado"; username?: string }
  | { status: "error"; message: string };

export function InstagramCard({
  state,
  onChange,
  onAuthError,
}: {
  state: IGState;
  onChange: (s: IGState) => void;
  onAuthError: () => void;
}) {
  const [busy, setBusy] = useState(false);

  async function connect() {
    setBusy(true);
    try {
      const res = await apiFetch("/api/instagram/auth-url");
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const body = (await res.json()) as { url: string };
      window.location.href = body.url;
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        onAuthError();
        return;
      }
      onChange({
        status: "error",
        message: e instanceof Error ? e.message : "No pudimos iniciar la conexión",
      });
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    try {
      await apiFetch("/api/instagram/disconnect", { method: "DELETE" });
      onChange({ status: "desconectado" });
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        onAuthError();
        return;
      }
      onChange({
        status: "error",
        message: e instanceof Error ? e.message : "No pudimos desconectar",
      });
    } finally {
      setBusy(false);
    }
  }

  const badgeVariant =
    state.status === "conectado"
      ? ("solid" as const)
      : state.status === "expirado" || state.status === "error"
        ? ("ember" as const)
        : ("ghost" as const);
  const badgeLabel: Record<IGState["status"], string> = {
    loading: "Cargando…",
    desconectado: "Desconectado",
    conectado: "Conectado",
    expirado: "Requiere reconexión",
    error: "Error",
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-black/50 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-display flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
          <InstagramGlyph className="h-3.5 w-3.5" /> Instagram
        </p>
        <Badge variant={badgeVariant}>{badgeLabel[state.status]}</Badge>
      </div>

      {state.status === "loading" && (
        <p className="mt-3 flex items-center gap-2 text-sm text-zinc-400">
          <Loader2 className="h-4 w-4 animate-spin text-[#FF5C00]" /> Verificando conexión…
        </p>
      )}

      {state.status === "desconectado" && (
        <>
          <p className="mt-3 text-sm leading-relaxed text-zinc-300">
            Conectá tu Instagram profesional para gestionar tus publicaciones desde acá. Sin
            página de Facebook, con tu cuenta nomás.
          </p>
          <div className="mt-4">
            <Button variant="primary" size="md" onClick={connect} disabled={busy}>
              {busy ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Conectando…
                </>
              ) : (
                <>
                  <InstagramGlyph className="h-4 w-4" /> Conectá tu Instagram
                </>
              )}
            </Button>
          </div>
          <p className="mt-3 text-xs text-zinc-600">
            Si tu cuenta no es profesional, te guiamos para cambiarla con un toque.
          </p>
        </>
      )}

      {state.status === "conectado" && (
        <>
          <p className="mt-3 text-sm text-zinc-200">
            <span className="font-semibold text-white">@{state.profile.username}</span>
            {state.profile.followers_count != null && (
              <span className="text-zinc-400">
                {" "}
                · {state.profile.followers_count} seguidores
              </span>
            )}
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            La publicación automática llega tras la aprobación de Meta. Por ahora: copiá y
            exportá tus borradores.
          </p>
          <div className="mt-4">
            <Button variant="ghost" size="sm" onClick={disconnect} disabled={busy}>
              Desconectar
            </Button>
          </div>
        </>
      )}

      {state.status === "expirado" && (
        <>
          <p className="mt-3 text-sm text-zinc-300">
            Tu conexión venció{state.username ? ` (@${state.username})` : ""}. Reconectá para
            seguir gestionando tus publicaciones.
          </p>
          <div className="mt-4">
            <Button variant="primary" size="md" onClick={connect} disabled={busy}>
              Reconectar Instagram
            </Button>
          </div>
        </>
      )}

      {state.status === "error" && (
        <div className="mt-3">
          <ErrorState
            text={state.message}
            onRetry={() => onChange({ status: "desconectado" })}
          />
        </div>
      )}
    </div>
  );
}

export function igStatusOf(api: string): IGStatus {
  if (api === "conectado") return "conectado";
  if (api === "expirado") return "expirado";
  return "desconectado";
}
