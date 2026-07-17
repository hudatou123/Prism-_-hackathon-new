"""
FastAPI + SSE Backend — streaming seam between pipeline and frontend.
"""

import os
import uuid
import logging
from typing import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .schema import AnalyzeRequest, ProvisionalVerdict, FacetResult, SSEEvent
from .pipeline_router import run_pipeline, PIPELINE_MODE
from .synthesizer import synthesize
from .cache import cache_stats, clear_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events."""
    logger.info(f"Prism backend starting — pipeline_mode={PIPELINE_MODE}")
    yield
    logger.info("Prism backend shutting down")


app = FastAPI(
    title="Prism Backend",
    description="Live fact-checking agent — Person D's ownership",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS (hackathon scope — allow all)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "pipeline_mode": PIPELINE_MODE
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """Return cache statistics."""
    return cache_stats()


@app.post("/cache/clear")
async def clear_all_cache():
    """Clear all caches (dev only)."""
    clear_cache()
    return {"status": "cleared"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest, req: Request):
    """
    SSE stream endpoint. Yields:
    - provisional_verdict (within ~3s)
    - facet_ready × 3 (as each resolves)
    - final_verdict (computed after all facets)
    - done
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Analyzing topic: {request.topic}")

    async def event_generator() -> AsyncIterator[dict]:
        try:
            # Collect facets as they arrive
            collected_facets = []

            async for item in run_pipeline(request.topic):
                if isinstance(item, ProvisionalVerdict):
                    logger.info(f"[{request_id}] Provisional verdict ready")
                    yield {
                        "event": "provisional_verdict",
                        "data": item.model_dump_json()
                    }
                elif isinstance(item, FacetResult):
                    logger.info(f"[{request_id}] Facet ready: {item.facet_id}")
                    collected_facets.append(item)
                    yield {
                        "event": "facet_ready",
                        "data": item.model_dump_json()
                    }

            # Synthesize final verdict
            if collected_facets:
                logger.info(f"[{request_id}] Synthesizing final verdict from {len(collected_facets)} facets")
                final_verdict = synthesize(collected_facets)
                yield {
                    "event": "final_verdict",
                    "data": final_verdict.model_dump_json()
                }
            else:
                logger.warning(f"[{request_id}] No facets collected, cannot synthesize")
                yield {
                    "event": "error",
                    "data": '{"message": "No facets returned from pipeline", "recoverable": false}'
                }

            # Done
            logger.info(f"[{request_id}] Stream complete")
            yield {
                "event": "done",
                "data": "{}"
            }

        except Exception as e:
            logger.error(f"[{request_id}] Error during analysis: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": f'{{"message": "Internal error: {str(e)}", "recoverable": false}}'
            }

    return EventSourceResponse(event_generator())
