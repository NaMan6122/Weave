"""
Metrics fetcher — pulls real SEO metrics from external APIs during domain vetting.

Supports:
- Moz API (free tier): Domain Authority, spam score
- DataForSEO (if configured): organic traffic, DR estimate

Falls back gracefully if APIs aren't configured — returns None for missing metrics.
"""

import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DomainMetrics:
    da: float | None = None
    dr: float | None = None
    spam_score: float | None = None
    organic_traffic: int | None = None
    domain_age_days: int | None = None


async def fetch_moz_metrics(domain: str) -> DomainMetrics:
    """Fetch DA and spam score from Moz API (free tier).

    Requires MOZ_API_KEY in settings. Returns empty metrics if not configured.
    Moz free tier: 10 requests/month for URL Metrics.
    """
    api_key = settings.moz_api_key
    if not api_key:
        logger.debug("Moz API key not configured, skipping")
        return DomainMetrics()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://lsapi.seomoz.com/v2/url_metrics",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "targets": [domain],
                    "metrics": ["domain_authority", "spam_score"],
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if results:
                r = results[0]
                return DomainMetrics(
                    da=r.get("domain_authority"),
                    spam_score=r.get("spam_score"),
                )
    except Exception as e:
        logger.warning("Moz API call failed for %s: %s", domain, e)

    return DomainMetrics()


async def fetch_dataforseo_metrics(domain: str) -> DomainMetrics:
    """Fetch traffic and DR estimate from DataForSEO API.

    Requires DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD in settings.
    Returns empty metrics if not configured.
    """
    login = getattr(settings, "dataforseo_login", None)
    password = getattr(settings, "dataforseo_password", None)
    if not login or not password:
        logger.debug("DataForSEO not configured, skipping")
        return DomainMetrics()

    try:
        async with httpx.AsyncClient(timeout=15, auth=(login, password)) as client:
            resp = await client.post(
                "https://api.dataforseo.com/v3/domain_analytics/technologies/domain_technologies/live",
                json=[{"target": domain, "limit": 1}],
            )
            resp.raise_for_status()
            data = resp.json()

            tasks = data.get("tasks", [])
            if tasks and tasks[0].get("result"):
                r = tasks[0]["result"][0]
                return DomainMetrics(
                    organic_traffic=r.get("organic_traffic"),
                    dr=r.get("domain_rank"),
                )
    except Exception as e:
        logger.warning("DataForSEO call failed for %s: %s", domain, e)

    return DomainMetrics()


async def fetch_domain_age(domain: str) -> int | None:
    """Estimate domain age via WHOIS creation date.

    Uses python-whois (already a dependency). Returns age in days or None.
    """
    try:
        import whois
        from datetime import datetime, timezone

        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date:
            age = (datetime.now(timezone.utc) - creation_date.replace(tzinfo=timezone.utc)).days
            return max(0, age)
    except Exception as e:
        logger.debug("WHOIS lookup failed for %s: %s", domain, e)

    return None


async def fetch_all_metrics(domain: str) -> DomainMetrics:
    """Fetch metrics from all available sources and merge.

    Priority: DataForSEO > Moz > WHOIS for overlapping fields.
    """
    moz = await fetch_moz_metrics(domain)
    dseo = await fetch_dataforseo_metrics(domain)
    age = await fetch_domain_age(domain)

    return DomainMetrics(
        da=dseo.da or moz.da,
        dr=dseo.dr or moz.da,  # Use DA as DR proxy if no direct DR source
        spam_score=moz.spam_score,
        organic_traffic=dseo.organic_traffic,
        domain_age_days=age,
    )
