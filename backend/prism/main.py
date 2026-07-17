"""FastAPI application exposing the frontend-compatible named SSE stream."""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .cache import cache_stats, clear_cache
from .pipeline_router import run_pipeline
from .schema import AnalyzeRequest, FacetResult, ProvisionalVerdict
from .settings import get_settings
from .synthesizer import synthesize
from .ui_stream import CumulativeCounts, done_event, facet_event, final_event, provisional_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Prism backend starting — pipeline_mode=%s", settings.pipeline_mode)
    yield
    logger.info("Prism backend shutting down")


app = FastAPI(title="Prism Backend", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "pipeline_mode": settings.pipeline_mode}


@app.get("/cache/stats")
async def get_cache_stats():
    return cache_stats()


@app.post("/cache/clear")
async def clear_all_cache():
    if not settings.is_development:
        raise HTTPException(status_code=403, detail="Cache clearing is disabled")
    clear_cache()
    return {"status": "cleared"}

def _named_event(name: str, payload: dict) -> dict[str, str]:
    return {"event": name, "data": json.dumps(payload, separators=(",", ":"))}


def _stream(topic: str, req: Request) -> EventSourceResponse:
    request_id = uuid.uuid4().hex[:8]

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        facets: list[FacetResult] = []
        counts = CumulativeCounts()
        try:
            if await req.is_disconnected():
                return
            async for item in run_pipeline(topic):
                if await req.is_disconnected():
                    logger.info("[%s] client disconnected", request_id)
                    return
                if isinstance(item, ProvisionalVerdict):
                    yield _named_event("provisional", provisional_event(topic, item))
                elif isinstance(item, FacetResult):
                    facets.append(item)
                    yield _named_event("facet", facet_event(item))
                    if await req.is_disconnected():
                        return
                    yield _named_event("counts", counts.add(item))

            if await req.is_disconnected():
                return
            if not facets:
                raise RuntimeError("pipeline returned no facets")
            yield _named_event("final", final_event(synthesize(facets)))
            if not await req.is_disconnected():
                yield _named_event("done", done_event())
        except Exception:
            logger.exception("[%s] analysis failed", request_id)
            if not await req.is_disconnected():
                yield _named_event("error", {"type": "error", "message": "Analysis failed"})

    return EventSourceResponse(
        event_generator(),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/analyze")
async def analyze(body: AnalyzeRequest, req: Request):
    return _stream(body.topic, req)


@app.get("/analyze")
async def analyze_event_source(req: Request, claim: str = Query(..., min_length=1, max_length=500)):
    """EventSource-compatible form used by the current frontend."""
    return _stream(claim, req)
