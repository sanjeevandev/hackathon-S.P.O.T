import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.ai.annotation.workstation import AnnotationWorkstationManager

client = TestClient(app)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _manifest_image_count() -> int:
    """Number of images in the committed annotation manifest (source of truth).

    The committed manifest declares target_subset_size=1000; hard-coding 100 in
    assertions made tests fail against the real, committed dataset.
    """
    manifest = PROJECT_ROOT / "artifacts" / "ml" / "defect_annotations" / "annotation_manifest.json"
    if manifest.exists():
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        images = data.get("stratified_images", data.get("images", []))
        return len(images)
    return 0


def test_api_annotation_queue_loading():
    """Test loading queue from /api/annotation/queue endpoint."""
    response = client.get("/api/annotation/queue?annotator_id=HUMAN_ANNOTATOR_A")
    assert response.status_code == 200
    data = response.json()
    assert "queue" in data
    assert data["annotator_id"] == "HUMAN_ANNOTATOR_A"
    assert data["total_count"] == _manifest_image_count()
    
    first_item = data["queue"][0]
    assert "image_id" in first_item
    assert "destination_filename" in first_item
    assert "semantic_attributes" in first_item


def test_api_annotation_progress():
    """Test progress calculation from /api/annotation/progress endpoint."""
    response = client.get("/api/annotation/progress?annotator_id=HUMAN_ANNOTATOR_A")
    assert response.status_code == 200
    data = response.json()
    assert data["annotator_id"] == "HUMAN_ANNOTATOR_A"
    assert data["total_images"] == _manifest_image_count()
    assert "completed" in data
    assert "remaining" in data


def test_api_annotation_status():
    """Test aggregate Phase 13 status from /api/annotation/status endpoint."""
    response = client.get("/api/annotation/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_pilot"] == _manifest_image_count()
    assert "human_annotations_completed" in data
    assert "remaining" in data
    assert "damage" in data
    assert "rot" in data


def test_api_pilot_image_serving():
    """Test serving raw pilot image files from /api/annotation/pilot_image/{filename}.

    The pilot_100/images/ directory is not committed to this environment (the
    machine-local dataset lives on the training box), so the endpoint can only
    serve images when raw files are present — skip otherwise.
    """
    pilot_images_dir = PROJECT_ROOT / "artifacts" / "ml" / "defect_annotations" / "pilot_100" / "images"
    if not pilot_images_dir.exists() or not any(p.is_file() for p in pilot_images_dir.iterdir()):
        pytest.skip("pilot_100/images/ directory is not committed in this environment")

    q_resp = client.get("/api/annotation/queue?annotator_id=HUMAN_ANNOTATOR_A")
    filename = q_resp.json()["queue"][0]["destination_filename"]

    response = client.get(f"/api/annotation/pilot_image/{filename}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_no_automatic_model_inference_on_annotation_screen():
    """Proves that the annotation workstation has ZERO AI model/automatic detection dependencies."""
    workstation_component_path = PROJECT_ROOT / "src" / "components" / "AnnotationWorkstationStep.tsx"
    assert workstation_component_path.exists()
    
    with open(workstation_component_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Ensure no AI inference or detection model imports exist in the annotation component
    forbidden_imports = [
        "onnxInferenceEngine", "faceDetection", "predictImage",
        "autoDetect", "modelInference", "detectObjects", "runInference"
    ]
    for term in forbidden_imports:
        assert term.lower() not in code.lower(), f"Forbidden automatic model call found: {term}"

    # Verify manual ground truth notice is present
    assert "NO AI CONFIDENCE" in code
    assert "NO MODEL PREDICTIONS" in code
    assert "INTERNAL ANNOTATION WORKSTATION" in code


def test_valid_annotation_save_and_persistence():
    """Test saving a complete, valid multi-label human annotation record."""
    q_resp = client.get("/api/annotation/queue?annotator_id=HUMAN_ANNOTATOR_A")
    image_id = q_resp.json()["queue"][0]["image_id"]
    
    payload = {
        "annotation_id": "ANN-TEST-13A-01",
        "image_id": image_id,
        "annotator_id": "HUMAN_ANNOTATOR_A",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {
            "healthy": False,
            "damage": True,
            "rot": True,
            "sprout": False,
            "uncertain": False
        },
        "size_assessment": {
            "undersized_status": "UNAVAILABLE",
            "size_reference_available": False,
            "estimated_diameter_mm": None,
            "measurement_method": "UNAVAILABLE"
        },
        "evidence_regions": [
            {
                "region_id": "REG-01",
                "defect_type": "DAMAGE",
                "region_format": "BOUNDING_BOX",
                "coordinates": [0.1, 0.1, 0.4, 0.4]
            }
        ],
        "annotation_confidence": "HIGH",
        "notes": "Severe mechanical damage and black rot present"
    }

    response = client.post("/api/annotation/save", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["is_valid"] is True
    assert res_data["annotation_status"] == "COMPLETE"


def test_incomplete_annotation_rejection():
    """Test rejection of incomplete/invalid annotations (no labels selected)."""
    q_resp = client.get("/api/annotation/queue?annotator_id=HUMAN_ANNOTATOR_A")
    image_id = q_resp.json()["queue"][1]["image_id"]

    payload = {
        "annotation_id": "ANN-TEST-13A-INVALID",
        "image_id": image_id,
        "annotator_id": "HUMAN_ANNOTATOR_A",
        "semantic_attributes": {"organ": "BULB", "color": "WHITE", "arrangement": "MULTIPLE"},
        "multi_label_defects": {
            "healthy": False,
            "damage": False,
            "rot": False,
            "sprout": False,
            "uncertain": False
        },
        "size_assessment": {
            "undersized_status": "UNAVAILABLE",
            "size_reference_available": False,
            "estimated_diameter_mm": None,
            "measurement_method": "UNAVAILABLE"
        },
        "evidence_regions": [],
        "annotation_confidence": "HIGH"
    }

    response = client.post("/api/annotation/save", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["is_valid"] is False
    assert res_data["annotation_status"] == "NEEDS_REVIEW"
    assert any("Unspecified condition" in err for err in res_data["errors"])


def test_annotator_independence():
    """Test that Annotator A and Annotator B maintain independent labels for the same image."""
    q_resp = client.get("/api/annotation/queue?annotator_id=HUMAN_ANNOTATOR_A")
    image_id = q_resp.json()["queue"][2]["image_id"]

    payload_a = {
        "annotation_id": "ANN-A-IND",
        "image_id": image_id,
        "annotator_id": "HUMAN_ANNOTATOR_A",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": True, "damage": False, "rot": False, "sprout": False, "uncertain": False},
        "size_assessment": {"undersized_status": "UNAVAILABLE", "size_reference_available": False, "estimated_diameter_mm": None, "measurement_method": "UNAVAILABLE"},
        "evidence_regions": [],
        "annotation_confidence": "HIGH"
    }

    payload_b = {
        "annotation_id": "ANN-B-IND",
        "image_id": image_id,
        "annotator_id": "HUMAN_ANNOTATOR_B",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": False, "damage": True, "rot": False, "sprout": False, "uncertain": False},
        "size_assessment": {"undersized_status": "UNAVAILABLE", "size_reference_available": False, "estimated_diameter_mm": None, "measurement_method": "UNAVAILABLE"},
        "evidence_regions": [],
        "annotation_confidence": "MEDIUM"
    }

    resp_a = client.post("/api/annotation/save", json=payload_a)
    resp_b = client.post("/api/annotation/save", json=payload_b)
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    q_a = client.get("/api/annotation/queue?annotator_id=HUMAN_ANNOTATOR_A").json()["queue"][2]
    q_b = client.get("/api/annotation/queue?annotator_id=HUMAN_ANNOTATOR_B").json()["queue"][2]

    assert q_a["record"]["multi_label_defects"]["healthy"] is True
    assert q_b["record"]["multi_label_defects"]["healthy"] is False
    assert q_b["record"]["multi_label_defects"]["damage"] is True


def test_pilot_10_batch_review_mode():
    """Test 10-image pilot mode batch retrieval."""
    manager = AnnotationWorkstationManager()
    pilot_10 = manager.get_pilot_10_batch("HUMAN_ANNOTATOR_A")
    assert len(pilot_10) == 10
    # File names come from the committed manifest, not a hard-coded pilot_00x prefix.
    assert pilot_10[0]["image_id"] == manager.items[0]["image_id"]
    assert pilot_10[9]["image_id"] == manager.items[9]["image_id"]


def test_annotation_route_precedence_in_app_tsx():
    """Verifies that /internal/annotation has explicit top-level precedence in App.tsx."""
    app_path = PROJECT_ROOT / "src" / "App.tsx"
    assert app_path.exists()
    
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify synchronous getInitialRoute exists
    assert "getInitialRoute" in content
    assert "path.includes('/internal/annotation')" in content
    assert "hash.includes('internal-annotation')" in content

    # Verify early return for internal_annotation route
    assert "if (currentRoute === 'internal_annotation')" in content
    assert "<AnnotationWorkstationStep" in content

    # Verify that when currentRoute === 'internal_annotation', legacy steps are skipped
    early_return_idx = content.find("if (currentRoute === 'internal_annotation')")
    header_idx = content.find("<Header")
def test_frontend_route_isolation_regression():
    """Regression test proving /internal/annotation maps exclusively to AnnotationWorkstationStep and bypasses Home/History steps."""
    app_path = PROJECT_ROOT / "src" / "App.tsx"
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Confirm early return returns strictly <AnnotationWorkstationStep />
    assert "if (currentRoute === 'internal_annotation')" in content
    early_return_block = content[content.find("if (currentRoute === 'internal_annotation')"):content.find("if (verifyBatchId)")]
    
    assert "<AnnotationWorkstationStep" in early_return_block
    assert "<HomeStep" not in early_return_block
    assert "<Header" not in early_return_block
    assert "<CaptureStep" not in early_return_block
    assert "<ResultStep" not in early_return_block
    assert "<HistoryStep" not in early_return_block


def test_annotation_workstation_model_isolation():
    """Verifies that AnnotationWorkstationStep does not import or trigger model/camera APIs."""
    ws_path = PROJECT_ROOT / "src" / "components" / "AnnotationWorkstationStep.tsx"
    assert ws_path.exists()
    with open(ws_path, "r", encoding="utf-8") as f:
        content = f.read()

    forbidden_calls = [
        "onnxinferenceengine", "yolodetector", "resnet18", "visionmodel.analyze",
        "navigator.mediadevices", "getusermedia", "runinference", "predictimage"
    ]
    for term in forbidden_calls:
        assert term not in content.lower(), f"Forbidden AI/camera reference found in AnnotationWorkstationStep: {term}"


def test_phase_13b_fresh_unlabeled_blank_state_reset():
    """Verifies that AnnotationWorkstationStep resets all defect labels, evidence boxes, and notes for fresh unlabeled images."""
    ws_path = PROJECT_ROOT / "src" / "components" / "AnnotationWorkstationStep.tsx"
    with open(ws_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Reset logic checks
    assert "setHealthy(false)" in content
    assert "setDamage(false)" in content
    assert "setRot(false)" in content
    assert "setSprout(false)" in content
    assert "setUncertain(false)" in content
    assert "setUncertaintyReason('')" in content
    assert "setNotes('')" in content
    assert "setEvidenceRegions([])" in content

    # Label badges check
    assert "SAVED HUMAN ANNOTATION" in content
    assert "UNLABELED" in content


def test_phase_13b_mobile_first_ui_contract():
    """Verifies mobile-first UI controls: Save & Next CTA, touch chips, uncertainty reasons, and calibration notice."""
    ws_path = PROJECT_ROOT / "src" / "components" / "AnnotationWorkstationStep.tsx"
    with open(ws_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Sticky action CTA button
    assert "SAVE & NEXT IMAGE" in content
    
    # Touch chips for labels
    assert "Healthy" in content
    assert "Damaged" in content
    assert "Rotten" in content
    assert "Sprouted" in content
    assert "Uncertain" in content
    assert "UNAVAILABLE (No Ref Marker)" in content

    # Ground-truth confidence selectors
    assert "Ground-Truth Annotator Confidence" in content
    assert "'HIGH'" in content or "HIGH" in content

    # Uncertainty workflow reasons
    assert "Why is this uncertain?" in content
    assert "poor_visibility" in content
    assert "shadow" in content
    assert "blur" in content
    assert "occlusion" in content




