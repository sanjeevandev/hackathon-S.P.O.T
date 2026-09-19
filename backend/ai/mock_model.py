"""Development-only mock vision model for testing S.P.O.T. pipeline mechanics.

STRICT REALISM RULES:
- This is a TEST DOUBLE ONLY for pipeline integration testing.
- Must NEVER use random.Random or pseudo-random heuristics.
- Must NEVER fabricate fake model precision, latency, moisture %, or firmness.
- Output source MUST BE explicitly set to 'development_mock'.
- Production code MUST NEVER silently fall back to this mock model.
"""

import time
from typing import Literal
from backend.ai.base import VisionModel
from backend.ai.schemas import (
    ImageInput,
    VisionResult,
    OnionDetection,
    DefectProbabilities,
    SizeEstimate,
    EvidenceRegion,
)


class DevelopmentMockVisionModel(VisionModel):
    """Deterministic synthetic mock vision model for pipeline integration testing."""

    @property
    def model_name(self) -> str:
        return "DevelopmentMockVisionModel"

    @property
    def model_version(self) -> str:
        return "0.1.0-test"

    @property
    def source(self) -> Literal["development_mock", "real_model"]:
        return "development_mock"

    def analyze(self, image_input: ImageInput, image_bytes: bytes) -> VisionResult:
        """Executes deterministic test inference returning fixed synthetic detections.

        No random numbers or fake image hashes are used. Given the same inputs,
        it produces the exact same deterministic synthetic result every time.
        """
        start_time = time.perf_counter()

        # Fixed deterministic synthetic test bounding box 1 (Center-Left Bulb)
        # Scaled safely within input dimensions
        w, h = image_input.width, image_input.height
        box1_coords = [int(w * 0.1), int(h * 0.1), int(w * 0.4), int(h * 0.4)]
        box2_coords = [int(w * 0.5), int(h * 0.5), int(w * 0.8), int(h * 0.8)]

        detections = [
            OnionDetection(
                onion_id="MOCK-DETECTION-01",
                bbox=box1_coords,
                detection_confidence=0.90,
                defect_probabilities=DefectProbabilities(
                    damage=0.0,
                    rot=0.0,
                    sprouting=0.0
                ),
                size_estimate=SizeEstimate(
                    status="UNAVAILABLE",
                    estimated_diameter_mm=None,
                    calibration_method=None,
                    confidence=0.0
                ),
                evidence_regions=[]
            ),
            OnionDetection(
                onion_id="MOCK-DETECTION-02",
                bbox=box2_coords,
                detection_confidence=0.85,
                defect_probabilities=DefectProbabilities(
                    damage=0.10,
                    rot=0.0,
                    sprouting=0.0
                ),
                size_estimate=SizeEstimate(
                    status="UNAVAILABLE",
                    estimated_diameter_mm=None,
                    calibration_method=None,
                    confidence=0.0
                ),
                evidence_regions=[
                    EvidenceRegion(
                        type="synthetic_test_scuff",
                        coordinates=[box2_coords[0] + 5, box2_coords[1] + 5, box2_coords[0] + 20, box2_coords[1] + 20],
                        confidence=0.80
                    )
                ]
            )
        ]

        processing_time_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        return VisionResult(
            request_id=image_input.image_id,
            model_name=self.model_name,
            model_version=self.model_version,
            source=self.source,
            processing_time_ms=processing_time_ms,
            onions=detections,
            overall_confidence=0.875,
            status="SUCCESS",
            error_message=None
        )
