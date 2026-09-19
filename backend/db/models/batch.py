"""Batch ORM model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.engine import Base


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    supplier_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("suppliers.id"), nullable=True)
    procurement_center_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("procurement_centers.id"), nullable=True)
    declared_weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_source: Mapped[str] = mapped_column(String(32), default="UNAVAILABLE")
    sampling_status: Mapped[str] = mapped_column(String(32), default="SAMPLE_ONLY")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", lazy="joined")
    procurement_center: Mapped[Optional["ProcurementCenter"]] = relationship("ProcurementCenter", lazy="joined")
