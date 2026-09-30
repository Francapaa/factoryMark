"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Flame } from "lucide-react";
import { AuthRequiredError, apiFetch } from "@/lib/api";
import type {
  AnalyzeResultWithScore,
  BusinessMine,
  DashboardPost,
  IGProfile,
} from "@/types/dashboard";
import { BusinessSummary } from "./BusinessSummary";
import { CompetitorsSection, type CompetitorsState } from "./CompetitorsSection";
import {
  OpportunitiesSection,
  PublicationsSection,
  StudioEntry,
} from "./ContentSections";
import { InstagramCard, type IGState } from "./InstagramCard";
import { SectionCard } from "./SectionCard";

export function DashboardClient() {
  const router = useRouter();
  const [business, setBusiness] = useState<BusinessMine | null>(null);
  const [businessLoading, setBusinessLoading] = useState(true);
  const [businessMissing, setBusinessMissing] = useState(false);

  const [compState, setCompState] = useState<CompetitorsState>({ status: "idle" });
  const [opportunities, setOpportunities] = useState<AnalyzeResultWithScore["opportunities"]>([]);
  const [draft, setDraft] = useState<DashboardPost | null>(null);
  const [searched, setSearched] = useState(false);

  const [ig, setIg] = useState<IGState>({ status: "loading" });

  const goLogin = useCallback(() => router.push("/login"), [router]);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      setBusinessLoading(true);
      try {
        const res = await apiFetch("/api/businesses/mine");
        if (cancelled) return;
        if (res.status === 404) {
          setBusiness(null);
          setBusinessMissing(true);
          return;
        }
        if (!res.ok) throw new Error(`Error ${res.status}`);
        setBusiness((await res.json()) as BusinessMine);
        setBusinessMissing(false);
      } catch (e) {
        if (cancelled) return;
        if (e instanceof AuthRequiredError) {
          router.push("/login");
          return;
        }
        setBusiness(null);
        setBusinessMissing(false);
      } finally {
        if (!cancelled) setBusinessLoading(false);
      }
    })();

    void (async () => {
      try {
        const res = await apiFetch("/api/instagram/status");
        if (cancelled) return;
        if (!res.ok) {
          setIg({ status: "desconectado" });
          return;
        }
        const body = (await res.json()) as {
          estado: string;
          username?: string;
          followers_count?: number;
          media_count?: number;
        };
        if (body.estado === "conectado" && body.username) {
          const profile: IGProfile = {
            username: body.username,
            followers_count: body.followers_count,
            media_count: body.media_count,
          };
          setIg({ status: "conectado", profile });
        } else if (body.estado === "expirado") {
          setIg({ status: "expirado", username: body.username });
        } else {
          setIg({ status: "desconectado" });
        }
      } catch (e) {
        if (cancelled) return;
        if (e instanceof AuthRequiredError) {
          router.push("/login");
          return;
        }
        setIg({ status: "desconectado" });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [router]);

  const search = useCallback(async () => {
    if (!business) return;
    setCompState({ status: "loading" });
    try {
      const res = await apiFetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: business.name,
          business_type: business.business_type,
          zone: business.zone,
          sales_channel: business.sales_channel,
        }),
      });
      if (res.status === 404) {
        setCompState({
          status: "error",
          message:
            "No encontramos tu negocio en Maps con esos datos. Verificá el nombre en el onboarding.",
        });
        return;
      }
      if (res.status === 409) {
        setCompState({
          status: "error",
          message: "Completá tu onboarding antes de analizar: tu negocio aún no está guardado.",
        });
        return;
      }
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
        const detail =
          typeof body?.detail === "string" ? body.detail : `Error ${res.status}`;
        throw new Error(detail);
      }
      const result = (await res.json()) as AnalyzeResultWithScore;
      const sorted = [...result.competitors].sort((a, b) => {
        if (a.score != null && b.score != null) return b.score - a.score;
        if (a.score != null) return -1;
        if (b.score != null) return 1;
        if (a.distance_m != null && b.distance_m != null) return a.distance_m - b.distance_m;
        return 0;
      });
      setCompState({ status: "done", competitors: sorted });
      setOpportunities(result.opportunities);
      setDraft(
        result.draft_post
          ? {
              id: "draft-actual",
              state: "borrador",
              copy_text: result.draft_post.copy_text,
              hashtags: result.draft_post.hashtags,
            }
          : null
      );
      setSearched(true);
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        router.push("/login");
        return;
      }
      setCompState({
        status: "error",
        message: e instanceof Error ? e.message : "Falló el análisis de tu zona",
      });
    }
  }, [business, router]);

  return (
    <div className="relative min-h-screen bg-[#0A0A0B]">
      <div className="bg-grid-orange pointer-events-none absolute inset-0 opacity-60" />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-72"
        style={{
          background:
            "radial-gradient(60% 100% at 50% 0%, rgba(255,92,0,0.14), transparent 70%)",
        }}
      />
      <div className="relative z-10 mx-auto flex max-w-6xl flex-col gap-5 px-4 py-8 sm:px-6">
        <header className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-[#0A0A0B]/40 px-4 py-2.5 backdrop-blur-lg">
          <span className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#FF5C00] shadow-[0_0_24px_rgba(255,92,0,0.55)]">
              <Flame className="h-5 w-5 text-[#0A0A0B]" strokeWidth={2.5} />
            </span>
            <span className="font-display text-lg font-bold tracking-tight text-white">
              Factory<span className="text-[#FF5C00]">Mark</span>
            </span>
          </span>
          <span className="font-display text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-500">
            Panel
          </span>
        </header>

        <div>
          <h1 className="font-display text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Tu cuadra,{" "}
            <span className="bg-gradient-to-r from-[#FF5C00] via-[#FF8A3D] to-[#FFD9A3] bg-clip-text text-transparent">
              en claro.
            </span>
          </h1>
          <p className="mt-2 max-w-2xl text-zinc-400">
            Competidores, oportunidades y publicaciones de tu negocio. Detectar → decidir →
            ejecutar. Nada se publica sin tu OK.
          </p>
        </div>

        <SectionCard
          badge="Tu negocio"
          title={business?.name ?? "Tu negocio"}
          hint="Guardado en el onboarding. Todo análisis usa estos datos."
        >
          <BusinessSummary business={business} loading={businessLoading} />
        </SectionCard>

        <SectionCard
          badge="Competencia"
          title="Quién compite con vos"
          hint="Búsqueda real en Maps por cercanía a tu local, con distancias y origen."
        >
          {businessMissing || (!businessLoading && !business) ? (
            <p className="rounded-2xl border border-white/10 bg-black/50 p-5 text-center text-sm text-zinc-400">
              Guardá tu negocio primero para buscar competidores en tu zona.
            </p>
          ) : (
            <CompetitorsSection state={compState} onSearch={search} />
          )}
        </SectionCard>

        <div className="grid gap-5 lg:grid-cols-2">
          <SectionCard
            badge="Oportunidades"
            title="Huecos detectados"
            hint="Lo que nadie cubre, con evidencia y confianza."
          >
            <OpportunitiesSection opportunities={opportunities} searched={searched} />
          </SectionCard>
          <SectionCard
            badge="Instagram"
            title="Tu canal"
            hint="Conectá tu cuenta profesional para gestionar todo desde acá."
          >
            <InstagramCard state={ig} onChange={setIg} onAuthError={goLogin} />
          </SectionCard>
        </div>

        <SectionCard
          badge="Publicaciones"
          title="Borradores y publicaciones"
          hint="Copiá y exportá tus textos. La publicación automática llega tras la aprobación de Meta."
        >
          <PublicationsSection
            draft={draft}
            opportunityTitle={opportunities[0]?.title}
            searched={searched}
          />
        </SectionCard>

        <SectionCard badge="Video" title="Estudio de video">
          <StudioEntry />
        </SectionCard>
      </div>
    </div>
  );
}
