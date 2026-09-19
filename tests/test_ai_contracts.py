"""Unit tests for AI Vision schemas and contract validation."""

import pytest
from pydantic import ValidationError
from backend.ai.schemas import (
    ImageInput,
    VisionResult,
    OnionDetection,
    DefectProbabilities,
    SizeEstimate,
    EvidenceRegion,
)


def test_ai_schema_fields_valid():
    """Verify VisionResult schema contains mandatory tracking fields."""
    result = VisionResult(
        request_id="REQ-TEST-01",
        model_name="TestModel",
        model_version="1.0.0",
        source="development_mock",
        processing_time_ms=12.5,
        onions=[],
        overall_confidence=0.90,
        status="SUCCESS"
    )
    assert result.request_id == "REQ-TEST-01"
    assert result.source == "development_mock"
    assert result.processing_time_ms == 12.5
    assert result.status == "SUCCESS"


def test_defect_probabilities_independent():
    """Verify defect probabilities support independent multi-label indicators."""
    defects = DefectProbabilities(
        damage=0.85,
        rot=0.40,
        sprouting=0.10
    )
    assert defects.damage == 0.85
    assert defects.rot == 0.40
    assert defects.sprouting == 0.10


def test_size_estimate_defaults_to_unavailable():
    """Verify SizeEstimate defaults to UNAVAILABLE status without uncalibrated pixel sizes."""
    size = SizeEstimate()
    assert size.status == "UNAVAILABLE"
    assert size.estimated_diameter_mm is None
    assert size.calibration_method is None


def test_schema_excludes_fake_physical_properties():
    """Verify VisionResult and OnionDetection schemas do NOT include fake moisture/firmness fields."""
    detection_fields = OnionDetection.model_fields.keys()
    result_fields = VisionResult.model_fields.keys()

    assert "moisture" not in detection_fields
    assert "moisture_level" not in result_fields
    assert "firmness" not in detection_fields
    assert "firmness_rating" not in result_fields
    assert "internal_rot" not in detection_fields

