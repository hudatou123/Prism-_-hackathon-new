import type { ConfidenceBand, FacetStatus } from "@/lib/types";

const labels: Record<FacetStatus | ConfidenceBand, string> = {
  pending: "Pending",
  confirmed: "Confirmed",
  mostly_confirmed: "Mostly confirmed",
  disputed: "Disputed",
  refuted: "Refuted",
  unclear: "Insufficient data",
  high: "High",
  moderate: "Moderate",
  low: "Low",
  contested: "Contested",
};

export function StatusChip({ value }: { value: FacetStatus | ConfidenceBand }) {
  return <span className="status-chip mono" data-status={value}>{labels[value]}</span>;
}
