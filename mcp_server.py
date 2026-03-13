"""
mcp_server.py - FastMCP server exposing domain checker tools.

Tools:
  - check_domain       : single domain availability lookup
  - check_domains_bulk : up to 50 domains at once
  - suggest_domains    : keyword → generate + check 10-15 domain ideas
"""
from __future__ import annotations

import sys
import asyncio
from typing import Any

from fastmcp import FastMCP

from domain_lookup import check_domain as _check_domain, check_domains
from affiliate import add_affiliate_links
from analytics import log_check, log_link_served

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SOURCE = "mcp"
_BULK_LIMIT = 50

_SUFFIXES = [
    ".com", "app.com", ".io", ".co", ".dev", ".ai",
    "hq.com", "ly.com", "hub.com", "lab.com",
]
_PREFIXES = ["get", "my", "try", "go", "the"]

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("domain-checker")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _result_to_dict(result: Any) -> dict:
    """Convert a DomainResult to a plain dict for JSON serialisation."""
    return result.model_dump(exclude_none=True)


async def _enrich_and_log(result: Any) -> dict:
    """Add affiliate links, fire analytics, return dict."""
    await log_check(result.domain, result.available, source=_SOURCE)
    if result.available:
        result = add_affiliate_links(result)
        if result.register_urls:
            for registrar in result.register_urls:
                await log_link_served(result.domain, registrar, source=_SOURCE)
    return _result_to_dict(result)


# ---------------------------------------------------------------------------
# Tool: check_domain
# ---------------------------------------------------------------------------


@mcp.tool()
async def check_domain(domain: str) -> dict:
    """Check availability of a single domain name.

    Returns availability status, registrar info if taken, and affiliate
    registration links if the domain is available.

    Args:
        domain: The domain name to check (e.g. "example.com").
    """
    result = await _check_domain(domain)
    return await _enrich_and_log(result)


# ---------------------------------------------------------------------------
# Tool: check_domains_bulk
# ---------------------------------------------------------------------------


@mcp.tool()
async def check_domains_bulk(domains: list[str]) -> dict:
    """Check availability of up to 50 domain names in one call.

    Returns a summary with total/available/taken counts plus per-domain
    details and affiliate registration links for available domains.

    Args:
        domains: List of domain names (max 50).
    """
    if len(domains) > _BULK_LIMIT:
        return {
            "error": f"Too many domains: {len(domains)} provided, maximum is {_BULK_LIMIT}.",
            "limit": _BULK_LIMIT,
        }

    results = await check_domains(domains)

    enriched: list[dict] = []
    for result in results:
        enriched.append(await _enrich_and_log(result))

    available = [r for r in enriched if r.get("available")]
    taken = [r for r in enriched if not r.get("available")]

    return {
        "summary": {
            "total": len(enriched),
            "available": len(available),
            "taken": len(taken),
        },
        "available": available,
        "taken": taken,
    }


# ---------------------------------------------------------------------------
# Tool: suggest_domains
# ---------------------------------------------------------------------------


def _generate_candidates(keyword: str) -> list[str]:
    """Generate domain name ideas from a keyword using prefix/suffix patterns."""
    kw = keyword.strip().lower().replace(" ", "")
    candidates: list[str] = []

    # Suffix patterns
    for suffix in _SUFFIXES:
        candidates.append(f"{kw}{suffix}")

    # Prefix patterns (only for .com to keep count manageable)
    for prefix in _PREFIXES:
        candidates.append(f"{prefix}{kw}.com")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    return unique[:15]


@mcp.tool()
async def suggest_domains(keyword: str) -> dict:
    """Generate domain name ideas from a keyword and check their availability.

    Uses common prefix/suffix patterns (no LLM call) to generate 10–15
    domain candidates, then checks all of them. Returns available domains
    with affiliate registration links.

    Args:
        keyword: A keyword or short business description (e.g. "taskflow").
    """
    candidates = _generate_candidates(keyword)
    results = await check_domains(candidates)

    enriched: list[dict] = []
    for result in results:
        enriched.append(await _enrich_and_log(result))

    available = [r for r in enriched if r.get("available")]
    taken = [r for r in enriched if not r.get("available")]

    return {
        "keyword": keyword,
        "candidates_checked": len(enriched),
        "summary": {
            "available": len(available),
            "taken": len(taken),
        },
        "available": available,
        "taken": taken,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--http" in sys.argv:
        # Streamable HTTP transport for remote / hosted use
        mcp.run(transport="streamable-http")
    else:
        # Default: stdio transport for local Claude Desktop
        mcp.run(transport="stdio")
