"use client";

import { MotionConfig, useReducedMotion } from "motion/react";
import { useEffect, useReducer, useRef, useState } from "react";
import { PRODUCT_NAME } from "@/lib/brand";
import { connectStream } from "@/lib/sse";
import type { CountsEvent, Evidence, FacetEvent, FacetId, FinalEvent, ProvisionalEvent, StreamEvent } from "@/lib/types";
import { ClaimInput } from "./claim-input";
import { CountTicker } from "./count-ticker";
import { EvidenceModal } from "./evidence-modal";
import { FacetSpectrum } from "./facet-spectrum";
import { VerdictCard } from "./verdict-card";

const DEMO_CLAIM = "Did Meta really lay off 5% of its workforce?";
const emptyCounts: CountsEvent = { type: "counts", sourcesExamined: 0, quotesVerified: 0, quotesTotal: 0 };

interface State {
  phase: "idle" | "running" | "final" | "error";
  provisional: ProvisionalEvent | null;
  facets: Partial<Record<FacetId, FacetEvent>>;
  counts: CountsEvent;
  final: FinalEvent | null;
}

const initialState: State = { phase: "idle", provisional: null, facets: {}, counts: emptyCounts, final: null };
type Action = { type: "start" | "reset" | "error" } | { type: "event"; event: StreamEvent };

function reducer(state: State, action: Action): State {
  if (action.type === "start") return { ...initialState, phase: "running" };
  if (action.type === "reset") return initialState;
  if (action.type === "error") return { ...state, phase: "error" };
  if (action.type !== "event") return state;
  const event = action.event;
  if (event.type === "provisional") return { ...state, provisional: event };
  if (event.type === "facet") return { ...state, facets: { ...state.facets, [event.facet]: event } };
  if (event.type === "counts") return { ...state, counts: event };
  return { ...state, final: event, phase: "final" };
}

function PrismMark() {
  return <svg className="prism-mark" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 4 28 25H4Z" /><path d="m2 15 10 1m8 1 10 1" /></svg>;
}

export function TruthscopeApp() {
  const reduceMotion = useReducedMotion();
  const [state, dispatch] = useReducer(reducer, initialState);
  const [claim, setClaim] = useState(DEMO_CLAIM);
  const [activeId, setActiveId] = useState<FacetId | null>(null);
  const [modal, setModal] = useState<{ evidence: Evidence; facet: FacetEvent } | null>(null);
  const disconnectRef = useRef<null | (() => void)>(null);

  useEffect(() => () => disconnectRef.current?.(), []);

  function submit() {
    if (!claim.trim() || state.phase === "running") return;
    disconnectRef.current?.();
    setActiveId(null);
    dispatch({ type: "start" });
    disconnectRef.current = connectStream(
      claim.trim(),
      (event) => dispatch({ type: "event", event }),
      () => dispatch({ type: "error" }),
    );
  }

  function reset() {
    disconnectRef.current?.();
    setActiveId(null);
    setModal(null);
    dispatch({ type: "reset" });
  }

  function toggleFacet(id: FacetId) {
    setActiveId((current) => current === id ? null : id);
  }

  function selectFacet(id: FacetId) {
    if (!state.facets[id]) return;
    setActiveId(id);
    requestAnimationFrame(() => document.getElementById(`facet-${id}`)?.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" }));
  }

  const hasResult = state.phase !== "idle";
  const running = state.phase === "running";

  return (
    <MotionConfig reducedMotion="user">
      <a className="skip-link" href="#claim">Skip to claim input</a>
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label={`${PRODUCT_NAME} home`}><PrismMark />{PRODUCT_NAME}</a>
        <div className="global-counts mono tnum" aria-live="polite">
          <span>Sources <CountTicker value={state.counts.sourcesExamined} /></span>
          <i aria-hidden="true" />
          <span>Quotes <CountTicker value={state.counts.quotesVerified} />/{state.counts.quotesTotal}</span>
        </div>
      </header>
      <main id="top">
        <section className={`input-stage ${hasResult ? "has-result" : ""}`}>
          <div><span className="eyebrow">Source-first fact checking</span><h1>See the structure of a claim.</h1><p>One clear verdict. Every facet, argument, and source when you need it.</p></div>
          <ClaimInput claim={claim} running={running} hasResult={hasResult} onClaimChange={setClaim} onSubmit={submit} onReset={reset} />
        </section>

        {state.phase === "error" && <p className="stream-error" role="alert">Couldn&apos;t reach the pipeline. Check the backend and try again.</p>}
        {running && !state.provisional && (
          <section className="acquiring" aria-live="polite"><span className="eyebrow pending-label">Acquiring sources</span><p className="mono">Building a preliminary reading...</p></section>
        )}
        {state.provisional && (
          <VerdictCard provisional={state.provisional} final={state.final} counts={state.counts} facets={state.facets} onFacetSelect={selectFacet} onZoom={() => document.getElementById("facets")?.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" })} />
        )}
        {state.provisional && (
          <FacetSpectrum
            facets={state.facets}
            final={state.final}
            activeId={activeId}
            onToggle={toggleFacet}
            onEvidence={(evidence, facet) => setModal({ evidence, facet })}
          />
        )}
      </main>
      <footer className="site-footer"><span>{PRODUCT_NAME}</span><span className="mono">Grounded evidence · visible reasoning</span></footer>
      <EvidenceModal evidence={modal?.evidence ?? null} status={modal?.facet.status ?? "unclear"} onClose={() => setModal(null)} />
    </MotionConfig>
  );
}
