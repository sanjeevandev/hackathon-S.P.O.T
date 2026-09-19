"""Unit tests for deterministic Explanation Engine."""

import pytest
from backend.contracts.schemas import BatchStatistics, GradingPresentation
from backend.reporting.explanation_engine import ExplanationEngine


@pytest.fixture
def sample_stats():
    return BatchStatistics(
        total_visible_onions=10, total_analyzed_onions=10, healthy_count=9,
        damaged_count=1, rotten_count=0, sprouted_count=0, undersized_count=0,
        healthy_percentage=90.0, damaged_percentage=10.0, rotten_percentage=0.0,
        sprouted_percentage=0.0, undersized_percentage=0.0
    )


@pytest.fixture
def sample_grading():
    return GradingPresentation(
        quality_score=90.0, prototype_grade="Grade-A", grade_a_percent=90.0, urs_percent=10.0,
        review_status="ACCEPTED", review_reason=[], inspection_confidence=0.92,
        grading_profile_id="prototype-procurement-v1", grading_profile_version="1.1.0-dev"
    )


def test_explanation_engine_complete_status(sample_stats, sample_grading):
    """Verify explanation for completed inspection matches numerical parameters."""
    exp = ExplanationEngine.generate("COMPLETE", sample_stats, sample_grading)
    assert "Grade-A" in exp.headline
    assert any("90.0%" in p for p in exp.primary_factors)
    assert exp.review_message is None
    assert len(exp.limitations) >= 4


def test_explanation_engine_retake_required_status(sample_stats, sample_grading):
    """Verify RETAKE_REQUIRED suppresses final grade and supplies retake guidance."""
    exp = ExplanationEngine.generate("RETAKE_REQUIRED", sample_stats, sample_grading)
    assert "Retake Required" in exp.headline
    assert exp.review_message is not None
    assert "retake" in exp.review_message.lower()


def test_explanation_engine_review_required_status(sample_stats, sample_grading):
    """Verify REVIEW_REQUIRED highlights human review guidance."""
    exp = ExplanationEngine.generate("REVIEW_REQUIRED", sample_stats, sample_grading, review_status="REVIEW_REQUIRED", review_reasons=["LOW_CONFIDENCE"])
    assert "Human Review Required" in exp.headline
    assert exp.review_message is not None
    assert any("LOW_CONFIDENCE" in p for p in exp.primary_factors)
