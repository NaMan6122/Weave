"""SLA checker worker — flags links approaching or past SLA deadlines. Run daily."""

import asyncio
import logging

from app.dependencies import async_session
from app.services.crawler import LinkValidatorService

logger = logging.getLogger(__name__)


async def run() -> None:
    async with async_session() as db:
        flagged_links = await LinkValidatorService.check_sla_expirations(db)
        await db.commit()
        logger.info("SLA check complete: %d links flagged", len(flagged_links))
        for link in flagged_links:
            logger.warning("SLA flag: link %s status=%s", link.id, link.status)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
