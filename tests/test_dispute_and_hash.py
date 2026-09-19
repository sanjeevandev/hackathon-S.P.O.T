import io
import uuid
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import log_grading_session, get_session_by_batch_id

client = TestClient(app)


def test_dispute_endpoint_404_on_missing_batch():
    """POST /api/v1/sessions/{batch_id}/dispute returns 404 when batch_id does not exist."""
    fake_batch_id = f"NONEXISTENT-BATCH-{uuid.uuid4().hex[:8]}"
    response = client.post(f"/api/v1/sessions/{fake_batch_id}/dispute")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_dispute_endpoint_200_and_status_update():
    """POST /api/v1/sessions/{batch_id}/dispute updates review_status to DISPUTED for existing batch."""
    batch_id = f"TEST-DISPUTE-BATCH-{uuid.uuid4().hex[:6]}"
    sha_dummy = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    # Seed a grading session
    log_grading_session({
        "batch_id": batch_id,
        "center_id": "APMC-NASHIK-CENTER-04",
        "total_weight_kg": 100.0,
        "confidence_score": 95.0,
        "grade_a_percentage": 85.0,
        "grade_urs_percentage": 10.0,
        "overall_grade": "Grade-A",
        "sha256_hash": sha_dummy
    })

    # Verify session retrieval contains sha256_hash
    session_data = get_session_by_batch_id(batch_id)
    assert session_data is not None
    assert session_data["sha256_hash"] == sha_dummy
    assert session_data["status"] == "NOT_REVIEWED"

    # Flag dispute
    dispute_resp = client.post(f"/api/v1/sessions/{batch_id}/dispute")
    assert dispute_resp.status_code == 200
    dispute_data = dispute_resp.json()
    assert dispute_data["status"] == "success"
    assert dispute_data["review_status"] == "DISPUTED"

    # Verify updated status
    updated_session = get_session_by_batch_id(batch_id)
    assert updated_session is not None
    assert updated_session["status"] == "DISPUTED"
