"""
F3 — deterministic substring match. Anti-hallucination centerpiece.
Zero LLM involvement.
"""

import unicodedata
import re
from .schema import Argument
from .grounding import fetch as default_fetch


def normalize(text: str) -> str:
    """
    Lowercase, collapse whitespace, normalize Unicode (NFKC),
    strip smart quotes and dashes to ASCII equivalents.
    """
    if not text:
        return ""

    # Unicode normalization (NFKC — compatibility decomposition + canonical composition)
    text = unicodedata.normalize('NFKC', text)

    # Smart quotes to ASCII
    text = text.replace('“', '"')  # "
    text = text.replace('”', '"')  # "
    text = text.replace('‘', "'")  # '
    text = text.replace('’', "'")  # '
    text = text.replace('`', "'")  # ` (backtick)
    text = text.replace('´', "'")  # ´ (acute accent)

    # Dashes to ASCII hyphen
    text = text.replace('—', '-')  # — (em-dash)
    text = text.replace('–', '-')  # – (en-dash)

    # Ellipsis to three dots
    text = text.replace('…', '...')  # …

    # Lowercase
    text = text.lower()

    # Collapse whitespace (including newlines, tabs)
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def verify_quote(quote: str, page_text: str) -> bool:
    """
    Returns True iff normalize(quote) is a substring of normalize(page_text).
    """
    if not quote or not page_text:
        return False

    norm_quote = normalize(quote)
    norm_page = normalize(page_text)

    # Empty quote after normalization should not match everything
    if not norm_quote:
        return False

    return norm_quote in norm_page


def verify_argument(arg: Argument, fetch_fn=None) -> bool:
    """
    Fetches the arg's URL and runs verify_quote. Updates arg.quote_verified in-place.
    Returns the boolean too.
    """
    if fetch_fn is None:
        fetch_fn = default_fetch

    page_text = fetch_fn(arg.url)
    result = verify_quote(arg.quote, page_text)

    # Update in-place
    arg.quote_verified = result

    return result
