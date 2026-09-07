"""Strict validation engine for VisionModel outputs.

Guarantees that all model predictions conform to schema bounds, confidence limits,
coordinate boundaries, and status integrity. Rejects malformed predictions with explicit errors
and NEVER silently repairs invalid predictions.
"""

from typing import List, Optional
from backend.ai.schemas import VisionResult, OnionDetection, DefectProbabilities, EvidenceRegion


class ModelValidationError(Exception):
    """Raised when a VisionModel produces malformed or out-of-bounds output."""
    pass


class VisionOutputValidator:
    """Validator for VisionResult predictions."""

    @staticmethod
    def validate_vision_result(result: VisionResult, image_width: int, image_height: int) -> None:
        """Validate all fields of a VisionResult against strict criteria.

        Args:
            result: VisionResult object to validate.
            image_width: Width of the input frame in pixels.
            image_height: Height of the input frame in pixels.

        Raises:
            ModelValidationError: If any constraint is violated.
        """
        # 1. Status validation
        valid_statuses = {"SUCCESS", "NO_VALID_DETECTIONS", "MODEL_UNAVAILABLE", "ERROR"}
        if result.status not in valid_statuses:
            raise ModelValidationError(f"Invalid vision status: '{result.status}'. Must be one of {valid_statuses}")

        # 2. Source validation
        if result.source not in ("development_mock", "real_model"):
            raise ModelValidationError(f"Invalid model source: '{result.source}'. Must be 'development_mock' or 'real_model'")

        # 3. Overall confidence bounds
        if not (0.0 <= result.overall_confidence <= 1.0):
            raise ModelValidationError(f"Overall confidence {result.overall_confidence} out of bounds [0.0, 1.0]")

        # 4. Processing time bounds
        if result.processing_time_ms < 0.0:
            raise ModelValidationError(f"Processing time {result.processing_time_ms} cannot be negative")

        # 5. Validate each onion detection
        for idx, onion in enumerate(result.onions):
            VisionOutputValidator._validate_onion_detection(onion, idx, image_width, image_height)

    @staticmethod
    def _validate_onion_detection(onion: OnionDetection, index: int, img_w: int, img_h: int) -> None:
        """Validate a single onion detection."""
        # Bounding box format: [xmin, ymin, xmax, ymax]
        bbox = onion.bbox
        if len(bbox) != 4:
            raise ModelValidationError(f"Onion detection index {index} ({onion.onion_id}) bbox must contain 4 integers, got {len(bbox)}")

        xmin, ymin, xmax, ymax = bbox
        if xmin < 0 or ymin < 0:
            raise ModelValidationError(f"Onion detection index {index} ({onion.onion_id}) bbox coordinates cannot be negative: {bbox}")

        if xmin > xmax or ymin > ymax:
            raise ModelValidationError(f"Onion detection index {index} ({onion.onion_id}) invalid bbox order: [xmin, ymin, xmax, ymax] = {bbox}")

        # Coordinate dimension bounds
        if xmax > img_w or ymax > img_h:
            raise ModelValidationError(
                f"Onion detection index {index} ({onion.onion_id}) bbox {bbox} exceeds frame dimensions ({img_w}x{img_h})"
            )

        # Detection confidence
        if not (0.0 <= onion.detection_confidence <= 1.0):
            raise ModelValidationError(
                f"Onion detection index {index} ({onion.onion_id}) confidence {onion.detection_confidence} out of bounds [0.0, 1.0]"
            )

        # Defect probabilities validation
        VisionOutputValidator._validate_defect_probabilities(onion.defect_probabilities, onion.onion_id)

        # Evidence regions validation
        for ev in onion.evidence_regions:
            if not (0.0 <= ev.confidence <= 1.0):
                raise ModelValidationError(f"Evidence region '{ev.type}' on onion '{onion.onion_id}' confidence {ev.confidence} out of bounds")
            if len(ev.coordinates) != 4:
                raise ModelValidationError(f"Evidence region '{ev.type}' on onion '{onion.onion_id}' coordinates must be 4 integers")

    @staticmethod
    def _validate_defect_probabilities(probs: DefectProbabilities, onion_id: str) -> None:
        """Validate defect probability ranges."""
        for field_name in ("damage", "rot", "sprouting"):
            val = getattr(probs, field_name)
            if not (0.0 <= val <= 1.0):
                raise ModelValidationError(f"Onion '{onion_id}' defect probability '{field_name}' = {val} out of bounds [0.0, 1.0]")
