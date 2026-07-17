"""Adapter from backend models to the frontend's exact camelCase stream contract."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .schema import Argument, FacetResult, FinalVerdict, ProvisionalVerdict

_FACET_NAMES = {
    "fact": "fact",
    "scale": "scale",
    "stakeholder_reactions": "stakeholders",
}
_BANDS = {"HIGH": "high", "MODERATE": "moderate", "LOW": "low", "CONTESTED": "contested"}


def _side(facet: FacetResult, argument: Argument, fallback: str) -> str:
    if facet.facet_id == "stakeholder_reactions" and argument.stakeholder_kind:
        return argument.stakeholder_kind
    return fallback


def _evidence_id(facet: FacetResult, side: str, argument: Argument) -> str:
    raw = "\x1f".join((facet.facet_id, side, argument.url, argument.quote))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{_FACET_NAMES[facet.facet_id]}-{side}-{digest}"


def _evidence(facet: FacetResult, argument: Argument, fallback_side: str) -> dict[str, Any]:
    side = _side(facet, argument, fallback_side)
    source = (
        argument.stakeholder_name
        if side == "grassroots" and argument.stakeholder_name
        else argument.source_domain
    )
    item: dict[str, Any] = {
        "id": _evidence_id(facet, side, argument),
        "side": side,
        "claim": argument.claim,
        "quote": argument.quote,
        "url": argument.url,
        "source": source,
        "verified": True,
    }
    if argument.published_date:
        item["publishedAt"] = argument.published_date
    return item


def provisional_event(claim: str, item: ProvisionalVerdict) -> dict[str, Any]:
    return {
        "type": "provisional",
        "claim": claim,
        "earlyRead": item.verdict,
        "sourcesSoFar": item.sources_so_far,
    }

def facet_event(item: FacetResult) -> dict[str, Any]:
    # UI evidence is a strict verified-only view. Failed quote checks still
    # contribute to quotesTotal, but never become clickable evidence cards.
    evidence = [
        *(
            _evidence(item, argument, "pro")
            for argument in item.pro_arguments
            if argument.quote_verified
        ),
        *(
            _evidence(item, argument, "con")
            for argument in item.con_arguments
            if argument.quote_verified
        ),
    ]
    return {
        "type": "facet",
        "facet": _FACET_NAMES[item.facet_id],
        "status": item.status,
        "summary": item.summary,
        "evidence": evidence,
        "conEmpty": item.con_empty,
        "conSearched": item.con_searched,
        "sourcesExamined": item.sources_examined,
        "quotesVerified": item.quotes_verified,
        "quotesTotal": item.quotes_attempted,
    }


@dataclass
class CumulativeCounts:
    sources_examined: int = 0
    quotes_verified: int = 0
    quotes_attempted: int = 0

    def add(self, facet: FacetResult) -> dict[str, Any]:
        self.sources_examined += facet.sources_examined
        self.quotes_verified += facet.quotes_verified
        self.quotes_attempted += facet.quotes_attempted
        return {
            "type": "counts",
            "sourcesExamined": self.sources_examined,
            "quotesVerified": self.quotes_verified,
            "quotesTotal": self.quotes_attempted,
        }


def final_event(item: FinalVerdict) -> dict[str, Any]:
    backend_scores = item.confidence_inputs.facet_scores
    scores = {
        "fact": backend_scores.get("fact"),
        "scale": backend_scores.get("scale"),
        "stakeholders": backend_scores.get("stakeholder_reactions"),
    }
    verdict, separator, qualifier = item.verdict.partition(" — ")
    payload: dict[str, Any] = {
        "type": "final",
        "verdict": verdict.title(),
        "band": _BANDS[item.confidence_band],
        "facetScores": scores,
        "agreement": {
            "agree": item.confidence_inputs.sources_agreeing,
            "total": item.confidence_inputs.sources_total,
        },
    }
    if separator and qualifier:
        payload["qualifier"] = qualifier
    return payload


def done_event() -> dict[str, str]:
    return {"type": "done"}
