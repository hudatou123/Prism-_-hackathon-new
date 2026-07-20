# Prism (Truthscope)

Prism is a source-first fact-checking demo built at HackwithSeattle 2.0 (Track 1, Live Fact-Checking). It presents a claim across four progressive levels — verdict, facets, debate, and exact source evidence — so you can stop at the one-line answer or drill all the way down to the quoted page text.

## What makes it different (and what actually ships)

The core idea: **don't ask an LLM whether a quote is real — fetch the page and grep for it.** The running service is grounded by construction, not by trusting a model.

- **Anti-hallucination by construction.** Every displayed quote is a literal substring of the fetched page, confirmed by a deterministic normalized substring match ([backend/prism/quote_verify.py](backend/prism/quote_verify.py)). In the live paths the LLM never writes the quotes, so a fabricated quote cannot reach the UI.
- **Hardened live fetching (SSRF).** Public HTTP(S) targets only; private/loopback/link-local/metadata addresses rejected; DNS-rebinding mitigation; every redirect target re-validated; content-type, size, redirect, and timeout caps ([backend/prism/grounding.py](backend/prism/grounding.py)).
- **Deterministic verdict + transparent confidence.** Rule-based facet scoring and qualitative confidence bands, shown with their inputs — no mystery percentage ([backend/prism/synthesizer.py](backend/prism/synthesizer.py)).
- **Streaming UI.** Named SSE events → a typed reducer → progressive disclosure (verdict → facets → debate → evidence), with a provisional verdict that swaps for the synthesized final one.

## Architecture (as built)

```text
Browser
  → POST /api/analyze (Next.js proxy, same origin)
  → POST /analyze (FastAPI on 127.0.0.1:8000)
  → mock, Tavily, or Tavily + one Anthropic "early read" pipeline
  → named SSE events
  → typed reducer and streaming UI
```

Secrets stay in `backend/.env`; no API key is exposed through a `NEXT_PUBLIC_*` variable.

## Pipeline modes

- `auto`: mock without keys, Tavily with a Tavily key, agent with Tavily and Anthropic keys.
- `mock`: deterministic, no network, no keys (settled "Earth is round" claims short-circuit in ~3s).
- `tavily`: live search, bounded public-page fetching, and exact-quote verification.
- `agent`: the same verified Tavily evidence path, plus a single Anthropic "early read" sentence.

**On LLM usage:** in `agent` mode the *only* LLM call is one cautious "early read" sentence used for the provisional verdict (Haiku), explicitly forbidden from asserting facts or citing sources. Evidence gathering, quote verification, and the final verdict are deterministic and LLM-free in every mode.

## Not yet integrated (honest status)

Two things the original design doc pitched are present as exploration but are **not wired into the running app**:

- **Multi-agent debate engine (`pipeline/`).** A standalone Pro/Con/Judge engine with an asymmetric Con contract, a settled-fact short-circuit, and Reddit grassroots evidence. It runs on its own, but the FastAPI service does not call it — `agent` mode uses the deterministic Tavily path above, not this engine.
- **RocketRide Cloud.** Only an authenticated connectivity + `.pipe` execution smoke test exists ([backend/scripts/test_rocketride.py](backend/scripts/test_rocketride.py)). The fact-checking graph does not run on RocketRide.

See [Truthscope_Design_Doc_v2_EN.md](Truthscope_Design_Doc_v2_EN.md) for the original design intent; where it and this README disagree, this README reflects what actually ships.

## Local setup

From the workspace root:

```bash
npm install
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Use Python 3.11–3.13. (`rocketride` in `requirements.txt` is only needed for the optional connectivity check below; if it fails to install, it can be safely omitted.) After setup, run both services with:

```bash
./scripts/run-local.sh
```

Open `http://localhost:3000`. The Next.js proxy connects to FastAPI through `PRISM_BACKEND_URL`; the default is `http://127.0.0.1:8000`.

For browser-only UI development, use `http://localhost:3000/?mock=1` or set `NEXT_PUBLIC_MOCK=1`.

## Validation

```bash
npm run build
backend/.venv/bin/python -m pytest -q backend/tests
```

The backend contract uses verified-only evidence, cumulative real counters, deterministic quote matching, strict public-URL fetching, bounded responses, and redacted stream errors.

## RocketRide connectivity check (optional, exploratory)

This verifies token auth and a trivial `.pipe` run only; it does not run the fact-checking pipeline. Paste your token into the ignored file `backend/.env`:

```dotenv
ROCKETRIDE_URI=https://api.rocketride.ai
ROCKETRIDE_APIKEY=your-token-here
```

Then run:

```bash
backend/.venv/bin/python backend/scripts/test_rocketride.py
```

See the [RocketRide Cloud configuration](https://docs.rocketride.org/cloud) and [Python SDK](https://docs.rocketride.org/develop/python).

---

## Team

Prism was built at HackwithSeattle 2.0 by:

- **Hu** ([@hudatou123](https://github.com/hudatou123)) — Pipeline & Agents Lead
- **Jay** ([@sjayy1212-prog](https://github.com/sjayy1212-prog)) — Prompts & Judge Design
- **Graeme** ([@NovusViduus](https://github.com/NovusViduus)) — Frontend, UI & Integration Lead
- **Lingli** ([@lingli8](https://github.com/lingli8)) — Backend & Integration
