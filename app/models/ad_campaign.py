import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any
from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent import AgentProfile


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ad_archive_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    page_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ad_headline: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    ad_body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cta_type: Mapped[str] = mapped_column(String(100), default="LEARN_MORE", nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), default="IMAGE", nullable=False)  # IMAGE, VIDEO, CAROUSEL
    target_segment: Mapped[str] = mapped_column(String(50), default="RESALE", nullable=False)
    target_district: Mapped[str] = mapped_column(String(50), default="ALL", nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    detected_hooks: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    agent: Mapped["AgentProfile"] = relationship("AgentProfile", backref="ad_campaigns")

    __table_args__ = (
        Index("ix_ad_district_active", "target_district", "is_active"),
    )
