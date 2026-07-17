"""
judge.py — Anti-hallucination verification + deterministic facet verdict.

This is the trust layer. It has THREE steps:
  A) Provenance check       (Python, no LLM) — was this URL actually in search results?
  B) Quote-grep verification (Python, no LLM) — does the quote appear in the page?
  C) Facet verdict           (Python, no LLM) — quality-weighted deterministic scoring.

Key design decision: the verdict is computed in Python, not by an LLM.
Rationale: it's auditable, deterministic, and directly demonstrates the
"we don't trust the model with things we can verify ourselves" narrative
that makes the project distinctive. When a judge asks "why did this get
'Disputed'?", you show them this file.
"""
from __future__ import annotations

from grounding import fetch
from matching import verify_quote
from quality import quality_of, weight_of
from schemas import Claim, ConResult, FacetResult, FacetVerdict, ProResult, VerifiedClaim


# ── Step A + B: verify a batch of claims ────────────────────────────────
def _verify_claims(
    claims: list[Claim],
    allowed_urls: set[str],
) -> tuple[list[VerifiedClaim], int, int]:
    """
    Run provenance check + quote-grep on each claim.

    Returns (verified_claims, quotes_attempted, quotes_verified).

    A claim is dropped (not verified) if:
      - Its URL is not in allowed_urls (provenance fail)
      - The fetched page text is empty (source unfetchable)
      - Its quote fails both exact and fuzzy match
    """
    verified: list[VerifiedClaim] = []
    attempted = 0
    passed = 0

    for c in claims:
        attempted += 1

        # A) Provenance
        if c.url not in allowed_urls:
            print(f"[judge] DROP (provenance): {c.url} not in search results")
            continue

        # B) Quote-grep
        page_text = fetch(c.url)  # cached
        if not page_text:
            print(f"[judge] DROP (empty page): {c.url}")
            continue

        match_type, score = verify_quote(c.quote, page_text)
        if match_type == "none":
            print(f"[judge] DROP (quote not found, score={score:.1f}): {c.quote[:60]!r}")
            continue

        passed += 1
        verified.append(
            VerifiedClaim(
                claim=c,
                quality_tier=quality_of(c.url),
                match_type=match_type,
            )
        )

    return verified, attempted, passed


# ── Step C: deterministic facet verdict ─────────────────────────────────
def _compute_verdict(
    pro: list[VerifiedClaim],
    con: list[VerifiedClaim],
    con_abstained: bool,
) -> FacetVerdict:
    """
    Deterministic verdict from quality-weighted evidence.

    Design (F4, F6):
      - If we have no Pro evidence: unclear (insufficient data).
      - If Con abstained OR no Con evidence:
          → confirmed (pro dominates unopposed)
      - If Pro weight is much greater than Con weight (>= 2x):
          → mostly_confirmed
      - If Con weight is much greater than Pro weight (>= 2x):
          → refuted
      - Otherwise: disputed (both sides brought quality evidence).

    "Much greater" = 2x weighted ratio. This is a knob you can tune.
    """
    pro_weight = sum(weight_of(v.quality_tier) for v in pro)
    con_weight = sum(weight_of(v.quality_tier) for v in con)

    # No supporting evidence at all → we don't know
    if pro_weight == 0:
        return "unclear"

    # Con abstained or produced no verified claims → pro dominates
    if con_abstained or con_weight == 0:
        return "confirmed"

    # Both sides brought weight — compare
    if pro_weight >= 2 * con_weight:
        return "mostly_confirmed"
    if con_weight >= 2 * pro_weight:
        return "refuted"
    return "disputed"


# ── Public entry point ──────────────────────────────────────────────────
def judge_facet(
    facet_name: str,
    pro: ProResult,
    con: ConResult,
    pro_urls_examined: list[str],
    con_urls_examined: list[str],
) -> FacetResult:
    """
    Verify Pro and Con evidence, then compute the facet verdict.

    Called by facet_runner.py after Pro and Con have executed.
    """
    all_urls = set(pro_urls_examined) | set(con_urls_examined)

    pro_verified, pro_attempted, pro_passed = _verify_claims(pro.claims, all_urls)
    con_verified, con_attempted, con_passed = _verify_claims(con.claims, all_urls)

    verdict = _compute_verdict(
        pro=pro_verified,
        con=con_verified,
        con_abstained=con.no_credible_counter_evidence_found,
    )

    return FacetResult(
        facet_name=facet_name,
        verdict=verdict,
        pro_claims=pro_verified,
        con_claims=con_verified,
        con_abstained=con.no_credible_counter_evidence_found,
        abstain_reason=con.reason if con.no_credible_counter_evidence_found else "",
        sources_examined=len(all_urls),
        quotes_attempted=pro_attempted + con_attempted,
        quotes_verified=pro_passed + con_passed,
    )
