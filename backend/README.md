# Prism backend

FastAPI/SSE backend for the Truthscope UI. Python 3.11+ is required.

## Setup

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn prism.main:app --reload
```

Configuration is loaded centrally from `backend/.env`. The secure runtime default is `PRISM_ENV=production`; the example file explicitly selects development for local use. `PRISM_PIPELINE_MODE` accepts only:

- `auto` (default): `agent` when Anthropic and Tavily keys are present, `tavily` when only Tavily is present, otherwise `mock`.
- `mock`: deterministic no-network demo, about 12.5 seconds; settled Earth claims short-circuit in about 3 seconds.
- `tavily`: deterministic, parallel three-facet search and exact fetched-page quote checks. A Tavily key is required and live failures never fall back to mock data.
- `agent`: a lazy Anthropic early-read adapter plus the same hardened, exact-quote Tavily evidence path. Both keys are required.

`PRISM_CORS_ORIGINS` is a comma-separated list of exact origins. `*` is rejected. `POST /cache/clear` is available only when `PRISM_ENV` is `development`, `dev`, `local`, or `test`.

## API

- `GET /health` returns the resolved pipeline mode.
- `GET /analyze?claim=...` supports the browser `EventSource` client.
- `POST /analyze` accepts `{"topic":"..."}`.
- `GET /cache/stats` returns local cache metrics.
- `POST /cache/clear` clears caches in development only.

`/analyze` emits named SSE events: `provisional`, `facet`, `counts`, `final`, and `done`. Every JSON payload has a matching `type` discriminator; errors use a generic `error` payload without internal exception details. Facet payloads follow the UI's camelCase contract, including `stakeholder_reactions` → `stakeholders`, verified-only flattened evidence, deterministic evidence IDs, `conEmpty`, `conSearched`, and per-facet `sourcesExamined`/`quotesVerified`/`quotesTotal`. A `counts` event follows every facet with cumulative values.

Live fetching accepts only public HTTP(S) targets, resolves and rejects private/local/link-local/metadata addresses, validates each redirect target, and enforces response type, size, redirect, and timeout limits.

## Tests

Tests require no API keys and make no network requests:

```bash
cd backend
pytest -q
```

No RocketRide integration is claimed or provided.

## RocketRide Cloud connectivity

The repository includes `pipelines/hello.pipe` and `scripts/test_rocketride.py` for an authenticated Cloud execution check. This verifies the key, WebSocket connection, upload, send, response, and termination lifecycle; it does not claim the local fact-checking graph has already been converted to RocketRide nodes.

After creating `backend/.env`, set:

```dotenv
ROCKETRIDE_URI=https://api.rocketride.ai
ROCKETRIDE_APIKEY=your-token-here
```

Then run from `backend/` with the virtual environment active:

```bash
python scripts/test_rocketride.py
```

The variable names and secure endpoint follow the [RocketRide Cloud documentation](https://docs.rocketride.org/cloud) and the smoke script follows the [Python SDK lifecycle](https://docs.rocketride.org/develop/python).
