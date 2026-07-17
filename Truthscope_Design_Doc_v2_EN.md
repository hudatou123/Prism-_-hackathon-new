# Truthscope Design Doc v2

> **HackwithSeattle 2.0 · Track 1 (Live Fact-Checking) · 6-Hour Sprint · Team of 4**
>
> **v2 note:** This is the original design doc with review fixes folded in. Every change is marked with a 🔧 callout explaining what changed and why. Unmarked text is unchanged from v1.

---

## Changelog at a Glance

| # | Change | Where it lands |
|---|--------|----------------|
| CH0 | **Linkup removed** (no credits; hosts waived the requirement) → free pluggable grounding stack | §5, everywhere Linkup appeared |
| F1 | Provisional verdict kills the demo dead-air problem | §3, §6, §8, §11 |
| F2 | Hour-zero Cloud deploy + streaming spike | §6, §10 |
| F3 | Quote-grep verification in the Judge | §6, §8, §9 |
| F4 | Asymmetric Con contract, no manufactured false balance | §6, §9 |
| F5 | Fixed facet taxonomy; Sentiment → Stakeholder Reactions (split into Named + Grassroots sub-buckets) | §5, §6, §8 |
| F6 | Transparent confidence instead of a mystery percentage | §8 |
| F7 | Search budget plan: caching, burst test, backup keys | §5, §10 |
| F8 | Media bias tags: static lookup table or cut | §8 |
| F9 | Source counts must be real numbers | §8 |
| F10 | Name recommendation: Prism | §12 |
| T1 | Team rebalanced to 4 equal engineering tracks (pipeline split across A + D; no standalone demo role) | §7, §10, §12 |

---

## 1. One-Liner

Truth isn't binary. It's a tree you can zoom into. Truthscope gives you the verdict in one line, or the full depth in one click.

---

## 2. The Problem

Every controversial claim online today collapses into a single answer: "true" or "false", "left" or "right", a headline or a hot take. But real controversies are **multi-layered**:

- A company **did** lay people off (fact), but the **scale** is disputed, the **motive** is contested, and **public sentiment** is polarized.
- Existing fact-checkers give you *one* verdict. LLMs hallucinate whole citations. Neither shows you the **shape** of the disagreement.

---

## 3. The Concept

### Progressive Disclosure of Truth

Truth should behave like Google Maps: one zoom level shows you the country, another shows you the street, another shows you the door number. Truthscope applies this to fact-checking:

- **Level 0 — Verdict:** A one-line conclusion. Appears in two stages: a **provisional verdict within seconds**, replaced by the **final synthesized verdict** once all facets resolve.
- **Level 1 — Facets:** The controversy broken into orthogonal layers, each with its own status.
- **Level 2 — Debate:** For any facet, a Pro-Agent vs Con-Agent showdown, split-screen, with arguments on both sides.
- **Level 3 — Evidence:** For any argument, the raw quote, source URL, timestamp, and verification status. Every claim traceable to a live web source.

**Each level is a complete answer on its own.** Want the TL;DR? Stop at Level 0. Want to verify? Drill to Level 3.

> 🔧 **F1 · Provisional verdict**
> **Was:** Level 0 only rendered after the entire facet tree resolved, meaning judges type a query and stare at a spinner for 60+ seconds while decomposer → search → Pro/Con → Judge → synthesizer all complete in sequence.
> **Now:** A fast path fires immediately on input: one cheap search + one fast LLM call produce a provisional verdict on screen in roughly 2-4 seconds, badged "Preliminary, verifying...". Facets stream in as they resolve, and the final synthesized verdict replaces the provisional one with a visible swap.
> **Why:** The demo script promised streaming that the v1 architecture couldn't deliver. This turns latency into a visible "the system is working" moment instead of dead air, and the provisional→final swap is itself a nice honesty beat: watch the system upgrade its own answer as evidence lands.

---

## 4. Why This Wins the Hackathon

| Judging Criterion | How Truthscope Satisfies It |
|---|---|
| **Grounded / cited output** | Every argument at Level 2 is backed by a live URL, and every quote is mechanically verified against the fetched page text. No URL, no argument. No matching quote, no argument. |
| **Deep grounding integration** | 8-14 live web calls per query (fast path + facets × Pro/Con + page fetches), behind a pluggable search interface. |
| **Deep RocketRide integration** | True multi-agent tree (Decomposer → Facet × N → Pro/Con/Judge × N); observability is a real feature, not decoration. |
| **Fancy demo moment** | Verdict in seconds, then the facet spectrum streams in live. Judges can throw any controversy at it. |
| **Clear business value** | Media, journalism, research, corporate comms, policy: a universal tool for the post-truth internet. |

> 🔧 **CH0 note on judging**
> The written rules made Linkup mandatory, but the hosts have waived it for teams without credits. Action items: (1) screenshot that host announcement in case a judge hasn't gotten the memo, (2) keep the cited-output bar exactly as high as before, because grounding is still the theme being scored, and (3) mention in the pitch that the grounding layer is vendor-agnostic by design. "Our sponsor API ran out of credits and we swapped search providers without touching agent logic" is a resilience story, not an apology.

---

## 5. Grounding Layer (replaces Linkup)

> 🔧 **CH0 · Linkup → free pluggable stack**
> **Was:** All web grounding ran through Linkup Search + Fetch.
> **Now:** A thin provider-agnostic interface, with free-tier providers behind it.
> **Why:** No Linkup credits, and the hosts confirmed it's not required. Everything the design needed from Linkup (search with URLs, page content for verification) is available free.

### The interface

All agents call these two functions and never know which provider is underneath:

```python
search(query: str) -> list[{url, title, snippet, published_date?}]
fetch(url: str)    -> clean_page_text
```

### Providers

| Layer | Primary | Fallback |
|---|---|---|
| `search()` | **Tavily** free tier: 1,000 API credits/month, no credit card, basic search = 1 credit. Each teammate creates a key, so 4,000 credits available worst case. | Brave Search API free tier (verify current limits during setup), or the LLM provider's native web-search tool on the fast model. |
| `fetch()` | **httpx + trafilatura**: plain HTTP GET plus article-text extraction. No API, no key, no credits. | Tavily's extract endpoint (cheap in credits) for pages that resist plain fetching. |

### Grassroots source (for F5's grassroots sub-bucket)

The grassroots half of Stakeholder Reactions pulls from **Reddit's public JSON**: append `.json` to a thread or search URL to get structured comment data (author handle, score, permalink) with no key and no credits. `search()` scoped to `reddit.com` finds relevant threads; `fetch()` on the thread's `.json` returns the top comments to display. Set a descriptive User-Agent and validate rate limits during the F7 burst test, same as any other provider. If Reddit read access is flaky at the venue, this sub-bucket degrades gracefully to news-only stakeholder reactions rather than failing the facet.

### Budget math

MVP query cost: 1 fast-path search + 3 facets × (Pro 1-2 + Con 1-2 searches) ≈ **7-13 search credits per fresh query**, plus free fetches. The free tier covers 70+ fresh full queries even before teammate backup keys. This is not a real constraint if dev-time caching is in place (below).

### Caching (do this in setup, not later)

- **Dev cache:** every `search()` and `fetch()` result cached to disk, keyed by normalized query / URL. Prompt tuning then costs **zero** credits and runs instantly.
- **Demo safety net:** pre-warm the cache with the 3-5 hero topics. If conference wifi or the search API dies mid-demo, the pipeline transparently serves cached evidence and the demo still runs. This upgrades the "backup video" safety net to a live fallback.

> 🔧 **F7 · Budget discipline**
> **Was:** "Test Linkup rate limits" scheduled at hour 2.
> **Now:** Burst-test the search provider (10 parallel calls, measure latency and rate limits) during setup in the first 45 minutes, stand up the cache harness at the same time, and hold backup keys from teammates.
> **Why:** The pipeline fires 6-10 concurrent searches per query. Discovering a rate ceiling at hour 2, mid-build, costs far more than discovering it at minute 20. And prompt iteration against live search is the single biggest silent credit burner on any team; the cache eliminates it entirely.

---

## 6. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     USER INPUT                            │
│   "Did Meta really lay off 5% of its workforce?"          │
└──────────────────────────────────────────────────────────┘
        │
        ├────────────► FAST PATH (fires immediately)                [F1]
        │              search() top results → fast LLM
        │              → PROVISIONAL Level 0 verdict in ~2-4s
        │                badge: "Preliminary · verifying..."
        ▼
┌───────────────────────────────┐
│  Layer Decomposer (Agent #1)  │
│  · writes facet-specific      │
│    queries for the FIXED      │
│    facet set                  │                            [F5]
│  · settled-fact detector:     │
│    non-controversies short-   │
│    circuit to a single        │
│    confirm/refute lane        │                            [F4]
└───────────────────────────────┘
        │
   ┌────┴─────┬──────────────┐
   ▼          ▼              ▼
[Fact]     [Scale]   [Stakeholder Reactions]    ← fixed 3 for MVP
   │  each facet, in parallel:
   ├─ Pro Agent   — search()+fetch() → supporting evidence,
   │                URL required on every claim
   ├─ Con Agent   — search()+fetch() → STRONGEST verified
   │                counter-evidence, or an explicit
   │                "no credible counter-evidence found"     [F4]
   └─ Judge Agent — provenance check
                    + QUOTE-GREP vs fetched page text        [F3]
                    + source-quality-weighted facet verdict
        │
        ▼
┌───────────────────────────────┐
│  Verdict Synthesizer          │
│  → FINAL Level 0, replaces    │
│    the provisional verdict    │                            [F1]
└───────────────────────────────┘
        │
        ▼
   Streams to frontend as each stage lands
```

> 🔧 **F5 · Fixed facet taxonomy, and Sentiment becomes Stakeholder Reactions**
> **Was:** The decomposer invented 3-5 facets per topic, and one of them was aggregate "Sentiment."
> **Now:** The facet set is fixed (MVP: Fact, Scale, Stakeholder Reactions). The decomposer's only job is writing good facet-specific search queries. "Stakeholder Reactions" means what named parties publicly said, each statement quoted and linked: CEO memo, employee posts, analyst notes.
> **Why:** A freeform decomposer is an extra failure surface and makes demos inconsistent; a fixed set is reliable and few-shottable in twenty minutes. And aggregate sentiment ("the public is angry") is unfalsifiable, which is a terrible look inside a tool whose entire pitch is groundability. Named statements with URLs keep the visual richness while staying checkable.
>
> **Review refinement (v2):** Split Stakeholder Reactions into two sub-buckets rather than one flat list:
> - **Named stakeholders** (from news): CEO memo, analyst notes, employee statements. Each quoted and linked.
> - **Grassroots reactions** (from Reddit): the top-voted comments on the topic, each shown with author handle and permalink.
>
> Rationale: F5 as originally written kept groundability but flattened the "media narrative vs public reaction" contrast, which was one of our differentiated angles. Splitting the facet restores that contrast while every item on both sides still carries a quote and a live link, so the checkability F5 bought us is untouched. This adds Reddit as a source in §5.

> 🔧 **F4 · No manufactured false balance**
> **Was:** Pro and Con agents were perfectly symmetric: both instructed to find evidence for their side.
> **Now:** Three changes. The Con agent's contract is "find the strongest *verified* counter-evidence, or explicitly report that none credible exists," and that empty report renders in the UI as a positive finding. The Judge weighs source quality, not argument count, so two SEC filings beat five anonymous posts. The decomposer detects settled facts and routes them down a single confirm/refute lane with no debate theater.
> **Why:** Prompt an agent to oppose a settled fact and it will dredge up fringe sources, making "Confirmed" things look "Disputed." Human judges will probe exactly this ("try it on something obviously true"), and v1 would have failed that probe.

### Streaming: decide by minute 45

> 🔧 **F2 · Streaming spike + hour-zero deploy**
> **Was:** "How does RocketRide stream to the frontend?" was an open question checked "first thing," but Cloud deployment was scheduled at 3:30, so a bad answer would be discovered with the concept already built around it.
> **Now:** Two spikes in the first 45 minutes. (a) Deploy a trivial hello-world .pipe to RocketRide Cloud immediately, before any real logic exists. (b) Determine whether a deployed pipeline can emit intermediate results.
> **Plan A** if yes: one pipeline, native streaming.
> **Plan B** (default assumption): one small .pipe per facet plus one for the fast path. A thin backend (FastAPI) invokes them in parallel through the SDK/webhook source nodes and streams SSE to the frontend as each resolves. All agent logic stays inside RocketRide, so integration depth and observability survive; only the fan-out glue lives outside.
> **Why:** "Facets stream in one by one" is the demo. If the deployed pipeline only returns one final payload and the team learns that at hour four, the demo concept dies. Plan B is also independently attractive: per-facet pipelines give per-facet traces, which makes the observability story cleaner on screen.

### Deployment

- **RocketRide Cloud** hosts every pipeline. Hello-world deployed by minute 45 (CH0/F2), full system redeployed by 4:30 over an already-proven path. Local dev in the VS Code extension throughout.
- **Grounding** via the §5 stack, called from custom Python nodes.
- **First 15 minutes:** check RocketRide's node catalog for a native web-search or HTTP node. If one exists, prefer it (deeper platform integration, one less custom node); if not, the custom Python node plan stands.

---

## 7. Team Split (4 People)

> 🔧 **Team refinement (v2): four equal engineering tracks.** The old standalone "Integration/Demo Lead" is gone. All four people now carry a roughly equal engineering load, and the pipeline (previously one person's job) is split across two. **Person A owns the front of the pipeline plus deployment; Person D owns the back of the pipeline plus the streaming/integration seam.** Person B (prompting) and Person C (UI) are unchanged in scope. The non-code demo work the old Person D absorbed (backup video, slide deck, rehearsal) becomes a shared all-hands push in the final block. See §12 for who pitches.
>
> Clean seams between the two pipeline halves: A's fan-out emits per-facet verdicts, D's synthesizer consumes them (schema agreed at hour 0); D's SSE backend streams both facet results and the final verdict to C's UI.

### 👤 Person A — Pipeline & Deployment
**Owns:** Front of the pipeline (input → decompose → fan-out) + RocketRide Cloud deployment
- 🔧 **Minute 0:** hello-world .pipe deployed to Cloud; run the streaming spike; lock Plan A vs Plan B by minute 45 (F2). Check the node catalog for a native search node.
- Build Layer Decomposer (fixed facets + settled-fact detector) (F5, F4)
- Wire the fast path / provisional verdict (F1)
- Build the parallel facet-execution scaffold: fan out to 3 facets, each running Pro/Con/Judge
- 🔧 Own the full redeploy to Cloud by 4:30 over the proven path (with Person D)

### 👤 Person B — Agent/Prompt Engineer
**Owns:** Pro/Con/Judge design + grounding calls
- Design Pro-Agent prompt (URL required on every claim)
- 🔧 Design Con-Agent with the asymmetric contract: strongest verified counter-evidence or explicit "none found" (F4)
- 🔧 Implement the Judge's quote-grep: deterministic normalized substring match against fetched page text, no LLM involved (F3)
- Judge scoring weighted by source quality, not count (F4)
- 🔧 Reddit grassroots fetch + top-comment extraction for the Stakeholder Reactions grassroots sub-bucket (F5)
- Handle "no evidence found" as a first-class honest output

### 👤 Person C — Frontend Lead
**Owns:** The zoomable UI, the visual "wow"
- 🔧 Level 0 verdict card with provisional → final states and the swap animation (F1)
- Level 1 facet spectrum (animated status pills, streaming in)
- Level 2 split-screen debate view (Pro left, Con right, tilting scale)
- Level 3 evidence modal (quote + URL + verified badge)
- 🔧 Render the real source/quote counts fed from the backend (F9, UI side)

### 👤 Person D — Synthesis, Streaming & Integration
**Owns:** Everything after fan-out: aggregation, the streaming seam, and end-to-end wiring
- 🔧 **Minute 0 setup:** search-provider burst test, cache harness, backup API keys from teammates (F7); agree the facet/verdict schema with Person A
- Build the Verdict Synthesizer (aggregates facet verdicts → final Level 0) and the F6 confidence formula
- 🔧 Stand up the FastAPI backend + per-facet .pipe invocation + SSE fan-out to the frontend (Plan B)
- 🔧 Plumb real counts backend-side: sources examined, quotes verified (F9)
- End-to-end integration (pipeline ↔ backend ↔ frontend); pre-warm the demo cache (F7)

---

## 8. UI Levels Detail

### Level 0 — Verdict Card (two states)

```
┌────────────────────────────────────────────────────┐
│  "Meta laid off ~5% of its workforce"              │
│                                                    │
│  ⏳ PRELIMINARY · verifying across 3 facets...     │
│  Early read: Likely true, scale disputed           │
│  Sources so far: 4                                 │
└────────────────────────────────────────────────────┘
                    ↓ facets resolve, card swaps
┌────────────────────────────────────────────────────┐
│  Verdict: MOSTLY TRUE — scale disputed             │
│  Confidence: HIGH                                  │
│    2/3 facets confirmed · 9 of 11 quality          │
│    sources agree                                   │
│  Sources examined: 11 · Quotes verified: 6/6 ✓     │
│                                                    │
│  [ Zoom in ↓ ]                                     │
└────────────────────────────────────────────────────┘
```

> 🔧 **F6 · Transparent confidence**
> **Was:** "Confidence: 78%", an unexplained number.
> **Now:** A qualitative band (High / Moderate / Low / Contested) derived from a formula anyone can audit, displayed *with its inputs*: per-facet scores plus the source-agreement ratio among quality-weighted sources. Facet scores are:
> - **Confirmed** = 1.0
> - **Mostly confirmed** = 0.75
> - **Disputed** = 0.5
> - **Refuted** = 0
> - **Unclear** = excluded from the average, displayed as "insufficient data"
>
> Confidence is the average of the *scored* facets, so an Unclear facet lowers coverage (fewer facets resolved) without dragging the score itself.
> **Why:** In a grounding-themed hackathon, "what does 78% mean?" is a guaranteed judge question, and "the model felt 78%" loses the room. Showing the inputs makes confidence itself a grounded claim.
>
> **Review refinement (v2):** The earlier draft scored both Disputed and Unclear at 0.5, which is semantically wrong. Disputed means both sides brought quality evidence and genuinely conflict; Unclear means neither side found quality evidence. Those are opposite situations and shouldn't land on the same number. Unclear is now pulled out of the average entirely and shown as "insufficient data," and a Mostly-confirmed tier (0.75) fills the gap between a fully nailed-down fact and a live dispute.

> 🔧 **F9 · Real counts only**
> "Sources examined: 24" must be an actual counter over search results processed, and "Quotes verified: 6/6" an actual counter over grep passes. Someone will ask. Decorative numbers in a truth tool are self-immolation.

### Level 1 — Facet Spectrum (fixed 3 for MVP, per F5)

```
📌 Fact                    🟢 Confirmed   (7 sources agree)
📊 Scale                   🟡 Disputed    (5% filing vs 8-10% leak)
🗣️ Stakeholder Reactions   🟡 Split       Named:      CEO memo, analyst notes
                                          Grassroots: top Reddit comments
                                          (both sides quoted + linked)
```
Each row clickable → opens Level 2.

### Level 2 — Debate Split-Screen

```
Facet: Scale                                     ⚖️
┌────────────────────┬────────────────────┐
│ PRO (5% official)  │  CON (higher est.) │
│ ─────────────────  │  ─────────────────  │
│ • Company filing   │  • Insider leak    │
│   states 5%     ▶  │    claims 8-10% ▶  │
│                    │                    │
│ • CEO memo         │  • Layoff tracker  │
│   confirms 5%   ▶  │    logs 4,200 ▶    │
└────────────────────┴────────────────────┘
```
Each `▶` opens Level 3. Note: under F4, a Con column may legitimately render **"No credible counter-evidence found ✓"** and that is a feature, not an empty state.

### Level 3 — Evidence Detail

```
┌────────────────────────────────────────────────┐
│  💬 "We are reducing our workforce by          │
│      approximately 5% across affected teams."  │
│                                                │
│  🔗 reuters.com/business/tech/... [Open]       │
│  📅 3 hours ago                                │
│  ⚖️  Source bias: Center (lookup table)        │
│  ✅ Quote verified: exact match found in       │
│     fetched page text                          │
└────────────────────────────────────────────────┘
```

> 🔧 **F3 in the UI**
> The badge changed from "URL confirmed" to "Quote verified: exact match found in fetched page text." The URL check proved the link was real; this proves the *words* are real. See §9.

> 🔧 **F8 · Bias tags**
> **Was:** "Media bias" tag of unspecified origin, implicitly LLM-judged.
> **Now:** A hand-made static lookup table (~30 major domains → Left/Center/Right labels) or cut the feature. It stays in stretch scope.
> **Why:** An LLM-generated bias label is an unsourced claim living inside a product whose entire premise is that claims need sources.

---

## 9. Anti-Hallucination Design

This is the technical hard part. Five defenses, layered:

1. **URL-required prompt contract.** Pro/Con agents cannot state any claim without attaching a URL returned by `search()`. Claims without URLs are dropped by the Judge.
2. **Provenance check.** The Judge confirms each cited URL actually appeared in the search results for that facet's queries. Necessary, but not sufficient, which is why:
3. **Quote-grep verification.** The Judge fetches the page and runs a deterministic, normalized substring match of the quoted text against the page content. No match, argument dropped. No LLM in the loop for this step.
4. **No manufactured balance.** Asymmetric Con contract, quality-weighted judging, settled-fact short-circuit (F4).
5. **"No evidence" is an honest answer.** If a side genuinely can't find support, the UI says so rather than fabricating. This *increases* trust.

> 🔧 **F3 · Why quote-grep replaced URL-checking as the centerpiece**
> **Was:** Defense 2 was the last line: "was this URL actually in the search response?"
> **Now:** Defense 3 exists and is the star.
> **Why:** URL verification only proves the agent copied a real link. The actual failure mode of LLM fact-checkers, the one this product is pitched against, is attaching a *fabricated quote* to a *genuine URL*. A substring match over fetched page text catches exactly that, deterministically, for free. It also produces the best line in the pitch: **"We don't ask a model whether the quote is real. We grep the page for it."**

---

## 10. 6-Hour Timeline

| Time | Person A (Pipeline & Deploy) | Person B (Agents/Prompting) | Person C (Frontend/UI) | Person D (Synthesis/Streaming/Integration) |
|------|------------------------------|-----------------------------|------------------------|---------------------------------------------|
| 0:00-0:45 | 🔧 Hello-world .pipe **deployed to Cloud**; streaming spike; lock Plan A/B (F2). Check node catalog for native search node. | Accounts + keys; first Pro prompt drafted against cached sample data | Wireframe; provisional/final card states designed (F1) | 🔧 Search burst test, cache harness, backup keys (F7); agree facet/verdict schema with A |
| 0:45-2:00 | 🔧 **~1:00: 10-min all-hands to pick the 5 hero topics** (see note), then Decomposer (fixed facets + settled-fact path) + fast path (F1) + fan-out scaffold | Pro/Con/Judge working for **one** facet, quote-grep included (F3) | Level 0 + Level 1 live against mock SSE | FastAPI backend + SSE glue skeleton (Plan B); API contract with A |
| 2:00-3:30 | Fan out to 3 parallel facets | Judge scoring (quality-weighted) + Con asymmetric tuning (F4); Reddit grassroots fetch (F5) | Level 2 split-screen | Verdict Synthesizer + F6 confidence; wire real pipeline → frontend over SSE |
| 3:30-4:30 | **Full redeploy to RocketRide Cloud** over the proven path (with D) | Prompt tuning on hero topics (cached, zero credits) | Level 3 modal + streaming polish; wire real counts display (F9) | Expose real counts (F9); end-to-end test against the deployed cloud pipeline |
| 4:30-5:15 | Bug fixes + observability screenshots | Edge cases | Polish animations, one hero interaction | Pre-warm demo cache; integration hardening |
| 5:15-5:45 | 🔧 **All hands: record backup demo video, finalize pitch deck, rehearse** (pitcher leads; no new features) |
| 5:45-6:00 | All hands: final rehearsal, buffer |

> 🔧 **Timeline refinement (v2):** **Hero-topic selection is a ~10-minute all-hands right after the first hour** (inside the 0:45-2:00 block), not a solo task in anyone's setup window. By hour one everyone has enough of the pipeline in hand to judge what will actually demo well, and choosing the five topics then still leaves plenty of runway for the cache pre-warm and rehearsals later. The final 45 minutes (5:15 on) is a shared demo-prep push, not feature work.

### ⚠️ Non-negotiables (updated)

- 🔧 **Hello-world deployed to Cloud by 0:45**, and the streaming Plan A/B decision locked at the same time. Deployment surprises get discovered when they're cheap. (F2)
- **Full redeploy by 4:30**, not later.
- **Backup video by 5:45**, no exceptions. Live networks fail. The pre-warmed demo cache (F7) is the second safety net.
- **MVP scope = 3 facets, not 5.** Add more only if time remains.
- **One hero demo that always works** beats five that sometimes work.

---

## 11. Demo Script

**Opening (15 sec):**
> "LLMs hallucinate. Fact-checkers give binary answers. But real controversies aren't binary, they're layered. So we built Truthscope: an adversarial fact-checker you can zoom into, at any depth."

**Live demo (90 sec):**
1. Type a fresh, real controversy from today's news.
2. 🔧 **Provisional verdict appears in ~3 seconds** with the "verifying..." badge. No dead air. (F1)
3. Level 1 facets stream in one by one; the final verdict **swaps in over the provisional one** (visual moment).
4. Click the disputed facet: split-screen debate appears.
5. Click a Pro argument: Level 3 shows the quote, the **"exact match found in page text ✓"** badge, and the live URL. **Click the URL**, the real article opens.

**Closing (15 sec):**
> 🔧 "Every claim you saw is tied to a live source, and we don't ask a model whether a quote is real, we grep the fetched page for it. Every agent ran as an observable pipeline on RocketRide Cloud. This isn't a script, it's production. Try one yourself."

*[Invite judges to give a topic. The settled-fact path (F4) means even a softball like "is the earth round" demos cleanly instead of generating fake debate.]*

---

## 12. Open Questions → Mostly Resolved

1. ~~Which 3 facets for MVP?~~ **Locked: Fact + Scale + Stakeholder Reactions** (F5), with Stakeholder Reactions split into Named (news) and Grassroots (Reddit) sub-buckets.
2. **Frontend framework?** Next.js + Tailwind + Framer Motion stands.
3. ~~How does RocketRide stream to the frontend?~~ **The minute-45 spike decides Plan A vs Plan B** (F2). Plan B is the default assumption; build the frontend against SSE either way.
4. **Who pitches?** 🔧 No dedicated demo role now, so this is a team call. Natural candidates: Person C (knows the zoom flow cold) or Person D (wired the end-to-end path). Lock it by 4:30 so the pitcher gets real rehearsal reps.
5. **Name?**

> 🔧 **F10 · Prism**
> Recommendation: rename to **Prism**. Level 1 is literally called a facet *spectrum*; one input splitting into its component wavelengths is the entire product in a single image. "Truthscope" sounds like a 2019 browser extension. Team's call, and now is the cheapest moment to make it.
>
> **Review refinement (v2):** One flag worth a quick team vote before we commit. "PRISM" is also the NSA mass-surveillance program, and for a transparency and source-checking product that association cuts both ways: it's either a sharp opening joke ("not that PRISM") or a subtle wrong-foot with judges. If the room isn't sold on owning that, the same wavelength/spectrum metaphor survives under **Facet**, **Spectrum**, or **Lens**. Pick one by show of hands and move on.

---

## 13. Success Criteria

Minimum viable win:
- [ ] Hello-world pipeline on RocketRide Cloud by 0:45; full system deployed by 4:30 (not local)
- [ ] 🔧 Provisional verdict on screen in under 5 seconds (F1)
- [ ] ≥ 6 live web searches per fresh query (3 facets × Pro/Con) through the pluggable grounding layer (CH0)
- [ ] Every displayed claim has a clickable, working source URL
- [ ] 🔧 Every displayed quote passes the page-text grep, and the UI shows it (F3)
- [ ] Level 0 → 1 → 2 → 3 zoom flow works end-to-end for ≥ 1 topic
- [ ] Backup demo video recorded, demo cache pre-warmed

Stretch:
- [ ] 5 facets instead of 3
- [ ] Source bias tag via static lookup table (F8)
- [ ] Judges can input a live topic and it works
- [ ] Observability dashboard shown briefly during pitch (per-facet traces under Plan B)

---

**Let's ship it.**
