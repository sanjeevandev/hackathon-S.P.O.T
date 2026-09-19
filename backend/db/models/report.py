"""Report ORM model."""

from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.engine import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inspection_id: Mapped[str] = mapped_column(String(64), ForeignKey("inspections.id"), nullable=False)
    report_reference: Mapped[str] = mapped_column(String(256), nullable=False)
    report_type: Mapped[str] = mapped_column(String(64), default="INSPECTION_CERTIFICATE")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    inspection: Mapped["Inspection"] = relationship("Inspection")
