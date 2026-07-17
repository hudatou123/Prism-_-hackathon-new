"""F3 quote-grep robustness — the demo lives or dies on these passing.

Run: python -m pytest tests/  (or: python tests/test_quotecheck.py)
"""
from __future__ import annotations

from prism.quotecheck import quote_in_page


def _check(name, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return ok


def run() -> bool:
    results = []

    # exact match
    results.append(_check(
        "exact",
        quote_in_page("reducing our workforce by approximately 5%",
                      "We are reducing our workforce by approximately 5% across teams."),
        True,
    ))
    # smart quotes / apostrophe in page, straight in quote
    results.append(_check(
        "smart-quotes",
        quote_in_page("it's the company's plan",
                      "They said it’s the company’s plan going forward."),
        True,
    ))
    # HTML entities in page
    results.append(_check(
        "html-entities",
        quote_in_page("Q&A about layoffs",
                      "A short Q&amp;A about layoffs was held."),
        True,
    ))
    # collapsed whitespace / newlines
    results.append(_check(
        "whitespace",
        quote_in_page("approximately 5% across affected teams",
                      "approximately   5%\n across    affected\tteams"),
        True,
    ))
    # fabricated quote -> must FAIL
    results.append(_check(
        "fabrication-rejected",
        quote_in_page("we are cutting exactly 25% of everyone",
                      "We are reducing our workforce by approximately 5%."),
        False,
    ))
    # empty page (dead fetch) -> must FAIL, never crash
    results.append(_check("empty-page", quote_in_page("anything at all here", ""), False))
    # too-short quote -> not enough to verify
    results.append(_check("too-short", quote_in_page("5%", "we cut 5% of staff"), False))
    # ellipsis stitch: both real segments present
    results.append(_check(
        "ellipsis-both-present",
        quote_in_page("reducing our workforce ... across affected teams",
                      "reducing our workforce by approximately 5% across affected teams"),
        True,
    ))
    # ellipsis stitch: one segment fabricated -> FAIL
    results.append(_check(
        "ellipsis-one-fake",
        quote_in_page("reducing our workforce ... by a total of 90 percent",
                      "reducing our workforce by approximately 5% across affected teams"),
        False,
    ))

    passed = all(results)
    print(f"\n{sum(results)}/{len(results)} passed")
    return passed


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
