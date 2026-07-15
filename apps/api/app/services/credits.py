import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit import CreditAccount, CreditTransaction


EXPIRY_DAYS = 180
LOW_BALANCE_THRESHOLD = Decimal("10")

PLAN_BONUS_RATES = {
    "free": Decimal("0"),
    "starter": Decimal("0.10"),
    "pro": Decimal("0.25"),
    "agency": Decimal("0.50"),
}
PLAN_BONUS_MINIMUMS = {
    "free": Decimal("0"),
    "starter": Decimal("5"),
    "pro": Decimal("15"),
    "agency": Decimal("30"),
}

PLACEMENT_MULTIPLIERS = {
    "body": Decimal("1.0"),
    "sidebar": Decimal("0.5"),
    "footer": Decimal("0.3"),
    "author_bio": Decimal("0.3"),
}

DR_TIER_MULTIPLIERS = [
    (20, Decimal("0.5")),
    (40, Decimal("1.0")),
    (60, Decimal("2.0")),
    (80, Decimal("4.0")),
]
DR_TIER_MAX = Decimal("8.0")

# Minimum credit floor for any calculation
MIN_CREDITS = Decimal("1")


def credit_value(dr: int) -> int:
    """Standalone credit value: max(1, int(log10(max(dr,1)+1) * 100)).
    Used by seed scripts and standalone calculations."""
    import math
    return max(1, int(math.log10(max(dr, 1) + 1) * 100))


class CreditService:

    @staticmethod
    def calculate_credits_earned(
        source_dr: float,
        match_score: float = 70.0,
        placement_type: str = "body",
    ) -> Decimal:
        """PRD formula: base(10) * DR/50 * relevance * placement_quality."""
        base = Decimal("10")
        dr_mult = Decimal(str(max(source_dr, 1) / 50))
        relevance_mult = Decimal(str(max(min(match_score, 100), 0) / 100))
        placement_mult = PLACEMENT_MULTIPLIERS.get(placement_type, Decimal("1.0"))
        result = base * dr_mult * relevance_mult * placement_mult
        return max(result, MIN_CREDITS).quantize(Decimal("0.01"))

    @staticmethod
    def calculate_credits_required(target_dr: float) -> Decimal:
        """PRD formula: base(10) * DR tier multiplier."""
        base = Decimal("10")
        for threshold, multiplier in DR_TIER_MULTIPLIERS:
            if target_dr <= threshold:
                return (base * multiplier).quantize(Decimal("0.01"))
        return (base * DR_TIER_MAX).quantize(Decimal("0.01"))

    @staticmethod
    async def _get_account_for_update(
        db: AsyncSession, domain_id: uuid.UUID
    ) -> CreditAccount:
        result = await db.execute(
            select(CreditAccount)
            .where(CreditAccount.domain_id == domain_id)
            .with_for_update()
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise ValueError(f"No credit account for domain {domain_id}")
        return account

    @staticmethod
    async def earn_credits(
        db: AsyncSession,
        domain_id: uuid.UUID,
        amount: Decimal,
        link_id: uuid.UUID | None,
        description: str,
    ) -> CreditTransaction:
        account = await CreditService._get_account_for_update(db, domain_id)
        account.balance += amount
        account.lifetime_earned += amount

        txn = CreditTransaction(
            account_id=account.id,
            type="earned",
            amount=amount,
            link_id=link_id,
            description=description,
        )
        db.add(txn)
        await db.flush()
        return txn

    @staticmethod
    async def spend_credits(
        db: AsyncSession,
        domain_id: uuid.UUID,
        amount: Decimal,
        link_id: uuid.UUID | None,
        description: str,
    ) -> CreditTransaction:
        account = await CreditService._get_account_for_update(db, domain_id)
        if account.balance < amount:
            raise ValueError(
                f"Insufficient balance: {account.balance} < {amount}"
            )
        account.balance -= amount
        account.lifetime_spent += amount

        txn = CreditTransaction(
            account_id=account.id,
            type="spent",
            amount=amount,
            link_id=link_id,
            description=description,
        )
        db.add(txn)
        await db.flush()

        # Low balance notification (spec-003 §4)
        if account.balance < LOW_BALANCE_THRESHOLD:
            import asyncio
            domain_id_copy = domain_id
            balance_copy = account.balance
            async def _fire_low_balance():
                from app.workers.webhook_worker import run_credits_low
                await run_credits_low({
                    "domain_id": str(domain_id_copy),
                    "balance": float(balance_copy),
                    "threshold": float(LOW_BALANCE_THRESHOLD),
                })
            asyncio.create_task(_fire_low_balance())

            from app.models.domain import Domain
            from app.services.notification import NotificationService
            domain_result = await db.execute(
                select(Domain).where(Domain.id == domain_id)
            )
            domain = domain_result.scalar_one_or_none()
            if domain:
                await NotificationService.create(
                    db,
                    domain.user_id,
                    "credits_low",
                    "Low credit balance",
                    f"Your credit balance on {domain.domain} dropped below 10.",
                    {"domain_id": str(domain_id), "balance": str(account.balance)},
                )

        return txn

    @staticmethod
    async def reverse_credits(
        db: AsyncSession,
        domain_id: uuid.UUID,
        amount: Decimal,
        link_id: uuid.UUID | None,
        description: str,
    ) -> CreditTransaction:
        account = await CreditService._get_account_for_update(db, domain_id)
        account.balance -= amount

        txn = CreditTransaction(
            account_id=account.id,
            type="reversed",
            amount=amount,
            link_id=link_id,
            description=description,
        )
        db.add(txn)
        await db.flush()
        return txn

    @staticmethod
    async def add_bonus(
        db: AsyncSession,
        domain_id: uuid.UUID,
        amount: Decimal,
        description: str,
    ) -> CreditTransaction:
        account = await CreditService._get_account_for_update(db, domain_id)
        account.balance += amount
        account.lifetime_earned += amount

        txn = CreditTransaction(
            account_id=account.id,
            type="bonus",
            amount=amount,
            link_id=None,
            description=description,
        )
        db.add(txn)
        await db.flush()
        return txn

    @staticmethod
    async def get_balance(
        db: AsyncSession, domain_id: uuid.UUID
    ) -> CreditAccount:
        result = await db.execute(
            select(CreditAccount).where(CreditAccount.domain_id == domain_id)
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise ValueError(f"No credit account for domain {domain_id}")
        return account

    @staticmethod
    async def get_transaction_history(
        db: AsyncSession,
        domain_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CreditTransaction]:
        account = await CreditService.get_balance(db, domain_id)
        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.account_id == account.id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_transaction_count(
        db: AsyncSession, domain_id: uuid.UUID
    ) -> int:
        account = await CreditService.get_balance(db, domain_id)
        result = await db.execute(
            select(func.count())
            .select_from(CreditTransaction)
            .where(CreditTransaction.account_id == account.id)
        )
        return result.scalar_one()

    @staticmethod
    async def expire_old_credits(db: AsyncSession) -> int:
        """Expire credits from earned/bonus transactions older than 180 days (FIFO)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=EXPIRY_DAYS)

        # Find earned/bonus transactions older than cutoff
        old_txns_result = await db.execute(
            select(CreditTransaction).where(
                CreditTransaction.type.in_(["earned", "bonus"]),
                CreditTransaction.created_at < cutoff,
            )
        )
        old_txns = list(old_txns_result.scalars().all())

        # Get already-expired references
        already_expired_result = await db.execute(
            select(CreditTransaction.description).where(
                CreditTransaction.type == "expired"
            )
        )
        already_expired = {r[0] for r in already_expired_result.all() if r[0]}

        count = 0
        for txn in old_txns:
            marker = f"Expired txn:{txn.id}"
            if marker in already_expired:
                continue

            account = await CreditService._get_account_for_update(db,
                (await db.execute(
                    select(CreditAccount.domain_id).where(CreditAccount.id == txn.account_id)
                )).scalar_one()
            )

            expire_amount = min(txn.amount, account.balance)
            if expire_amount <= 0:
                continue

            account.balance -= expire_amount
            db.add(CreditTransaction(
                account_id=txn.account_id,
                type="expired",
                amount=expire_amount,
                link_id=txn.link_id,
                description=marker,
            ))
            count += 1

        await db.flush()
        return count

    @staticmethod
    async def transfer_credits(
        db: AsyncSession,
        from_domain_id: uuid.UUID,
        to_domain_id: uuid.UUID,
        amount: Decimal,
        user_id: str,
    ) -> tuple[CreditAccount, CreditAccount]:
        """Transfer credits between domains owned by the same user."""
        from app.models.domain import Domain

        if from_domain_id == to_domain_id:
            raise ValueError("Cannot transfer to the same domain")

        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

        # Verify ownership
        for did in (from_domain_id, to_domain_id):
            result = await db.execute(select(Domain).where(Domain.id == did))
            domain = result.scalar_one_or_none()
            if domain is None:
                raise ValueError(f"Domain {did} not found")
            if domain.user_id != uid:
                raise PermissionError("Cannot transfer between domains you don't own")
            if domain.status != "active" or domain.vetting_status != "approved":
                raise ValueError(f"Domain {domain.domain} is not active/approved")

        from_account = await CreditService._get_account_for_update(db, from_domain_id)
        if from_account.balance < amount:
            raise ValueError(f"Insufficient balance: {from_account.balance} < {amount}")

        to_account = await CreditService._get_account_for_update(db, to_domain_id)

        from_account.balance -= amount
        from_account.lifetime_spent += amount
        to_account.balance += amount
        to_account.lifetime_earned += amount

        db.add(CreditTransaction(
            account_id=from_account.id,
            type="spent",
            amount=amount,
            description=f"Transfer to domain {to_domain_id}",
        ))
        db.add(CreditTransaction(
            account_id=to_account.id,
            type="earned",
            amount=amount,
            description=f"Transfer from domain {from_domain_id}",
        ))

        await db.flush()
        return from_account, to_account

    @staticmethod
    async def distribute_monthly_bonus(
        db: AsyncSession,
        domain_id: uuid.UUID,
        plan: str,
    ) -> CreditTransaction | None:
        """Calculate and distribute monthly plan bonus based on last month's earnings."""
        rate = PLAN_BONUS_RATES.get(plan, Decimal("0"))
        minimum = PLAN_BONUS_MINIMUMS.get(plan, Decimal("0"))
        if rate == 0 and minimum == 0:
            return None

        # Sum earned transactions from last calendar month
        now = datetime.now(timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_of_prev = (first_of_month - timedelta(days=1)).replace(day=1)

        account = await CreditService.get_balance(db, domain_id)
        result = await db.execute(
            select(func.coalesce(func.sum(CreditTransaction.amount), Decimal("0")))
            .where(
                CreditTransaction.account_id == account.id,
                CreditTransaction.type == "earned",
                CreditTransaction.created_at >= first_of_prev,
                CreditTransaction.created_at < first_of_month,
            )
        )
        earned_last_month = result.scalar_one()

        bonus = max(earned_last_month * rate, minimum)
        if bonus <= 0:
            return None

        return await CreditService.add_bonus(
            db, domain_id, bonus,
            f"Monthly {plan} plan bonus ({rate*100:.0f}% of {earned_last_month} earned)",
        )

    @staticmethod
    def is_low_balance(account: CreditAccount) -> bool:
        return account.balance < LOW_BALANCE_THRESHOLD
