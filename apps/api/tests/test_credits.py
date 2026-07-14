import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit import CreditAccount
from app.models.domain import Domain
from app.models.user import User
from app.services.credits import CreditService, credit_value


# ---------------------------------------------------------------------------
# Pure calculation tests (no DB)
# ---------------------------------------------------------------------------

class TestCreditValue:
    def test_logarithmic_scaling(self):
        assert credit_value(10) < credit_value(50) < credit_value(90)

    def test_minimum_is_one(self):
        assert credit_value(0) >= 1

    def test_known_values(self):
        # log10(10+1)*100 = log10(11)*100 ≈ 104
        assert credit_value(10) == 104
        # log10(50+1)*100 = log10(51)*100 ≈ 170
        assert credit_value(50) == 170
        # log10(90+1)*100 = log10(91)*100 ≈ 195
        assert credit_value(90) == 195


class TestCalculateCreditsEarned:
    def test_returns_dr_based_value(self):
        result = CreditService.calculate_credits_earned(50)
        # PRD: 10 * (50/50) * (70/100) * 1.0 = 7.00
        assert result == Decimal("7.00")

    def test_low_dr(self):
        result = CreditService.calculate_credits_earned(10)
        # PRD: 10 * (10/50) * (70/100) * 1.0 = 1.40
        assert result == Decimal("1.40")

    def test_zero_dr(self):
        result = CreditService.calculate_credits_earned(0)
        # PRD floor: at least 1 credit
        assert result == Decimal("1.00")


class TestCalculateCreditsRequired:
    def test_returns_dr_based_value(self):
        # DR=50 → 50≤60 tier → multiplier=2.0 → 10*2.0=20.00
        assert CreditService.calculate_credits_required(50) == Decimal("20.00")

    def test_low_dr_target(self):
        # DR=10 → 10≤20 tier → multiplier=0.5 → 10*0.5=5.00
        assert CreditService.calculate_credits_required(10) == Decimal("5.00")

    def test_high_dr_target(self):
        # DR=90 → above 80 → max multiplier=8.0 → 10*8.0=80.00
        assert CreditService.calculate_credits_required(90) == Decimal("80.00")


# ---------------------------------------------------------------------------
# DB-backed earn / spend flow tests
# ---------------------------------------------------------------------------

@pytest.fixture
async def domain_with_account(db: AsyncSession, fake_user: User) -> Domain:
    domain = Domain(
        user_id=fake_user.id,
        domain="credits-test.com",
        status="active",
        verified=True,
    )
    db.add(domain)
    await db.flush()

    account = CreditAccount(
        domain_id=domain.id,
        balance=Decimal("0.00"),
        lifetime_earned=Decimal("0.00"),
        lifetime_spent=Decimal("0.00"),
    )
    db.add(account)
    await db.commit()
    await db.refresh(domain)
    return domain


class TestEarnCredits:
    async def test_earn_credits_increases_balance(self, db: AsyncSession, domain_with_account: Domain):
        txn = await CreditService.earn_credits(
            db, domain_with_account.id, Decimal("10.00"), None, "test earn"
        )
        assert txn.type == "earned"
        assert txn.amount == Decimal("10.00")

        account = await CreditService.get_balance(db, domain_with_account.id)
        assert account.balance == Decimal("10.00")
        assert account.lifetime_earned == Decimal("10.00")

    async def test_earn_credits_accumulates(self, db: AsyncSession, domain_with_account: Domain):
        await CreditService.earn_credits(db, domain_with_account.id, Decimal("5.00"), None, "first")
        await CreditService.earn_credits(db, domain_with_account.id, Decimal("3.00"), None, "second")

        account = await CreditService.get_balance(db, domain_with_account.id)
        assert account.balance == Decimal("8.00")


class TestSpendCredits:
    async def test_spend_credits_decreases_balance(self, db: AsyncSession, domain_with_account: Domain):
        await CreditService.earn_credits(db, domain_with_account.id, Decimal("20.00"), None, "seed")
        txn = await CreditService.spend_credits(
            db, domain_with_account.id, Decimal("7.50"), None, "test spend"
        )
        assert txn.type == "spent"
        assert txn.amount == Decimal("7.50")

        account = await CreditService.get_balance(db, domain_with_account.id)
        assert account.balance == Decimal("12.50")
        assert account.lifetime_spent == Decimal("7.50")

    async def test_spend_insufficient_balance_raises(self, db: AsyncSession, domain_with_account: Domain):
        with pytest.raises(ValueError, match="Insufficient balance"):
            await CreditService.spend_credits(
                db, domain_with_account.id, Decimal("1.00"), None, "overdraw"
            )
