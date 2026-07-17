"use client";

import { AnimatePresence, motion } from "motion/react";
import type { FacetEvent, FacetId, FinalEvent } from "@/lib/types";

const facetOrder: FacetId[] = ["fact", "scale", "stakeholders"];
const labels: Record<FacetId, string> = {
  fact: "Fact",
  scale: "Scale",
  stakeholders: "Stakeholder reactions",
};

interface SpectrumBarProps {
  facets: Partial<Record<FacetId, FacetEvent>>;
  final: FinalEvent | null;
  miniature?: boolean;
  onSelect?: (facet: FacetId) => void;
}

export function SpectrumBar({ facets, final, miniature = false, onSelect }: SpectrumBarProps) {
  return (
    <div className={`spectrum ${miniature ? "spectrum-mini" : ""}`} aria-label="Facet resolution spectrum">
      {facetOrder.map((id) => {
        const facet = facets[id];
        const score = final?.facetScores[id];
        const scoreText = score === null ? "Insufficient data" : score === undefined ? facet?.status.replace("_", " ") : `${score.toFixed(2)} confidence input`;
        return (
          <button
            className={`spectrum-segment ${facet ? "is-resolved" : "is-pending"}`}
            data-status={facet?.status ?? "pending"}
            disabled={!facet || !onSelect}
            key={id}
            onClick={() => onSelect?.(id)}
            title={`${labels[id]} · ${scoreText ?? "Pending"}`}
            type="button"
          >
            <motion.span initial={false} animate={{ scaleX: facet ? 1 : 0 }} transition={{ duration: 0.35, ease: "easeOut" }} />
            <span className="sr-only">{labels[id]}: {scoreText ?? "Pending"}</span>
          </button>
        );
      })}
      <AnimatePresence>{final && <motion.i className="spectrum-sweep" initial={{ x: "-140%" }} animate={{ x: "340%" }} transition={{ duration: 0.7, ease: "easeInOut" }} />}</AnimatePresence>
    </div>
  );
}
