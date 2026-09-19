"""Contract Compatibility Test demonstrating interface-driven vision model design.

Proves that the InspectionPipeline depends strictly on the abstract VisionModel interface
and can run seamlessly with an independent implementation (ContractTestVisionModel)
without code modifications.
"""

from typing import Literal
from backend.ai.base import VisionModel
from backend.ai.schemas import ImageInput, VisionResult, OnionDetection, DefectProbabilities, SizeEstimate
from backend.pipeline.pipeline import InspectionPipeline
from tests.fixtures import create_clean_image


class ContractTestVisionModel(VisionModel):
    """Independent test implementation of VisionModel interface."""

    @property
    def model_name(self) -> str:
        return "ContractTestVisionModel"

    @property
    def model_version(self) -> str:
        return "1.0.0-test"

    @property
    def source(self) -> Literal["development_mock", "real_model"]:
        return "real_model"

    def analyze(self, image_input: ImageInput, image_bytes: bytes) -> VisionResult:
        detection = OnionDetection(
            onion_id="ONION-TEST-01",
            bbox=[50, 50, 200, 200],
            detection_confidence=0.98,
            defect_probabilities=DefectProbabilities(damage=0.0, rot=0.0, sprouting=0.0),
            size_estimate=SizeEstimate(status="AVAILABLE", estimated_diameter_mm=55.0, confidence=0.9)
        )
        return VisionResult(
            request_id=image_input.image_id,
            model_name=self.model_name,
            model_version=self.model_version,
            source=self.source,
            processing_time_ms=12.5,
            onions=[detection],
            overall_confidence=0.98,
            status="SUCCESS",
            error_message=None
        )


def test_pipeline_with_contract_test_vision_model():
    """Verify that InspectionPipeline executes successfully with ContractTestVisionModel."""
    model = ContractTestVisionModel()
    pipeline = InspectionPipeline(vision_model=model)
    clean_bytes = create_clean_image(640, 480)

    image_input = ImageInput(
        image_id="REQ-CONTRACT-TEST",
        width=640,
        height=480,
        mime_type="image/jpeg"
    )

    result = pipeline.execute(image_input, clean_bytes)

    assert result.status == "SUCCESS"
    assert result.vision_result is not None
    assert result.vision_result.model_name == "ContractTestVisionModel"
    assert result.vision_result.source == "real_model"
    assert len(result.vision_result.onions) == 1
    assert result.vision_result.onions[0].onion_id == "ONION-TEST-01"
