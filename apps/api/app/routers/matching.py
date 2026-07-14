import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.credit import CreditAccount
from app.models.domain import Domain
from app.schemas.link import (
    DiscoverRequest,
    DiscoverResponse,
    IndexPageRequest,
    IndexPageResponse,
    PlaceLinkRequest,
    PlaceLinkResponse,
)
from app.services.matching import MatchingService

router = APIRouter()


async def _resolve_domain(
    db: AsyncSession, user_id: str, url: str
) -> Domain:
    """Find the user's domain that matches the given URL."""
    from urllib.parse import urlparse

    hostname = urlparse(url).hostname or ""
    # Strip www.
    if hostname.startswith("www."):
        hostname = hostname[4:]

    result = await db.execute(
        select(Domain).where(
            Domain.user_id == uuid.UUID(user_id),
            Domain.domain == hostname,
        )
    )
    domain = result.scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=404, detail=f"Domain not found for URL: {url}")
    return domain


@router.post("/discover", response_model=DiscoverResponse)
async def discover_matches(
    req: DiscoverRequest,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> DiscoverResponse:
    domain = await _resolve_domain(db, user.id, req.url)

    try:
        suggestions = await MatchingService.discover_links(
            db=db,
            content=req.content,
            source_url=req.url,
            source_domain_id=domain.id,
            max_results=req.max_results,
            niche_strict=req.niche_strict,
            min_dr=req.min_dr,
            exclude_domains=req.exclude_domains,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get credit balance
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.domain_id == domain.id)
    )
    account = result.scalar_one_or_none()
    balance = account.balance if account else 0

    return DiscoverResponse(suggestions=suggestions, credit_balance=balance)


@router.post("/place", response_model=PlaceLinkResponse)
async def place_link(
    req: PlaceLinkRequest,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> PlaceLinkResponse:
    domain = await _resolve_domain(db, user.id, req.source_url)

    try:
        link = await MatchingService.place_link(
            db=db,
            source_url=req.source_url,
            target_url=req.target_url,
            anchor_text=req.anchor_text,
            placement_type=req.placement_type,
            source_domain_id=domain.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()

    # Get updated balance
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.domain_id == domain.id)
    )
    account = result.scalar_one_or_none()
    balance = account.balance if account else 0

    return PlaceLinkResponse(
        link_id=link.id,
        credits_earned=link.credits_earned,
        credit_balance=balance,
        status=link.status,
    )


@router.post("/index", response_model=IndexPageResponse)
async def index_page(
    req: IndexPageRequest,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> IndexPageResponse:
    """Embed page content and store the vector for semantic matching."""
    try:
        await MatchingService.index_page(db=db, page_id=req.page_id, content=req.content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await db.commit()
    return IndexPageResponse(success=True)
