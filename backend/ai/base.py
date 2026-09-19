"""Abstract VisionModel interface for S.P.O.T. AI pipeline.

All vision model implementations (development mocks, YOLO11 runners, segmentation variants)
must implement this abstract contract. The application code depends solely on this interface.
"""

from abc import ABC, abstractmethod
from typing import Literal
from backend.ai.schemas import ImageInput, VisionResult


class VisionModel(ABC):
    """Abstract base class for all S.P.O.T. AI Vision models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name identifying the vision model implementation."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Semantic version of the model build or weights checkpoint."""
        pass

    @property
    @abstractmethod
    def source(self) -> Literal["development_mock", "real_model"]:
        """Explicit indicator of model source ('development_mock' or 'real_model')."""
        pass

    @abstractmethod
    def analyze(self, image_input: ImageInput, image_bytes: bytes) -> VisionResult:
        """Analyze an input image and return a structured VisionResult.

        Args:
            image_input: Metadata about the image (ID, dimensions, MIME type).
            image_bytes: Raw image byte stream.

        Returns:
            VisionResult object conforming to backend.ai.schemas.VisionResult.
        """
        pass
