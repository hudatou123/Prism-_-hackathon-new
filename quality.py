"""
quality.py — Source quality tier lookup for F4 quality-weighted judging.

Hand-curated domain → tier mapping. Unknown domains default to "medium".

Add more domains as you spot them during hero-topic testing.
Reddit is intentionally tagged "low" as a general source, but when it
appears in the grassroots sub-bucket of Stakeholder Reactions, that
facet's verdict logic uses a different scoring path (see judge.py).
"""
from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

QualityTier = Literal["high", "medium", "low"]


# High-quality: primary sources, wire services, papers of record, gov filings
_HIGH = {
    # Wire services & AP-tier
    "reuters.com", "apnews.com", "afp.com",
    # Papers of record
    "nytimes.com", "wsj.com", "washingtonpost.com", "ft.com", "economist.com",
    "bloomberg.com", "theguardian.com", "bbc.com", "bbc.co.uk", "npr.org",
    # Government / regulatory / primary
    "sec.gov", "whitehouse.gov", "supremecourt.gov", "justice.gov",
    "federalregister.gov", "congress.gov", "gao.gov", "cbo.gov",
    "who.int", "cdc.gov", "nih.gov", "fda.gov", "europa.eu", "un.org",
    # Peer-reviewed / academic
    "nature.com", "science.org", "nejm.org", "thelancet.com",
    "pnas.org", "arxiv.org", "pubmed.ncbi.nlm.nih.gov",
    # Fact-checkers themselves (useful when the topic *is* fact-checking)
    "politifact.com", "factcheck.org", "snopes.com",
}

# Medium: reputable industry press, major outlets, established magazines
_MEDIUM = {
    "cnbc.com", "cnn.com", "abcnews.go.com", "nbcnews.com", "cbsnews.com",
    "techcrunch.com", "theverge.com", "arstechnica.com", "wired.com",
    "engadget.com", "vox.com", "axios.com", "politico.com", "propublica.org",
    "theatlantic.com", "newyorker.com", "time.com", "forbes.com",
    "businessinsider.com", "usatoday.com", "latimes.com",
    "semafor.com", "theinformation.com",
}

# Low: user-generated, aggregators, forums, low-editorial
_LOW = {
    "reddit.com", "twitter.com", "x.com", "facebook.com", "instagram.com",
    "tiktok.com", "youtube.com", "medium.com", "substack.com",
    "quora.com", "yahoo.com", "msn.com",
}


def _domain_of(url: str) -> str:
    """Extract eTLD+1-ish. Not perfect, but good enough for a lookup table."""
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return ""
    host = host.lower().lstrip(".")
    # Strip www.
    if host.startswith("www."):
        host = host[4:]
    return host


def _match_domain(host: str, table: set[str]) -> bool:
    """Match host against table, allowing subdomain matches."""
    if host in table:
        return True
    for d in table:
        if host.endswith("." + d):
            return True
    return False


def quality_of(url: str) -> QualityTier:
    """
    Return the quality tier for a URL's domain.
    Unknown domains default to 'medium' — most niche outlets are fine.
    """
    host = _domain_of(url)
    if not host:
        return "medium"
    if _match_domain(host, _HIGH):
        return "high"
    if _match_domain(host, _LOW):
        return "low"
    if _match_domain(host, _MEDIUM):
        return "medium"
    return "medium"


# Weight for the deterministic verdict math in judge.py
_WEIGHTS = {"high": 3, "medium": 1, "low": 0.3}


def weight_of(tier: QualityTier) -> float:
    return _WEIGHTS[tier]
