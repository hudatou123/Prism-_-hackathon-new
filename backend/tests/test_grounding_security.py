import socket

import httpx
import pytest

from prism import grounding


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/x", "http://[::1]/x", "http://169.254.169.254/latest",
    "http://10.0.0.1/x", "http://localhost/x", "file:///etc/passwd",
])
def test_private_and_non_http_targets_are_blocked(url):
    with pytest.raises(ValueError):
        grounding.validate_public_url(url)


def test_dns_resolving_to_private_address_is_blocked(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.5", 443)),
    ])
    with pytest.raises(ValueError, match="non-public"):
        grounding.validate_public_url("https://attacker.test/article")


def test_response_type_and_size_limits_fail_closed():
    bad_type = httpx.Response(200, headers={"content-type": "application/octet-stream"},
                              content=b"small")
    with pytest.raises(ValueError, match="content type"):
        grounding._read_response(bad_type, ("text/html",), 100)
    too_large = httpx.Response(200, headers={"content-type": "text/html"}, content=b"12345")
    with pytest.raises(ValueError, match="byte limit"):
        grounding._read_response(too_large, ("text/html",), 4)


def test_live_fetch_failure_returns_no_evidence(monkeypatch):
    def reject(*_args, **_kwargs):
        raise ValueError("unsafe redirect")
    monkeypatch.setattr(grounding, "_get_bytes", reject)
    assert grounding.fetch("https://public.example/article") == ""
