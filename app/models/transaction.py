import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent import AgentProfile


class AgentTransaction(Base):
    __tablename__ = "agent_transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_ref: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    property_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., CONDOMINIUM_APARTMENTS, HDB, LANDED
    property_category: Mapped[str] = mapped_column(
        String(50), default="CONDO_APT", nullable=False, index=True
    )  # HDB, CONDO_APT, LANDED, COMMERCIAL
    transaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # NEW_SALE, RESALE, RENTAL
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    town: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    agent: Mapped["AgentProfile"] = relationship(
        "AgentProfile", back_populates="transactions"
    )

    __table_args__ = (
        UniqueConstraint(
            "agent_id", "transaction_ref", "transaction_date", name="uq_agent_tx_ref"
        ),
        Index("ix_tx_agent_date", "agent_id", "transaction_date"),
        Index("ix_tx_type_date", "transaction_type", "transaction_date"),
        Index("ix_tx_cat_type_date", "property_category", "transaction_type", "transaction_date"),
    )
