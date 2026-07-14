import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class DomainMetricsHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "domain_metrics_history"

    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False
    )
    dr: Mapped[int | None] = mapped_column(Integer)
    da: Mapped[int | None] = mapped_column(Integer)
    wts: Mapped[int | None] = mapped_column(Integer)
    organic_traffic: Mapped[int | None] = mapped_column(Integer)
    spam_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
