"""Audit repository for immutable append-only audit trail."""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.db.models.audit_event import AuditEvent


class AuditRepository:
    """Data access repository enforcing append-only audit trail semantics."""

    def __init__(self, db: Session):
        self.db = db

    def get_latest_event(self) -> Optional[AuditEvent]:
        """Retrieves the most recent audit event for SHA-256 hash chaining."""
        return self.db.query(AuditEvent).order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc()).first()

    def log_event(
        self,
        entity_type: str,
        entity_id: str,
        event_type: str,
        actor_id: str = "SYSTEM",
        payload: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Appends a new immutable audit event to the cryptographic audit trail chain."""
        latest = self.get_latest_event()
        prev_hash = latest.event_hash if latest else None

        now = datetime.now(timezone.utc)
        timestamp_iso = now.isoformat()
        payload_str = json.dumps(payload or {}, sort_keys=True)

        event_hash = AuditEvent.compute_hash(
            previous_hash=prev_hash,
            timestamp_iso=timestamp_iso,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor_id=actor_id,
            payload_json=payload_str
        )

        event_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
        event = AuditEvent(
            id=event_id,
            event_id=event_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor_id=actor_id,
            timestamp=now,
            payload_json=payload_str,
            previous_event_hash=prev_hash,
            event_hash=event_hash
        )
        self.db.add(event)
        self.db.flush()
        return event

    def list_by_entity(self, entity_type: str, entity_id: str) -> List[AuditEvent]:
        return (
            self.db.query(AuditEvent)
            .filter(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
            .order_by(AuditEvent.timestamp.asc())
            .all()
        )
