"use client";

import { useCallback, useEffect, useState } from "react";
import { CalendarClock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AuthRequiredError } from "@/lib/api";
import {
  cancelScheduledPost,
  createScheduledPost,
  getScheduledPosts,
  publishScheduledNow,
  runDueScheduled,
} from "@/lib/instagram";
import type { ScheduledPost } from "@/types/dashboard";
import { ErrorState } from "./SectionCard";

const ESTADOS: Record<string, string> = {
  programado: "Programado",
  publicado: "Publicado",
  rechazado: "Cancelado",
  error: "Falló",
  borrador: "Borrador",
  aprobado: "Aprobado",
};

function isDueSoon(iso: string | null): boolean {
  if (!iso) return false;
  const when = new Date(iso).getTime();
  const now = Date.now();
  return when > now && when - now < 24 * 3600 * 1000;
}

function isOverdue(iso: string | null, estado: string): boolean {
  if (!iso || estado !== "programado") return false;
  return new Date(iso).getTime() <= Date.now();
}

function formatWhen(iso: string | null): string {
  if (!iso) return "sin fecha";
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ScheduledPosts({
  connected,
  onAuthError,
}: {
  connected: boolean;
  onAuthError: () => void;
}) {
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [caption, setCaption] = useState("");
  const [when, setWhen] = useState("");

  const refresh = useCallback(async () => {
    if (!connected) return;
    setLoading(true);
    setError(null);
    try {
      setPosts(await getScheduledPosts());
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        onAuthError();
        return;
      }
      setError(e instanceof Error ? e.message : "No pudimos listar programadas");
    } finally {
      setLoading(false);
    }
  }, [connected, onAuthError]);

  useEffect(() => {
    if (!connected) return;
    let cancelled = false;
    getScheduledPosts().then(
      (items) => {
        if (cancelled) return;
        setPosts(items);
        setLoaded(true);
      },
      (e: unknown) => {
        if (cancelled) return;
        if (e instanceof AuthRequiredError) {
          onAuthError();
          return;
        }
        setError(e instanceof Error ? e.message : "No pudimos listar programadas");
        setLoaded(true);
      }
    );
    return () => {
      cancelled = true;
    };
    // Solo al conectar: los reintentos manuales usan refresh() desde eventos.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connected]);

  if (!connected) {
    return (
      <p className="rounded-2xl border border-white/10 bg-black/50 p-5 text-center text-sm text-zinc-400">
        Conectá tu Instagram para programar publicaciones.
      </p>
    );
  }

  async function handleCreate() {
    if (!imageUrl.trim() || !when) {
      setError("Completá la imagen (URL pública) y la fecha.");
      return;
    }
    setCreating(true);
    setError(null);
    setMessage(null);
    try {
      const post = await createScheduledPost({
        image_url: imageUrl.trim(),
        caption: caption.trim(),
        programada_para: new Date(when).toISOString(),
      });
      setPosts((prev) => [post, ...prev]);
      setImageUrl("");
      setCaption("");
      setWhen("");
      setMessage(`Programada para el ${formatWhen(post.programada_para)}. Te avisamos acá cuando se publique.`);
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        onAuthError();
        return;
      }
      setError(e instanceof Error ? e.message : "No pudimos programar");
    } finally {
      setCreating(false);
    }
  }

  async function handleCancel(id: string) {
    setBusyId(id);
    setError(null);
    try {
      const updated = await cancelScheduledPost(id);
      setPosts((prev) => prev.map((p) => (p.id === id ? updated : p)));
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        onAuthError();
        return;
      }
      setError(e instanceof Error ? e.message : "No pudimos cancelar");
    } finally {
      setBusyId(null);
    }
  }

  async function handlePublishNow(id: string) {
    setBusyId(id);
    setError(null);
    setMessage(null);
    try {
      await publishScheduledNow(id);
      setMessage("Publicada en Instagram.");
      await refresh();
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        onAuthError();
        return;
      }
      setError(e instanceof Error ? e.message : "No pudimos publicar");
      await refresh();
    } finally {
      setBusyId(null);
    }
  }

  async function handleRunDue() {
    setBusyId("run-due");
    setError(null);
    setMessage(null);
    try {
      const result = await runDueScheduled();
      setMessage(
        result.revisados === 0
          ? "Nada vencido por ahora."
          : `Se publicaron ${result.publicados} de ${result.revisados} vencidas.` +
              (result.errores.length > 0 ? ` ${result.errores.length} fallaron: revisá el detalle.` : "")
      );
      await refresh();
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        onAuthError();
        return;
      }
      setError(e instanceof Error ? e.message : "No pudimos publicar vencidas");
    } finally {
      setBusyId(null);
    }
  }

  const overdue = posts.filter((p) => isOverdue(p.programada_para, p.estado));

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl border border-white/10 bg-black/50 p-5">
        <p className="font-display flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
          <CalendarClock className="h-3.5 w-3.5" /> Nueva programada
        </p>
        <div className="mt-3 flex flex-col gap-2.5">
          <input
            type="url"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="URL pública de la imagen (https://…)"
            className="h-10 rounded-xl border border-white/15 bg-black/60 px-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#FF5C00] focus:outline-none"
          />
          <textarea
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="Texto de la publicación (máx. 2200 caracteres)"
            maxLength={2200}
            rows={2}
            className="rounded-xl border border-white/15 bg-black/60 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#FF5C00] focus:outline-none"
          />
          <div className="flex flex-wrap items-center gap-2.5">
            <input
              type="datetime-local"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
              className="h-10 rounded-xl border border-white/15 bg-black/60 px-3 text-sm text-zinc-100 focus:border-[#FF5C00] focus:outline-none"
            />
            <Button variant="primary" size="md" onClick={handleCreate} disabled={creating}>
              {creating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Programando…
                </>
              ) : (
                "Programar"
              )}
            </Button>
          </div>
          <p className="text-xs text-zinc-600">
            Instagram no programa nativamente: guardamos tu post y lo publicamos a esa hora. La
            imagen debe estar en una URL pública (JPG).
          </p>
        </div>
      </div>

      {message && (
        <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-sm text-emerald-200">
          {message}
        </p>
      )}
      {error && <ErrorState text={error} onRetry={() => setError(null)} />}

      {overdue.length > 0 && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5">
          <p className="text-sm font-medium text-amber-200">
            Tenés {overdue.length} vencida{overdue.length > 1 ? "s" : ""} sin publicar.
          </p>
          <div className="mt-3">
            <Button
              variant="primary"
              size="sm"
              onClick={handleRunDue}
              disabled={busyId === "run-due"}
            >
              {busyId === "run-due" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Publicando…
                </>
              ) : (
                "Publicar vencidas ahora"
              )}
            </Button>
          </div>
        </div>
      )}

      {loading || (!loaded && !error) ? (
        <p className="flex items-center gap-2 text-sm text-zinc-400">
          <Loader2 className="h-4 w-4 animate-spin text-[#FF5C00]" /> Cargando programadas…
        </p>
      ) : posts.length === 0 ? (
        <p className="rounded-2xl border border-white/10 bg-black/50 p-5 text-center text-sm text-zinc-400">
          Todavía no programaste nada. La primera aparece acá con su recordatorio.
        </p>
      ) : (
        <ul className="flex flex-col gap-2.5">
          {posts.map((p) => (
            <li key={p.id} className="rounded-xl border border-white/10 bg-black/50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Badge variant={p.estado === "publicado" ? "solid" : p.estado === "error" ? "ember" : "ghost"}>
                  {ESTADOS[p.estado] ?? p.estado}
                </Badge>
                <span className="text-xs text-zinc-500">{formatWhen(p.programada_para)}</span>
              </div>
              {p.caption && <p className="mt-2 text-sm text-zinc-200">{p.caption}</p>}
              {p.estado === "programado" && isDueSoon(p.programada_para) && (
                <p className="mt-1 text-xs text-amber-300">
                  Se publica en menos de 24 h. Podés cancelarla o adelantarla.
                </p>
              )}
              {isOverdue(p.programada_para, p.estado) && (
                <p className="mt-1 text-xs text-amber-300">
                  Vencida: publicala ahora o usá “Publicar vencidas”.
                </p>
              )}
              {p.estado === "error" && p.error && (
                <p className="mt-1 text-xs text-red-300">{p.error}</p>
              )}
              {p.estado === "publicado" && p.external_id && (
                <p className="mt-1 text-xs text-zinc-600">ID {p.external_id}</p>
              )}
              {(p.estado === "programado" || p.estado === "error") && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handlePublishNow(p.id)}
                    disabled={busyId === p.id}
                  >
                    {busyId === p.id ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" /> Publicando…
                      </>
                    ) : p.estado === "error" ? (
                      "Reintentar ahora"
                    ) : (
                      "Adelantar y publicar"
                    )}
                  </Button>
                  {p.estado === "programado" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCancel(p.id)}
                      disabled={busyId === p.id}
                    >
                      Cancelar
                    </Button>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
