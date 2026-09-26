/** Shared contracts for the /api/analyze flow (mirror backend state.py). */

export type AnalysisStatus = "idle" | "loading" | "done" | "error";

export type SalesChannel = "local" | "online" | "mixto";

export type Opportunity = {
  title: string;
  evidence: string;
  confidence: string;
};

export type Draft = {
  copy_text: string;
  hashtags: string[];
  status: string;
};

export type Competitor = {
  place_id: string;
  name: string;
  rating: number | null;
  user_ratings_total: number;
  address: string;
  cached: boolean;
  source?: string;
  distance_m?: number | null;
};

export type AnalyzeResult = {
  competitors: Competitor[];
  opportunities: Opportunity[];
  draft_post: Draft | null;
  meta: Record<string, unknown>;
};

export type AnalyzeFormState = {
  businessName: string;
  businessType: string;
  zone: string;
  salesChannel: SalesChannel;
  status: AnalysisStatus;
  error: string;
  result: AnalyzeResult | null;
};

export type AnalyzeFormAction =
  | {
      type: "setField";
      field: "businessName" | "businessType" | "zone" | "salesChannel";
      value: string;
    }
  | { type: "submit" }
  | { type: "success"; result: AnalyzeResult }
  | { type: "failure"; error: string };

export const initialAnalyzeFormState: AnalyzeFormState = {
  businessName: "",
  businessType: "café de especialidad",
  zone: "Palermo Soho, Buenos Aires",
  salesChannel: "local",
  status: "idle",
  error: "",
  result: null,
};

export function analyzeFormReducer(
  state: AnalyzeFormState,
  action: AnalyzeFormAction,
): AnalyzeFormState {
  switch (action.type) {
    case "setField":
      return { ...state, [action.field]: action.value };
    case "submit":
      return { ...state, status: "loading", error: "" };
    case "success":
      return { ...state, status: "done", result: action.result };
    case "failure":
      return { ...state, status: "error", error: action.error };
  }
}
