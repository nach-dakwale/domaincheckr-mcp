"""
api_server.py - FastAPI REST server for domain availability checking.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, field_validator

from affiliate import add_affiliate_links, build_register_urls, _TEMPLATES
from analytics import log_check, log_link_served, log_click
from domain_lookup import check_domain, check_domains, DomainResult
from landing import LANDING_HTML, PRIVACY_HTML

# ---------------------------------------------------------------------------
# Domain suggestion patterns
# ---------------------------------------------------------------------------

_SUGGESTION_PATTERNS = [
    "{keyword}.com",
    "{keyword}app.com",
    "get{keyword}.com",
    "{keyword}hq.com",
    "my{keyword}.com",
    "{keyword}.io",
    "{keyword}.co",
    "{keyword}.dev",
    "{keyword}.ai",
    "try{keyword}.com",
    "{keyword}ly.com",
    "go{keyword}.com",
    "the{keyword}.com",
    "{keyword}hub.com",
    "{keyword}lab.com",
]


def generate_suggestions(keyword: str) -> list[str]:
    """Generate domain suggestions from a keyword using predefined patterns."""
    kw = keyword.strip().lower().replace(" ", "")
    return [p.format(keyword=kw) for p in _SUGGESTION_PATTERNS]


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

SOURCE = "api"


class BulkCheckRequest(BaseModel):
    domains: list[str]

    @field_validator("domains")
    @classmethod
    def max_fifty(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("Maximum 50 domains per request")
        return v


class BulkCheckResponse(BaseModel):
    results: list[DomainResult]
    total: int
    available: int
    taken: int


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Domain Checker API",
    description="Check domain availability and get affiliate registration links.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _enrich_and_log(result: DomainResult) -> DomainResult:
    """Add affiliate links and fire analytics for a single result."""
    result = add_affiliate_links(result)
    await log_check(result.domain, result.available, SOURCE)
    if result.available and result.register_urls:
        await asyncio.gather(
            *[log_link_served(result.domain, registrar, SOURCE)
              for registrar in result.register_urls]
        )
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing():
    return LANDING_HTML


@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy():
    return PRIVACY_HTML


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/check/{domain}", response_model=DomainResult)
async def check_single(domain: str) -> DomainResult:
    """Check availability of a single domain."""
    result = await check_domain(domain)
    return await _enrich_and_log(result)


@app.post("/check", response_model=BulkCheckResponse)
async def check_bulk(body: BulkCheckRequest) -> BulkCheckResponse:
    """Check availability of up to 50 domains in parallel."""
    raw_results = await check_domains(body.domains)
    enriched = await asyncio.gather(*[_enrich_and_log(r) for r in raw_results])
    results = list(enriched)
    available = sum(1 for r in results if r.available)
    return BulkCheckResponse(
        results=results,
        total=len(results),
        available=available,
        taken=len(results) - available,
    )


@app.get("/suggest", response_model=BulkCheckResponse)
async def suggest(keyword: str = Query(..., min_length=1, description="Keyword to build domain ideas from")) -> BulkCheckResponse:
    """Generate and check domain suggestions for a keyword."""
    domains = generate_suggestions(keyword)
    raw_results = await check_domains(domains)
    enriched = await asyncio.gather(*[_enrich_and_log(r) for r in raw_results])
    results = list(enriched)
    available = sum(1 for r in results if r.available)
    return BulkCheckResponse(
        results=results,
        total=len(results),
        available=available,
        taken=len(results) - available,
    )


@app.get("/go/{registrar}/{domain}")
async def click_redirect(registrar: str, domain: str) -> RedirectResponse:
    """Track a click and redirect to the registrar's registration page."""
    if registrar not in _TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Unknown registrar: {registrar}")
    urls = build_register_urls(domain)
    redirect_url = urls[registrar]
    await log_click(domain, registrar)
    return RedirectResponse(url=redirect_url, status_code=302)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    from config import settings
    uvicorn.run("api_server:app", host=settings.api_host, port=settings.api_port, reload=False)
