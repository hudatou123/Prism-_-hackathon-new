"""
Provider-agnostic search() and fetch() grounding layer.
Agents call these — they don't know if Tavily, Brave, or mock is underneath.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import httpx
import trafilatura

from .cache import cached

logger = logging.getLogger(__name__)

# Configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SEARCH_TIMEOUT = 10
FETCH_TIMEOUT = 15
USER_AGENT = "prism-hackathon/0.1 (fact-checking agent)"

# Mock fixtures path
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
MOCK_SEARCH_RESULTS_FILE = FIXTURES_DIR / "mock_search_results.json"


class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    published_date: Optional[str] = None


@cached(namespace="search")
def search(query: str, max_results: int = 5) -> list[SearchResult]:
    """
    Provider order: try TAVILY_API_KEY if set, else fall back to a mock that returns
    canned results from tests/fixtures/mock_search_results.json.
    """
    if TAVILY_API_KEY:
        try:
            return _search_tavily(query, max_results)
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}, falling back to mock")
            return _search_mock(query, max_results)
    else:
        logger.info("TAVILY_API_KEY not set, using mock search results")
        return _search_mock(query, max_results)


def _search_tavily(query: str, max_results: int) -> list[SearchResult]:
    """Call Tavily API."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query, max_results=max_results)

        results = []
        for item in response.get('results', [])[:max_results]:
            results.append(SearchResult(
                url=item.get('url', ''),
                title=item.get('title', ''),
                snippet=item.get('content', ''),
                published_date=item.get('published_date')
            ))
        return results
    except Exception as e:
        logger.error(f"Tavily API error: {e}")
        raise


def _search_mock(query: str, max_results: int) -> list[SearchResult]:
    """Return canned mock results."""
    if not MOCK_SEARCH_RESULTS_FILE.exists():
        logger.warning(f"Mock search file not found: {MOCK_SEARCH_RESULTS_FILE}")
        return []

    with open(MOCK_SEARCH_RESULTS_FILE, 'r') as f:
        mock_data = json.load(f)

    results = [SearchResult(**item) for item in mock_data[:max_results]]
    return results


@cached(namespace="fetch")
def fetch(url: str) -> str:
    """
    Returns clean article text. Uses httpx to GET, then trafilatura.extract() to
    strip boilerplate. Sets a descriptive User-Agent header.
    On any error (HTTP, timeout, extraction fail), return "" and log a warning —
    NEVER raise, because callers use this in tight loops.
    """
    try:
        with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            headers = {"User-Agent": USER_AGENT}
            response = client.get(url, headers=headers)
            response.raise_for_status()

            # Extract clean text
            text = trafilatura.extract(response.text)
            if text is None:
                logger.warning(f"trafilatura extraction failed for {url}")
                return ""

            return text
    except httpx.HTTPError as e:
        logger.warning(f"HTTP error fetching {url}: {e}")
        return ""
    except Exception as e:
        logger.warning(f"Unexpected error fetching {url}: {e}")
        return ""


@cached(namespace="reddit")
def reddit_thread_json(url_or_permalink: str) -> dict:
    """
    Special-case grounding for Reddit grassroots sub-bucket (F5).
    Append '.json' to any reddit.com URL and return parsed JSON.
    Extract top comments only: author, score, body, permalink.
    Cached under namespace='reddit'.
    User-Agent: 'prism-hackathon/0.1 (by /u/anonymous)'
    """
    try:
        # Ensure URL ends with .json
        if not url_or_permalink.endswith('.json'):
            if '?' in url_or_permalink:
                url = url_or_permalink.replace('?', '.json?')
            else:
                url = url_or_permalink + '.json'
        else:
            url = url_or_permalink

        user_agent = 'prism-hackathon/0.1 (by /u/anonymous)'
        with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            headers = {"User-Agent": user_agent}
            response = client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Extract top comments
            comments = []
            if isinstance(data, list) and len(data) > 1:
                comment_listing = data[1].get('data', {}).get('children', [])
                for comment_data in comment_listing[:10]:  # Top 10 comments
                    comment = comment_data.get('data', {})
                    if comment.get('author') != '[deleted]':
                        comments.append({
                            'author': comment.get('author', ''),
                            'score': comment.get('score', 0),
                            'body': comment.get('body', ''),
                            'permalink': comment.get('permalink', '')
                        })

            return {
                'url': url_or_permalink,
                'comments': comments
            }
    except Exception as e:
        logger.warning(f"Reddit thread fetch failed for {url_or_permalink}: {e}")
        return {'url': url_or_permalink, 'comments': []}


# Log startup configuration
if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY not set — using mock search results for all queries")
