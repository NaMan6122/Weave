import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_admin
from app.models.domain import Domain
from app.models.link import Link
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
