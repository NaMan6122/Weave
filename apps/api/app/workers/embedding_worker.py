"""Embedding worker — generates pgvector embeddings for pages without them. Run daily."""

import asyncio
import logging

from sqlalchemy import select

from app.dependencies import async_session
from app.models.page import Page
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


async def run() -> None:
    async with async_session() as db:
        # Find pages without embeddings that are active
        stmt = (
            select(Page)
            .where(Page.embedding.is_(None))
            .where(Page.status == "active")
            .limit(BATCH_SIZE)
        )
        result = await db.execute(stmt)
        pages = list(result.scalars().all())

        logger.info("Found %d pages without embeddings", len(pages))

        if not pages:
            return

        successes = 0
        failures = 0

        for page in pages:
            try:
                # Fetch page content
                content = await _fetch_page_content(page.url)
                if not content:
                    logger.warning("No content fetched for %s", page.url)
                    failures += 1
                    continue

                # Generate embedding
                embedding = await EmbeddingService.embed_text(content)

                # Store embedding
                page.embedding = embedding
                page.last_crawled_at = __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                )

                await db.flush()
                successes += 1
                logger.debug("Embedded page %s (%d chars)", page.url, len(content))

            except Exception:
                logger.exception("Failed to embed page %s", page.url)
                failures += 1

        await db.commit()
        logger.info(
            "Embedding worker complete: %d successes, %d failures",
            successes,
            failures,
        )


async def _fetch_page_content(url: str) -> str | None:
    """Fetch and extract text content from a page URL."""
    try:
        async with __import__("httpx").AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; weaveBot/1.0; +https://weave.io/bot)"},
        ) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return None

            # Simple text extraction (could be enhanced with BeautifulSoup)
            html = resp.text
            # Remove scripts and styles
            import re

            html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
            # Get text from body
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()

            return text[:8000]  # Limit for embedding

    except Exception:
        logger.exception("Error fetching content for %s", url)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())