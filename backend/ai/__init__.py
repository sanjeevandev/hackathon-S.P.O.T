"""S.P.O.T. AI Pipeline Package."""

from backend.ai.base import VisionModel
from backend.ai.mock_model import DevelopmentMockVisionModel
from backend.ai.yolo_cls_model import YOLO26ClassifierModel
from backend.ai.registry import (
    get_vision_model,
    register_vision_model,
    ProductionModelUnavailableError,
)
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
    "YOLO26ClassifierModel",
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
