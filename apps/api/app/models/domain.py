import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Domain(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "domains"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_method: Mapped[str | None] = mapped_column(String(50))
    verification_token: Mapped[str | None] = mapped_column(String(255))

    # SEO metrics
    wts: Mapped[float | None] = mapped_column(Float)
    dr: Mapped[float | None] = mapped_column(Float)
    da: Mapped[float | None] = mapped_column(Float)
    spam_score: Mapped[float | None] = mapped_column(Float)
    domain_age_days: Mapped[int | None] = mapped_column(Integer)
    organic_traffic: Mapped[int | None] = mapped_column(Integer)
    content_quality: Mapped[float | None] = mapped_column(Float)
    is_pbn: Mapped[bool | None] = mapped_column(Boolean)

    # Vetting
    vetted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vetting_status: Mapped[str | None] = mapped_column(String(50))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    # Classification
    niche: Mapped[str | None] = mapped_column(String(100))
    language: Mapped[str | None] = mapped_column(String(10))
    blocklist: Mapped[dict | None] = mapped_column(JSON)
    niche_strict: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(String(50), default="pending")

    # Relationships
    pages = relationship("Page", back_populates="domain", lazy="selectin")
    credit_account = relationship("CreditAccount", back_populates="domain", uselist=False)
