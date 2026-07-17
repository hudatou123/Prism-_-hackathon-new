"use client";

import { motion } from "motion/react";
import { Check, ExternalLink, X } from "lucide-react";
import { useEffect, useRef } from "react";
import type { Evidence, FacetStatus } from "@/lib/types";

interface EvidenceModalProps {
  evidence: Evidence | null;
  status: FacetStatus;
  onClose: () => void;
}

export function EvidenceModal({ evidence, status, onClose }: EvidenceModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (evidence && !dialogRef.current?.open) dialogRef.current?.showModal();
  }, [evidence]);

  if (!evidence) return null;
  const published = evidence.publishedAt
    ? new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(evidence.publishedAt))
    : "Timestamp unavailable";

  return (
    <dialog
      className="evidence-dialog"
      onCancel={onClose}
      onClick={(event) => { if (event.target === dialogRef.current) dialogRef.current?.close(); }}
      onClose={onClose}
      ref={dialogRef}
    >
      <motion.div className="evidence-panel" data-status={status} initial={{ opacity: 0, scale: 0.96, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ type: "spring", stiffness: 300, damping: 28 }}>
        <div className="modal-topline"><span className="eyebrow">Evidence detail</span><button className="icon-button" onClick={() => dialogRef.current?.close()} type="button" aria-label="Close evidence"><X size={20} strokeWidth={1.5} /></button></div>
        <blockquote className="modal-quote mono">“{evidence.quote}”</blockquote>
        <div className="source-line">
          <strong>{evidence.source}</strong>
          <a href={evidence.url} target="_blank" rel="noreferrer">Open source <ExternalLink aria-hidden="true" size={16} strokeWidth={1.5} /></a>
        </div>
        <p className="modal-timestamp mono">{published}</p>
        <div className={`verification-strip ${evidence.verified ? "is-verified" : "is-unverified"}`}>
          {evidence.verified && (
            <svg viewBox="0 0 24 24" aria-hidden="true"><motion.path d="m5 12 4 4L19 6" fill="none" stroke="currentColor" strokeWidth="2" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.3 }} /></svg>
          )}
          {!evidence.verified && <X aria-hidden="true" size={20} strokeWidth={1.5} />}
          <div><span className="eyebrow">{evidence.verified ? "Quote verified" : "Not verified · excluded from scoring"}</span><p>{evidence.verified ? "Exact match found in fetched page text" : "This item is shown for context and does not affect the verdict."}</p></div>
        </div>
        {evidence.bias && <p className="bias-line mono">Source bias: {evidence.bias[0].toUpperCase() + evidence.bias.slice(1)} · static lookup</p>}
      </motion.div>
    </dialog>
  );
}
