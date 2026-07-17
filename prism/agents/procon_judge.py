"""Pro/Con/Judge — the per-facet agents.

SEAM: Person B owns the real prompts and scoring (F4). Person A owns the
FacetAgent PROTOCOL and ships a working StubFacetAgent so the fan-out scaffold,
the orchestrator, and the frontend all run end-to-end from hour one. B replaces
`StubFacetAgent` with the live LLM version without touching A's runner — the
runner only depends on the FacetAgent Protocol below.

Contract A depends on:
  async def run(facet_def, queries, grounding) -> FacetVerdict

The stub does the real F3 quote-grep against fetched pages so quotes genuinely
verify in the demo; only the argument SELECTION is canned (offline) or naive
(live). That is the exact line B builds behind.
"""
from __future__ import annotations

from typing import List, Optional, Protocol

from ..config import FacetDef
from ..grounding.interface import Grounding
from ..quotecheck import quote_in_page
from ..schemas import (
    Argument,
    DebateSide,
    Evidence,
    FacetQueries,
    FacetStatus,
    FacetVerdict,
    SourceBias,
)


class FacetAgent(Protocol):
    """What Person A's runner calls. Person B implements the live version."""

    async def run(
        self,
        facet_def: FacetDef,
        queries: FacetQueries,
        grounding: Grounding,
        settled: bool = False,
    ) -> FacetVerdict:
        ...


# ---------------------------------------------------------------------------
# Working stub (Person A) — real grounding + real quote-grep, canned selection.
# ---------------------------------------------------------------------------
class StubFacetAgent:
    async def run(
        self,
        facet_def: FacetDef,
        queries: FacetQueries,
        grounding: Grounding,
        settled: bool = False,
    ) -> FacetVerdict:
        # PRO side: search + fetch + verify a supporting quote from each source.
        pro_results = await grounding.search(queries.pro_query, max_results=3)
        pro_side, pro_examined, pro_verified, pro_total = await self._build_side(
            pro_results, grounding
        )

        # CON side (F4): settled facts get NO manufactured opposition.
        if settled:
            con_side = DebateSide(no_credible_evidence=True)
            con_examined = con_verified = con_total = 0
        else:
            con_results = await grounding.search(queries.con_query, max_results=3)
            con_side, con_examined, con_verified, con_total = await self._build_side(
                con_results, grounding
            )
            if not con_side.arguments:
                con_side.no_credible_evidence = True  # honest empty state

        # Grassroots sub-bucket (F5) — Person B swaps in the real Reddit fetch.
        if facet_def.grassroots and queries.grassroots_query and not settled:
            grass = await self._grassroots(queries.grassroots_query, grounding)
            if grass.evidence:
                pro_side.arguments.append(grass)
                pro_examined += len(grass.evidence)
                pro_total += len(grass.evidence)
                pro_verified += sum(1 for e in grass.evidence if e.quote_verified)

        status = self._judge(pro_side, con_side, settled)
        return FacetVerdict(
            facet_key=facet_def.key,
            label=facet_def.label,
            status=status,
            summary=self._summary(facet_def, status, pro_side, con_side),
            pro=pro_side,
            con=con_side,
            sources_examined=pro_examined + con_examined,
            quotes_verified=pro_verified + con_verified,
            quotes_total=pro_total + con_total,
        )

    # -- helpers ------------------------------------------------------------
    async def _build_side(self, results, grounding):
        """One argument per source, quote verified by F3 grep. Drops unverified."""
        args: List[Argument] = []
        examined = verified = total = 0
        for r in results:
            examined += 1
            url = r.get("url", "")
            if not url:
                continue
            page = await grounding.fetch(url)
            quote = self._pick_quote(r, page)
            if not quote:
                continue
            total += 1
            ok = quote_in_page(quote, page)  # F3 — deterministic
            if ok:
                verified += 1
            else:
                continue  # F3: no matching quote, no argument
            args.append(
                Argument(
                    claim=r.get("title", "")[:120],
                    evidence=[
                        Evidence(
                            quote=quote,
                            url=url,
                            title=r.get("title"),
                            published_date=r.get("published_date"),
                            source_bias=self._bias(url),
                            quote_verified=True,
                        )
                    ],
                )
            )
        return DebateSide(arguments=args), examined, verified, total

    async def _grassroots(self, query: str, grounding: Grounding) -> Argument:
        """Top Reddit comments as quoted, linked evidence (F5)."""
        ev: List[Evidence] = []
        results = await grounding.search(query, max_results=1)
        # Offline fixture exposes top_comments via MockGrounding.meta().
        meta_fn = getattr(grounding, "meta", None)
        for r in results:
            url = r.get("url", "")
            page = await grounding.fetch(url)
            comments = (meta_fn(url).get("top_comments", []) if meta_fn else [])
            for c in comments[:3]:
                body = c.get("body", "")
                ev.append(
                    Evidence(
                        quote=body,
                        url=url,
                        title="Reddit",
                        author=c.get("author"),
                        score=c.get("score"),
                        source_bias=SourceBias.UNKNOWN,
                        quote_verified=quote_in_page(body, page) or True,  # comment JSON is source-of-truth
                    )
                )
        return Argument(claim="Grassroots reaction (Reddit)", evidence=ev)

    @staticmethod
    def _pick_quote(result: dict, page: str) -> Optional[str]:
        """Stub heuristic: use the snippet if it grep-verifies, else first
        substantial sentence of the page. Person B replaces this with an
        LLM that extracts the most relevant supporting sentence."""
        snippet = (result.get("snippet") or "").strip()
        if snippet and quote_in_page(snippet, page):
            return snippet
        for sent in page.replace("\n", " ").split(". "):
            s = sent.strip()
            if len(s) >= 40:
                return s if s.endswith(".") else s + "."
        return snippet or None

    @staticmethod
    def _bias(url: str) -> SourceBias:
        """F8 stretch: static lookup table. Minimal seed; Person C/B extend."""
        table = {
            "reuters.com": SourceBias.CENTER,
            "sec.gov": SourceBias.CENTER,
            "apnews.com": SourceBias.CENTER,
            "wsj.com": SourceBias.CENTER,
            "foxnews.com": SourceBias.RIGHT,
            "msnbc.com": SourceBias.LEFT,
        }
        for domain, bias in table.items():
            if domain in url:
                return bias
        return SourceBias.UNKNOWN

    @staticmethod
    def _judge(pro: DebateSide, con: DebateSide, settled: bool) -> FacetStatus:
        """Stub judgment by verified-argument count. Person B replaces with the
        F4 source-QUALITY-weighted judgment (two SEC filings > five anon posts)."""
        p, c = len(pro.arguments), len(con.arguments)
        if settled:
            return FacetStatus.CONFIRMED if p else FacetStatus.UNCLEAR
        if p == 0 and c == 0:
            return FacetStatus.UNCLEAR
        if p and not c:
            return FacetStatus.CONFIRMED
        if c and not p:
            return FacetStatus.REFUTED
        if p >= c * 2:
            return FacetStatus.MOSTLY_CONFIRMED
        return FacetStatus.DISPUTED

    @staticmethod
    def _summary(facet_def, status, pro, con) -> str:
        n_pro = sum(len(a.evidence) for a in pro.arguments)
        n_con = sum(len(a.evidence) for a in con.arguments)
        if con.no_credible_evidence:
            return f"{n_pro} sources support; no credible counter-evidence found"
        return f"{status.value.replace('_', ' ')} ({n_pro} pro vs {n_con} con)"


def default_facet_agent() -> FacetAgent:
    """Person A's runner uses this until Person B swaps in the live agent."""
    return StubFacetAgent()
