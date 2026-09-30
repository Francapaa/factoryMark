"use client";

import { ArrowRight, Loader2, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { CompetitorsState, CompetitorWithScore } from "@/types/dashboard";
import { mapsUrl } from "@/types/dashboard";
import { EmptyState, ErrorState } from "./SectionCard";

function distanceLabel(c: CompetitorWithScore): string {
  if (c.distance_m != null) return `${Math.round(c.distance_m)} m`;
  if (c.source === "web") return "web";
  return "—";
}

export function CompetitorsSection({
  state,
  onSearch,
}: {
  state: CompetitorsState;
  onSearch: () => void;
}) {
  const searching = state.status === "loading";

  const action = (
    <Button variant="primary" size="md" onClick={onSearch} disabled={searching}>
      {searching ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" /> Analizando…
        </>
      ) : (
        <>
          Buscar competidores en mi zona <ArrowRight className="h-4 w-4" />
        </>
      )}
    </Button>
  );

  if (state.status === "idle") {
    return (
      <EmptyState
        text="Todavía no analizaste tu zona. Buscá los locales que compiten con vos en Maps."
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
            Buscando locales de tu cuadra…
          </p>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
          <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-[#FF5C00] to-[#FFD9A3]" />
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Resolviendo tu negocio en Maps y midiendo distancias.
        </p>
      </div>
    );
  }

  if (state.status === "error") {
    return <ErrorState text={state.message} onRetry={onSearch} />;
  }

  if (state.competitors.length === 0) {
    return (
      <EmptyState
        text="No encontramos competidores en tu zona con ese radio. Probá ampliar la zona o reintentá el análisis."
        action={action}
      />
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-black/50 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-display flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
          <TrendingUp className="h-3.5 w-3.5" /> {state.competitors.length} competidores
          detectados
        </p>
        {action}
      </div>
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
                <td className="py-2 pr-4 font-medium text-zinc-100">{c.name}</td>
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
