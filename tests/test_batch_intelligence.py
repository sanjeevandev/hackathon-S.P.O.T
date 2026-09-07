"""Unit tests for BatchIntelligenceEngine aggregation logic and weight estimation rules."""

import pytest
from backend.ai.schemas import (
    VisionResult,
    OnionDetection,
    DefectProbabilities,
)
from backend.grading.batch_engine import BatchIntelligenceEngine


def test_batch_aggregation_sampling_status_defaults_to_sample_only():
    """Verify sampling_status defaults to SAMPLE_ONLY and coverage notes bound physical lot scope."""
    vr = VisionResult(
        request_id="REQ-1", model_name="TestModel", model_version="1.0",
        source="development_mock", processing_time_ms=10.0, onions=[], overall_confidence=0.90, status="SUCCESS"
    )

    agg = BatchIntelligenceEngine.aggregate_batch("BATCH-001", [vr])

    assert agg.sampling_status == "SAMPLE_ONLY"
    assert agg.coverage.captured_sample_images_count == 1
    assert "Analysis represents captured sample frame lot only" in agg.coverage.coverage_notes


def test_weight_is_not_fabricated_when_unsupplied():
    """Verify weight fields are marked UNAVAILABLE and not fabricated when declared weight is unsupplied."""
    onions = [
        OnionDetection(
            onion_id="O1", bbox=[10, 10, 50, 50], detection_confidence=0.90,
            defect_probabilities=DefectProbabilities(damage=0.0, rot=0.0, sprouting=0.0)
        )
    ]
    vr = VisionResult(
        request_id="REQ-1", model_name="TestModel", model_version="1.0",
        source="development_mock", processing_time_ms=10.0, onions=onions, overall_confidence=0.90, status="SUCCESS"
    )

    agg = BatchIntelligenceEngine.aggregate_batch("BATCH-002", [vr], declared_total_weight_kg=None)

    assert agg.weight_distribution.is_weight_estimated is False
    assert agg.weight_distribution.weight_source == "UNAVAILABLE"
    assert agg.weight_distribution.total_batch_weight_kg is None
    assert agg.weight_distribution.grade_a_weight_kg is None


def test_weight_is_labeled_proportional_estimate_when_supplied():
    """Verify weight is clearly marked as PROPORTIONAL_SAMPLE_ESTIMATE when declared weight is provided."""
    onions = [
        OnionDetection(
            onion_id="O1", bbox=[10, 10, 50, 50], detection_confidence=0.90,
            defect_probabilities=DefectProbabilities(damage=0.0, rot=0.0, sprouting=0.0)
        )
    ]
    vr = VisionResult(
        request_id="REQ-1", model_name="TestModel", model_version="1.0",
        source="development_mock", processing_time_ms=10.0, onions=onions, overall_confidence=0.90, status="SUCCESS"
    )

    agg = BatchIntelligenceEngine.aggregate_batch("BATCH-003", [vr], declared_total_weight_kg=50.0)

    assert agg.weight_distribution.is_weight_estimated is True
    assert agg.weight_distribution.weight_source == "PROPORTIONAL_SAMPLE_ESTIMATE"
    assert agg.weight_distribution.total_batch_weight_kg == 50.0
    assert agg.weight_distribution.grade_a_weight_kg == 50.0
