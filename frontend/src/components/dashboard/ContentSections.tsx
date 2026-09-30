"use client";

import { FileCheck } from "lucide-react";
import type { Opportunity } from "@/types/analysis";
import type { DashboardPost } from "@/types/dashboard";
import { EmptyState } from "./SectionCard";

export function OpportunitiesSection({
  opportunities,
  searched,
}: {
  opportunities: Opportunity[];
  searched: boolean;
}) {
  if (!searched || opportunities.length === 0) {
    return (
      <EmptyState
        text={
          searched
            ? "El análisis no detectó huecos claros esta vez. Probá con otra zona o radio."
            : "Las oportunidades aparecen después de analizar tu zona: huecos concretos con su evidencia."
        }
      />
    );
  }
  return (
    <div className="rounded-2xl border border-[#FF5C00]/25 bg-[#FF5C00]/[0.06] p-5">
      <p className="font-display text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
        Oportunidades
      </p>
      <ul className="mt-3 flex flex-col gap-2.5">
        {opportunities.map((o) => (
          <li key={o.title} className="rounded-xl bg-black/50 p-3 text-sm">
            <p className="font-medium text-white">{o.title}</p>
            <p className="mt-1 text-xs text-zinc-500">
              {o.evidence} · confianza {o.confidence}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function PublicationsSection({
  draft,
  opportunityTitle,
  searched,
}: {
  draft: DashboardPost | null;
  opportunityTitle?: string;
  searched: boolean;
}) {
  if (!draft) {
    return (
      <EmptyState
        text={
          searched
            ? "Este análisis no generó borrador. Reintentá o ajustá tu negocio."
            : "Acá vas a ver tus borradores y publicaciones, con copiar y exportar. Nada se publica sin tu OK."
        }
      />
    );
  }
  return (
    <div className="rounded-2xl border border-white/10 bg-black/50 p-5">
      <p className="font-display flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
        <FileCheck className="h-3.5 w-3.5" /> Borrador · {draft.state}
      </p>
      <p className="mt-3 text-[15px] leading-relaxed text-zinc-100">{draft.copy_text}</p>
      <p className="mt-1 text-sm text-zinc-500">{draft.hashtags.join(" ")}</p>
      {opportunityTitle && (
        <p className="mt-2 text-xs text-zinc-600">Basado en: {opportunityTitle}</p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() =>
            navigator.clipboard.writeText(
              `${draft.copy_text} ${draft.hashtags.join(" ")}`.trim()
            )
          }
          className="font-display inline-flex h-9 items-center rounded-full bg-[#FF5C00] px-4 text-sm font-semibold text-[#0A0A0B] transition-all hover:bg-[#FF8A3D]"
        >
          Copiar texto
        </button>
        <span className="inline-flex h-9 items-center rounded-full border border-white/15 px-4 text-sm text-zinc-400">
          Publicación automática próximamente
        </span>
      </div>
    </div>
  );
}

export function StudioEntry() {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/50 p-5 opacity-70">
      <p className="font-display text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
        Estudio de video · próximamente
      </p>
      <p className="mt-2 text-sm text-zinc-400">
        El estudio llega después: primero analizá tu zona y conectá tu Instagram.
      </p>
    </div>
  );
}
