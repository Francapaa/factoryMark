"use client";

import { MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { BusinessMine } from "@/types/dashboard";
import { EmptyState } from "./SectionCard";

export function BusinessSummary({
  business,
  loading,
}: {
  business: BusinessMine | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-2xl border border-white/10 bg-black/50 p-5">
        <div className="h-5 w-48 rounded bg-white/10" />
        <div className="mt-2 h-4 w-72 rounded bg-white/5" />
      </div>
    );
  }

  if (!business) {
    return (
      <EmptyState
        text="Todavía no guardaste tu negocio. Completá el onboarding para desbloquear el análisis de tu zona."
        action={
          <a
            href="/onboarding"
            className="font-display inline-flex h-11 items-center rounded-full bg-[#FF5C00] px-6 text-[15px] font-semibold text-[#0A0A0B] shadow-[0_0_32px_rgba(255,92,0,0.45)] transition-all hover:-translate-y-0.5 hover:bg-[#FF8A3D]"
          >
            Completar onboarding
          </a>
        }
      />
    );
  }

  const snap = business.anchor_snapshot;
  return (
    <div className="rounded-2xl border border-white/10 bg-black/50 p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="solid">{business.name}</Badge>
        <span className="text-sm text-zinc-400">
          {business.business_type} · {business.zone}
        </span>
      </div>
      <p className="mt-3 flex items-start gap-2 text-sm text-zinc-300">
        <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-[#FF5C00]" />
        {snap.address || business.zone}
        {snap.rating != null && <span className="text-[#FFB25C]"> · ★ {snap.rating}</span>}
      </p>
    </div>
  );
}
