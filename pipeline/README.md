# Prism — Person A: RocketRide Pipeline + Agent Orchestration

Person A's implementation of the RocketRide pipeline with multi-agent orchestration for the Prism hackathon.

## What's Inside

- **Fast Path**: Provisional verdict pipeline for quick consensus detection
- **Facet Pipelines**: Three parallel analysis tracks (fact, scale, stakeholder_reactions)
- **Agent Orchestration**: Pro/Con/Judge agents with quote-grep grounding
- **Entry Points**: Clean interfaces for Person D's backend integration

## Quick Start

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and TAVILY_API_KEY
python test_smoke.py
```

## Public API (what Person D calls)

```python
from pipeline.facet_runner import run_fast_path, run_facet

# Fast path (provisional verdict)
result = run_fast_path(topic="climate policy")

# Individual facet execution
result = run_facet(facet_id="fact", topic="climate policy")
# facet_id options: "fact", "scale", "stakeholder_reactions"

# Result structure for Person D's backend/real_pipeline.py adapter:
result.facet_name           # "fact"
result.verdict              # "confirmed" | "mostly_confirmed" | "disputed" | "refuted" | "unclear"
result.pro_claims           # list[VerifiedClaim]
result.con_claims           # list[VerifiedClaim]
result.con_abstained        # bool — True means "no credible opposition"
result.abstain_reason       # str, only populated when abstained
result.sources_examined     # real counter for F9
result.quotes_attempted     # real counter for F9
result.quotes_verified      # real counter for F9
```

## Architecture

```
   Topic input
        │
        ▼
   ┌─────────────────────┐
   │   Fast Path or      │
   │   Individual Facet  │
   └──────────┬──────────┘
              │
              ▼
   ┌────────────┬────────────┐
   │  Pro Agent │  Con Agent │       ← LLM calls (Claude Sonnet)
   │  (evidence)│ (evidence  │
   │            │  or abstain)│
   └─────┬──────┴─────┬──────┘
         │            │
         ▼            ▼
      ┌──── Judge Agent ────┐
      │ • Provenance check  │       ← Pure Python, no LLM
      │ • Quote-grep (F3)   │       ← "we grep the page for it"
      │ • Deterministic     │
      │   verdict (F4/F6)   │
      └──────────┬──────────┘
                 ▼
          FacetResult → Person D's backend
```

## Files

| File | Purpose |
|---|---|
| `config.py` | Env vars, model names, thresholds |
| `schemas.py` | Pydantic contracts (agreed with A + D) |
| `grounding.py` | `search()` and `fetch()` with disk cache |
| `llm.py` | Anthropic wrapper with JSON self-repair retry |
| `matching.py` | Quote normalization + exact/fuzzy match (F3) |
| `quality.py` | Domain quality tier lookup (F4) |
| `prompts.py` | Pro + Con system prompts |
| `pro_agent.py` | Pro-Agent |
| `con_agent.py` | Con-Agent with F4 asymmetric contract |
| `judge.py` | Provenance + grep + deterministic verdict |
| `reddit_fetcher.py` | Grassroots comments (F5 v2) |
| `facet_runner.py` | Public entry point |
| `test_smoke.py` | The 3 canonical tests |

## Test Cases That Must Always Pass

1. **"The earth is round"** → `con_abstained=True`, `verdict='confirmed'`.
   If this fails, your Con-Agent has manufactured false balance. Revert.
2. **"Meta laid off 5%"** → Con should return real dispute evidence
   (leaked scale numbers etc.), verdict likely `disputed` or `mostly_confirmed`.
3. **Live fresh claim** → pipeline runs end-to-end without crashes.

Run these after every prompt change:
```bash
python test_smoke.py            # uses cache (fast, free)
python test_smoke.py --live     # clears cache, hits real APIs
```

## TODO

- **RocketRide Cloud Deployment**: Pending F2 spike
  - Finalize serverless function packaging
  - Determine state persistence strategy
  - Configure secrets management for production
  - Integration with Person D's FastAPI backend endpoints

## What Not To Do

- Do not put an LLM in the Judge's verdict logic. Deterministic is the pitch.
- Do not let Pro and Con drift into structurally different code. They share `_gather_evidence` shape for a reason.
- Do not "clean up" the Con prompt's asymmetric contract. The imbalance is load-bearing.
- Do not raise LLM temperature above 0.3. You want transcription, not creativity.
- Do not skip the smoke tests before demo. If test 1 fails, the demo will fail on the judge's first probe.
