# Prism — Pipeline & Deployment (Person A)

Progressive-disclosure fact-checker for HackwithSeattle 2.0, Track 1.
This repo is **Person A's** deliverables: the front of the pipeline
(input → decompose → fan-out), the streaming orchestrator, and the RocketRide
deploy adapter. It runs **end-to-end today**, offline, with zero API keys.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt          # or just `pip install pydantic` for offline
python run_local.py                      # streams the Meta hero topic from the fixture
python -m prism.rocketride hello    # F2 hour-0 deploy spike
PYTHONPATH=. python tests/test_quotecheck.py
```

With no keys it runs against `fixtures/meta_layoffs.json` (the F7 demo safety
net). Set `ANTHROPIC_API_KEY` + `TAVILY_API_KEY` in `.env` to run live.

## What's built (Person A scope, per §7/§10)

| Doc item | Where |
|---|---|
| **F2** hello-world .pipe + deploy adapter, hour-0 spike | [prism/rocketride.py](prism/rocketride.py), [pipelines/hello_world.py](pipelines/hello_world.py) |
| **F5/F4** Layer Decomposer: fixed facets + settled-fact detector | [prism/agents/decomposer.py](prism/agents/decomposer.py) |
| **F1** Fast path / provisional verdict | [prism/agents/fast_path.py](prism/agents/fast_path.py) |
| Parallel facet fan-out, streams as each resolves | [prism/orchestrator.py](prism/orchestrator.py) |
| **Plan B** per-facet pipe unit | [pipelines/facet_pipeline.py](pipelines/facet_pipeline.py) |
| **CH0** pluggable grounding (Tavily + httpx/trafilatura) + F7 cache | [prism/grounding/](prism/grounding/) |
| The **A↔D contract** (schemas, StreamEvent, SSE) | [prism/schemas.py](prism/schemas.py) |

## The seams (so B/C/D aren't blocked)

Everything another person owns sits behind an interface with a working default,
so the whole tree runs now and each owner swaps their piece in without touching
A's code:

- **Person B** (Pro/Con/Judge + F3 quote-grep): implement the `FacetAgent`
  protocol in [prism/agents/procon_judge.py](prism/agents/procon_judge.py).
  A ships a `StubFacetAgent` that already does the *real* F3 grep
  ([prism/quotecheck.py](prism/quotecheck.py)) — B replaces argument
  *selection* and the quality-weighted judgment. Reddit grassroots fetch is
  stubbed against the fixture; wire the real `.json` fetch here.
- **Person C** (UI): render `StreamEvent`s from `run_pipeline()`. Run
  `run_local.py` to see every event shape you'll get, in resolution order.
- **Person D** (synthesis + SSE): consume `run_pipeline()` and forward
  `StreamEvent.sse()`. A ships a correct F6 confidence implementation in
  [prism/synthesizer.py](prism/synthesizer.py) for D to refine;
  D owns the FastAPI backend + the full F7 cache harness + real counts plumbing.

## Event stream contract (what D pipes into SSE)

`run_pipeline(claim)` yields `StreamEvent`s in **resolution order**:

```
provisional_verdict   # F1, ~2-4s, badged "verifying..."
decomposed            # facet queries ready (settled_fact flag set here)
facet_started × N     # fan-out begins
facet_resolved × N    # each FacetVerdict lands independently (slow ≠ blocks fast)
final_verdict         # F1 swap, F6 confidence with inputs
done
```

## Assumptions flagged for the team

1. **RocketRide SDK unknown** → all pipes are plain async callables behind a
   `Pipe` protocol; `deploy()`/`invoke()` in `rocketride.py` are the *only* two
   functions to reimplement against the real SDK. Do this in the minute-0 F2
   spike and confirm Plan A vs Plan B.
2. **LLM = Claude** (Haiku fast path / Sonnet reasoning). One file to swap:
   [prism/llm.py](prism/llm.py).
3. **Offline mock** returns canned decomposition/fast-path JSON
   ([prism/mocks.py](prism/mocks.py)) so the pipeline runs with no
   keys. Delete-safe once live keys are in.
