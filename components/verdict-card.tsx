"use client";

import { AnimatePresence, motion } from "motion/react";
import { Check, ChevronDown } from "lucide-react";
import type { CountsEvent, FacetEvent, FacetId, FinalEvent, ProvisionalEvent } from "@/lib/types";
import { CountTicker } from "./count-ticker";
import { SpectrumBar } from "./spectrum-bar";
import { StatusChip } from "./status-chip";

interface VerdictCardProps {
  provisional: ProvisionalEvent | null;
  final: FinalEvent | null;
  counts: CountsEvent;
  facets: Partial<Record<FacetId, FacetEvent>>;
  onFacetSelect: (id: FacetId) => void;
  onZoom: () => void;
}

export function VerdictCard(props: VerdictCardProps) {
  const { provisional, final, counts, facets, onFacetSelect, onZoom } = props;
  const scored = final ? Object.values(final.facetScores).filter((score) => score !== null) : [];
  const confirmed = scored.filter((score) => score === 1).length;

  return (
    <section className="verdict-card" data-final={Boolean(final)} data-status={final?.band ?? "pending"} aria-live="polite">
      <SpectrumBar facets={facets} final={final} onSelect={onFacetSelect} />
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.div
          className="verdict-body"
          key={final ? "final" : "provisional"}
          initial={{ opacity: 0, y: 12, scale: 0.985 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8 }}
          transition={final ? { type: "spring", stiffness: 260, damping: 24 } : { duration: 0.2 }}
        >
          {!final && provisional ? (
            <>
              <span className="eyebrow pending-label">PRELIMINARY · VERIFYING ACROSS 3 FACETS</span>
              <h1 className="provisional-read">Early read: {provisional.earlyRead}</h1>
              <p className="mono count-line">Sources so far: <CountTicker value={provisional.sourcesSoFar} /></p>
            </>
          ) : final ? (
            <>
              <span className="eyebrow">Verdict</span>
              <h1 className="final-verdict">{final.verdict} {final.qualifier && <span>· {final.qualifier}</span>}</h1>
              <div className="confidence-block">
                <StatusChip value={final.band} />
                <p className="mono tnum">{confirmed}/{scored.length} facets confirmed · {final.agreement.agree} of {final.agreement.total} quality sources agree</p>
              </div>
              <p className="final-counts mono tnum">
                Sources examined: <CountTicker value={counts.sourcesExamined} />
                <i aria-hidden="true" /> Quotes verified: <CountTicker value={counts.quotesVerified} />/{counts.quotesTotal}
                <Check aria-label="Verified" size={16} strokeWidth={1.5} />
              </p>
              <button className="zoom-button" onClick={onZoom} type="button">Zoom in <ChevronDown aria-hidden="true" size={18} strokeWidth={1.5} /></button>
            </>
          ) : null}
        </motion.div>
      </AnimatePresence>
    </section>
  );
}
