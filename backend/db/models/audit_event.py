"""AuditEvent ORM model for append-only audit trail."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.engine import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(64), default="SYSTEM")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    previous_event_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def compute_hash(
        previous_hash: Optional[str],
        timestamp_iso: str,
        entity_type: str,
        entity_id: str,
        event_type: str,
        actor_id: str,
        payload_json: str
    ) -> str:
        """Computes SHA-256 cryptographic digest for audit trail integrity."""
        prev = previous_hash or "GENESIS_BLOCK_HASH"
        raw_str = f"{prev}|{timestamp_iso}|{entity_type}|{entity_id}|{event_type}|{actor_id}|{payload_json}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
