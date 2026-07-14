import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CreditBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    domain_id: uuid.UUID
    balance: Decimal
    lifetime_earned: Decimal
    lifetime_spent: Decimal
    updated_at: datetime


class CreditTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    type: str
    amount: Decimal
    link_id: uuid.UUID | None
    description: str | None
    created_at: datetime


class CreditHistoryResponse(BaseModel):
    transactions: list[CreditTransactionResponse]
    total: int


class BonusRequest(BaseModel):
    amount: Decimal
    description: str


class TransferRequest(BaseModel):
    from_domain_id: uuid.UUID
    to_domain_id: uuid.UUID
    amount: Decimal


class TransferResponse(BaseModel):
    from_balance: Decimal
    to_balance: Decimal
    amount_transferred: Decimal
