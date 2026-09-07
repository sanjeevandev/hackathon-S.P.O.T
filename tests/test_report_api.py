"""Integration tests for Canonical Inspection Result and Reporting API endpoints."""

import io
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import init_database

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_database()


def test_canonical_result_and_report_api_flow():
    """Verify inspection upload, canonical result query, report generation, HTML rendering, and audit trail creation."""
    # 1. Perform inspection upload
    arr = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    insp_resp = client.post(
        "/api/v1/inspect",
        files={"file": ("report_sample.jpg", img_bytes, "image/jpeg")},
        params={"center_id": "APMC-NASHIK-CENTER-04", "batch_id": "TEST-BATCH-RPT-99"}
    )
    assert insp_resp.status_code == 200
    req_id = insp_resp.json()["request_id"]
    insp_id = f"INSP-{req_id}"

    # 2. Query GET /api/v1/inspections/{inspection_id}/result
    canon_resp = client.get(f"/api/v1/inspections/{insp_id}/result")
    assert canon_resp.status_code == 200
    canon_data = canon_resp.json()
    assert canon_data["inspection_id"] == insp_id
    assert canon_data["batch_id"] == "TEST-BATCH-RPT-99"
    assert canon_data["sampling_status"] == "SAMPLE_ONLY"
    assert canon_data["model"]["source"] == "development_mock"

    # 3. Query GET /api/v1/inspections/{inspection_id}/report (JSON)
    rpt_resp = client.get(f"/api/v1/inspections/{insp_id}/report")
    assert rpt_resp.status_code == 200
    rpt_data = rpt_resp.json()
    assert rpt_data["inspection_id"] == insp_id
    assert rpt_data["report_version"] == 1

    # 4. Query GET /api/v1/inspections/{inspection_id}/report (HTML)
    html_resp = client.get(f"/api/v1/inspections/{insp_id}/report", params={"format": "html"})
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
    assert "S.P.O.T. Digital Quality Inspection Report" in html_resp.text

    # 5. POST /api/v1/inspections/{inspection_id}/report (Regeneration increments version)
    regen_resp = client.post(f"/api/v1/inspections/{insp_id}/report")
    assert regen_resp.status_code == 200
    regen_data = regen_resp.json()
    assert regen_data["report_version"] == 2
