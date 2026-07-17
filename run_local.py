#!/usr/bin/env python3
"""Local runner — watch the tree stream in, exactly as the frontend will.

    python run_local.py                         # hero topic, offline fixture
    python run_local.py "Did X really do Y?"    # any claim (needs keys, else fixture)

With no API keys it runs against the cached hero-topic fixture, so this is the
zero-setup way for Person C to see real StreamEvent shapes and for A to smoke
the fan-out. With keys set it runs live through Tavily + Claude.
"""
from __future__ import annotations

import asyncio
import sys

from prism.config import settings
from prism.orchestrator import run_pipeline
from prism.schemas import EventType


def _line(s: str) -> None:
    print(s, flush=True)


async def main(claim: str) -> None:
    mode = "OFFLINE (fixture)" if settings.offline else "LIVE (Tavily + Claude)"
    _line(f"\n=== Prism · {mode} ===")
    _line(f'CLAIM: "{claim}"\n')

    async for ev in run_pipeline(claim):
        if ev.type == EventType.PROVISIONAL and ev.provisional:
            p = ev.provisional
            _line(f"[~3s] ⏳ PRELIMINARY · {p.badge}")
            _line(f"      Early read: {p.early_read}  (sources so far: {p.sources_so_far})\n")

        elif ev.type == EventType.DECOMPOSED and ev.decomposition:
            d = ev.decomposition
            tag = "  [SETTLED FACT → confirm/refute lane]" if d.settled_fact else ""
            _line(f"[decompose]{tag}")
            for fq in d.facet_queries:
                _line(f"   · {fq.facet_key}: pro='{fq.pro_query}'")
            _line("")

        elif ev.type == EventType.FACET_STARTED:
            _line(f"[facet ▸] {ev.facet_key} started…")

        elif ev.type == EventType.FACET_RESOLVED and ev.facet:
            f = ev.facet
            _line(f"[facet ✓] {f.label}: {f.status.value.upper()}  — {f.summary}")
            _line(f"          sources={f.sources_examined} quotes_verified={f.quotes_verified}/{f.quotes_total}")
            if f.con.no_credible_evidence:
                _line("          CON: no credible counter-evidence found ✓ (F4)")
            _line("")

        elif ev.type == EventType.FINAL and ev.final:
            v = ev.final
            _line("─" * 56)
            _line(f"FINAL VERDICT: {v.verdict}")
            _line(f"Confidence: {v.confidence_band.value.upper()}")
            _line(f"   {v.scored_facet_count}/{v.total_facet_count} facets scored · "
                  f"scores={ {k: s for k, s in v.facet_scores.items()} }")
            if v.source_agreement_ratio is not None:
                _line(f"   quote agreement: {v.source_agreement_ratio:.0%}")
            _line(f"Sources examined: {v.sources_examined} · "
                  f"Quotes verified: {v.quotes_verified}/{v.quotes_total} ✓")
            _line("─" * 56)

        elif ev.type == EventType.ERROR:
            _line(f"[error] {ev.message}")


if __name__ == "__main__":
    claim = sys.argv[1] if len(sys.argv) > 1 else "Did Meta really lay off 5% of its workforce?"
    asyncio.run(main(claim))
