import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WhitespaceOpportunity(Base):
    __tablename__ = "whitespace_opportunities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    target_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # PROJECT, MOP_PRECINCT, DISTRICT
    target_identifier: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # e.g., 'NORWOOD GRAND', 'PUNGGOL'
    district: Mapped[str] = mapped_column(String(50), default="ALL", nullable=False, index=True)
    property_category: Mapped[str] = mapped_column(String(50), default="CONDO_APT", nullable=False)
    market_demand_index: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    ad_competition_index: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    whitespace_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # 0.0 to 100.0
    recommended_persona: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    recommended_hook_angle: Mapped[str] = mapped_column(Text, default="", nullable=False)
    estimated_target_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("target_identifier", "target_type", "snapshot_date", name="uq_whitespace_target_date"),
        Index("ix_whitespace_score_date", "whitespace_score", "snapshot_date"),
    )
