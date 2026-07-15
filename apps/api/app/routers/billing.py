"""DoDo Payments integration — checkout sessions, webhook handling, subscription management.

All endpoints are wired up but gracefully no-op when DODO_API_KEY is not configured.
Set DODO_API_KEY and DODO_WEBHOOK_SECRET in environment to activate.
"""

import json
import logging
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.domain import Domain
from app.models.user import User
from app.services.credits import CreditService

logger = logging.getLogger(__name__)

router = APIRouter()

CREDIT_TOP_UPS = {
    "credits_1000": Decimal("1000"),
    "credits_5000": Decimal("5000"),
}

DODO_PLAN_IDS = json.loads(settings.dodo_product_ids)


def _get_dodo_config():
    """Check DoDo configuration. Returns None if not configured."""
    if not getattr(settings, "dodo_api_key", None):
        return None
    return {
        "api_key": settings.dodo_api_key,
        "webhook_secret": settings.dodo_webhook_secret,
        "base_url": settings.dodo_base_url,
        "product_ids": DODO_PLAN_IDS,
    }


@router.post("/checkout")
async def create_checkout_session(
    plan: str = "starter_monthly",
    domain_id: str | None = None,
    user: Any = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a DoDo Checkout session for subscription or credit top-up."""
    dodo_config = _get_dodo_config()
    if dodo_config is None:
        raise HTTPException(503, "Payments not configured. Set DODO_API_KEY to enable.")

    product_id = dodo_config["product_ids"].get(plan)
    if not product_id:
        raise HTTPException(400, f"Unknown plan: {plan}. Available: {list(dodo_config['product_ids'].keys())}")

    if domain_id:
        result = await db.execute(
            select(Domain).where(Domain.id == uuid.UUID(domain_id), Domain.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(400, "Domain not found or not owned by you")

    is_credit_purchase = plan.startswith("credits_")

    try:
        async with __import__("httpx").AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{dodo_config['base_url']}/v1/checkout/sessions",
                headers={
                    "Authorization": f"Bearer {dodo_config['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "product_id": product_id,
                    "mode": "payment" if is_credit_purchase else "subscription",
                    "success_url": f"{settings.cors_origins[0]}/dashboard/settings?payment=success",
                    "cancel_url": f"{settings.cors_origins[0]}/dashboard/settings?payment=cancelled",
                    "metadata": {
                        "user_id": str(user.id),
                        "domain_id": domain_id or "",
                        "plan": plan,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"checkout_url": data.get("checkout_url"), "session_id": data.get("session_id")}
    except Exception as e:
        logger.exception("DoDo checkout session creation failed")
        raise HTTPException(502, f"Payment provider error: {e}")


@router.post("/webhook")
async def dodo_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    dodo_signature: str = Header(None, alias="dodo-signature"),
) -> dict:
    """Handle DoDo webhook events."""
    dodo_config = _get_dodo_config()
    if dodo_config is None:
        raise HTTPException(503, "Payments not configured")

    webhook_secret = dodo_config.get("webhook_secret")
    if not webhook_secret:
        raise HTTPException(503, "Webhook secret not configured")

    body = await request.body()

    # Verify signature (HMAC-SHA256)
    import hmac
    import hashlib

    expected = hmac.new(
        webhook_secret.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, dodo_signature or ""):
        raise HTTPException(400, "Invalid webhook signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON body")

    event_type = event.get("type", "")

    if event_type == "checkout.completed":
        session = event.get("data", {})
        metadata = session.get("metadata", {})
        plan = metadata.get("plan", "")
        domain_id_str = metadata.get("domain_id", "")
        user_id_str = metadata.get("user_id", "")

        if plan in CREDIT_TOP_UPS and domain_id_str:
            amount = CREDIT_TOP_UPS[plan]
            await CreditService.add_bonus(
                db, uuid.UUID(domain_id_str), amount,
                f"DoDo credit top-up: {plan}",
            )
            await db.commit()
            logger.info("Credit top-up: %s credits to domain %s", amount, domain_id_str)

        elif plan in ("starter_monthly", "pro_monthly", "agency_monthly"):
            if user_id_str:
                update_result = await db.execute(
                    select(User).where(User.id == uuid.UUID(user_id_str))
                )
                user_obj = update_result.scalar_one_or_none()
                if user_obj:
                    user_obj.plan = plan.split("_")[0]
                    user_obj.dodo_customer_id = session.get("customer_id")
                    await db.commit()
            logger.info("Subscription activated: %s for user %s", plan, user_id_str)

    elif event_type == "subscription.cancelled":
        subscription = event.get("data", {})
        customer_id = subscription.get("customer_id", "")
        if customer_id:
            update_result = await db.execute(
                select(User).where(User.dodo_customer_id == customer_id)
            )
            user_obj = update_result.scalar_one_or_none()
            if user_obj:
                user_obj.plan = "free"
                await db.commit()
                logger.info("Subscription cancelled for user %s", user_obj.id)

    elif event_type == "subscription.updated":
        subscription = event.get("data", {})
        customer_id = subscription.get("customer_id", "")
        new_plan = subscription.get("plan_id", "")
        if customer_id and new_plan:
            update_result = await db.execute(
                select(User).where(User.dodo_customer_id == customer_id)
            )
            user_obj = update_result.scalar_one_or_none()
            if user_obj:
                user_obj.plan = new_plan.split("_")[0] if "_" in new_plan else new_plan
                await db.commit()
                logger.info("Subscription updated for user %s to %s", user_obj.id, new_plan)

    return {"received": True}


@router.get("/portal")
async def get_billing_portal(
    user: Any = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate DoDo Billing Portal session for the user."""
    dodo_config = _get_dodo_config()
    if dodo_config is None:
        raise HTTPException(503, "Payments not configured. Set DODO_API_KEY to enable.")

    update_result = await db.execute(
        select(User).where(User.id == uuid.UUID(user.id))
    )
    user_obj = update_result.scalar_one_or_none()
    if user_obj is None or not user_obj.dodo_customer_id:
        raise HTTPException(400, "No billing account found. Subscribe first.")

    try:
        async with __import__("httpx").AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{dodo_config['base_url']}/v1/portal/sessions",
                headers={
                    "Authorization": f"Bearer {dodo_config['api_key']}",
                    "Content-Type": "application/json",
                },
                json={"customer_id": user_obj.dodo_customer_id},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"portal_url": data.get("portal_url")}
    except Exception as e:
        logger.exception("DoDo portal session creation failed")
        raise HTTPException(502, f"Payment provider error: {e}")


@router.get("/plans")
async def list_plans() -> dict:
    """Return available plans and pricing with DoDo product IDs."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "dodo_product_id": None,
                "credits": 500,
                "features": ["5 link discoveries/day", "Basic matching", "Community support"],
            },
            {
                "id": "starter_monthly",
                "name": "Starter",
                "price": 29,
                "dodo_product_id": DODO_PLAN_IDS.get("starter_monthly", ""),
                "credits": 5000,
                "features": ["Unlimited discoveries", "Priority matching", "Email digest", "API access (1k req/day)"],
            },
            {
                "id": "pro_monthly",
                "name": "Pro",
                "price": 79,
                "dodo_product_id": DODO_PLAN_IDS.get("pro_monthly", ""),
                "credits": 15000,
                "features": ["Everything in Starter", "A-B-C routing", "API access (10k req/day)", "Priority support"],
            },
            {
                "id": "agency_monthly",
                "name": "Agency",
                "price": 199,
                "dodo_product_id": DODO_PLAN_IDS.get("agency_monthly", ""),
                "credits": 50000,
                "features": ["Everything in Pro", "White-label dashboard", "Dedicated support", "Unlimited API"],
            },
        ],
        "credit_packs": [
            {"id": "credits_1000", "name": "1,000 Credits", "price": 10, "dodo_product_id": DODO_PLAN_IDS.get("credits_1000", "")},
            {"id": "credits_5000", "name": "5,000 Credits", "price": 40, "dodo_product_id": DODO_PLAN_IDS.get("credits_5000", "")},
        ],
    }