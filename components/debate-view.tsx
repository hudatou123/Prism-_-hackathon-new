"use client";

import { motion } from "motion/react";
import { Check, ChevronRight } from "lucide-react";
import type { Evidence, FacetEvent } from "@/lib/types";
import { StatusChip } from "./status-chip";

function BalanceScale({ tilt }: { tilt: number }) {
  return (
    <svg className="balance-scale" viewBox="0 0 112 48" role="img" aria-label={`Evidence balance ${tilt > 0 ? "leans toward support" : "is mixed"}`}>
      <motion.line x1="16" y1="17" x2="96" y2="17" className="scale-line" style={{ transformOrigin: "56px 17px" }} animate={{ rotate: tilt }} transition={{ type: "spring", stiffness: 120, damping: 14 }} />
      <line x1="56" y1="18" x2="56" y2="37" className="scale-line" />
      <path d="M46 40 L56 27 L66 40 Z" className="scale-fulcrum" />
    </svg>
  );
}

function EvidenceItem({ evidence, onOpen }: { evidence: Evidence; onOpen: (item: Evidence) => void }) {
  return (
    <button className="evidence-item" onClick={() => onOpen(evidence)} type="button">
      <span className="evidence-source">{evidence.source}</span>
      <strong>{evidence.claim}</strong>
      <span className="evidence-quote mono">“{evidence.quote.slice(0, 90)}{evidence.quote.length > 90 ? "…" : ""}”</span>
      <span className="evidence-meta mono">
        {evidence.verified && <><Check aria-hidden="true" size={14} strokeWidth={1.5} /> Verified</>}
        {evidence.score !== undefined && <span className="tnum">{evidence.score} points</span>}
      </span>
      <ChevronRight className="evidence-chevron" aria-hidden="true" size={18} strokeWidth={1.5} />
    </button>
  );
}

export function DebateView({ facet, onOpen }: { facet: FacetEvent; onOpen: (item: Evidence) => void }) {
  const reactions = facet.facet === "stakeholders";
  const leftSide = reactions ? "named" : "pro";
  const rightSide = reactions ? "grassroots" : "con";
  const left = facet.evidence.filter((item) => item.side === leftSide);
  const right = facet.evidence.filter((item) => item.side === rightSide);
  const tilt = facet.conEmpty ? -12 : facet.status === "confirmed" ? -8 : 0;

  return (
    <motion.div className="debate-view" layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ layout: { type: "spring", stiffness: 300, damping: 32 } }}>
      <header className="debate-header">
        <div><span className="eyebrow">Level 2 · Debate</span><motion.h3 layoutId={`facet-title-${facet.facet}`}>{facet.facet === "stakeholders" ? "Stakeholder reactions" : facet.facet[0].toUpperCase() + facet.facet.slice(1)}</motion.h3></div>
        <StatusChip value={facet.status} />
        {!reactions && <BalanceScale tilt={tilt} />}
      </header>
      <div className="debate-columns">
        <section>
          <header className="column-header"><span className="eyebrow">{reactions ? "Named" : "Pro"}</span><span>{reactions ? "Public statements" : "Evidence that supports"}</span></header>
          <div className="evidence-list">{left.map((item) => <EvidenceItem evidence={item} key={item.id} onOpen={onOpen} />)}</div>
        </section>
        <section>
          <header className="column-header"><span className="eyebrow">{reactions ? "Grassroots" : "Con"}</span><span>{reactions ? "Public reactions" : "Strongest counter-evidence"}</span></header>
          {facet.conEmpty ? (
            <div className="positive-empty">
              <Check aria-hidden="true" size={22} strokeWidth={1.5} />
              <strong>No credible counter-evidence found</strong>
              <span className="mono tnum">Searched {facet.conSearched ?? 0} sources · {right.length} verifiable counterclaims</span>
            </div>
          ) : <div className="evidence-list">{right.map((item) => <EvidenceItem evidence={item} key={item.id} onOpen={onOpen} />)}</div>}
        </section>
      </div>
    </motion.div>
  );
}
