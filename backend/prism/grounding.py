"""Live search and SSRF-hardened page fetching."""

from __future__ import annotations

import ipaddress
import logging
import socket
from typing import Optional
from urllib.parse import urljoin, urlsplit

import httpx
import trafilatura
from pydantic import BaseModel

from .settings import get_settings

logger = logging.getLogger(__name__)
USER_AGENT = "truthscope-prism/1.0 (fact-checking; contact: local-operator)"
_ALLOWED_ARTICLE_TYPES = ("text/html", "text/plain", "application/xhtml+xml")
_BLOCKED_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata",
}


class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    published_date: Optional[str] = None


def _is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value.split("%", 1)[0])
    except ValueError:
        return False
    return address.is_global and not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def validate_public_url(url: str) -> str:
    """Return a normalized public HTTP(S) URL or raise ValueError."""
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only absolute http(s) URLs are allowed")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in _BLOCKED_HOSTS or hostname.endswith(".localhost"):
        raise ValueError("local and metadata hosts are blocked")
    if parsed.username or parsed.password:
        raise ValueError("credential-bearing URLs are blocked")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("invalid port")

    try:
        literal = ipaddress.ip_address(hostname.split("%", 1)[0])
    except ValueError:
        literal = None
    if literal is not None:
        if not _is_public_ip(hostname):
            raise ValueError("non-public IP address is blocked")
    else:
        try:
            records = socket.getaddrinfo(hostname, port or (443 if parsed.scheme == "https" else 80))
        except socket.gaierror as exc:
            raise ValueError("host could not be resolved") from exc
        addresses = {record[4][0] for record in records}
        if not addresses or any(not _is_public_ip(address) for address in addresses):
            raise ValueError("host resolves to a non-public IP address")
    return parsed.geturl()

def _read_response(response: httpx.Response, allowed_types: tuple[str, ...], max_bytes: int) -> bytes:
    if response.status_code >= 400:
        try:
            request = response.request
        except RuntimeError:
            request = httpx.Request("GET", "https://invalid.local")
        raise httpx.HTTPStatusError(
            f"HTTP {response.status_code}", request=request, response=response
        )
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in allowed_types:
        raise ValueError(f"unsupported content type: {content_type or 'missing'}")
    content_length = response.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise ValueError("response exceeds byte limit")
        except ValueError as exc:
            if str(exc) == "response exceeds byte limit":
                raise
    body = bytearray()
    for chunk in response.iter_bytes():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise ValueError("response exceeds byte limit")
    return bytes(body)


def _get_bytes(url: str, allowed_types: tuple[str, ...]) -> tuple[bytes, str]:
    settings = get_settings()
    current = validate_public_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": ", ".join(allowed_types)}
    with httpx.Client(timeout=settings.fetch_timeout_seconds, follow_redirects=False) as client:
        for redirect_count in range(settings.fetch_max_redirects + 1):
            # Revalidate before every request, including every redirect target.
            current = validate_public_url(current)
            with client.stream("GET", current, headers=headers) as response:
                if response.is_redirect:
                    if redirect_count >= settings.fetch_max_redirects:
                        raise ValueError("too many redirects")
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("redirect missing location")
                    current = validate_public_url(urljoin(current, location))
                    continue
                return _read_response(response, allowed_types, settings.fetch_max_bytes), current
    raise ValueError("too many redirects")


def search(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search Tavily. Live failures are surfaced; there is no mock fallback."""
    settings = get_settings()
    if not settings.tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY is required for live search")
    from tavily import TavilyClient
    from tavily.errors import InvalidAPIKeyError

    search_options = {
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
    }
    try:
        response = TavilyClient(api_key=settings.tavily_api_key).search(**search_options)
    except InvalidAPIKeyError:
        # Tavily's current SDK supports live keyless search. This remains a
        # real network-grounded result and never substitutes mock evidence.
        logger.warning("Configured Tavily key was rejected; retrying with live keyless search")
        response = TavilyClient(api_key="").search(**search_options)
    results: list[SearchResult] = []
    for item in response.get("results", []):
        raw_url = str(item.get("url") or "").strip()
        try:
            url = validate_public_url(raw_url)
        except ValueError:
            logger.warning("Discarding unsafe or missing search result URL")
            continue
        results.append(SearchResult(
            url=url,
            title=str(item.get("title") or ""),
            snippet=str(item.get("content") or ""),
            published_date=item.get("published_date"),
        ))
    return results


def fetch(url: str) -> str:
    """Fetch and extract a bounded public article, returning an empty string on failure."""
    try:
        body, final_url = _get_bytes(url, _ALLOWED_ARTICLE_TYPES)
        decoded = body.decode("utf-8", errors="replace")
        content = trafilatura.extract(decoded, include_comments=False, include_tables=False)
        return content or decoded
    except (httpx.HTTPError, ValueError, UnicodeError) as exc:
        logger.warning("Fetch rejected for %s: %s", url, exc)
        return ""

def reddit_thread_json(url_or_permalink: str) -> dict:
    """Fetch bounded Reddit JSON through the same URL and redirect protections."""
    base_url = url_or_permalink if url_or_permalink.endswith(".json") else f"{url_or_permalink}.json"
    try:
        body, _ = _get_bytes(base_url, ("application/json",))
        data = httpx.Response(200, content=body).json()
        comments = []
        if isinstance(data, list) and len(data) > 1:
            children = data[1].get("data", {}).get("children", [])
            for child in children[:10]:
                comment = child.get("data", {})
                if comment.get("author") not in {None, "[deleted]"}:
                    comments.append({
                        "author": comment.get("author", ""),
                        "score": comment.get("score", 0),
                        "body": comment.get("body", ""),
                        "permalink": comment.get("permalink", ""),
                    })
        return {"url": url_or_permalink, "comments": comments}
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Reddit fetch rejected for %s: %s", url_or_permalink, exc)
        return {"url": url_or_permalink, "comments": []}
