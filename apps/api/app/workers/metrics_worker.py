"""Domain metrics refresh worker — re-vets active domains and records history. Run weekly."""

import asyncio
import logging

from sqlalchemy import select

from app.dependencies import async_session
from app.models.domain import Domain
from app.models.metrics_history import DomainMetricsHistory
from app.services.domain import DomainService

logger = logging.getLogger(__name__)


async def run() -> None:
    async with async_session() as db:
        result = await db.execute(
            select(Domain).where(Domain.status == "active")
        )
        domains = list(result.scalars().all())
        logger.info("Refreshing metrics for %d active domains", len(domains))

        updated = 0
        for domain in domains:
            try:
                refreshed = await DomainService.vet_domain(db, domain.id)
                history = DomainMetricsHistory(
                    domain_id=domain.id,
                    dr=int(refreshed.dr) if refreshed.dr is not None else None,
                    da=int(refreshed.da) if refreshed.da is not None else None,
                    wts=int(refreshed.wts) if refreshed.wts is not None else None,
                    organic_traffic=refreshed.organic_traffic,
                    spam_score=refreshed.spam_score,
                )
                db.add(history)
                updated += 1
            except Exception:
                logger.exception("Failed to refresh metrics for domain %s", domain.domain)

        await db.commit()
        logger.info("Metrics refresh complete: %d/%d domains updated", updated, len(domains))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
