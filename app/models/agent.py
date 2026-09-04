import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agency import Agency
    from app.models.snapshot import AgentRankSnapshot
    from app.models.transaction import AgentTransaction


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    cea_reg_no: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    agency_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    registration_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    agency: Mapped["Agency"] = relationship("Agency", back_populates="agents")
    transactions: Mapped[list["AgentTransaction"]] = relationship(
        "AgentTransaction", back_populates="agent", cascade="all, delete-orphan"
    )
    rank_snapshots: Mapped[list["AgentRankSnapshot"]] = relationship(
        "AgentRankSnapshot", back_populates="agent", cascade="all, delete-orphan"
    )
