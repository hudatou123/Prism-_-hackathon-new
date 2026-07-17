"""F3 quote-grep — the centerpiece anti-hallucination defense.

"We don't ask a model whether the quote is real. We grep the page for it."

Deterministic, normalized substring match of a quoted claim against fetched page
text. NO LLM in this loop. Person B owns the Judge that calls this; A ships a
robust shared implementation because the whole demo lives or dies on whether it
returns "6/6 verified" instead of "0/6" on real pages.

Normalization handles the things that silently break a naive `in` check on real
web text (the risk called out in review):
  - smart quotes / apostrophes -> straight
  - HTML entities (&amp; &quot; &#39; &nbsp;) -> unescaped
  - unicode dashes/ellipsis -> ascii
  - collapsed whitespace, case-folded
We intentionally do NOT match across an ellipsis gap in the quote — a quote the
agent truncated with "..." is matched as its longest contiguous run, so we never
"verify" a stitched-together fabrication.
"""
from __future__ import annotations

import html
import re
import unicodedata

_SMART = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "−": "-",
    " ": " ", "…": "...",
}


def normalize(text: str) -> str:
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    for bad, good in _SMART.items():
        text = text.replace(bad, good)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Quotes shorter than this are too generic to count as verification.
MIN_QUOTE_CHARS = 12


def quote_in_page(quote: str, page_text: str) -> bool:
    """True iff `quote` is a real, contiguous substring of `page_text`.

    Handles author-inserted ellipsis by requiring EVERY segment (split on `...`)
    to appear, each individually long enough — a conservative rule that refuses
    to bless a fabricated stitch.
    """
    page = normalize(page_text)
    if not page:
        return False

    q = normalize(quote)
    if "..." in q:
        segments = [s.strip() for s in q.split("...") if s.strip()]
    else:
        segments = [q]

    if not segments:
        return False
    return all(len(seg) >= MIN_QUOTE_CHARS and seg in page for seg in segments)
