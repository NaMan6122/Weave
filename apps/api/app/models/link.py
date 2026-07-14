import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class Link(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "links"

    source_page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False
    )
    target_page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False
    )
    source_domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False
    )
    target_domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False
    )
    anchor_text: Mapped[str] = mapped_column(String(512), nullable=False)
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    match_breakdown: Mapped[dict | None] = mapped_column(JSON)
    placement_type: Mapped[str] = mapped_column(
        String(50), default="body", nullable=False
    )
    credits_earned: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    credits_spent: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    triangle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("triangles.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    placed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Triangle(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "triangles"

    domain_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False
    )
    domain_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False
    )
    domain_c_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False
    )
    link_ab_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("links.id", use_alter=True), nullable=True
    )
    link_bc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("links.id", use_alter=True), nullable=True
    )
    link_ca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("links.id", use_alter=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="forming", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
