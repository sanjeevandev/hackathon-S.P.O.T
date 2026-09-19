"""Unit tests for cryptographic append-only audit trail."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.engine import Base
from backend.db.repositories.audit_repository import AuditRepository
from backend.db.models.audit_event import AuditEvent


@pytest.fixture
def audit_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_audit_event_hash_chaining(audit_db):
    """Verify audit repository creates cryptographic SHA-256 hash chain across events."""
    audit_repo = AuditRepository(audit_db)

    # Event 1: Genesis event
    e1 = audit_repo.log_event(
        entity_type="INSPECTION", entity_id="TEST-FIXTURE-INSP-1",
        event_type="CREATED", actor_id="INSPECTOR-1", payload={"action": "start"}
    )
    audit_db.commit()

    assert e1.previous_event_hash is None
    assert len(e1.event_hash) == 64

    # Event 2: Chained event
    e2 = audit_repo.log_event(
        entity_type="INSPECTION", entity_id="TEST-FIXTURE-INSP-1",
        event_type="COMPLETED", actor_id="INSPECTOR-1", payload={"action": "finish", "grade": "Grade-A"}
    )
    audit_db.commit()

    assert e2.previous_event_hash == e1.event_hash
    assert e2.event_hash != e1.event_hash

    # Query trail
    history = audit_repo.list_by_entity("INSPECTION", "TEST-FIXTURE-INSP-1")
    assert len(history) == 2
    assert history[0].event_hash == history[1].previous_event_hash
