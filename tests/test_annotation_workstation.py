import os
import json
import pytest
from backend.ai.annotation.workstation import AnnotationWorkstationManager

def test_workstation_queue_loading():
    manager = AnnotationWorkstationManager()
    queue = manager.get_queue("ANNOTATOR_01")
    assert len(queue) == 1000
    first_item = queue[0]
    assert "image_id" in first_item
    assert "semantic_attributes" in first_item
    assert first_item["annotation_status"] in ["UNLABELED", "COMPLETE", "NEEDS_REVIEW"]

def test_workstation_save_and_multi_label():
    manager = AnnotationWorkstationManager()
    test_rec = {
        "annotation_id": "TEST-ANN-100",
        "image_id": "New Onion - Copy/2. Bulb/1. Healthy/1. Red Onion/1. Single/Onion00001.jpg",
        "dataset_version": "1.0.0-audited",
        "defect_dataset_version": "0.1.0",
        "annotation_version": "0.1.0",
        "annotator_id": "ANNOTATOR_TEST_SUITE",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": False, "damage": True, "rot": True, "sprout": False},
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
                "coordinates": [0.1, 0.1, 0.5, 0.5]
            }
        ],
        "annotation_confidence": "HIGH",
        "notes": "Unit test multi-label entry",
        "created_at": "2026-09-04T23:00:00Z"
    }

    is_valid, errors, status = manager.save_annotation(test_rec)
    assert is_valid is True
    assert status == "COMPLETE"

def test_workstation_uncertainty_state():
    manager = AnnotationWorkstationManager()
    test_rec = {
        "annotation_id": "TEST-ANN-101",
        "image_id": "New Onion - Copy/2. Bulb/2. Unhealthy/1. Red Onion/1. Single/Onion12261.jpg",
        "dataset_version": "1.0.0-audited",
        "defect_dataset_version": "0.1.0",
        "annotation_version": "0.1.0",
        "annotator_id": "ANNOTATOR_TEST_SUITE",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": False, "damage": False, "rot": False, "sprout": False},
        "size_assessment": {
            "undersized_status": "UNAVAILABLE",
            "size_reference_available": False,
            "estimated_diameter_mm": None,
            "measurement_method": "UNAVAILABLE"
        },
        "evidence_regions": [],
        "annotation_confidence": "LOW",
        "uncertainty_reason": "Ambiguous rot lesion vs dirt smudge",
        "notes": "Marked uncertain",
        "created_at": "2026-09-04T23:00:00Z"
    }

    is_valid, errors, status = manager.save_annotation(test_rec)
    assert is_valid is False # Triggered unspecified condition check requiring review
    assert status == "NEEDS_REVIEW"

def test_double_annotation_independence():
    manager = AnnotationWorkstationManager()
    img_id = "New Onion - Copy/2. Bulb/1. Healthy/1. Red Onion/1. Single/Onion00002.jpg"

    rec_a = {
        "annotation_id": "ANN-A-01", "image_id": img_id, "dataset_version": "1.0.0-audited",
        "defect_dataset_version": "0.1.0", "annotation_version": "0.1.0", "annotator_id": "ANNOTATOR_A",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": True, "damage": False, "rot": False, "sprout": False},
        "size_assessment": {"undersized_status": "UNAVAILABLE", "size_reference_available": False, "estimated_diameter_mm": None, "measurement_method": "UNAVAILABLE"},
        "evidence_regions": [], "annotation_confidence": "HIGH", "created_at": "2026-09-04T23:00:00Z"
    }
    rec_b = {
        "annotation_id": "ANN-B-01", "image_id": img_id, "dataset_version": "1.0.0-audited",
        "defect_dataset_version": "0.1.0", "annotation_version": "0.1.0", "annotator_id": "ANNOTATOR_B",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": False, "damage": True, "rot": False, "sprout": False},
        "size_assessment": {"undersized_status": "UNAVAILABLE", "size_reference_available": False, "estimated_diameter_mm": None, "measurement_method": "UNAVAILABLE"},
        "evidence_regions": [], "annotation_confidence": "MEDIUM", "created_at": "2026-09-04T23:00:00Z"
    }

    manager.save_annotation(rec_a)
    manager.save_annotation(rec_b)

    path_a = manager._get_record_path(img_id, "ANNOTATOR_A")
    path_b = manager._get_record_path(img_id, "ANNOTATOR_B")

    assert path_a != path_b
    with open(path_a, "r") as f:
        data_a = json.load(f)
    with open(path_b, "r") as f:
        data_b = json.load(f)

    assert data_a["multi_label_defects"]["healthy"] is True
    assert data_b["multi_label_defects"]["healthy"] is False
