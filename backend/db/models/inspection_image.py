"""InspectionImage ORM model."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.engine import Base


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inspection_id: Mapped[str] = mapped_column(String(64), ForeignKey("inspections.id"), nullable=False)
    image_reference: Mapped[str] = mapped_column(String(256), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(128), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), default="image/jpeg")
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    quality_status: Mapped[str] = mapped_column(String(32), default="PASS")
    quality_metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="images")
    detections: Mapped[List["OnionDetectionModel"]] = relationship("OnionDetectionModel", back_populates="image", cascade="all, delete-orphan")
