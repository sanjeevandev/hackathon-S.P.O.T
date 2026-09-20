"""Vision Model Registry for S.P.O.T. pipeline.

Manages model loading and guarantees that production environment requests NEVER
silently fall back to development mock models.
"""

import os
from typing import Optional, Dict, Type
from backend.ai.base import VisionModel
from backend.ai.mock_model import DevelopmentMockVisionModel
from backend.ai.yolo_cls_model import YOLO26ClassifierModel, _DEFAULT_CHECKPOINT, _YOLO26_CHECKPOINT_EXISTS


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


# Cache the (expensive) load-time contract validation so repeated registry
# lookups on `/api/v1/inspect` and `/api/v1/ai/status` don't re-load the
# checkpoint on every single request.
_yolo26_contract_cache: Optional[bool] = None


def _yolo26_contract_valid() -> bool:
    """True iff the YOLO26 checkpoint is present AND loads as a binary classifier.

    Computed once per process; the checkpoint file is expected to be static at
    runtime (re-deploying weights requires a process restart).
    """
    global _yolo26_contract_cache
    if _yolo26_contract_cache is None:
        if not _YOLO26_CHECKPOINT_EXISTS:
            _yolo26_contract_cache = False
        else:
            try:
                probe = YOLO26ClassifierModel()
                probe._load_model()
                _yolo26_contract_cache = True
            except Exception:
                _yolo26_contract_cache = False
    return _yolo26_contract_cache


def available_real_models() -> Dict[str, Type[VisionModel]]:
    """Return registry entries whose actual source is 'real_model' and whose
    checkpoint is present on disk and passes the runtime contract check (so we
    never advertise or select a model we cannot actually execute)."""
    real: Dict[str, Type[VisionModel]] = {}
    for name, cls in _MODEL_REGISTRY.items():
        try:
            instance = cls()
        except Exception:
            # Cannot even be constructed (e.g. missing checkpoint) — skip.
            continue
        if instance.source != "real_model":
            continue
        if name == "YOLO26ClassifierModel" and not _yolo26_contract_valid():
            continue
        real[name] = cls
    return real


def get_vision_model(environment: Optional[str] = None, model_name: Optional[str] = None) -> VisionModel:
    """Retrieve a VisionModel instance based on environment and requested model name.

    Selection order:
      1. Explicit `model_name` (development only or when it names a real model).
      2. `SPOT_VISION_MODEL` env variable.
      3. **A real model** (the intended production path). Only if no real model is
         registered does development fall back to the mock — and even then the
         result's `source` field stays 'development_mock' so callers can detect it.

    Raises:
        ProductionModelUnavailableError: If operating in production and no real
            validated model is available, or if a mock is explicitly requested.
        ValueError: If an unknown model name is requested.
    """
    env = (environment or os.getenv("SPOT_ENV", "development")).lower()
    model_name = model_name or os.getenv("SPOT_VISION_MODEL")

    if env == "production":
        # In production mode, we MUST NOT silently fall back to DevelopmentMockVisionModel.
        if model_name:
            if model_name == "DevelopmentMockVisionModel":
                raise ProductionModelUnavailableError(
                    f"Forbidden: Requested model '{model_name}' is a development mock model, "
                    "which cannot be executed in production environment (SPOT_ENV=production)."
                )
            if model_name in _MODEL_REGISTRY:
                return _MODEL_REGISTRY[model_name]()
            raise ValueError(
                f"Model '{model_name}' is not registered in the S.P.O.T. Vision Model Registry."
            )

        real = available_real_models()
        if real:
            # Prefer an explicitly configured production model name, else first available real model.
            first_cls = next(iter(real.values()))
            return first_cls()

        raise ProductionModelUnavailableError(
            "Production Mode Error: No real vision model is available. "
            "Ensure a validated model checkpoint is present (e.g. run scripts/train_yolo26_cls.py "
            "or scripts/train_yolo11_cls.py and register its runner)."
        )

    # Development mode
    if model_name:
        if model_name in _MODEL_REGISTRY:
            return _MODEL_REGISTRY[model_name]()
        raise ValueError(
            f"Model '{model_name}' is not registered in the S.P.O.T. Vision Model Registry."
        )

    # Development default: prefer a real model when available; otherwise the
    # development mock (explicitly labelled by its source field).
    real = available_real_models()
    if real:
        first_cls = next(iter(real.values()))
        return first_cls()

    return DevelopmentMockVisionModel()
