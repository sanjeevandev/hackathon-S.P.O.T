"""Integration tests for InspectionPipeline orchestration."""

import pytest
from typing import Literal
from backend.ai.base import VisionModel
from backend.ai.schemas import ImageInput, VisionResult
from backend.pipeline.pipeline import InspectionPipeline
from tests.fixtures import create_clean_image, create_blurry_image


class SpyVisionModel(VisionModel):
    """Spy vision model test double tracking execution calls."""

    def __init__(self):
        self.call_count = 0

    @property
    def model_name(self) -> str:
        return "SpyVisionModel"

    @property
    def model_version(self) -> str:
        return "1.0.0-spy"

    @property
    def source(self) -> Literal["development_mock", "real_model"]:
        return "development_mock"

    def analyze(self, image_input: ImageInput, image_bytes: bytes) -> VisionResult:
        self.call_count += 1
        return VisionResult(
            request_id=image_input.image_id,
            model_name=self.model_name,
            model_version=self.model_version,
            source=self.source,
            processing_time_ms=5.0,
            onions=[],
            overall_confidence=0.95,
            status="SUCCESS"
        )


def test_quality_gate_failure_prevents_vision_model_execution():
    """CRITICAL TEST: Verify RETAKE_REQUIRED prevents vision model analyze() from being called."""
    spy_model = SpyVisionModel()
    pipeline = InspectionPipeline(vision_model=spy_model)

    blurry_bytes = create_blurry_image()
    image_input = ImageInput(image_id="REQ-SPY-01", width=640, height=480)

    res = pipeline.execute(image_input, blurry_bytes)

    assert res.status == "RETAKE_REQUIRED"
    assert res.quality_gate.passed is False
    assert res.vision_result is None
    # CRITICAL CHECK: Vision model analyze() was NEVER executed
    assert spy_model.call_count == 0


def test_successful_pipeline_returns_results_and_timings():
    """Verify clean image passes quality gate and executes vision model with measured timings."""
    spy_model = SpyVisionModel()
    pipeline = InspectionPipeline(vision_model=spy_model)

    clean_bytes = create_clean_image()
    image_input = ImageInput(image_id="REQ-PASS-01", width=640, height=480)

    res = pipeline.execute(image_input, clean_bytes)

    assert res.status == "SUCCESS"
    assert res.quality_gate.status == "PASS"
    assert res.quality_gate.passed is True
    assert res.vision_result is not None
    assert spy_model.call_count == 1
    assert res.timings.quality_gate_time_ms > 0
    assert res.timings.total_pipeline_time_ms >= res.timings.quality_gate_time_ms


def test_pipeline_production_model_unavailable_handling():
    """Verify production pipeline resolves the REAL model now that the trained
    checkpoint is committed, and explicitly refuses the mock when requested."""
    pipeline = InspectionPipeline(environment="production")

    clean_bytes = create_clean_image()
    image_input = ImageInput(image_id="REQ-PROD-01", width=640, height=480)

    res = pipeline.execute(image_input, clean_bytes)
    assert res.status == "SUCCESS"
    assert res.vision_result is not None
    assert res.vision_result.source == "real_model"
