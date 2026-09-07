"""Unit tests for report contract, HTML rendering, and versioning."""

import pytest
from backend.contracts.schemas import (
    BatchStatistics, Coverage, GradingPresentation, Explanation,
    ModelInformation, GradingProfileInformation, CanonicalInspectionResult
)
from backend.reporting.report_contract import InspectionReport
from backend.reporting.report_renderer import ReportRenderer


@pytest.fixture
def canonical_result():
    stats = BatchStatistics(
        total_visible_onions=5, total_analyzed_onions=5, healthy_count=5,
        damaged_count=0, rotten_count=0, sprouted_count=0, undersized_count=0,
        healthy_percentage=100.0, damaged_percentage=0.0, rotten_percentage=0.0,
        sprouted_percentage=0.0, undersized_percentage=0.0
    )
    cov = Coverage(captured_sample_images_count=1, total_visible_onions=5, total_analyzed_onions=5, sampling_status="SAMPLE_ONLY")
    grading = GradingPresentation(
        quality_score=100.0, prototype_grade="Grade-A", grade_a_percent=100.0, urs_percent=0.0,
        review_status="ACCEPTED", review_reason=[], inspection_confidence=0.95,
        grading_profile_id="prototype-procurement-v1", grading_profile_version="1.1.0-dev"
    )
    exp = Explanation(
        headline="Prototype Grade-A — Complete",
        primary_factors=["100% Grade-A"],
        supporting_factors=["Quality score: 100/100"],
        limitations=["Sample images only (SAMPLE_ONLY)."]
    )
    model_info = ModelInformation(model_id="DevMock", model_name="Mock", model_version="0.1.0", source="development_mock")
    profile_info = GradingProfileInformation(
        profile_id="prototype-procurement-v1", profile_name="Experimental Profile", version="1.1.0-dev",
        status="EXPERIMENTAL", official_status="NOT_OFFICIAL",
        disclaimer="Prototype grading profile. Not an official government certification or statutory grading standard."
    )
    return CanonicalInspectionResult(
        inspection_id="TEST-INSP-RPT-1",
        batch_id="TEST-BATCH-RPT-1",
        status="COMPLETE",
        sampling_status="SAMPLE_ONLY",
        image_quality={"quality_status": "PASS"},
        coverage=cov,
        onions=[],
        batch_statistics=stats,
        grading=grading,
        explanation=exp,
        confidence=0.95,
        review={"review_status": "ACCEPTED", "review_reason": ""},
        model=model_info,
        grading_profile=profile_info
    )


def test_structured_report_generation(canonical_result):
    """Verify structured InspectionReport generation from canonical result."""
    report = InspectionReport.from_canonical_result("RPT-101", canonical_result, report_version=1)
    assert report.report_id == "RPT-101"
    assert report.report_version == 1
    assert report.inspection_id == "TEST-INSP-RPT-1"
    assert report.model_information["source"] == "development_mock"
    assert report.disclaimer == "Prototype grading profile. Not an official government certification or statutory grading standard."


def test_html_report_rendering(canonical_result):
    """Verify HTML rendering contains key traceability metadata and disclaimers."""
    report = InspectionReport.from_canonical_result("RPT-101", canonical_result, report_version=1)
    html = ReportRenderer.render_html(report)
    assert "S.P.O.T. Digital Quality Inspection Report" in html
    assert "RPT-101" in html
    assert "Grade-A" in html
    assert "development_mock" in html
    assert "Prototype grading profile" in html
