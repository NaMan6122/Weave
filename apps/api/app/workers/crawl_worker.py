"""Link validator worker — validates all placed links. Run daily."""

import asyncio
import logging

from app.dependencies import async_session
from app.services.crawler import LinkValidatorService

logger = logging.getLogger(__name__)


async def run() -> None:
    async with async_session() as db:
        result = await LinkValidatorService.validate_all_links(db)
        await db.commit()
        logger.info("Crawl complete: %s", result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
