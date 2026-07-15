"""Webhook dispatcher worker — dispatches webhook events with HMAC signing and retry."""

import asyncio
import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import and_, select

from app.dependencies import async_session
from app.models.webhook import Webhook

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [30, 120, 600]  # seconds (30s, 2m, 10m)


async def dispatch_event(
    event_type: str, payload: dict, webhook: Webhook
) -> bool:
    """Dispatch a single event to a webhook endpoint. Returns True on success."""
    body = json.dumps({
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    })
    signature = hmac.new(
        webhook.secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    webhook.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Weave-Signature": signature,
                        "X-Weave-Event": event_type,
                    },
                )
                if resp.status_code < 400:
                    logger.info("Webhook dispatched: %s -> %s (attempt %d)",
                        event_type, webhook.url, attempt + 1)
                    return True
                logger.warning("Webhook %s returned %d (attempt %d)",
                    webhook.url, resp.status_code, attempt + 1)
        except Exception:
            logger.exception("Webhook dispatch failed: %s -> %s (attempt %d)",
                event_type, webhook.url, attempt + 1)

        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAYS[attempt])

    logger.error("Webhook permanently failed: %s -> %s", event_type, webhook.url)
    return False


async def run_event(event_type: str, payload: dict) -> dict:
    """Dispatch an event to all active webhooks subscribed to this event type."""
    async with async_session() as db:
        result = await db.execute(
            select(Webhook).where(
                Webhook.active.is_(True),
                Webhook.events.contains([event_type]),
            )
        )
        webhooks = list(result.scalars().all())

        if not webhooks:
            return {"dispatched": 0, "success": 0, "failed": 0}

        tasks = [dispatch_event(event_type, payload, w) for w in webhooks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is False)

        logger.info("Webhook event %s: %d dispatched, %d success, %d failed",
            event_type, len(webhooks), success, failed)
        return {"dispatched": len(webhooks), "success": success, "failed": failed}


# Convenience functions for specific event types
async def run_link_placed(payload: dict) -> dict:
    return await run_event("link.placed", payload)

async def run_link_removed(payload: dict) -> dict:
    return await run_event("link.removed", payload)

async def run_credits_low(payload: dict) -> dict:
    return await run_event("credits.low", payload)

async def run_domain_vetted(payload: dict) -> dict:
    return await run_event("domain.vetted", payload)