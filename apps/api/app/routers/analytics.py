import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.credit import CreditAccount, CreditTransaction
from app.models.domain import Domain
from app.models.link import Link
from app.models.metrics_history import DomainMetricsHistory
from app.models.user import User

router = APIRouter()


async def _require_domain(domain_id: uuid.UUID, user: User, db: AsyncSession) -> Domain:
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.user_id == user.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.get("/metrics/{domain_id}")
async def get_metrics(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_domain(domain_id, user, db)

    result = await db.execute(
        select(DomainMetricsHistory)
        .where(DomainMetricsHistory.domain_id == domain_id)
        .order_by(DomainMetricsHistory.recorded_at.asc())
    )
    history = result.scalars().all()

    return {
        "history": [
            {
                "recorded_at": h.recorded_at.isoformat(),
                "dr": h.dr,
                "da": h.da,
                "wts": h.wts,
                "organic_traffic": h.organic_traffic,
                "spam_score": float(h.spam_score) if h.spam_score is not None else None,
            }
            for h in history
        ]
    }


@router.get("/links/{domain_id}")
async def get_link_series(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_domain(domain_id, user, db)

    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    result = await db.execute(
        select(
            func.date(Link.created_at).label("date"),
            func.count().label("count"),
        )
        .where(
            (Link.source_domain_id == domain_id) | (Link.target_domain_id == domain_id),
            Link.created_at >= cutoff,
        )
        .group_by(func.date(Link.created_at))
        .order_by(func.date(Link.created_at).asc())
    )
    rows = result.all()

    series = []
    cumulative = 0
    for row in rows:
        cumulative += row.count
        series.append({
            "date": str(row.date),
            "new_that_week": row.count,
            "cumulative": cumulative,
        })

    return {"series": series}


@router.get("/credits/{domain_id}")
async def get_credit_series(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_domain(domain_id, user, db)

    account_result = await db.execute(
        select(CreditAccount).where(CreditAccount.domain_id == domain_id)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        return {"series": []}

    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    result = await db.execute(
        select(
            func.date_trunc("week", CreditTransaction.created_at).label("week"),
            CreditTransaction.type,
            func.sum(CreditTransaction.amount).label("total"),
        )
        .where(
            CreditTransaction.account_id == account.id,
            CreditTransaction.type.in_(["earned", "spent"]),
            CreditTransaction.created_at >= cutoff,
        )
        .group_by(func.date_trunc("week", CreditTransaction.created_at), CreditTransaction.type)
        .order_by(func.date_trunc("week", CreditTransaction.created_at).asc())
    )
    rows = result.all()

    weeks: dict[str, dict[str, float]] = {}
    for row in rows:
        week_key = str(row.week)[:10]
        if week_key not in weeks:
            weeks[week_key] = {"earned": 0.0, "spent": 0.0}
        weeks[week_key][row.type] = float(row.total)

    series = [
        {"week": week, "earned": data["earned"], "spent": data["spent"]}
        for week, data in sorted(weeks.items())
    ]

    return {"series": series}
