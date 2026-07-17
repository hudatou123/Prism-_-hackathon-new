# Prism Backend

Live fact-checking agent backend — Person D's ownership (grounding + synthesizer + FastAPI/SSE + integration).

## Overview

Prism decomposes controversies into fixed facets, runs adversarial Pro/Con agents grounded in real web evidence, and streams verdicts progressively via SSE. This backend provides:

1. **Grounding layer** — pluggable search() + fetch() with disk caching
2. **Verdict Synthesizer** — aggregates per-facet results into final verdict with transparent confidence
3. **FastAPI + SSE backend** — streaming seam between pipeline and frontend
4. **Integration harness** — mock mode for early parallel development, real pipeline integration ready

## Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` to configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `TAVILY_API_KEY` | (empty) | Optional — falls back to mock search if not set |
| `PRISM_PIPELINE_MODE` | `mock` | Pipeline mode: `mock` or `real` |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |

## Running

Start the development server:

```bash
uvicorn prism.main:app --reload --port 8000
```

Or in production mode:

```bash
uvicorn prism.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### `GET /health`

Health check.

**Response:**
```json
{
  "status": "ok",
  "pipeline_mode": "mock"
}
```

### `POST /analyze`

SSE stream endpoint. Streams fact-checking results progressively.

**Request:**
```bash
curl -N -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"topic": "Did Meta lay off 5% of its workforce?"}'
```

**Response:** `Content-Type: text/event-stream`

Event sequence:
1. `provisional_verdict` — fast read within ~3s
2. `facet_ready` × 3 — one per facet as they resolve
3. `final_verdict` — synthesized after all facets
4. `done` — stream complete

Example:
```
event: provisional_verdict
data: {"verdict": "Likely true, scale disputed", "reasoning": "...", "sources_so_far": 4}

event: facet_ready
data: {"facet_id": "fact", "status": "confirmed", ...}

event: facet_ready
data: {"facet_id": "scale", "status": "disputed", ...}

event: facet_ready
data: {"facet_id": "stakeholder_reactions", "status": "mostly_confirmed", ...}

event: final_verdict
data: {"verdict": "MOSTLY TRUE — scale disputed", "confidence_band": "MODERATE", ...}

event: done
data: {}
```

### `GET /cache/stats`

Get cache statistics.

### `POST /cache/clear`

Clear all caches (dev only).

## Testing

Run the full test suite:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/test_schema.py -v
```

Run with coverage:

```bash
pytest --cov=prism --cov-report=html
```

## Scripts

### Warm Cache

Pre-warm cache with hero topics for demo:

```bash
python scripts/warm_cache.py
```

### Burst Test

Test search provider rate limit and latency:

```bash
python scripts/burst_test.py
```

## Pipeline Mode Switching

The backend supports two pipeline modes:

- **`mock`** (default) — Uses realistic fake data, unblocks frontend development
- **`real`** — Integrates with Person A's RocketRide pipeline (stub ready)

Switch via environment variable:

```bash
export PRISM_PIPELINE_MODE=real
uvicorn prism.main:app --reload
```

## Architecture

```
prism/
├── schema.py           # Pydantic data contract
├── cache.py            # Disk-caching decorator
├── grounding.py        # search() + fetch() with providers
├── quote_verify.py     # Deterministic substring match
├── synthesizer.py      # Verdict aggregation + confidence
├── mock_pipeline.py    # Fake pipeline for parallel dev
├── real_pipeline.py    # Real pipeline stub (awaiting Person A)
├── pipeline_router.py  # Mode switching
└── main.py             # FastAPI + SSE endpoints
```

## Development

- All code follows Pydantic v2 schema (data contract with teammates)
- Quote verification is deterministic (zero LLM involvement)
- Cache hits disk for all search/fetch calls during development
- CORS enabled for `localhost:3000` frontend (hackathon scope)
- Structured logging with request IDs

## License

Hackathon project — see team for details.
