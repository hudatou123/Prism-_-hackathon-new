# Truthscope

Truthscope is a source-first fact-checking demo with four progressive levels: verdict, facets, debate, and exact source evidence.

## Integrated architecture

```text
Browser
  → POST /api/analyze (Next.js, same origin)
  → POST /analyze (FastAPI on 127.0.0.1:8000)
  → mock, Tavily, or Anthropic+Tavily pipeline
  → named SSE events
  → typed reducer and streaming UI
```

Secrets remain in `backend/.env`; no API key is exposed through a `NEXT_PUBLIC_*` variable.

## Pipeline modes

- `auto`: mock without keys, Tavily with a Tavily key, agent with Tavily and Anthropic keys.
- `mock`: deterministic, no network, no keys.
- `tavily`: live search, bounded public-page fetching, and exact-quote verification.
- `agent`: Anthropic early read plus the verified Tavily evidence path.

RocketRide Cloud currently has an authenticated connectivity and `.pipe` execution smoke test. The app does not claim the full fact-checking graph runs on RocketRide until production `.pipe` graphs are built and deployed.

## Local setup

From the workspace root:

```bash
npm install
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Use Python 3.11–3.13. After setup, run both services with:

```bash
./scripts/run-local.sh
```

Open `http://localhost:3000`. The Next.js proxy connects to FastAPI through `PRISM_BACKEND_URL` from `.env.example`; the default is `http://127.0.0.1:8000`.

For browser-only UI development, use `http://localhost:3000/?mock=1` or set `NEXT_PUBLIC_MOCK=1`.

## RocketRide key check

Paste your token only into ignored file `backend/.env`:

```dotenv
ROCKETRIDE_URI=https://api.rocketride.ai
ROCKETRIDE_APIKEY=your-token-here
```

Then run:

```bash
backend/.venv/bin/python backend/scripts/test_rocketride.py
```

This follows the [RocketRide Cloud configuration](https://docs.rocketride.org/cloud) and [Python SDK](https://docs.rocketride.org/develop/python).

## Validation

```bash
npm run build
backend/.venv/bin/python -m pytest -q backend/tests
```

The backend contract uses verified-only evidence, cumulative real counters, deterministic quote matching, strict public-URL fetching, bounded responses, and redacted stream errors.

---

## Team

Prism was built at HackwithSeattle 2.0 by:

- **Haogeng Hu** ([@hudatou123](https://github.com/hudatou123)) — Pipeline & Agents Lead
- **Jay Shivanna** _(GitHub handle pending)_ — Prompts & Judge Design
- **Graeme Huntley** ([@NovusViduus](https://github.com/NovusViduus)) — Frontend, UI & Integration Lead
- **Lingli Yang** ([@lingli8](https://github.com/lingli8)) — Backend & Integration

Built in a 6-hour sprint. Grounded in [Linkup](https://linkup.so) for live web evidence, orchestrated on [RocketRide Cloud](https://cloud.rocketride.ai), and stitched together over too much coffee.
