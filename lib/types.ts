export type FacetId = "fact" | "scale" | "stakeholders";

export type FacetStatus =
  | "pending"
  | "confirmed"
  | "mostly_confirmed"
  | "disputed"
  | "refuted"
  | "unclear";

export type ConfidenceBand = "high" | "moderate" | "low" | "contested";
export type EvidenceSide = "pro" | "con" | "named" | "grassroots";

export interface Evidence {
  id: string;
  side: EvidenceSide;
  claim: string;
  quote: string;
  url: string;
  source: string;
  publishedAt?: string;
  verified: boolean;
  score?: number;
  bias?: "left" | "center" | "right";
}

export type StreamEvent =
  | { type: "provisional"; claim: string; earlyRead: string; sourcesSoFar: number }
  | { type: "facet"; facet: FacetId; status: FacetStatus; summary: string;
      evidence: Evidence[]; conEmpty?: boolean; conSearched?: number;
      sourcesExamined: number; quotesVerified: number; quotesTotal: number }
  | { type: "counts"; sourcesExamined: number; quotesVerified: number; quotesTotal: number }
  | { type: "final"; verdict: string; qualifier?: string; band: ConfidenceBand;
      facetScores: Record<FacetId, number | null>;
      agreement: { agree: number; total: number } };

export type FacetEvent = Extract<StreamEvent, { type: "facet" }>;
export type FinalEvent = Extract<StreamEvent, { type: "final" }>;
export type ProvisionalEvent = Extract<StreamEvent, { type: "provisional" }>;
export type CountsEvent = Extract<StreamEvent, { type: "counts" }>;
