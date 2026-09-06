import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MarketPriceBenchmark(Base):
    __tablename__ = "market_price_benchmarks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    district: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. D10, D15, D19
    town: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    market_segment: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # CCR, RCR, OCR, HDB
    property_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # CONDO_APT, HDB, LANDED
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    median_psf: Mapped[float] = mapped_column(Float, nullable=False)
    p25_psf: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p75_psf: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    median_quantum: Mapped[float] = mapped_column(Float, nullable=False)
    quarterly_volume: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("district", "market_segment", "property_category", "snapshot_date", name="uq_market_benchmark"),
        Index("ix_benchmark_lookup", "district", "market_segment", "snapshot_date"),
    )
