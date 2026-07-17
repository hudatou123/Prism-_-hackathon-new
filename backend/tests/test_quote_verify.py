"""
Tests for quote verification — deterministic substring matching.
"""

import pytest
from prism.quote_verify import normalize, verify_quote, verify_argument
from prism.schema import Argument


def test_normalize_exact_match():
    """Exact match after normalization."""
    text = "Hello World"
    assert normalize(text) == "hello world"


def test_normalize_smart_quotes():
    """Smart quotes in quote, ASCII in page."""
    quote = 'This is a "test" quote'
    page = 'This is a "test" quote'
    assert verify_quote(quote, page) is True


def test_normalize_apostrophes():
    """Smart apostrophes normalized to ASCII."""
    quote = "It's a test"
    page = "It's a test"
    assert verify_quote(quote, page) is True


def test_normalize_dashes():
    """Em-dash and en-dash normalized to hyphen."""
    quote = "This is—a test"
    page = "This is-a test"
    assert verify_quote(quote, page) is True

    quote2 = "Range: 10–20"
    page2 = "Range: 10-20"
    assert verify_quote(quote2, page2) is True


def test_normalize_ellipsis():
    """Ellipsis character normalized to three dots."""
    quote = "Wait… for it"
    page = "Wait... for it"
    assert verify_quote(quote, page) is True


def test_normalize_whitespace():
    """Multiple whitespace collapsed to single space."""
    quote = "Hello    world\n\twith   spaces"
    page = "Hello world with spaces"
    assert verify_quote(quote, page) is True


def test_verify_quote_genuine_mismatch():
    """Genuinely different text returns false."""
    quote = "The company fired 5000 employees"
    page = "The company hired 5000 employees"
    assert verify_quote(quote, page) is False


def test_verify_quote_empty():
    """Empty quote should not match everything."""
    assert verify_quote("", "Some text") is False
    assert verify_quote("   ", "Some text") is False


def test_verify_quote_substring():
    """Quote is a substring of page."""
    quote = "critical passage"
    page = "This is the critical passage in the middle of a long document."
    assert verify_quote(quote, page) is True


def test_verify_argument_integration():
    """Test verify_argument with mock fetch function."""
    def mock_fetch(url):
        return "This document contains the critical passage we need."

    arg = Argument(
        claim="Test claim",
        quote="critical passage",
        url="https://example.com",
        source_domain="example.com",
        quote_verified=False,
        source_quality="high"
    )

    result = verify_argument(arg, fetch_fn=mock_fetch)
    assert result is True
    assert arg.quote_verified is True  # Updated in-place


def test_verify_argument_fetch_failure():
    """Test verify_argument with failed fetch."""
    def mock_fetch_fail(url):
        return ""  # Fetch returns empty on error

    arg = Argument(
        claim="Test claim",
        quote="missing passage",
        url="https://example.com",
        source_domain="example.com",
        quote_verified=False,
        source_quality="high"
    )

    result = verify_argument(arg, fetch_fn=mock_fetch_fail)
    assert result is False
    assert arg.quote_verified is False


def test_normalize_unicode():
    """Test Unicode normalization (NFKC)."""
    # NFKC normalization example
    text1 = "café"  # é as single char
    text2 = "café"  # é as e + combining acute
    assert normalize(text1) == normalize(text2)
