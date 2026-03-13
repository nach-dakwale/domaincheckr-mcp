"""
analytics.py - Async SQLite event logging for domain checker.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Any, AsyncIterator

import aiosqlite

from config import settings


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS domain_checks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    domain    TEXT    NOT NULL,
    available INTEGER NOT NULL,
    source    TEXT    NOT NULL,
    ts        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS links_served (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    domain    TEXT    NOT NULL,
    registrar TEXT    NOT NULL,
    source    TEXT    NOT NULL,
    ts        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS clicks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    domain    TEXT    NOT NULL,
    registrar TEXT    NOT NULL,
    ts        TEXT    NOT NULL
);
"""


@asynccontextmanager
async def _db() -> AsyncIterator[aiosqlite.Connection]:
    """Yield an open, initialised analytics database connection."""
    db_path = settings.db_path
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.executescript(_DDL)
        await conn.commit()
        yield conn


# ---------------------------------------------------------------------------
# Write events
# ---------------------------------------------------------------------------


async def log_check(domain: str, available: bool, source: str) -> None:
    """Record a domain availability check."""
    if not settings.enable_analytics:
        return
    ts = datetime.now(timezone.utc).isoformat()
    async with _db() as db:
        await db.execute(
            "INSERT INTO domain_checks (domain, available, source, ts) VALUES (?, ?, ?, ?)",
            (domain, int(available), source, ts),
        )
        await db.commit()


async def log_link_served(domain: str, registrar: str, source: str) -> None:
    """Record that an affiliate link was included in a response."""
    if not settings.enable_analytics:
        return
    ts = datetime.now(timezone.utc).isoformat()
    async with _db() as db:
        await db.execute(
            "INSERT INTO links_served (domain, registrar, source, ts) VALUES (?, ?, ?, ?)",
            (domain, registrar, source, ts),
        )
        await db.commit()


async def log_click(domain: str, registrar: str) -> None:
    """Record a click on an affiliate registration link (redirect tracking)."""
    if not settings.enable_analytics:
        return
    ts = datetime.now(timezone.utc).isoformat()
    async with _db() as db:
        await db.execute(
            "INSERT INTO clicks (domain, registrar, ts) VALUES (?, ?, ?)",
            (domain, registrar, ts),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Read / aggregate
# ---------------------------------------------------------------------------


async def get_stats(days: int = 30) -> dict[str, Any]:
    """Return aggregate counts for the last N days."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    async with _db() as db:
        async with db.execute(
            "SELECT COUNT(*) as total, SUM(available) as available FROM domain_checks WHERE ts >= ?",
            (since,),
        ) as cur:
            row = await cur.fetchone()
            total_checks = row["total"] or 0
            available_checks = row["available"] or 0

        async with db.execute(
            "SELECT COUNT(*) as total FROM links_served WHERE ts >= ?",
            (since,),
        ) as cur:
            row = await cur.fetchone()
            links_served = row["total"] or 0

        async with db.execute(
            "SELECT COUNT(*) as total FROM clicks WHERE ts >= ?",
            (since,),
        ) as cur:
            row = await cur.fetchone()
            clicks = row["total"] or 0

        async with db.execute(
            "SELECT domain, COUNT(*) as n FROM domain_checks "
            "WHERE ts >= ? GROUP BY domain ORDER BY n DESC LIMIT 10",
            (since,),
        ) as cur:
            rows = await cur.fetchall()
            top_domains = [{"domain": r["domain"], "checks": r["n"]} for r in rows]

        async with db.execute(
            "SELECT registrar, COUNT(*) as n FROM clicks "
            "WHERE ts >= ? GROUP BY registrar ORDER BY n DESC",
            (since,),
        ) as cur:
            rows = await cur.fetchall()
            top_registrars = [{"registrar": r["registrar"], "clicks": r["n"]} for r in rows]

    return {
        "period_days": days,
        "total_checks": total_checks,
        "available_checks": available_checks,
        "taken_checks": total_checks - available_checks,
        "links_served": links_served,
        "clicks": clicks,
        "click_through_rate": round(clicks / links_served, 4) if links_served else 0.0,
        "top_domains": top_domains,
        "top_registrars": top_registrars,
    }
