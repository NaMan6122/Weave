"""Domain schemas for request/response validation."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DomainCreate(BaseModel):
    domain: str
    niche: str | None = None
    language: str = "en"
    niche_strict: bool = False


class DomainVerifyRequest(BaseModel):
    method: Literal["dns", "meta", "file"]


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    domain: str
    verified: bool
    verification_method: str | None = None
    verification_token: str | None = None
    status: str
    niche: str | None = None
    language: str | None = None
    niche_strict: bool = False

    # SEO metrics
    wts: float | None = None
    dr: float | None = None
    da: float | None = None
    spam_score: float | None = None
    domain_age_days: int | None = None
    organic_traffic: int | None = None
    content_quality: float | None = None
    is_pbn: bool | None = None

    # Vetting
    vetting_status: str | None = None
    rejection_reason: str | None = None
    vetted_at: datetime | None = None

    # Credit balance (injected from relationship)
    credit_balance: Decimal = Decimal("0.00")

    created_at: datetime
    updated_at: datetime


class DomainListResponse(BaseModel):
    domains: list[DomainResponse]
    total: int
