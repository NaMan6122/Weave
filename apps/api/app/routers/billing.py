"""Stripe integration — checkout sessions, webhook handling, subscription management.

All endpoints are wired up but gracefully no-op when STRIPE_SECRET_KEY is not configured.
Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in environment to activate.
"""

import logging
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.domain import Domain
from app.services.credits import CreditService

logger = logging.getLogger(__name__)

router = APIRouter()

PRICE_IDS = {
    "early_access": "price_placeholder_early_access",
    "pro": "price_placeholder_pro",
    "credits_1000": "price_placeholder_credits_1000",
    "credits_5000": "price_placeholder_credits_5000",
}

CREDIT_TOP_UPS = {
    "credits_1000": Decimal("1000"),
    "credits_5000": Decimal("5000"),
}


def _get_stripe():
    """Import and configure stripe. Returns None if not configured."""
    if not getattr(settings, "stripe_secret_key", None):
        return None
    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key
        return stripe
    except ImportError:
        logger.warning("stripe package not installed")
        return None


@router.post("/checkout")
async def create_checkout_session(
    plan: str = "early_access",
    domain_id: str | None = None,
    user: Any = Depends(get_current_user),
) -> dict:
    """Create a Stripe Checkout session for subscription or credit top-up."""
    stripe = _get_stripe()
    if stripe is None:
        raise HTTPException(503, "Payments not configured. Set STRIPE_SECRET_KEY to enable.")

    price_id = PRICE_IDS.get(plan)
    if not price_id:
        raise HTTPException(400, f"Unknown plan: {plan}")

    mode = "payment" if plan.startswith("credits_") else "subscription"

    session = stripe.checkout.Session.create(
        mode=mode,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.cors_origins[0]}/dashboard/settings?payment=success",
        cancel_url=f"{settings.cors_origins[0]}/dashboard/settings?payment=cancelled",
        metadata={
            "user_id": str(user.id),
            "domain_id": domain_id or "",
            "plan": plan,
        },
    )

    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None, alias="stripe-signature"),
) -> dict:
    """Handle Stripe webhook events (checkout.session.completed, etc.)."""
    stripe = _get_stripe()
    if stripe is None:
        raise HTTPException(503, "Payments not configured")

    webhook_secret = getattr(settings, "stripe_webhook_secret", None)
    if not webhook_secret:
        raise HTTPException(503, "Webhook secret not configured")

    body = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            body, stripe_signature, webhook_secret
        )
    except Exception as e:
        raise HTTPException(400, f"Webhook verification failed: {e}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        plan = metadata.get("plan", "")
        domain_id = metadata.get("domain_id", "")

        # Credit top-up
        if plan in CREDIT_TOP_UPS and domain_id:
            import uuid
            amount = CREDIT_TOP_UPS[plan]
            await CreditService.add_bonus(
                db, uuid.UUID(domain_id), amount,
                f"Stripe credit top-up: {plan}",
            )
            await db.commit()
            logger.info("Credit top-up: %s credits to domain %s", amount, domain_id)

        # Subscription activation
        elif plan in ("early_access", "pro"):
            logger.info("Subscription activated: %s for user %s", plan, metadata.get("user_id"))
            # TODO: Update user.plan field when subscription management is fully wired

    elif event["type"] == "customer.subscription.deleted":
        logger.info("Subscription cancelled: %s", event["data"]["object"]["id"])
        # TODO: Downgrade user plan

    return {"received": True}


@router.get("/plans")
async def list_plans() -> dict:
    """Return available plans and pricing (static for now)."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "credits": 500,
                "features": ["5 link discoveries/day", "Basic matching", "Community support"],
            },
            {
                "id": "early_access",
                "name": "Early Access",
                "price": 29,
                "credits": 5000,
                "features": ["Unlimited discoveries", "Priority matching", "Email digest", "API access (1k req/day)"],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 79,
                "credits": 15000,
                "features": ["Everything in Early Access", "A-B-C routing", "API access (10k req/day)", "Priority support"],
            },
        ],
    }
