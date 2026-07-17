"""
matching.py — Quote normalization + exact/fuzzy match.

This is the F3 star feature. The entire "we don't ask a model whether
the quote is real, we grep the page for it" pitch line depends on the
code in this file.

Design:
  1. Normalize both sides aggressively (unicode, quotes, whitespace).
  2. Try exact substring match first — this is the strong claim.
  3. If exact fails, try fuzzy partial-ratio match ≥ FUZZY_THRESHOLD.
     Rendered in UI as "paraphrased match" — still honest, still auditable.
  4. Below threshold: drop the claim. Judge treats this as a failed verification.

Person B: DO NOT let an LLM into this function. That defeats the whole point.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Literal

from rapidfuzz import fuzz

from config import FUZZY_THRESHOLD

MatchType = Literal["exact", "paraphrased", "none"]


# ── Normalization ───────────────────────────────────────────────────────
# Common curly-quote / dash / whitespace variants that LLMs silently mutate
_QUOTE_TRANSLATIONS = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'",
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u00A0": " ", "\u2009": " ", "\u200A": " ", "\u202F": " ",
})


def normalize(text: str) -> str:
    """
    Aggressive normalization for quote matching.

    - Unicode NFKC (fullwidth → ASCII, ligatures split, etc.)
    - Curly quotes → straight, em/en dashes → hyphen, nbsp → space
    - Lowercase
    - Collapse all whitespace runs to single space
    - Strip
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_QUOTE_TRANSLATIONS)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_edge_punct(text: str) -> str:
    """Strip punctuation from the ends — helpful when agents include trailing periods."""
    return re.sub(r'^[\s"\'.,;:!?()\[\]-]+|[\s"\'.,;:!?()\[\]-]+$', "", text)


# ── Match ───────────────────────────────────────────────────────────────
def verify_quote(quote: str, page_text: str) -> tuple[MatchType, float]:
    """
    Check whether `quote` appears in `page_text`.

    Returns (match_type, score). score is 100.0 for exact, or the
    partial-ratio (0-100) for paraphrased, or 0.0 for none.

    This is deterministic. No LLM. No model call. Just string matching.
    """
    if not quote or not page_text:
        return ("none", 0.0)

    nq = strip_edge_punct(normalize(quote))
    np = normalize(page_text)

    if not nq or not np:
        return ("none", 0.0)

    # Exact substring — the strong claim
    if nq in np:
        return ("exact", 100.0)

    # Fuzzy: partial_ratio scores the best matching window in the longer string
    score = fuzz.partial_ratio(nq, np)
    if score >= FUZZY_THRESHOLD:
        return ("paraphrased", float(score))

    return ("none", float(score))
