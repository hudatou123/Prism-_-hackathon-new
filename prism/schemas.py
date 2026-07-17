"""The A<->D contract, frozen at hour 0.

Person A's fan-out EMITS these; Person D's synthesizer + SSE backend CONSUME
them. Person C's UI renders them. If a field changes here, all three know.

Design notes:
- FacetStatus mirrors the F6 scoring bands exactly (see score_for).
- Evidence carries `quote_verified` because the F3 quote-grep is the whole
  product; the UI shows the badge straight off this bool.
- StreamEvent is the streaming unit: the orchestrator yields these in the
  order things actually resolve (provisional first, facets as they land,
  final last), which is exactly what D pipes into SSE.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Verdict vocabulary
# --------------------------------------------------------------------------
class FacetStatus(str, Enum):
    CONFIRMED = "confirmed"              # 1.0
    MOSTLY_CONFIRMED = "mostly_confirmed"  # 0.75
    DISPUTED = "disputed"               # 0.5  (both sides brought quality evidence)
    REFUTED = "refuted"                 # 0.0
    UNCLEAR = "unclear"                 # excluded from average (F6 v2)


# F6 scoring, in one auditable place.
_FACET_SCORE = {
    FacetStatus.CONFIRMED: 1.0,
    FacetStatus.MOSTLY_CONFIRMED: 0.75,
    FacetStatus.DISPUTED: 0.5,
    FacetStatus.REFUTED: 0.0,
    FacetStatus.UNCLEAR: None,  # excluded — "insufficient data"
}


def score_for(status: FacetStatus) -> Optional[float]:
    """F6 facet score, or None if the facet is excluded from the average."""
    return _FACET_SCORE[status]


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    CONTESTED = "contested"


class SourceBias(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    UNKNOWN = "unknown"  # not in the F8 static lookup table


# --------------------------------------------------------------------------
# Evidence tree (Level 2 / Level 3)
# --------------------------------------------------------------------------
class Evidence(BaseModel):
    """One traceable claim: a quote + where it came from + whether it checks out."""
    quote: str
    url: str
    title: Optional[str] = None
    published_date: Optional[str] = None
    source_bias: SourceBias = SourceBias.UNKNOWN
    # F3: set by the Judge's deterministic grep, NOT by any LLM.
    quote_verified: bool = False
    # Optional grassroots metadata (F5): Reddit handle + permalink.
    author: Optional[str] = None
    score: Optional[int] = None  # upvotes, for grassroots items


class Argument(BaseModel):
    claim: str
    evidence: List[Evidence] = Field(default_factory=list)


class DebateSide(BaseModel):
    """One column of the Level-2 split screen."""
    arguments: List[Argument] = Field(default_factory=list)
    # F4: an explicit, honest empty state — renders as a positive finding.
    no_credible_evidence: bool = False


# --------------------------------------------------------------------------
# Decomposer output (Person A -> facet runners)
# --------------------------------------------------------------------------
class FacetQueries(BaseModel):
    facet_key: str
    pro_query: str
    con_query: str
    grassroots_query: Optional[str] = None  # only for the grassroots sub-bucket


class Decomposition(BaseModel):
    claim: str
    facet_queries: List[FacetQueries]
    # F4: settled facts skip the debate theater and run one confirm/refute lane.
    settled_fact: bool = False
    settled_reason: Optional[str] = None


# --------------------------------------------------------------------------
# Facet result (Person A's fan-out EMITS -> Person D CONSUMES)
# --------------------------------------------------------------------------
class FacetVerdict(BaseModel):
    facet_key: str
    label: str
    status: FacetStatus
    summary: str                       # one-line Level-1 caption
    pro: DebateSide = Field(default_factory=DebateSide)
    con: DebateSide = Field(default_factory=DebateSide)
    # F9: real counters, never decorative.
    sources_examined: int = 0
    quotes_verified: int = 0
    quotes_total: int = 0

    @property
    def score(self) -> Optional[float]:
        return score_for(self.status)


# --------------------------------------------------------------------------
# Verdicts (Level 0)
# --------------------------------------------------------------------------
class ProvisionalVerdict(BaseModel):
    """F1: on screen in ~2-4s, badged 'Preliminary, verifying...'."""
    claim: str
    early_read: str
    reasoning: str = ""          # one-sentence rationale (maps to D's `reasoning`)
    sources_so_far: int = 0
    badge: str = "Preliminary · verifying..."


class FinalVerdict(BaseModel):
    """F1: replaces the provisional one with a visible swap. Built by Person D."""
    claim: str
    verdict: str
    confidence_band: ConfidenceBand
    # F6: show the inputs, not a mystery number.
    facet_scores: dict = Field(default_factory=dict)  # facet_key -> score|None
    scored_facet_count: int = 0
    total_facet_count: int = 0
    source_agreement_ratio: Optional[float] = None
    # F9: real totals.
    sources_examined: int = 0
    quotes_verified: int = 0
    quotes_total: int = 0


# --------------------------------------------------------------------------
# Streaming (the thing D pipes into SSE)
# --------------------------------------------------------------------------
class EventType(str, Enum):
    PROVISIONAL = "provisional_verdict"   # F1, fires first
    DECOMPOSED = "decomposed"             # facet queries ready
    FACET_STARTED = "facet_started"
    FACET_RESOLVED = "facet_resolved"     # a FacetVerdict landed
    FINAL = "final_verdict"               # F1 swap
    ERROR = "error"
    DONE = "done"


class StreamEvent(BaseModel):
    type: EventType
    # Exactly one of these is populated depending on `type`.
    provisional: Optional[ProvisionalVerdict] = None
    decomposition: Optional[Decomposition] = None
    facet_key: Optional[str] = None
    facet: Optional[FacetVerdict] = None
    final: Optional[FinalVerdict] = None
    message: Optional[str] = None

    def sse(self) -> str:
        """Serialize to an SSE frame — Person D calls this in the FastAPI layer."""
        return f"event: {self.type.value}\ndata: {self.model_dump_json(exclude_none=True)}\n\n"
