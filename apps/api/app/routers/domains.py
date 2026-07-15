"""Domain registration, verification, and vetting endpoints."""

import csv
import io
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.domain import Domain as DomainModel
from app.schemas.domain import (
    DomainCreate,
    DomainListResponse,
    DomainResponse,
    DomainVerifyRequest,
)
from app.services.domain import DomainService

router = APIRouter()


async def _require_domain_owner(
    domain_id: uuid.UUID,
    user: Any,
    db: AsyncSession,
) -> DomainModel:
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(DomainModel)
        .where(
            DomainModel.id == domain_id,
            DomainModel.user_id == user.id,
        )
        .options(selectinload(DomainModel.credit_account))
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


def _domain_to_response(domain: Any) -> DomainResponse:
    """Convert a Domain ORM object to a DomainResponse, injecting credit_balance."""
    balance = Decimal("0.00")
    if domain.credit_account:
        balance = domain.credit_account.balance
    data = {c.key: getattr(domain, c.key) for c in domain.__table__.columns}
    data["credit_balance"] = balance
    return DomainResponse.model_validate(data)


@router.post("/", status_code=201, response_model=DomainResponse)
async def create_domain(
    body: DomainCreate,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> DomainResponse:
    try:
        domain = await DomainService.create_domain(
            db,
            user_id=user.id,
            domain_name=body.domain,
            niche=body.niche,
            language=body.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return _domain_to_response(domain)


@router.get("/", response_model=DomainListResponse)
async def list_domains(
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> DomainListResponse:
    domains = await DomainService.list_domains(db, user.id)
    items = [_domain_to_response(d) for d in domains]
    return DomainListResponse(domains=items, total=len(items))


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> DomainResponse:
    domain = await _require_domain_owner(domain_id, user, db)
    return _domain_to_response(domain)


@router.post("/{domain_id}/verify", response_model=DomainResponse)
async def verify_domain(
    domain_id: uuid.UUID,
    body: DomainVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> DomainResponse:
    await _require_domain_owner(domain_id, user, db)
    try:
        domain = await DomainService.verify_domain(db, domain_id, body.method)
    except LookupError:
        raise HTTPException(status_code=404, detail="Domain not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _domain_to_response(domain)


@router.post("/{domain_id}/vet", response_model=DomainResponse)
async def vet_domain(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> DomainResponse:
    await _require_domain_owner(domain_id, user, db)
    try:
        domain = await DomainService.vet_domain(db, domain_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Domain not found")
    return _domain_to_response(domain)


@router.delete("/{domain_id}", status_code=204)
async def delete_domain(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> None:
    try:
        await DomainService.delete_domain(db, domain_id, user.id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Domain not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not your domain")


@router.get("/by-name/{domain_name}/status", response_model=DomainResponse)
async def get_domain_status_by_name(
    domain_name: str,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> DomainResponse:
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(DomainModel)
        .where(
            DomainModel.domain == domain_name,
            DomainModel.user_id == user.id,
        )
        .options(selectinload(DomainModel.credit_account))
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return _domain_to_response(domain)


@router.get("/export")
async def export_domains(
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> StreamingResponse:
    if user.plan in ("free", "starter"):
        raise HTTPException(status_code=403, detail="CSV export requires Pro or Agency plan")

    domains = await DomainService.list_domains(db, user.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["domain", "niche", "language", "dr", "wts", "status", "verified", "created_at"])
    for d in domains:
        writer.writerow([
            d.domain,
            d.niche or "",
            d.language or "",
            float(d.dr) if d.dr else "",
            float(d.wts) if d.wts else "",
            d.status,
            d.verified,
            d.created_at.isoformat() if d.created_at else "",
        ])

    output.seek(0)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="weave-domains-{date_str}.csv"'},
    )
