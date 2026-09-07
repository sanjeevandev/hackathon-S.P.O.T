"""Unit tests for Canonical Inspection Result serialization and contracts."""

import pytest
from backend.contracts.schemas import (
    EvidenceRegion,
    OnionResult,
    BatchStatistics,
    Coverage,
    GradingPresentation,
    Explanation,
    ModelInformation,
    GradingProfileInformation,
    CanonicalInspectionResult,
)


def test_canonical_inspection_result_serialization():
    """Verify CanonicalInspectionResult model fields and Pydantic serialization."""
    ev = EvidenceRegion(defect_type="DAMAGE", coordinates=[10, 10, 50, 50], confidence=0.85)
    onion = OnionResult(
        onion_id="O1",
        bounding_box=[10, 10, 100, 100],
        detection_confidence=0.95,
        defect_probabilities={"damage": 0.1, "rot": 0.0, "sprouting": 0.0},
        size_estimate={"estimated_diameter_mm": None, "status": "UNAVAILABLE", "confidence": 0.0},
        evidence_regions=[ev],
        final_status="HEALTHY"
    )

    stats = BatchStatistics(
        total_visible_onions=1, total_analyzed_onions=1, healthy_count=1,
        damaged_count=0, rotten_count=0, sprouted_count=0, undersized_count=0,
        healthy_percentage=100.0, damaged_percentage=0.0, rotten_percentage=0.0,
        sprouted_percentage=0.0, undersized_percentage=0.0
    )

    cov = Coverage(captured_sample_images_count=1, total_visible_onions=1, total_analyzed_onions=1, sampling_status="SAMPLE_ONLY")

    grading = GradingPresentation(
        quality_score=100.0, prototype_grade="Grade-A", grade_a_percent=100.0, urs_percent=0.0,
        review_status="ACCEPTED", review_reason=[], inspection_confidence=0.95,
        grading_profile_id="prototype-procurement-v1", grading_profile_version="1.1.0-dev"
    )

    exp = Explanation(
        headline="Prototype Grade-A — Complete",
        primary_factors=["Visible Grade-A percentage: 100.0%"],
        supporting_factors=["Quality score: 100/100"],
        limitations=["RGB imaging does not assess internal decay."]
    )

    model_info = ModelInformation(model_id="DevMock", model_name="Mock", model_version="0.1.0", source="development_mock")
    profile_info = GradingProfileInformation(
        profile_id="prototype-procurement-v1", profile_name="Experimental", version="1.1.0",
        status="EXPERIMENTAL", official_status="NOT_OFFICIAL",
        disclaimer="Prototype grading profile."
    )

    result = CanonicalInspectionResult(
        inspection_id="TEST-INSP-1",
        batch_id="TEST-BATCH-1",
        status="COMPLETE",
        sampling_status="SAMPLE_ONLY",
        image_quality={"quality_status": "PASS"},
        coverage=cov,
        onions=[onion],
        batch_statistics=stats,
        grading=grading,
        explanation=exp,
        confidence=0.95,
        review={"review_status": "ACCEPTED", "review_reason": ""},
        model=model_info,
        grading_profile=profile_info
    )

    assert result.inspection_id == "TEST-INSP-1"
    assert result.coverage.sampling_status == "SAMPLE_ONLY"
    assert result.model.source == "development_mock"
    assert len(result.onions[0].evidence_regions) == 1
