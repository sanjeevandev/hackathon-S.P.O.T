"""GradingResult ORM model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.engine import Base


class GradingResultModel(Base):
    __tablename__ = "grading_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inspection_id: Mapped[str] = mapped_column(String(64), ForeignKey("inspections.id"), nullable=False)
    grading_profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("grading_profiles.id"), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(32), nullable=False)  # Grade-A, Grade-URS, Grade-C
    grade_a_percent: Mapped[float] = mapped_column(Float, nullable=False)
    urs_percent: Mapped[float] = mapped_column(Float, nullable=False)
    healthy_percent: Mapped[float] = mapped_column(Float, nullable=False)
    damaged_percent: Mapped[float] = mapped_column(Float, nullable=False)
    rotten_percent: Mapped[float] = mapped_column(Float, nullable=False)
    sprouted_percent: Mapped[float] = mapped_column(Float, nullable=False)
    undersized_percent: Mapped[float] = mapped_column(Float, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="ACCEPTED")
    review_reason_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inspection_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    sampling_status: Mapped[str] = mapped_column(String(32), default="SAMPLE_ONLY")
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    rules_triggered_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="grading_result")
    grading_profile: Mapped["GradingProfileModel"] = relationship("GradingProfileModel", lazy="joined")
