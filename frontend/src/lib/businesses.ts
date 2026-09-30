"use client";

import { AuthRequiredError, apiFetch } from "./api";
import type { SalesChannel } from "@/types/analysis";

export type ResolvedBusiness = {
  place_id: string;
  name: string;
  address: string;
  rating: number | null;
  hours_summary: string[];
  photo_ref: string | null;
  latitude: number | null;
  longitude: number | null;
  maps_url: string;
  cached?: boolean;
};

export type MyBusiness = {
  id: string;
  owner_id: string;
  name: string;
  business_type: string;
  sales_channel: SalesChannel;
  zone: string;
  anchor_place_id: string;
  anchor_snapshot: Record<string, unknown>;
  brand_kit: Record<string, unknown> | null;
};

export type SaveBusinessPayload = {
  name: string;
  business_type: string;
  sales_channel: SalesChannel;
  zone: string;
  anchor_place_id: string;
  anchor_snapshot: Record<string, unknown>;
};

/** Extrae el mensaje legible de un error del backend (string o {code,message}). */
export function apiErrorMessage(body: unknown, fallback: string): string {
  if (typeof body === "string") return body;
  if (body !== null && typeof body === "object") {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (detail !== null && typeof detail === "object") {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === "string") return message;
    }
    // Errores de validación de FastAPI: [{loc, msg}]
    if (Array.isArray(detail)) {
      const first = detail[0] as { msg?: unknown } | undefined;
      if (first && typeof first.msg === "string") return first.msg;
    }
  }
  return fallback;
}

/** Extrae el código máquina del error (ej: onboarding_incompleto, sin_negocio). */
export function apiErrorCode(body: unknown): string | null {
  if (body !== null && typeof body === "object") {
    const detail = (body as { detail?: unknown }).detail;
    if (detail !== null && typeof detail === "object" && !Array.isArray(detail)) {
      const code = (detail as { code?: unknown }).code;
      if (typeof code === "string") return code;
    }
  }
  return null;
}

export async function resolveBusiness(name: string, zone: string): Promise<ResolvedBusiness> {
  const res = await apiFetch("/api/businesses/resolve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, zone }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(apiErrorMessage(body, `Error ${res.status}`));
  }
  return (await res.json()) as ResolvedBusiness;
}

export async function saveBusiness(payload: SaveBusinessPayload): Promise<MyBusiness> {
  const res = await apiFetch("/api/businesses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(apiErrorMessage(body, `Error ${res.status}`));
  }
  return (await res.json()) as MyBusiness;
}

/** Mi negocio guardado, o null si no completé onboarding (404 sin_negocio). */
export async function getMyBusiness(): Promise<MyBusiness | null> {
  const res = await apiFetch("/api/businesses/mine");
  if (res.status === 404) return null;
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(apiErrorMessage(body, `Error ${res.status}`));
  }
  return (await res.json()) as MyBusiness;
}

/** Foto del local como object URL (vía proxy con auth; la key nunca llega al browser). */
export async function getPhotoObjectUrl(photoRef: string): Promise<string> {
  const res = await apiFetch(`/api/businesses/photo?photo_ref=${encodeURIComponent(photoRef)}`);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export { AuthRequiredError };
