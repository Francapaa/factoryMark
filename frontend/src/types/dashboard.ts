/** Tipos del /dashboard (contratos con backend + specs dashboard). */

import type { AnalyzeResult, Competitor } from "./analysis";

export type BusinessMine = {
  id: string;
  name: string;
  business_type: string;
  sales_channel: "local" | "online" | "mixto";
  zone: string;
  anchor_place_id: string;
  anchor_snapshot: {
    address: string;
    lat: number | null;
    lng: number | null;
    rating: number | null;
    photo_ref?: string;
    resolved_at?: string;
  };
  brand_kit?: Record<string, unknown> | null;
};

export type CompetitorWithScore = Competitor & {
  score?: number | null;
  website?: string;
};

export type AnalyzeResultWithScore = Omit<AnalyzeResult, "competitors"> & {
  competitors: CompetitorWithScore[];
};

export type IGStatus = "desconectado" | "conectado" | "expirado";

export type IGProfile = {
  username: string;
  followers_count?: number;
  media_count?: number;
};

export type PostState = "borrador" | "aprobado" | "programado" | "publicado" | "rechazado";

export type DashboardPost = {
  id: string;
  state: PostState;
  copy_text: string;
  hashtags: string[];
  media_url?: string | null;
  external_id?: string | null;
};

export function mapsUrl(placeId: string): string {
  return `https://www.google.com/maps/search/?api=1&query_place_id=${encodeURIComponent(placeId)}`;
}
