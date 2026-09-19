"""GradingProfile ORM model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.engine import Base


class GradingProfileModel(Base):
    __tablename__ = "grading_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    profile_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="EXPERIMENTAL")
    official_status: Mapped[str] = mapped_column(String(32), default="NOT_OFFICIAL")
    source: Mapped[str] = mapped_column(String(32), default="PROJECT_DEFINED")
    source_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default="Prototype grading profile. Not an official government certification or statutory grading standard."
    )
    rules_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    effective_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
