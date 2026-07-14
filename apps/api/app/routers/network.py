"""Network browsing endpoint — browse member sites with filters."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.domain import Domain

router = APIRouter()


@router.get("/")
async def browse_network(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    niche: str | None = Query(None),
    min_dr: int | None = Query(None),
    max_dr: int | None = Query(None),
    language: str | None = Query(None),
    min_traffic: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> dict:
    conditions = [
        Domain.status == "active",
        Domain.vetting_status == "approved",
    ]

    if niche:
        conditions.append(Domain.niche == niche)
    if min_dr is not None:
        conditions.append(Domain.dr >= min_dr)
    if max_dr is not None:
        conditions.append(Domain.dr <= max_dr)
    if language:
        conditions.append(Domain.language == language)
    if min_traffic is not None:
        conditions.append(Domain.organic_traffic >= min_traffic)

    count_result = await db.execute(
        select(func.count()).select_from(Domain).where(*conditions)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Domain)
        .where(*conditions)
        .order_by(Domain.dr.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    domains = list(result.scalars().all())

    sites = []
    for d in domains:
        # Mask domain name for privacy (PRD spec)
        name = d.domain
        if len(name) > 4:
            masked = name[:3] + "***" + name[name.rfind("."):]
        else:
            masked = name

        sites.append({
            "domain": masked,
            "niche": d.niche,
            "dr": d.dr or 0,
            "monthly_traffic": d.organic_traffic or 0,
            "language": d.language or "en",
            "domain_age_months": (d.domain_age_days or 0) // 30,
            "wts": d.wts or 0,
        })

    return {
        "sites": sites,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
