/** Tipos del /dashboard (contratos con backend + specs dashboard).
 *
 * Regla: todos los types del dashboard viven acá. Ningún componente
 * define sus propios types de estado — los importa de este módulo.
 */

import type { AnalyzeResult, Competitor, Opportunity } from "./analysis";
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

export type CompetitorWithScore = Competitor & {
  score?: number | null;
  website?: string;
};

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

export type DashboardState = {
  business: MyBusiness | null;
  businessLoading: boolean;
  businessMissing: boolean;
  comp: CompetitorsState;
  opportunities: Opportunity[];
  draft: DashboardPost | null;
  searched: boolean;
  ig: IGState;
};

export type DashboardAction =
  | { type: "business/loading" }
  | { type: "business/loaded"; business: MyBusiness }
  | { type: "business/missing" }
  | { type: "business/error" }
  | { type: "comp/set"; state: CompetitorsState }
  | {
      type: "analysis/success";
      competitors: CompetitorWithScore[];
      opportunities: Opportunity[];
      draft: DashboardPost | null;
    }
  | { type: "ig/set"; state: IGState };

export const initialDashboardState: DashboardState = {
  business: null,
  businessLoading: true,
  businessMissing: false,
  comp: { status: "idle" },
  opportunities: [],
  draft: null,
  searched: false,
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
    case "comp/set":
      return { ...state, comp: action.state };
    case "analysis/success":
      return {
        ...state,
        comp: { status: "done", competitors: action.competitors },
        opportunities: action.opportunities,
        draft: action.draft,
        searched: true,
      };
    case "ig/set":
      return { ...state, ig: action.state };
  }
}

export function mapsUrl(placeId: string): string {
  return `https://www.google.com/maps/search/?api=1&query_place_id=${encodeURIComponent(placeId)}`;
}
