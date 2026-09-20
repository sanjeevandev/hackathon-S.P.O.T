"""Integration tests for end-to-end persistence flow and history retrieval API."""

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import init_database

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_database()


def test_inspection_persistence_flow():
    """Verify inspection request persists to database and is retrievable via history API."""
    import numpy as np
    arr = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    response = client.post(
        "/api/v1/inspect",
        files={"file": ("test_sample.jpg", img_bytes, "image/jpeg")},
        params={"center_id": "APMC-NASHIK-CENTER-04", "batch_id": "TEST-FIXTURE-BATCH-999"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"

    # Query history list API
    hist_resp = client.get("/api/v1/inspections", params={"batch_id": "TEST-FIXTURE-BATCH-999"})
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 1
    insp_item = history[0]
    assert insp_item["batch_id"] == "TEST-FIXTURE-BATCH-999"
    assert insp_item["grading_result"]["sampling_status"] == "SAMPLE_ONLY"

    # Query inspection detail API
    insp_id = insp_item["inspection_id"]
    detail_resp = client.get(f"/api/v1/inspections/{insp_id}")
    assert detail_resp.status_code == 200
    details = detail_resp.json()
    assert details["inspection_id"] == insp_id
    assert details["model_version"]["source"] == "real_model"
    assert details["grading_result"]["grade"] in ["Grade-A", "Grade-URS", "Grade-C"]
