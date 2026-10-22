"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Loader2, RefreshCw, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { AnalysisInfo } from "@/types/analysis";
import type { CompetitorsState, CompetitorWithScore } from "@/types/dashboard";
import { mapsUrl } from "@/types/dashboard";
import { EmptyState, ErrorState } from "./SectionCard";

const STALE_AFTER_MS = 7 * 24 * 60 * 60 * 1000;

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Math.max(0, Date.now() - then);
  const minutes = Math.round(diff / 60_000);
  if (minutes < 1) return "recién";
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  return `hace ${Math.round(hours / 24)} d`;
}

function NewBadge() {
  return (
    <span className="rounded-full bg-[#FF5C00]/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#FFB25C]">
      Nuevo
    </span>
  );
}

function AnalysisMeta({ analysis }: { analysis: AnalysisInfo }) {
  const [label, setLabel] = useState("");
  const [stale, setStale] = useState(false);

  useEffect(() => {
    function update() {
      setLabel(relativeTime(analysis.analyzed_at));
      const then = new Date(analysis.analyzed_at).getTime();
      setStale(!Number.isNaN(then) && Date.now() - then > STALE_AFTER_MS);
    }
    update();
    const timer = window.setInterval(update, 60_000);
    return () => window.clearInterval(timer);
  }, [analysis.analyzed_at]);

  return (
    <p className="mt-1 text-[11px] text-zinc-500">
      {label ? `Actualizado ${label}` : "Actualizado"}
      {analysis.new_competitors > 0 &&
        ` · ${analysis.new_competitors} ${
          analysis.new_competitors === 1 ? "nuevo" : "nuevos"
        }`}
      {stale && (
        <span className="text-amber-300"> · Datos de hace más de 7 días</span>
      )}
    </p>
  );
}

function distanceLabel(c: CompetitorWithScore): string {
  if (c.distance_m != null) return `${Math.round(c.distance_m)} m`;
  if (c.source === "web") return "web";
  return "—";
}

export function CompetitorsSection({
  state,
  analysis,
  analysisLoading,
  refreshing,
  refreshError,
  onAnalyze,
  onRefresh,
  onRetry,
}: {
  state: CompetitorsState;
  analysis: AnalysisInfo | null;
  analysisLoading: boolean;
  refreshing: boolean;
  refreshError: string;
  onAnalyze: () => void;
  onRefresh: () => void;
  onRetry: () => void;
}) {
  const searching = state.status === "loading";
  const hasData = state.status === "done";
  const busy = searching || analysisLoading || refreshing;

  const action = (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant="primary"
        size="md"
        onClick={hasData ? onRefresh : onAnalyze}
        disabled={busy}
      >
        {refreshing ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" /> Actualizando…
          </>
        ) : hasData ? (
          <>
            Refrescar análisis <RefreshCw className="h-4 w-4" />
          </>
        ) : (
          <>
            Generar análisis <ArrowRight className="h-4 w-4" />
          </>
        )}
      </Button>
      {hasData && (
        <p className="text-[11px] text-zinc-500">
          {refreshing
            ? "Mientras tanto seguís viendo la última foto."
            : "Vuelve a consultar las fuentes en vivo."}
        </p>
      )}
    </div>
  );

  if (state.status === "idle") {
    return (
      <EmptyState
        text="Todavía no hay un análisis guardado. Generá el primero para ver quién compite con vos en Maps."
        action={action}
      />
    );
  }

  if (state.status === "loading") {
    return (
      <div className="rounded-2xl border border-[#FF5C00]/25 bg-black/50 p-5">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-[#FF5C00]" />
          <p className="font-display font-semibold text-white">
            {analysisLoading ? "Cargando tu análisis guardado…" : "Buscando locales de tu cuadra…"}
          </p>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
          <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-[#FF5C00] to-[#FFD9A3]" />
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          {analysisLoading
            ? "Leyendo la última foto de tu zona, sin recalcular."
            : "Resolviendo tu negocio en Maps y midiendo distancias."}
        </p>
      </div>
    );
  }

  if (state.status === "error") {
    return <ErrorState text={state.message} onRetry={onRetry} />;
  }

  if (state.competitors.length === 0) {
    return (
      <EmptyState
        text="No encontramos competidores en tu zona con ese radio. Probá refrescar o ampliar la zona."
        action={action}
      />
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-black/50 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-display flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
            <TrendingUp className="h-3.5 w-3.5" /> {state.competitors.length}{" "}
            {state.competitors.length === 1 ? "competidor detectado" : "competidores detectados"}
          </p>
          {analysis && <AnalysisMeta analysis={analysis} />}
        </div>
        {action}
      </div>

      {refreshError && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-2.5 text-sm text-amber-200">
          <span>No pudimos actualizar: {refreshError}</span>
          <button
            type="button"
            onClick={onRefresh}
            className="font-display text-xs font-semibold text-amber-300 underline-offset-2 hover:underline"
          >
            Reintentar
          </button>
        </div>
      )}

      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-zinc-500">
              <th className="py-2 pr-4 font-medium">Nombre</th>
              <th className="py-2 pr-4 font-medium">Rating</th>
              <th className="py-2 pr-4 font-medium">Reviews</th>
              <th className="py-2 pr-4 font-medium">Distancia</th>
              <th className="py-2 pr-4 font-medium">Origen</th>
              <th className="py-2 font-medium">Mapa</th>
            </tr>
          </thead>
          <tbody>
            {state.competitors.map((c) => (
              <tr key={c.place_id} className="border-t border-white/10">
                <td className="py-2 pr-4 font-medium text-zinc-100">
                  <span className="flex flex-wrap items-center gap-2">
                    {c.name}
                    {c.is_new && <NewBadge />}
                  </span>
                </td>
                <td className="py-2 pr-4 text-zinc-200">{c.rating ?? "—"}</td>
                <td className="py-2 pr-4 text-zinc-200">{c.user_ratings_total}</td>
                <td className="py-2 pr-4 text-zinc-200">{distanceLabel(c)}</td>
                <td className="py-2 pr-4 text-zinc-400">{c.source ?? "maps"}</td>
                <td className="py-2">
                  {c.place_id.startsWith("web:") ? (
                    <span className="text-zinc-500">—</span>
                  ) : (
                    <a
                      href={mapsUrl(c.place_id)}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[#FFB25C] transition-colors hover:text-[#FFD9A3]"
                    >
                      Ver mapa
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
