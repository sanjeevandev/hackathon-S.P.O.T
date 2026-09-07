"""ModelVersion ORM model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.engine import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # "development_mock" or "real_model"
    framework: Mapped[str] = mapped_column(String(32), default="PyTorch")
    weights_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    dataset_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    training_config_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    metrics_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
