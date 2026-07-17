"use client";

import { AnimatePresence, motion } from "motion/react";
import { BarChart3, CheckCircle2, ChevronDown, Users } from "lucide-react";
import type { Evidence, FacetEvent, FacetId, FinalEvent } from "@/lib/types";
import { DebateView } from "./debate-view";
import { SpectrumBar } from "./spectrum-bar";
import { StatusChip } from "./status-chip";

const facetOrder: FacetId[] = ["fact", "scale", "stakeholders"];
const facetMeta = {
  fact: { label: "Fact", icon: CheckCircle2 },
  scale: { label: "Scale", icon: BarChart3 },
  stakeholders: { label: "Stakeholder reactions", icon: Users },
};

interface FacetSpectrumProps {
  facets: Partial<Record<FacetId, FacetEvent>>;
  final: FinalEvent | null;
  activeId: FacetId | null;
  onToggle: (id: FacetId) => void;
  onEvidence: (evidence: Evidence, facet: FacetEvent) => void;
}

export function FacetSpectrum(props: FacetSpectrumProps) {
  const { facets, final, activeId, onToggle, onEvidence } = props;
  const visibleIds = final
    ? facetOrder.filter((id) => final.facetScores[id] !== null || facets[id])
    : facetOrder;

  return (
    <section className="facet-section" id="facets" aria-labelledby="facet-title">
      <header className="section-header">
        <div><span className="eyebrow">Level 1 · Facet spectrum</span><h2 id="facet-title">The claim, split into measurable parts</h2></div>
        <SpectrumBar facets={facets} final={final} miniature />
      </header>
      <div className="facet-list">
        {visibleIds.map((id) => {
          const facet = facets[id];
          const meta = facetMeta[id];
          const Icon = meta.icon;
          const open = activeId === id;
          return (
            <motion.div className="facet-shell" id={`facet-${id}`} layout key={id}>
              <button className="facet-row" data-status={facet?.status ?? "pending"} disabled={!facet} onClick={() => onToggle(id)} aria-expanded={open} type="button">
                <Icon aria-hidden="true" className="facet-icon" size={24} strokeWidth={1.5} />
                <span className="facet-main">
                  <motion.strong layoutId={`facet-title-${id}`}>{meta.label}</motion.strong>
                  {facet ? <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }}>{facet.summary}</motion.span> : <span className="summary-skeleton" aria-label="Pending" />}
                </span>
                <span className="facet-result">
                  {facet ? <motion.span initial={{ scale: 0.9 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 400, damping: 30 }}><StatusChip value={facet.status} /></motion.span> : <span className="chip-skeleton" />}
                  {facet && <span className="mono tnum">{facet.sourcesExamined} sources</span>}
                </span>
                <ChevronDown className="facet-chevron" data-open={open} aria-hidden="true" size={20} strokeWidth={1.5} />
              </button>
              <AnimatePresence initial={false}>
                {open && facet && <DebateView facet={facet} onOpen={(item) => onEvidence(item, facet)} />}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
