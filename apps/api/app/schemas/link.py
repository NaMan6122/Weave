import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MatchScoreBreakdown(BaseModel):
    semantic_similarity: float
    dr_proximity: float
    freshness: float
    audience_overlap: float
    diversity: float
    total: float


class AnchorSuggestion(BaseModel):
    type: str  # "natural", "exact", "branded"
    text: str


class LinkSuggestion(BaseModel):
    target_url: str
    target_title: str | None
    match_score: MatchScoreBreakdown
    anchor_suggestions: list[AnchorSuggestion]
    insertion_hint: str | None = None
    credits_earned: Decimal


class DiscoverRequest(BaseModel):
    content: str
    url: str
    max_results: int = 5
    niche_strict: bool = False
    min_dr: int | None = None
    exclude_domains: list[str] | None = None


class DiscoverResponse(BaseModel):
    suggestions: list[LinkSuggestion]
    credit_balance: Decimal


class IndexPageRequest(BaseModel):
    page_id: uuid.UUID
    content: str


class IndexPageResponse(BaseModel):
    success: bool


class PlaceLinkRequest(BaseModel):
    source_url: str
    target_url: str
    anchor_text: str
    placement_type: str = "body"


class PlaceLinkResponse(BaseModel):
    link_id: uuid.UUID
    credits_earned: Decimal
    credit_balance: Decimal
    status: str


class LinkResponse(BaseModel):
    id: uuid.UUID
    source_domain_id: uuid.UUID
    target_domain_id: uuid.UUID
    anchor_text: str
    match_score: float | None
    match_breakdown: dict | None
    placement_type: str
    credits_earned: Decimal | None
    status: str
    placed_at: datetime | None
    verified_at: datetime | None
    sla_expires_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
