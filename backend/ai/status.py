"""AI Diagnostics and Health Status Tracker for S.P.O.T. pipeline.

Maintains runtime status, capabilities, preprocessing version, and last inference timing.
Exposes structured Pydantic models for GET /api/v1/ai/status.
"""

import os
import time
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from backend.ai.preprocessing import PREPROCESSING_VERSION


class AIStatusResponse(BaseModel):
    """Structured response schema for GET /api/v1/ai/status."""
    available: bool = Field(..., description="Whether a vision model is currently available for inference")
    model_name: str = Field(..., description="Name of registered active vision model")
    model_version: str = Field(..., description="Version of registered active vision model")
    source: Literal["development_mock", "real_model"] = Field(..., description="Explicit source identifier")
    loaded: bool = Field(..., description="Whether model weights/runtime are loaded in memory")
    runtime: str = Field(..., description="Execution device / runtime environment (e.g. PyTorch CPU, Ultralytics PyTorch)")
    capabilities: List[str] = Field(default_factory=list, description="Supported computer vision tasks")
    preprocessing_version: str = Field(default=PREPROCESSING_VERSION, description="Active image preprocessing contract version")
    status: Literal["READY", "NOT_CONFIGURED", "UNAVAILABLE", "ERROR"] = Field(..., description="Overall AI engine health status")
    last_successful_inference: Optional[str] = Field(default=None, description="ISO timestamp of last successful inference")
    last_inference_duration_ms: Optional[float] = Field(default=None, description="Duration in ms of last inference execution")
    environment: str = Field(..., description="Current environment setting (development/production)")


class AIHealthDiagnostics:
    """Global diagnostics recorder for AI vision engine."""
    _last_successful_inference: Optional[str] = None
    _last_inference_duration_ms: Optional[float] = None
    _total_inferences: int = 0

    @classmethod
    def record_inference(cls, duration_ms: float, timestamp_iso: str) -> None:
        """Record a completed inference event."""
        cls._last_inference_duration_ms = duration_ms
        cls._last_successful_inference = timestamp_iso
        cls._total_inferences += 1

    @classmethod
    def get_status(cls) -> AIStatusResponse:
        """Retrieve current AI engine health status."""
        env = os.getenv("SPOT_ENV", "development").lower()
        
        # Check model availability via registry
        from backend.ai.registry import get_vision_model, ProductionModelUnavailableError
        try:
            model = get_vision_model()
            is_available = True
            model_status: Literal["READY", "NOT_CONFIGURED", "UNAVAILABLE", "ERROR"] = "READY"
            source = model.source
            model_name = model.model_name
            model_version = model.model_version
            if source == "development_mock":
                runtime = "PyTorch / CPU (Mock Double)"
                capabilities = ["object_detection", "damage_classification", "rot_classification", "sprouting_classification"]
            else:
                # Real model: report the device it actually runs on.
                runtime = getattr(model, "runtime_device", None) or "PyTorch / CPU"
                capabilities = ["binary_quality_classification"]
        except ProductionModelUnavailableError:
            is_available = False
            model_status = "UNAVAILABLE"
            source = "real_model"
            model_name = "RealVisionModel"
            model_version = "unconfigured"
            runtime = "N/A"
            capabilities = []
        except Exception as e:
            is_available = False
            model_status = "ERROR"
            source = "development_mock"
            model_name = "Unknown"
            model_version = "0.0.0"
            runtime = f"Error: {str(e)}"
            capabilities = []

        return AIStatusResponse(
            available=is_available,
            model_name=model_name,
            model_version=model_version,
            source=source,
            loaded=is_available,
            runtime=runtime,
            capabilities=capabilities,
            preprocessing_version=PREPROCESSING_VERSION,
            status=model_status,
            last_successful_inference=cls._last_successful_inference,
            last_inference_duration_ms=cls._last_inference_duration_ms,
            environment=env,
        )
