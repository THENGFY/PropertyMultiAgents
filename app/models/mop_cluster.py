import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HDBMOPCluster(Base):
    __tablename__ = "hdb_mop_clusters"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    town: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    street_name: Mapped[str] = mapped_column(String(255), nullable=False)
    block: Mapped[str] = mapped_column(String(50), nullable=False)
    lease_commence_year: Mapped[int] = mapped_column(Integer, nullable=False)
    mop_completion_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_mop_upgrader_cohort: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    estimated_units: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    median_resale_psf: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("town", "street_name", "block", "mop_completion_year", name="uq_hdb_mop_block"),
        Index("ix_mop_town_year", "town", "mop_completion_year"),
    )
