"""Vision Model Registry for S.P.O.T. pipeline.

Manages model loading and guarantees that production environment requests NEVER
silently fall back to development mock models.
"""

import os
from typing import Optional, Dict, Type
from backend.ai.base import VisionModel
from backend.ai.mock_model import DevelopmentMockVisionModel
from backend.ai.yolo_cls_model import YOLO26ClassifierModel, _DEFAULT_CHECKPOINT


class ProductionModelUnavailableError(Exception):
    """Raised when a production model is requested but no validated real model is registered/available."""
    pass


_MODEL_REGISTRY: Dict[str, Type[VisionModel]] = {
    "DevelopmentMockVisionModel": DevelopmentMockVisionModel,
    "YOLO26ClassifierModel": YOLO26ClassifierModel,
}


def register_vision_model(name: str, model_cls: Type[VisionModel]) -> None:
    """Register a vision model implementation class in the registry."""
    _MODEL_REGISTRY[name] = model_cls


def get_vision_model(environment: Optional[str] = None, model_name: Optional[str] = None) -> VisionModel:
    """Retrieve a VisionModel instance based on environment and requested model name.

    Args:
        environment: Operating environment ('development' or 'production'). Defaults to SPOT_ENV env var.
        model_name: Optional specific model name requested.

    Returns:
        Instance of VisionModel conforming to VisionModel interface.

    Raises:
        ProductionModelUnavailableError: If operating in production and a real model is unavailable.
        ValueError: If an unknown model name is requested.
    """
    env = (environment or os.getenv("SPOT_ENV", "development")).lower()
    model_name = model_name or os.getenv("SPOT_VISION_MODEL")

    if env == "production":
        # In production mode, we MUST NOT silently fall back to DevelopmentMockVisionModel
        if model_name:
            if model_name in _MODEL_REGISTRY:
                model_cls = _MODEL_REGISTRY[model_name]
                instance = model_cls()
                if instance.source == "development_mock":
                    raise ProductionModelUnavailableError(
                        f"Forbidden: Requested model '{model_name}' is a development mock model, "
                        "which cannot be executed in production environment (SPOT_ENV=production)."
                    )
                return instance
            else:
                raise ValueError(
                    f"Model '{model_name}' is not registered in the S.P.O.T. Vision Model Registry."
                )
        else:
            # Default production request when no specific model is named:
            # Check if an explicit production model is registered (other than default dict entries)
            # If nothing was explicitly registered for production routing, raise ProductionModelUnavailableError
            real_models = {
                k: v for k, v in _MODEL_REGISTRY.items()
                if k != "DevelopmentMockVisionModel" and k != "YOLO26ClassifierModel"
            }
            if real_models:
                first_cls = next(iter(real_models.values()))
                return first_cls()

            raise ProductionModelUnavailableError(
                "Production Mode Error: No real vision model is registered. "
                "Ensure a validated model checkpoint (e.g. YOLO26 runner) is registered."
            )

    # In development mode: check requested model_name or env var
    if model_name:
        if model_name in _MODEL_REGISTRY:
            return _MODEL_REGISTRY[model_name]()
        raise ValueError(
            f"Model '{model_name}' is not registered in the S.P.O.T. Vision Model Registry."
        )

    return DevelopmentMockVisionModel()
