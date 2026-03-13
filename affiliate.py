"""
affiliate.py - Affiliate link generation for available domains.
"""
from __future__ import annotations

from urllib.parse import quote

from config import settings
from domain_lookup import DomainResult


# ---------------------------------------------------------------------------
# URL templates
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, str] = {
    "dynadot": (
        "https://www.dynadot.com/domain/search?domain={domain}&ref={affiliate_id}"
    ),
}

_AFFILIATE_IDS: dict[str, str] = {
    "dynadot": settings.dynadot_affiliate_id,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_register_urls(domain: str) -> dict[str, str]:
    """Return a {registrar: url} dict of affiliate registration links."""
    encoded_domain = quote(domain, safe=".-")
    urls: dict[str, str] = {}
    for registrar, template in _TEMPLATES.items():
        affiliate_id = _AFFILIATE_IDS.get(registrar, "PLACEHOLDER")
        urls[registrar] = template.format(domain=encoded_domain, affiliate_id=affiliate_id)
    return urls


def add_affiliate_links(result: DomainResult) -> DomainResult:
    """Attach register_urls to a DomainResult if the domain is available.

    Returns a new DomainResult (Pydantic models are immutable by default).
    """
    if not result.available or not settings.enable_affiliate_links:
        return result
    return result.model_copy(update={"register_urls": build_register_urls(result.domain)})
