# Pipeline Integration — Answers for Person D (from Person A)

> Re: `Pipeline_Integration_Questions.md`. TL;DR: **you can flip to `real`
> today without waiting on RocketRide.** I've shipped an in-process adapter
> that matches your async-generator contract and emits dicts that already pass
> your Pydantic schema. Answers to all 8 questions below, plus real example
> payloads and the defaults I picked for the fields I can't fully fill yet.

---

## The one thing that unblocks you now

I added `prism/integration.py`. It adapts my internal pipeline onto **your**
`schema.py` contract and exposes a drop-in for `mock_pipeline.run`:

```python
# backend/prism/real_pipeline.py
from prism.integration import run as prism_run   # see "Import note" at the bottom
from .schema import ProvisionalVerdict, FacetResult

async def run(topic: str):
    async for item in prism_run(topic):
        kind = item.pop("_kind")               # "provisional" | "facet"
        if kind == "provisional":
            yield ProvisionalVerdict(**item)
        else:
            yield FacetResult(**item)
```

That's the whole adapter. It yields **one provisional, then 3 facets as each
resolves** — exactly your ordering. It runs today with **zero API keys** (offline
fixture) and switches to live Tavily+Claude when keys are set, no code change.

I verified the output validates against a faithful copy of your `schema.py`:
```
✅ ProvisionalVerdict
✅ FacetResult:fact
✅ FacetResult:scale
✅ FacetResult:stakeholder_reactions
```

If you prefer your **Option B** (fan out fast-path + 3 facets as independent
calls), use these instead:
```python
from prism.integration import run_fast_path, run_facet, FACET_IDS
prov   = await run_fast_path(topic)                 # dict
facets = await asyncio.gather(*(run_facet(f, topic) for f in FACET_IDS))
```

---

## Answers to your 8 questions

### 1. How do I invoke your pipeline?
**Now (interim): in-process Python import** — `from prism.integration import run`.
No HTTP, no auth, no RocketRide dependency. This lets you test `real` mode today.
**Later: RocketRide SDK invoke** — same data, I swap the internals of
`integration.run` to call the deployed pipes once the F2 streaming spike is done.
Your `real_pipeline.py` won't change.

### 2. One pipeline or multiple?
**Option B** — 1 fast-path unit + 3 facet units, you fan out in parallel. That's
how my code is already structured (`pipelines/facet_pipeline.py`, one per facet).
`run()` (Option A-style single generator) is also provided and is the simplest
drop-in; pick whichever you like. Native RocketRide streaming (true Plan A) is
still pending the spike — assume B.

### 3. Authentication
**Interim: none** (in-process). **Later:** env var `ROCKETRIDE_API_KEY`; header
name TBD once the SDK is pinned. Nothing to hardcode on your side either way.

### 4. Response format
See **"Example payloads"** below — real output from my adapter. It already
matches your `Argument` / `FacetResult` / `ProvisionalVerdict` field-for-field:
- `pro_arguments` / `con_arguments`: ✅ same shape (see defaults note for the 3
  fields I fill heuristically).
- `quote_verified`: ✅ real boolean from the F3 quote-grep (deterministic
  normalized substring match; no LLM). Arguments that fail the grep are dropped
  before they reach you.
- `sources_examined` / `quotes_verified`: ✅ real counters, not decorative.
- `con_arguments == []` under F4 (settled fact / no credible counter) — you
  render it as "No credible counter-evidence found". My `fact` facet demonstrates
  this.

### 5. Timing expectations
- Fast path: **~2–4s** (live). Offline: instant.
- Each facet: **~5–15s** live (search + fetch + grep per side).
- Suggested timeout: **30–45s** per request.

### 6. Failure modes
- **Single facet fails:** I catch it and return a valid `unclear` FacetResult
  (empty args, `sources_examined=0`) so you keep streaming the other two. You
  never get a mid-stream exception from a facet.
- **Fast path fails:** I just don't emit a provisional; facets still stream.
- **All facets fail:** you'll receive 3 `unclear` FacetResults — surface your SSE
  `error` (or a low-confidence verdict; your synthesizer already handles
  all-unclear → CONTESTED).

### 7. Rate limits
Tavily free tier ≈ 1,000 credits/mo; ~7–13 credits per fresh query. Keep search
concurrency ≤ ~10. Demo-time back-to-back topic switches are fine **because of
caching** — please run your `warm_cache.py` on the hero topics before the demo.
Use your `burst_test.py` to confirm the ceiling during setup (F7).

### 8. Deployment
Interim (in-process): stable, no URL. RocketRide URL: I'll give you local +
demo URLs once deployed; will confirm whether they're the same. Until then
`integration.run` is the stable seam.

---

## Example payloads (real output, offline fixture)

### ProvisionalVerdict
```json
{
  "verdict": "Likely true, scale disputed",
  "reasoning": "Multiple outlets report a ~5% Meta reduction, but leaked figures suggest the real scale may be higher.",
  "sources_so_far": 2
}
```

### FacetResult — `fact` (confirmed, F4 empty con)
```json
{
  "facet_id": "fact",
  "status": "confirmed",
  "summary": "2 sources support; no credible counter-evidence found",
  "pro_arguments": [
    {
      "claim": "Meta to cut roughly 5% of staff in performance-based reduction",
      "quote": "Meta Platforms said on Wednesday it would cut roughly 5% of its workforce.",
      "url": "https://reuters.com/business/tech/meta-workforce-reduction-2026",
      "source_domain": "reuters.com",
      "published_date": "2026-07-16",
      "quote_verified": true,
      "source_quality": "high",
      "stakeholder_kind": null,
      "stakeholder_name": null
    }
  ],
  "con_arguments": [],
  "sources_examined": 2,
  "quotes_verified": 2
}
```

### FacetResult — `stakeholder_reactions` (grassroots sub-bucket)
```json
{
  "facet_id": "stakeholder_reactions",
  "status": "disputed",
  "summary": "disputed (5 pro vs 2 con)",
  "pro_arguments": [
    {
      "claim": "Grassroots reaction (Reddit)",
      "quote": "5% official but recruiting and several infra teams look way more than 5% hit.",
      "url": "https://www.reddit.com/r/technology/comments/metalayoffs2026",
      "source_domain": "reddit.com",
      "published_date": null,
      "quote_verified": true,
      "source_quality": "low",
      "stakeholder_kind": "grassroots",
      "stakeholder_name": "u/pnw_dev"
    }
  ],
  "con_arguments": [ /* ... low-quality counter sources ... */ ],
  "sources_examined": 7,
  "quotes_verified": 7
}
```
(Full dumps for all 3 facets available on request / in the repo — run
`python -c "import asyncio,json; from prism.integration import run; ..."`.)

---

## Defaults I picked for fields I can't fully fill yet

Your contract has 3 `Argument` fields my pipeline doesn't natively produce.
I fill them heuristically now so you're unblocked; **Person B refines them** with
the real Judge logic. All are in `prism/integration.py` — easy to see/change.

| Field | My default | Owner of the real value |
|---|---|---|
| `source_domain` | derived from `url` (netloc, `www.` stripped) | final — no change needed |
| `source_quality` | static domain table: SEC/Reuters/Bloomberg/… = `high`; reddit/medium/substack/`*.example.com` = `low`; everything else = `medium` | **Person B** (F4 quality-weighted judgment) |
| `stakeholder_kind` | `stakeholder_reactions` facet only: Reddit-authored = `grassroots`, else `named`; other facets = `null` | mostly final; B may reclassify |
| `stakeholder_name` | grassroots = `u/<handle>`; named = `null` | **Person B** (extract the actual person/org, e.g. "CEO Zuckerberg") |

Note: `source_quality` is a **different axis** from my existing `source_bias`
(political lean). I did not conflate them — bias isn't in your contract, so I
dropped it; quality is what your synthesizer weights on.

---

## Two things I need from you / we need to agree

1. **Import path / package-name collision.** My pipeline package is `prism/`
   (repo root); your backend is `backend/prism/`. If we merge into one repo,
   **two packages named `prism`** will clash. Proposal: at merge time I rename my
   pipeline package (e.g. to `pipeline/`) or move it under `backend/`. Until then
   the interim import works if my repo root is on `PYTHONPATH`. Let's pick the
   final layout before we merge.
2. **Duplicated infra — let's dedupe.** We both built grounding, disk-cache,
   quote-verify, and a synthesizer. Per the design doc §7 those are yours; I'll
   drop mine (they were standalone-dev stubs). One flag: my quote-grep
   (`prism/quotecheck.py`) is a bit stricter than your `quote_verify.py` — it
   also splits on `...` and requires a 12-char minimum so a truncated/stitched
   quote can't falsely "verify". Since B's Judge calls this, let's agree on
   **one** implementation (I'd keep the stricter one). Your call.

---

## Import note (interim)

Until we settle the package layout (#1 above), to import my adapter from your
`backend/`:
```bash
# from repo root, with my pipeline repo/dir on the path
export PYTHONPATH="/path/to/prism-pipeline-root:$PYTHONPATH"
```
Then `from prism.integration import run` resolves. Once merged + renamed this
becomes a normal intra-repo import.

---

## What's still pending (not blocking you)

- **RocketRide deploy (F2)** — mine; swaps `integration.run` internals to real
  invoke. Your `real_pipeline.py` is unaffected.
- **Real `source_quality` / `stakeholder_name`** — Person B.
- **Live-mode timing numbers** — I'll confirm once we run against real Tavily
  (offline is instant so the §5 numbers are estimates).

Ping me and I'll walk you through wiring `real_pipeline.py` — should be the
~30–60 min you estimated, probably less since the shapes already match.
