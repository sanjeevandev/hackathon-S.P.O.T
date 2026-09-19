"""Inspection ORM model."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.engine import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(64), ForeignKey("batches.id"), nullable=False)
    inspector_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    model_version_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("model_versions.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="CREATED")  # CREATED, PROCESSING, COMPLETED, FAILED
    inspection_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    review_status: Mapped[str] = mapped_column(String(32), default="NOT_REVIEWED")  # NOT_REVIEWED, PASS, REVIEW_REQUIRED
    review_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    batch: Mapped["Batch"] = relationship("Batch", lazy="joined")
    inspector: Mapped[Optional["User"]] = relationship("User", lazy="joined")
    model_version: Mapped[Optional["ModelVersion"]] = relationship("ModelVersion", lazy="joined")
    images: Mapped[List["InspectionImage"]] = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    grading_result: Mapped[Optional["GradingResultModel"]] = relationship("GradingResultModel", back_populates="inspection", uselist=False, cascade="all, delete-orphan")
