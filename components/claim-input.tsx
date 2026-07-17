"use client";

import { RotateCcw, Search } from "lucide-react";

interface ClaimInputProps {
  claim: string;
  running: boolean;
  hasResult: boolean;
  onClaimChange: (claim: string) => void;
  onSubmit: () => void;
  onReset: () => void;
}

export function ClaimInput(props: ClaimInputProps) {
  const { claim, running, hasResult, onClaimChange, onSubmit, onReset } = props;
  return (
    <form className="claim-form" onSubmit={(event) => { event.preventDefault(); onSubmit(); }}>
      <label className="sr-only" htmlFor="claim">Claim or controversy</label>
      <Search aria-hidden="true" size={22} strokeWidth={1.5} />
      <input
        id="claim"
        autoFocus
        value={claim}
        onChange={(event) => onClaimChange(event.target.value)}
        placeholder="Paste a claim or controversy..."
      />
      <button className="check-button" disabled={running || !claim.trim()} type="submit">
        {running ? "Checking..." : "Check it"}
      </button>
      {hasResult && !running && (
        <button className="reset-button" type="button" onClick={onReset}>
          <RotateCcw aria-hidden="true" size={15} strokeWidth={1.5} /> New check
        </button>
      )}
    </form>
  );
}
