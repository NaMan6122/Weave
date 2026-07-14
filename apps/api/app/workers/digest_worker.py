"""Weekly email digest worker — sends summary to all active domain owners."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import async_session
from app.models.credit import CreditAccount, CreditTransaction
from app.models.domain import Domain
from app.models.link import Link
from app.models.user import User

logger = logging.getLogger(__name__)


async def _build_digest(db: AsyncSession, domain: Domain) -> dict | None:
    """Build digest data for a single domain. Returns None if no activity."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Links placed this week (outgoing)
    placed_result = await db.execute(
        select(func.count()).select_from(Link).where(
            Link.source_domain_id == domain.id,
            Link.placed_at >= week_ago,
        )
    )
    placements_made = placed_result.scalar_one()

    # Backlinks received this week (incoming)
    received_result = await db.execute(
        select(func.count()).select_from(Link).where(
            Link.target_domain_id == domain.id,
            Link.placed_at >= week_ago,
        )
    )
    backlinks_received = received_result.scalar_one()

    # Credit movement
    account_result = await db.execute(
        select(CreditAccount).where(CreditAccount.domain_id == domain.id)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        return None

    earned_result = await db.execute(
        select(func.coalesce(func.sum(CreditTransaction.amount), 0)).where(
            CreditTransaction.account_id == account.id,
            CreditTransaction.type == "earned",
            CreditTransaction.created_at >= week_ago,
        )
    )
    credits_earned = float(earned_result.scalar_one())

    spent_result = await db.execute(
        select(func.coalesce(func.sum(CreditTransaction.amount), 0)).where(
            CreditTransaction.account_id == account.id,
            CreditTransaction.type == "spent",
            CreditTransaction.created_at >= week_ago,
        )
    )
    credits_spent = float(spent_result.scalar_one())

    if placements_made == 0 and backlinks_received == 0 and credits_earned == 0:
        return None

    return {
        "domain": domain.domain,
        "dr": domain.dr or 0,
        "credit_balance": float(account.balance),
        "placements_made": placements_made,
        "backlinks_received": backlinks_received,
        "credits_earned": credits_earned,
        "credits_spent": credits_spent,
    }


async def _send_digest_email(user_email: str, digests: list[dict]) -> None:
    """Send digest email via Resend (or log if not configured)."""
    try:
        from app.config import settings
        resend_key = getattr(settings, "resend_api_key", None)
        if not resend_key:
            logger.info("Digest for %s: %s (email not sent — no RESEND_API_KEY)", user_email, digests)
            return

        import httpx
        async with httpx.AsyncClient() as client:
            # Build simple text email
            lines = ["Your weekly weave digest:\n"]
            for d in digests:
                lines.append(f"  {d['domain']} (DR {d['dr']})")
                lines.append(f"    Placements made: {d['placements_made']}")
                lines.append(f"    Backlinks received: {d['backlinks_received']}")
                lines.append(f"    Credits earned: +{d['credits_earned']:.0f}")
                lines.append(f"    Credits spent: -{d['credits_spent']:.0f}")
                lines.append(f"    Balance: {d['credit_balance']:.0f}")
                lines.append("")

            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_key}"},
                json={
                    "from": "weave <digest@weave.io>",
                    "to": [user_email],
                    "subject": "Your weekly weave digest",
                    "text": "\n".join(lines),
                },
            )
            logger.info("Digest sent to %s", user_email)
    except Exception as e:
        logger.error("Failed to send digest to %s: %s", user_email, e)


async def run() -> None:
    async with async_session() as db:
        # Get all users with active domains
        result = await db.execute(
            select(User).join(Domain, Domain.user_id == User.id).where(
                Domain.status == "active"
            ).distinct()
        )
        users = list(result.scalars().all())

        for user in users:
            domains_result = await db.execute(
                select(Domain).where(
                    Domain.user_id == user.id, Domain.status == "active"
                )
            )
            domains = list(domains_result.scalars().all())

            digests = []
            for domain in domains:
                digest = await _build_digest(db, domain)
                if digest:
                    digests.append(digest)

            if digests:
                await _send_digest_email(user.email, digests)

    logger.info("Weekly digest complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
