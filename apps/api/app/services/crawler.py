import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import urlparse

import httpx
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain
from app.models.link import Link, Triangle
from app.models.page import Page
from app.services.credits import CreditService
from app.services.triangulation import TriangulationService

USER_AGENTS = [
    "Mozilla/5.0 (compatible; weaveBot/1.0; +https://weave.io/bot)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

MAX_CONCURRENT_PER_DOMAIN = 3
PENALTY_MULTIPLIER = 2
STRIKES_THRESHOLD = 3
STRIKES_WINDOW_DAYS = 90


class LinkValidatorService:

    @staticmethod
    async def validate_link(db: AsyncSession, link_id: uuid.UUID) -> str:
        result = await db.execute(select(Link).where(Link.id == link_id))
        link = result.scalar_one_or_none()
        if link is None:
            raise ValueError(f"Link {link_id} not found")

        result = await db.execute(
            select(Page).where(Page.id == link.source_page_id)
        )
        source_page = result.scalar_one_or_none()
        if source_page is None:
            raise ValueError(f"Source page {link.source_page_id} not found")

        result = await db.execute(
            select(Page).where(Page.id == link.target_page_id)
        )
        target_page = result.scalar_one_or_none()
        if target_page is None:
            raise ValueError(f"Target page {link.target_page_id} not found")

        now = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=15.0,
                headers={"User-Agent": random.choice(USER_AGENTS)},
            ) as client:
                resp = await client.get(source_page.url)

            if resp.status_code >= 400:
                new_status = "broken"
            else:
                html = resp.text
                target_url = target_page.url
                anchor = link.anchor_text

                if target_url in html and anchor in html:
                    new_status = "live"
                elif target_url in html:
                    new_status = "modified"
                else:
                    new_status = "removed"

        except (httpx.HTTPError, httpx.TimeoutException):
            new_status = "broken"

        link.status = new_status
        link.verified_at = now

        if new_status in ("removed", "broken"):
            await LinkValidatorService._handle_failure(db, link, new_status, now)

        await db.flush()
        return new_status

    @staticmethod
    async def _handle_failure(
        db: AsyncSession, link: Link, new_status: str, now: datetime
    ) -> None:
        if new_status == "removed":
            link.removed_at = now

        # PRD: penalty = credit_value(their_dr) * 2
        source_domain_result = await db.execute(
            select(Domain).where(Domain.id == link.source_domain_id)
        )
        source_domain = source_domain_result.scalar_one_or_none()

        if source_domain:
            base_penalty = CreditService.calculate_credits_earned(
                source_domain.dr or 0, 70.0, "body"
            )
            penalty = base_penalty * PENALTY_MULTIPLIER
            try:
                await CreditService.reverse_credits(
                    db,
                    link.source_domain_id,
                    penalty,
                    link.id,
                    f"Link {new_status}: penalty ({PENALTY_MULTIPLIER}x) for link {link.id}",
                )
            except ValueError:
                pass

        # Restore credits to the target domain owner
        if link.credits_earned and link.credits_earned > 0:
            try:
                await CreditService.earn_credits(
                    db,
                    link.target_domain_id,
                    link.credits_earned,
                    link.id,
                    f"Credits restored: partner link {new_status}",
                )
            except ValueError:
                pass

        # Check triangle health
        if link.triangle_id is not None:
            await TriangulationService.check_triangle_health(db, link.triangle_id)

        # Three-strikes check on the source domain
        await LinkValidatorService._check_three_strikes(db, link.source_domain_id, now)

    @staticmethod
    async def _check_three_strikes(
        db: AsyncSession, domain_id: uuid.UUID, now: datetime
    ) -> None:
        cutoff = now - timedelta(days=STRIKES_WINDOW_DAYS)
        result = await db.execute(
            select(func.count()).select_from(Link).where(
                Link.source_domain_id == domain_id,
                Link.status.in_(["removed", "broken"]),
                Link.verified_at >= cutoff,
            )
        )
        failure_count = result.scalar_one()

        if failure_count >= STRIKES_THRESHOLD:
            domain_result = await db.execute(
                select(Domain).where(Domain.id == domain_id)
            )
            domain = domain_result.scalar_one_or_none()
            if domain and domain.status != "suspended":
                domain.status = "suspended"
                domain.rejection_reason = (
                    f"Suspended: {failure_count} link failures in {STRIKES_WINDOW_DAYS} days"
                )

    @staticmethod
    async def validate_all_links(db: AsyncSession) -> dict:
        result = await db.execute(
            select(Link).where(Link.status.in_(["placed", "live", "modified"]))
        )
        links = list(result.scalars().all())

        summary = {"total": len(links), "live": 0, "modified": 0, "removed": 0, "broken": 0}

        # Group links by source domain for rate limiting
        domain_links: dict[uuid.UUID, list[Link]] = {}
        for link in links:
            domain_links.setdefault(link.source_domain_id, []).append(link)

        # Process each domain's links with concurrency limit
        sem = asyncio.Semaphore(MAX_CONCURRENT_PER_DOMAIN)

        async def validate_with_limit(link: Link) -> str:
            async with sem:
                return await LinkValidatorService.validate_link(db, link.id)

        for domain_id, domain_link_list in domain_links.items():
            tasks = [validate_with_limit(link) for link in domain_link_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, str) and r in summary:
                    summary[r] += 1

        return summary

    @staticmethod
    async def check_sla_expirations(db: AsyncSession) -> list[Link]:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Link).where(
                Link.sla_expires_at < now,
                Link.status.in_(["placed", "live"]),
            )
        )
        expired_links = list(result.scalars().all())

        for link in expired_links:
            link.status = "sla_expired"

        if expired_links:
            await db.flush()

        return expired_links
