import csv
import io
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_admin
from app.models.domain import Domain
from app.models.link import Link
from app.models.page import Page
from app.schemas.link import LinkResponse
from app.services.crawler import LinkValidatorService
from app.services.matching import MatchingService

router = APIRouter()


@router.get("/", response_model=list[LinkResponse])
async def list_links(
    status: str | None = Query(None, description="Filter by link status"),
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> list[LinkResponse]:
    """List all links for the current user's domains."""
    # Get user's domain IDs
    result = await db.execute(
        select(Domain.id).where(Domain.user_id == user.id)
    )
    domain_ids = [row[0] for row in result.all()]
    if not domain_ids:
        return []

    conditions = [
        (Link.source_domain_id.in_(domain_ids))
        | (Link.target_domain_id.in_(domain_ids))
    ]
    if status:
        conditions.append(Link.status == status)

    from sqlalchemy import and_

    stmt = (
        select(Link)
        .where(and_(*conditions))
        .order_by(Link.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/health", response_model=list[LinkResponse])
async def link_health(
    domain: str = Query(..., description="Domain name"),
    status: str = Query("all", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> list[LinkResponse]:
    """Get link health for a specific domain."""
    result = await db.execute(
        select(Domain).where(
            Domain.domain == domain,
            Domain.user_id == user.id,
        )
    )
    domain_obj = result.scalar_one_or_none()
    if domain_obj is None:
        raise HTTPException(status_code=404, detail="Domain not found")

    links = await MatchingService.get_link_health(
        db, domain_obj.id, status_filter=status
    )
    return links


@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> LinkResponse:
    """Get a single link by ID."""
    # Get user's domain IDs for authorization
    result = await db.execute(
        select(Domain.id).where(Domain.user_id == user.id)
    )
    domain_ids = [row[0] for row in result.all()]

    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")

    if (
        link.source_domain_id not in domain_ids
        and link.target_domain_id not in domain_ids
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    return link


@router.post("/validate/{link_id}")
async def validate_link(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Manually trigger validation for a single link."""
    # Verify user owns at least one side of the link
    result = await db.execute(
        select(Domain.id).where(Domain.user_id == user.id)
    )
    domain_ids = [row[0] for row in result.all()]

    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")

    if (
        link.source_domain_id not in domain_ids
        and link.target_domain_id not in domain_ids
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    new_status = await LinkValidatorService.validate_link(db, link_id)
    await db.commit()
    return {"link_id": str(link_id), "status": new_status}


@router.post("/validate-all")
async def validate_all_links(
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(require_admin),
) -> dict[str, Any]:
    """Trigger full network validation (admin only)."""
    summary = await LinkValidatorService.validate_all_links(db)
    await db.commit()
    return summary


@router.get("/export")
async def export_links(
    domain_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> StreamingResponse:
    if user.plan in ("free", "starter"):
        raise HTTPException(status_code=403, detail="CSV export requires Pro or Agency plan")

    result = await db.execute(select(Domain.id).where(Domain.user_id == user.id))
    domain_ids = [row[0] for row in result.all()]
    if not domain_ids:
        domain_ids = [uuid.UUID(int=0)]

    conditions = [
        (Link.source_domain_id.in_(domain_ids))
        | (Link.target_domain_id.in_(domain_ids))
    ]
    if domain_id:
        conditions.append(
            (Link.source_domain_id == domain_id) | (Link.target_domain_id == domain_id)
        )

    from sqlalchemy import and_
    stmt = select(Link).where(and_(*conditions)).order_by(Link.created_at.desc())
    result = await db.execute(stmt)
    links = list(result.scalars().all())

    page_cache: dict = {}
    for link in links:
        for pid in (link.source_page_id, link.target_page_id):
            if pid not in page_cache:
                pr = await db.execute(select(Page).where(Page.id == pid))
                page_cache[pid] = pr.scalar_one_or_none()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "source_url", "target_url", "anchor_text", "match_score", "status", "credits_earned", "credits_spent"])
    for link in links:
        source_url = page_cache.get(link.source_page_id)
        target_url = page_cache.get(link.target_page_id)
        writer.writerow([
            link.created_at.isoformat() if link.created_at else "",
            source_url.url if source_url else "",
            target_url.url if target_url else "",
            link.anchor_text,
            float(link.match_score) if link.match_score else "",
            link.status,
            float(link.credits_earned) if link.credits_earned else "",
            float(link.credits_spent) if link.credits_spent else "",
        ])

    output.seek(0)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="weave-links-{date_str}.csv"'},
    )
