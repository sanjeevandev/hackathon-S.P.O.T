import os
import json
import pytest
from backend.ai.annotation.validator import AnnotationValidator
from backend.ai.annotation.adjudication import AnnotationAdjudicator

def test_annotation_validator_valid_record():
    valid_record = {
        "annotation_id": "ANN-TEST-001",
        "image_id": "test_image.jpg",
        "dataset_version": "1.0.0-audited",
        "annotation_version": "0.1.0",
        "annotator_id": "TEST_ANNOTATOR",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": False, "damage": True, "rot": False, "sprout": False},
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
        "review_status": "VERIFIED",
        "created_at": "2026-09-04T23:00:00Z"
    }

    is_valid, errors, status = AnnotationValidator.validate_record(valid_record)
    assert is_valid is True
    assert len(errors) == 0
    assert status == "VERIFIED"

def test_annotation_validator_contradictory_labels():
    # healthy=True AND rot=True is contradictory
    contradictory_record = {
        "annotation_id": "ANN-TEST-002",
        "image_id": "test_image.jpg",
        "dataset_version": "1.0.0-audited",
        "annotation_version": "0.1.0",
        "annotator_id": "TEST_ANNOTATOR",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": True, "damage": False, "rot": True, "sprout": False},
        "size_assessment": {
            "undersized_status": "UNAVAILABLE",
            "size_reference_available": False,
            "estimated_diameter_mm": None,
            "measurement_method": "UNAVAILABLE"
        },
        "evidence_regions": [],
        "annotation_confidence": "HIGH",
        "review_status": "VERIFIED",
        "created_at": "2026-09-04T23:00:00Z"
    }

    is_valid, errors, status = AnnotationValidator.validate_record(contradictory_record)
    assert is_valid is False
    assert status == "NEEDS_REVIEW"
    assert any("Contradictory labels" in err for err in errors)

def test_annotation_validator_size_rules():
    # Cannot estimate diameter when size_reference_available is False
    invalid_size_record = {
        "annotation_id": "ANN-TEST-003",
        "image_id": "test_image.jpg",
        "dataset_version": "1.0.0-audited",
        "annotation_version": "0.1.0",
        "annotator_id": "TEST_ANNOTATOR",
        "semantic_attributes": {"organ": "BULB", "color": "RED", "arrangement": "SINGLE"},
        "multi_label_defects": {"healthy": True, "damage": False, "rot": False, "sprout": False},
        "size_assessment": {
            "undersized_status": "FALSE",
            "size_reference_available": False,
            "estimated_diameter_mm": 55.0, # INVALID: estimated diameter provided without reference scale
            "measurement_method": "UNAVAILABLE"
        },
        "evidence_regions": [],
        "annotation_confidence": "HIGH",
        "review_status": "VERIFIED",
        "created_at": "2026-09-04T23:00:00Z"
    }

    is_valid, errors, status = AnnotationValidator.validate_record(invalid_size_record)
    assert is_valid is False
    assert status == "NEEDS_REVIEW"
    assert any("Invalid diameter" in err for err in errors)

def test_cohens_kappa_perfect_agreement():
    seq_a = [1, 0, 1, 0, 1, 1, 0, 0]
    seq_b = [1, 0, 1, 0, 1, 1, 0, 0]
    kappa = AnnotationAdjudicator.calculate_cohens_kappa(seq_a, seq_b)
    assert kappa == 1.0

def test_artifact_files_exist():
    required_files = [
        "artifacts/ml/defect_annotations/annotation_manifest.json",
        "artifacts/ml/defect_annotations/annotation_distribution.json",
        "artifacts/ml/defect_annotations/agreement_report.json",
        "artifacts/ml/defect_annotations/quality_report.json",
        "docs/PHASE_11_ANNOTATION.md",
        "docs/ANNOTATION_ADJUDICATION.md",
        "docs/DEFECT_DATASET_SCHEMA.md"
    ]
    for filepath in required_files:
        assert os.path.exists(filepath), f"Missing artifact/doc file: {filepath}"
