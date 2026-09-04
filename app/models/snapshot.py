import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent import AgentProfile


class AgentRankSnapshot(Base):
    __tablename__ = "agent_rank_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    segment: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # new_sale, resale, rental, overall
    property_category: Mapped[str] = mapped_column(
        String(50), default="ALL", nullable=False, index=True
    )  # ALL, HDB, CONDO_APT, LANDED, COMMERCIAL
    transaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    percentile: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 100.0 (Top X%)
    trailing_window_months: Mapped[int] = mapped_column(
        Integer, default=12, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    agent: Mapped["AgentProfile"] = relationship(
        "AgentProfile", back_populates="rank_snapshots"
    )

    __table_args__ = (
        UniqueConstraint(
            "agent_id", "snapshot_date", "segment", "property_category", name="uq_agent_snapshot_seg_cat"
        ),
        Index("ix_snapshot_lookup", "snapshot_date", "segment", "property_category", "rank_position"),
    )
