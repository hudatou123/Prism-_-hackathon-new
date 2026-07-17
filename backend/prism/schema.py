"""
Pydantic v2 data contract for Prism.
Consumed by: Person A (produces FacetResult), Person C (renders all), Person D (produces verdicts).
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, Optional
from datetime import datetime

# ---------- Enums / literal types ----------

FacetId = Literal["fact", "scale", "stakeholder_reactions"]
FacetStatus = Literal["confirmed", "mostly_confirmed", "disputed", "refuted", "unclear"]
SourceQuality = Literal["high", "medium", "low"]
ConfidenceBand = Literal["HIGH", "MODERATE", "LOW", "CONTESTED"]
StakeholderKind = Literal["named", "grassroots"]  # For stakeholder_reactions facet only

# ---------- Argument (a single Pro/Con item at Level 3) ----------

class Argument(BaseModel):
    claim: str = Field(..., description="One-line summary of what this argument says")
    quote: str = Field(..., description="Exact text pulled from the source page")
    url: str = Field(..., description="Source URL, must be clickable")
    source_domain: str = Field(..., description="e.g. 'reuters.com'")
    published_date: Optional[str] = Field(None, description="ISO date string if known")
    quote_verified: bool = Field(..., description="True iff quote-grep succeeded against fetched page")
    source_quality: SourceQuality
    # Only populated when facet_id == "stakeholder_reactions"
    stakeholder_kind: Optional[StakeholderKind] = None
    stakeholder_name: Optional[str] = Field(None, description="e.g. 'CEO Zuckerberg', 'u/redditor123'")

# ---------- Per-facet result (produced by A, consumed by D) ----------

class FacetResult(BaseModel):
    facet_id: FacetId
    status: FacetStatus
    summary: str = Field(..., description="One-line human-readable summary of this facet")
    pro_arguments: list[Argument] = Field(default_factory=list)
    con_arguments: list[Argument] = Field(default_factory=list,
        description="May be empty; empty list under F4 renders as 'No credible counter-evidence found'")
    sources_examined: int = Field(..., ge=0, description="Actual count, not decorative")
    quotes_attempted: int = Field(0, ge=0, description="Actual quote checks attempted")
    quotes_verified: int = Field(..., ge=0, description="Actual count of successful quote-grep passes")
    con_empty: bool = Field(False, description="True only when counter-search ran and verified no counter evidence")
    con_searched: int = Field(0, ge=0, description="Actual counter-side results examined")

# ---------- Provisional verdict (fast path, produced by A, forwarded by D) ----------

class ProvisionalVerdict(BaseModel):
    verdict: str = Field(..., description="e.g. 'Likely true, scale disputed'")
    reasoning: str = Field(..., description="One-sentence rationale for the fast read")
    sources_so_far: int = Field(..., ge=0)

# ---------- Final verdict (produced by D's synthesizer) ----------

class ConfidenceInputs(BaseModel):
    facet_scores: dict[FacetId, Optional[float]] = Field(...,
        description="None for 'unclear' facets, else 0.0-1.0")
    scored_facets_count: int = Field(..., description="Facets excluded if 'unclear'")
    average_score: Optional[float] = Field(None, description="None if all facets unclear")
    sources_agreeing: int
    sources_total: int

class FinalVerdict(BaseModel):
    verdict: str = Field(..., description="e.g. 'MOSTLY TRUE — scale disputed'")
    confidence_band: ConfidenceBand
    confidence_inputs: ConfidenceInputs
    sources_examined_total: int
    quotes_verified_total: int

# ---------- SSE event envelope (D → C) ----------

SSEEventType = Literal["provisional", "facet", "counts", "final", "error", "done"]

class SSEEvent(BaseModel):
    event: SSEEventType
    data: dict  # Serialized model; keep loose here for JSON flexibility

# ---------- Request body (C → D) ----------

class AnalyzeRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
