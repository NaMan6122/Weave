"""Credit expiration worker — expires old credits. Run daily."""

import asyncio
import logging

from app.dependencies import async_session
from app.services.credits import CreditService

logger = logging.getLogger(__name__)


async def run() -> None:
    async with async_session() as db:
        expired_count = await CreditService.expire_old_credits(db)
        await db.commit()
        logger.info("Credit expiration complete: %d credits expired", expired_count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
