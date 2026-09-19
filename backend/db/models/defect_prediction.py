"""DefectPrediction ORM model."""

from datetime import datetime, timezone
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.engine import Base


class DefectPrediction(Base):
    __tablename__ = "defect_predictions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    onion_detection_id: Mapped[str] = mapped_column(String(64), ForeignKey("onion_detections.id"), nullable=False)
    damage_probability: Mapped[float] = mapped_column(Float, default=0.0)
    rot_probability: Mapped[float] = mapped_column(Float, default=0.0)
    sprout_probability: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    detection: Mapped["OnionDetectionModel"] = relationship("OnionDetectionModel", back_populates="defect_prediction")
