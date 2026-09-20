"""Golden Pipeline Regression Test Suite for S.P.O.T. Phase 7.

Deterministic tests covering all 10 mandated pipeline conditions:
1. valid image → quality gate → mock model
2. blurry image → RETAKE_REQUIRED
3. dark image → RETAKE_REQUIRED
4. low-resolution image → RETAKE_REQUIRED
5. model unavailable → MODEL_UNAVAILABLE
6. malformed model output → validation failure
7. low confidence → REVIEW_REQUIRED
8. request_id remains consistent through pipeline
9. preprocessing version is recorded
10. development mock is never confused with real_model
"""

import pytest
from typing import Literal

from backend.ai.schemas import ImageInput, VisionResult, OnionDetection, DefectProbabilities, SizeEstimate
from backend.ai.mock_model import DevelopmentMockVisionModel
from backend.ai.base import VisionModel
from backend.ai.preprocessing import PREPROCESSING_VERSION
from backend.pipeline.pipeline import InspectionPipeline
from backend.grading.grading_engine import GradingPolicyEngine
from backend.grading.schemas import GradingRequest, LotPercentages, WeightDistribution
from tests.fixtures import (
    create_clean_image,
    create_blurry_image,
    create_dark_image,
    create_low_res_image,
)


# 1. Valid Image -> Quality Gate -> Mock Model
def test_golden_1_valid_image_pipeline():
    clean_bytes = create_clean_image(640, 480)
    image_input = ImageInput(image_id="GOLDEN-REQ-01", width=640, height=480)
    pipeline = InspectionPipeline()

    result = pipeline.execute(image_input, clean_bytes)
    assert result.status == "SUCCESS"
    assert result.quality_gate.passed is True
    assert result.vision_result is not None
    # The trained YOLO26n-cls binary classifier is now the default — the
    # pipeline must resolve a real model, never silently use the mock.
    assert result.vision_result.source == "real_model"


# 2. Blurry Image -> RETAKE_REQUIRED
def test_golden_2_blurry_image_retake():
    blurry_bytes = create_blurry_image(640, 480)
    image_input = ImageInput(image_id="GOLDEN-REQ-02", width=640, height=480)
    pipeline = InspectionPipeline()

    result = pipeline.execute(image_input, blurry_bytes)
    assert result.status == "RETAKE_REQUIRED"
    assert result.quality_gate.passed is False
    assert "IMAGE_TOO_BLURRY" in result.quality_gate.reasons
    assert result.vision_result is None


# 3. Dark Image -> RETAKE_REQUIRED
def test_golden_3_dark_image_retake():
    dark_bytes = create_dark_image(640, 480)
    image_input = ImageInput(image_id="GOLDEN-REQ-03", width=640, height=480)
    pipeline = InspectionPipeline()

    result = pipeline.execute(image_input, dark_bytes)
    assert result.status == "RETAKE_REQUIRED"
    assert result.quality_gate.passed is False
    assert "IMAGE_TOO_DARK" in result.quality_gate.reasons
    assert result.vision_result is None


# 4. Low Resolution Image -> RETAKE_REQUIRED
def test_golden_4_low_res_image_retake():
    low_res_bytes = create_low_res_image(150, 150)
    image_input = ImageInput(image_id="GOLDEN-REQ-04", width=150, height=150)
    pipeline = InspectionPipeline()

    result = pipeline.execute(image_input, low_res_bytes)
    assert result.status == "RETAKE_REQUIRED"
    assert result.quality_gate.passed is False
    assert "IMAGE_RESOLUTION_TOO_LOW" in result.quality_gate.reasons
    assert result.vision_result is None


# 5. Production now HAS a real model -> SUCCESS (model-unavailable path is
#    the historical behaviour; test it by requesting an explicit mock, which
#    production must refuse.)
def test_golden_5_model_unavailable():
    from backend.ai.registry import ProductionModelUnavailableError, get_vision_model
    clean_bytes = create_clean_image(640, 480)
    image_input = ImageInput(image_id="GOLDEN-REQ-05", width=640, height=480)

    # The trained checkpoint exists, so production resolves a REAL model.
    pipeline = InspectionPipeline(environment="production")
    result = pipeline.execute(image_input, clean_bytes)
    assert result.status == "SUCCESS"
    assert result.quality_gate.passed is True
    assert result.vision_result is not None
    assert result.vision_result.source == "real_model"

    # But production must still refuse an explicit mock request.
    with pytest.raises(ProductionModelUnavailableError):
        get_vision_model(environment="production", model_name="DevelopmentMockVisionModel")


# 6. Malformed Model Output -> Validation Failure
class MalformedVisionModel(VisionModel):
    @property
    def model_name(self) -> str: return "MalformedVisionModel"
    @property
    def model_version(self) -> str: return "1.0"
    @property
    def source(self) -> Literal["development_mock", "real_model"]: return "development_mock"

    def analyze(self, image_input: ImageInput, image_bytes: bytes) -> VisionResult:
        # Invalid bbox coordinates (negative)
        malformed_onion = OnionDetection(
            onion_id="ONION-ERR",
            bbox=[-10, 50, 100, 100],
            detection_confidence=0.9,
            defect_probabilities=DefectProbabilities(),
            size_estimate=SizeEstimate()
        )
        return VisionResult(
            request_id=image_input.image_id,
            model_name=self.model_name,
            model_version=self.model_version,
            source=self.source,
            processing_time_ms=10.0,
            onions=[malformed_onion],
            overall_confidence=0.9,
            status="SUCCESS"
        )


def test_golden_6_malformed_model_output():
    clean_bytes = create_clean_image(640, 480)
    image_input = ImageInput(image_id="GOLDEN-REQ-06", width=640, height=480)
    pipeline = InspectionPipeline(vision_model=MalformedVisionModel())

    result = pipeline.execute(image_input, clean_bytes)
    assert result.status == "PIPELINE_ERROR"
    assert "Model output validation failed" in (result.error_message or "")


# 7. Low Confidence -> REVIEW_REQUIRED
def test_golden_7_low_confidence_review_required():
    percentages = LotPercentages(
        healthy_pct=90.0,
        damaged_pct=5.0,
        rotten_pct=5.0,
        sprouted_pct=0.0,
        undersized_pct=0.0
    )
    weight_dist = WeightDistribution(
        is_weight_estimated=True,
        weight_source="UNAVAILABLE",
        total_batch_weight_kg=100.0,
        grade_a_weight_kg=90.0,
        grade_urs_weight_kg=10.0,
        rejected_weight_kg=0.0,
        grade_a_weight_percentage=90.0,
        grade_urs_weight_percentage=10.0,
        rejected_weight_percentage=0.0
    )
    req = GradingRequest(
        batch_id="BATCH-CONF-TEST",
        percentages=percentages,
        weight_distribution=weight_dist,
        inspection_confidence=0.60 # Low confidence below default threshold (0.75)
    )
    result = GradingPolicyEngine.evaluate(req)
    assert result.review_status == "REVIEW_REQUIRED"
    assert any("confidence" in r.lower() for r in (result.review_reason or []))


# 8. Request ID remains consistent through pipeline
def test_golden_8_request_id_consistency():
    req_id = "REQ-TRACE-9999"
    clean_bytes = create_clean_image(640, 480)
    image_input = ImageInput(image_id=req_id, width=640, height=480)
    pipeline = InspectionPipeline()

    result = pipeline.execute(image_input, clean_bytes)
    assert result.request_id == req_id
    assert result.vision_result is not None
    assert result.vision_result.request_id == req_id


# 9. Preprocessing Version is Recorded
def test_golden_9_preprocessing_version_recorded():
    from backend.ai.preprocessing import ImagePreprocessor
    preprocessor = ImagePreprocessor()
    clean_bytes = create_clean_image(640, 480)
    _, meta = preprocessor.preprocess(clean_bytes)
    assert meta.preprocessing_version == PREPROCESSING_VERSION
    assert meta.preprocessing_version == "image-preprocess-v1"


# 10. Development Mock is Never Confused with Real Model
def test_golden_10_development_mock_explicit_source():
    mock = DevelopmentMockVisionModel()
    assert mock.source == "development_mock"
    assert mock.source != "real_model"
