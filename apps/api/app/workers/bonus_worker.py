"""Monthly bonus worker — distributes plan bonuses on 1st of each month."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.dependencies import async_session
from app.models.credit import CreditAccount, CreditTransaction
from app.models.domain import Domain
from app.models.user import User
from app.services.credits import CreditService, PLAN_BONUS_RATES, PLAN_BONUS_MINIMUMS

logger = logging.getLogger(__name__)


async def run() -> None:
    async with async_session() as db:
        now = datetime.now(timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_of_prev = (first_of_month - timedelta(days=1)).replace(day=1)

        # Get active domains with paid plans
        result = await db.execute(
            select(Domain, User)
            .join(User, Domain.user_id == User.id)
            .where(Domain.status == "active")
        )
        domain_users = list(result.all())

        if not domain_users:
            logger.info("No active domains to process bonuses for")
            return

        bonuses_distributed = 0
        for domain, user_obj in domain_users:
            plan = user_obj.plan
            rate = PLAN_BONUS_RATES.get(plan)
            minimum = PLAN_BONUS_MINIMUMS.get(plan)
            if rate is None or (rate == 0 and minimum == 0):
                continue

            try:
                account_result = await db.execute(
                    select(CreditAccount).where(CreditAccount.domain_id == domain.id)
                )
                account = account_result.scalar_one_or_none()
                if not account:
                    continue

                # Sum earned transactions from last calendar month
                earned_result = await db.execute(
                    select(func.coalesce(func.sum(CreditTransaction.amount), 0))
                    .where(
                        CreditTransaction.account_id == account.id,
                        CreditTransaction.type == "earned",
                        CreditTransaction.created_at >= first_of_prev,
                        CreditTransaction.created_at < first_of_month,
                    )
                )
                earned_last_month = float(earned_result.scalar_one())

                bonus = max(earned_last_month * float(rate), float(minimum))
                if bonus <= 0:
                    continue

                await CreditService.add_bonus(
                    db,
                    domain.id,
                    bonus,
                    f"Monthly {plan} plan bonus ({float(rate)*100:.0f}% of {earned_last_month} earned)",
                )
                bonuses_distributed += 1
                logger.info("Bonus: %s -> %s (%.2f credits)", plan, domain.domain, bonus)

            except Exception:
                logger.exception("Bonus calculation failed for domain %s", domain.domain)

        await db.commit()
        logger.info("Monthly bonuses complete: %d domains received bonuses", bonuses_distributed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())