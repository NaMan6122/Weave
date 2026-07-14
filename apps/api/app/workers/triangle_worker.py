"""Triangle formation worker — finds unmatched links and forms triangles. Run hourly."""

import asyncio
import logging

from sqlalchemy import select

from app.dependencies import async_session
from app.models.link import Link
from app.services.triangulation import TriangulationService

logger = logging.getLogger(__name__)


async def run() -> None:
    async with async_session() as db:
        result = await db.execute(
            select(Link).where(
                Link.status == "placed",
                Link.triangle_id.is_(None),
            )
        )
        links = list(result.scalars().all())
        logger.info("Found %d placed links without triangles", len(links))

        successes = 0
        failures = 0
        for link in links:
            try:
                triangle = await TriangulationService.form_triangle(
                    db, link.source_domain_id, link.target_domain_id
                )
                if triangle:
                    successes += 1
                else:
                    failures += 1
            except Exception:
                logger.exception("Triangle formation failed for link %s", link.id)
                failures += 1

        await db.commit()
        logger.info(
            "Triangle formation complete: %d successes, %d failures",
            successes,
            failures,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
