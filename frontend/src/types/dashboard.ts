/** Tipos del /dashboard (contratos con backend + specs dashboard).
 *
 * Regla: todos los types del dashboard viven acá. Ningún componente
 * define sus propios types de estado — los importa de este módulo.
 */

import type { AnalysisInfo, AnalyzeResult, Competitor, Opportunity } from "./analysis";
import type { MyBusiness } from "@/lib/businesses";

/** Snapshot del ancla con tipos estrechos (el contrato trae Record<string, unknown>). */
export type AnchorSnapshotView = {
  address: string;
  rating: number | null;
};

export function snapshotOf(business: MyBusiness): AnchorSnapshotView {
  const snap = business.anchor_snapshot ?? {};
  const address = snap["address"];
  const rating = snap["rating"];
  return {
    address: typeof address === "string" ? address : "",
    rating: typeof rating === "number" ? rating : null,
  };
}

export type CompetitorWithScore = Competitor;

export type AnalyzeResultWithScore = Omit<AnalyzeResult, "competitors"> & {
  competitors: CompetitorWithScore[];
};

export type CompetitorsState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; competitors: CompetitorWithScore[] }
  | { status: "error"; message: string };

export type IGStatus = "desconectado" | "conectado" | "expirado";

export type IGProfile = {
  username: string;
  followers_count?: number;
  media_count?: number;
  can_publish?: boolean;
};

export type IGState =
  | { status: "loading" }
  | { status: "desconectado" }
  | { status: "conectado"; profile: IGProfile }
  | { status: "expirado"; username?: string }
  | { status: "error"; message: string };

export type PostState = "borrador" | "aprobado" | "programado" | "publicado" | "rechazado";
export type DashboardPost = {
  id: string;
  state: PostState;
  copy_text: string;
  hashtags: string[];
  media_url?: string | null;
  external_id?: string | null;
};

/** Programada de Instagram (contrato con GET/POST /api/instagram/scheduled). */
export type ScheduledPost = {
  id: string;
  estado: string;
  image_url: string;
  caption: string;
  copy_text: string;
  hashtags: string[];
  programada_para: string | null;
  container_id: string | null;
  external_id: string | null;
  error: string | null;
  created_at: string | null;
  published_at: string | null;
};

export type DashboardState = {
  business: MyBusiness | null;
  businessLoading: boolean;
  businessMissing: boolean;
  comp: CompetitorsState;
  opportunities: Opportunity[];
  draft: DashboardPost | null;
  searched: boolean;
  analysis: AnalysisInfo | null;
  analysisLoading: boolean;
  refreshing: boolean;
  refreshError: string;
  retry: "load" | "analyze";
  ig: IGState;
};

export type DashboardAction =
  | { type: "business/loading" }
  | { type: "business/loaded"; business: MyBusiness }
  | { type: "business/missing" }
  | { type: "business/error" }
  | { type: "analysis/loading" }
  | { type: "analysis/empty" }
  | { type: "analysis/analyzing" }
  | { type: "analysis/refreshing" }
  | {
      type: "analysis/success";
      analysis: AnalysisInfo | null;
      competitors: CompetitorWithScore[];
      opportunities: Opportunity[];
      draft: DashboardPost | null;
    }
  | { type: "analysis/load-error"; message: string; retry: "load" | "analyze" }
  | { type: "analysis/refresh-error"; message: string }
  | { type: "ig/set"; state: IGState };

export const initialDashboardState: DashboardState = {
  business: null,
  businessLoading: true,
  businessMissing: false,
  comp: { status: "loading" },
  opportunities: [],
  draft: null,
  searched: false,
  analysis: null,
  analysisLoading: true,
  refreshing: false,
  refreshError: "",
  retry: "load",
  ig: { status: "loading" },
};

export function dashboardReducer(
  state: DashboardState,
  action: DashboardAction
): DashboardState {
  switch (action.type) {
    case "business/loading":
      return { ...state, businessLoading: true };
    case "business/loaded":
      return {
        ...state,
        business: action.business,
        businessLoading: false,
        businessMissing: false,
      };
    case "business/missing":
      return {
        ...state,
        business: null,
        businessLoading: false,
        businessMissing: true,
      };
    case "business/error":
      return {
        ...state,
        business: null,
        businessLoading: false,
        businessMissing: false,
      };
    case "analysis/loading":
      return {
        ...state,
        comp: { status: "loading" },
        analysisLoading: true,
        refreshing: false,
        refreshError: "",
        retry: "load",
      };
    case "analysis/empty":
      return {
        ...state,
        comp: { status: "idle" },
        opportunities: [],
        draft: null,
        searched: false,
        analysis: null,
        analysisLoading: false,
        refreshing: false,
        refreshError: "",
        retry: "load",
      };
    case "analysis/analyzing":
      return {
        ...state,
        comp: { status: "loading" },
        analysisLoading: false,
        refreshing: false,
        refreshError: "",
        retry: "analyze",
      };
    case "analysis/refreshing":
      return {
        ...state,
        refreshing: true,
        refreshError: "",
        retry: "analyze",
      };
    case "analysis/success":
      return {
        ...state,
        comp: { status: "done", competitors: action.competitors },
        opportunities: action.opportunities,
        draft: action.draft,
        searched: true,
        analysis: action.analysis,
        analysisLoading: false,
        refreshing: false,
        refreshError: "",
        retry: "load",
      };
    case "analysis/load-error":
      return {
        ...state,
        comp: { status: "error", message: action.message },
        analysisLoading: false,
        refreshing: false,
        retry: action.retry,
      };
    case "analysis/refresh-error":
      return {
        ...state,
        refreshing: false,
        refreshError: action.message,
      };
    case "ig/set":
      return { ...state, ig: action.state };
  }
}

export function mapsUrl(placeId: string): string {
  return `https://www.google.com/maps/search/?api=1&query_place_id=${encodeURIComponent(placeId)}`;
}
