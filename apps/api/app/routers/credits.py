import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_admin
from app.models.domain import Domain
from app.schemas.credit import (
    BonusRequest,
    CreditBalanceResponse,
    CreditHistoryResponse,
    CreditTransactionResponse,
    TransferRequest,
    TransferResponse,
)
from app.services.credits import CreditService

router = APIRouter()


async def _require_credit_domain(
    domain_id: uuid.UUID,
    user: Any,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Domain).where(
            Domain.id == domain_id,
            Domain.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Domain not found")


@router.get("/balance/by-name/{domain_name}", response_model=CreditBalanceResponse)
async def get_balance_by_name(
    domain_name: str,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> CreditBalanceResponse:
    result = await db.execute(
        select(Domain).where(
            Domain.domain == domain_name,
            Domain.user_id == user.id,
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    try:
        account = await CreditService.get_balance(db, domain.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Credit account not found")
    return CreditBalanceResponse.model_validate(account)


@router.get("/balance/{domain_id}", response_model=CreditBalanceResponse)
async def get_balance(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> CreditBalanceResponse:
    await _require_credit_domain(domain_id, user, db)
    try:
        account = await CreditService.get_balance(db, domain_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Credit account not found")
    return CreditBalanceResponse.model_validate(account)


@router.get("/history/{domain_id}", response_model=CreditHistoryResponse)
async def get_history(
    domain_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> CreditHistoryResponse:
    await _require_credit_domain(domain_id, user, db)
    try:
        transactions = await CreditService.get_transaction_history(
            db, domain_id, limit=limit, offset=offset
        )
        total = await CreditService.get_transaction_count(db, domain_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Credit account not found")
    return CreditHistoryResponse(
        transactions=[
            CreditTransactionResponse.model_validate(t) for t in transactions
        ],
        total=total,
    )


@router.post("/bonus/{domain_id}", response_model=CreditTransactionResponse)
async def add_bonus(
    domain_id: uuid.UUID,
    body: BonusRequest,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(require_admin),
) -> CreditTransactionResponse:
    try:
        txn = await CreditService.add_bonus(
            db, domain_id, body.amount, body.description
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return CreditTransactionResponse.model_validate(txn)


@router.post("/transfer", response_model=TransferResponse)
async def transfer_credits(
    body: TransferRequest,
    db: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> TransferResponse:
    try:
        from_acc, to_acc = await CreditService.transfer_credits(
            db,
            from_domain_id=body.from_domain_id,
            to_domain_id=body.to_domain_id,
            amount=body.amount,
            user_id=user.id,
        )
        await db.commit()
    except PermissionError:
        raise HTTPException(status_code=403, detail="Cannot transfer between domains you don't own")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TransferResponse(
        from_balance=from_acc.balance,
        to_balance=to_acc.balance,
        amount_transferred=body.amount,
    )
