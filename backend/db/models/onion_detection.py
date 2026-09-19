"""OnionDetection ORM model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.engine import Base


class OnionDetectionModel(Base):
    __tablename__ = "onion_detections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inspection_image_id: Mapped[str] = mapped_column(String(64), ForeignKey("inspection_images.id"), nullable=False)
    external_onion_id: Mapped[str] = mapped_column(String(64), nullable=False)
    bbox_json: Mapped[str] = mapped_column(Text, nullable=False)
    mask_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    detection_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    size_status: Mapped[str] = mapped_column(String(32), default="UNAVAILABLE")
    estimated_diameter_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    size_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    image: Mapped["InspectionImage"] = relationship("InspectionImage", back_populates="detections")
    defect_prediction: Mapped[Optional["DefectPrediction"]] = relationship("DefectPrediction", back_populates="detection", uselist=False, cascade="all, delete-orphan")
