"""Streaming orchestrator — Person A's fan-out scaffold.

This is the front-of-pipeline glue A owns. It is an async generator of
StreamEvents in RESOLUTION order — provisional first, each facet as it lands,
final last — which is precisely what Person D's FastAPI/SSE layer forwards to
the frontend (StreamEvent.sse()). Plan B (per-facet .pipe invoked in parallel)
maps onto this directly; Plan A (one native-streaming pipe) would emit the same
events from inside RocketRide.

Flow (F1 + F5 + F4):
  t0  ── fast path + decompose fire concurrently
  ~3s ── PROVISIONAL verdict yielded (dead-air killer)
      ── DECOMPOSED yielded (facet queries ready)
      ── 3 facets fan out in parallel; FACET_RESOLVED yielded as each finishes
      ── FINAL verdict yielded (the swap)
      ── DONE
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional

from .agents.decomposer import decompose
from .agents.fast_path import provisional_verdict
from .agents.procon_judge import FacetAgent, default_facet_agent
from .config import FIXED_FACETS
from .grounding import get_grounding
from .grounding.interface import Grounding
from .schemas import (
    Decomposition,
    EventType,
    FacetVerdict,
    StreamEvent,
)
from .synthesizer import synthesize

_FACET_BY_KEY = {f.key: f for f in FIXED_FACETS}


async def run_pipeline(
    claim: str,
    grounding: Optional[Grounding] = None,
    facet_agent: Optional[FacetAgent] = None,
) -> AsyncIterator[StreamEvent]:
    """Yield StreamEvents as the tree resolves. The one entry point D consumes."""
    own_grounding = grounding is None
    grounding = grounding or get_grounding()
    facet_agent = facet_agent or default_facet_agent()

    try:
        # --- fire fast path + decompose concurrently (F1) ------------------
        fast_task = asyncio.create_task(provisional_verdict(claim, grounding))
        decomp_task = asyncio.create_task(decompose(claim))

        # Provisional lands first and is emitted the instant it's ready.
        provisional = await fast_task
        yield StreamEvent(type=EventType.PROVISIONAL, provisional=provisional)

        decomposition: Decomposition = await decomp_task
        yield StreamEvent(type=EventType.DECOMPOSED, decomposition=decomposition)

        # --- fan out facets in parallel, emit as each resolves ------------
        facets: List[FacetVerdict] = []
        async for event in _fan_out(decomposition, grounding, facet_agent):
            if event.type == EventType.FACET_RESOLVED and event.facet:
                facets.append(event.facet)
            yield event

        # --- final synthesized verdict (F1 swap) --------------------------
        final = synthesize(claim, facets)
        yield StreamEvent(type=EventType.FINAL, final=final)
        yield StreamEvent(type=EventType.DONE)

    except Exception as exc:  # never leave the stream hanging — D needs a terminal event
        yield StreamEvent(type=EventType.ERROR, message=f"{type(exc).__name__}: {exc}")
    finally:
        if own_grounding:
            await grounding.aclose()


async def _fan_out(
    decomposition: Decomposition,
    grounding: Grounding,
    facet_agent: FacetAgent,
) -> AsyncIterator[StreamEvent]:
    """Run all facets concurrently; surface each result the moment it lands.

    Uses a queue so a slow facet never blocks a fast one from streaming in —
    this is the "facets stream in one by one" demo beat.
    """
    queue: "asyncio.Queue[StreamEvent]" = asyncio.Queue()

    async def worker(fq):
        facet_def = _FACET_BY_KEY[fq.facet_key]
        await queue.put(StreamEvent(type=EventType.FACET_STARTED, facet_key=fq.facet_key))
        try:
            verdict = await facet_agent.run(
                facet_def, fq, grounding, settled=decomposition.settled_fact
            )
            await queue.put(
                StreamEvent(
                    type=EventType.FACET_RESOLVED,
                    facet_key=fq.facet_key,
                    facet=verdict,
                )
            )
        except Exception as exc:
            # One facet failing must not kill the tree (§10 resilience).
            await queue.put(
                StreamEvent(
                    type=EventType.ERROR,
                    facet_key=fq.facet_key,
                    message=f"facet {fq.facet_key} failed: {exc}",
                )
            )

    workers = [asyncio.create_task(worker(fq)) for fq in decomposition.facet_queries]

    # Drain the queue until every worker has finished.
    pending = len(workers)
    started = 0
    resolved = 0
    while resolved < pending:
        event = await queue.get()
        if event.type == EventType.FACET_STARTED:
            started += 1
        elif event.type in (EventType.FACET_RESOLVED, EventType.ERROR):
            resolved += 1
        yield event

    await asyncio.gather(*workers, return_exceptions=True)
