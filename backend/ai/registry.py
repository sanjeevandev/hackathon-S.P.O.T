"""Vision Model Registry for S.P.O.T. pipeline.

Manages model loading and guarantees that production environment requests NEVER
silently fall back to development mock models.
"""

import os
from typing import Optional, Dict, Type
from backend.ai.base import VisionModel
from backend.ai.mock_model import DevelopmentMockVisionModel


class ProductionModelUnavailableError(Exception):
    """Raised when a production model is requested but no validated real model is registered/available."""
    pass


_MODEL_REGISTRY: Dict[str, Type[VisionModel]] = {
    "DevelopmentMockVisionModel": DevelopmentMockVisionModel,
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
                raise ProductionModelUnavailableError(
                    f"Forbidden: Requested production model '{model_name}' is not registered."
                )

        # Search for registered real model in production if no model_name specified
        real_models = [cls for cls in _MODEL_REGISTRY.values() if getattr(cls(), 'source', None) == 'real_model']
        if not real_models:
            raise ProductionModelUnavailableError(
                "Production Mode Error: No real vision model is registered or available. "
                "The system refuses to silently fall back to DevelopmentMockVisionModel in production. "
                "Ensure a validated model checkpoint (e.g. YOLO11 runner) is registered."
            )
        return real_models[0]()

    # Development or testing environment
    if model_name and model_name in _MODEL_REGISTRY:
        return _MODEL_REGISTRY[model_name]()

    # Default development fallback is explicitly DevelopmentMockVisionModel
    return DevelopmentMockVisionModel()

