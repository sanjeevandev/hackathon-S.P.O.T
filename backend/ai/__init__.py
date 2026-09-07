"""AI Abstraction Module for S.P.O.T."""

from backend.ai.base import VisionModel
from backend.ai.mock_model import DevelopmentMockVisionModel
from backend.ai.registry import get_vision_model, register_vision_model, ProductionModelUnavailableError
from backend.ai.schemas import (
    ImageInput,
    VisionResult,
    OnionDetection,
    DefectProbabilities,
    SizeEstimate,
    EvidenceRegion,
)

__all__ = [
    "VisionModel",
    "DevelopmentMockVisionModel",
    "get_vision_model",
    "register_vision_model",
    "ProductionModelUnavailableError",
    "ImageInput",
    "VisionResult",
    "OnionDetection",
    "DefectProbabilities",
    "SizeEstimate",
    "EvidenceRegion",
]
