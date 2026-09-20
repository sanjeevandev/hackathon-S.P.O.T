"""Typed Pydantic schemas for Quality Gate and Inspection Pipeline results."""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from backend.ai.schemas import VisionResult


class QualityGateMetrics(BaseModel):
    blur_score: float = Field(..., description="Calculated Laplacian variance blur score")
    brightness: float = Field(..., description="Average pixel intensity (0-255)")
    contrast: float = Field(..., description="Pixel intensity standard deviation")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")


class QualityGateResult(BaseModel):
    """Result returned by the Image Quality Gate screening layer."""

    status: Literal["PASS", "RETAKE_REQUIRED", "REJECTED_NOT_ONION"] = Field(
        ...,
        description="Quality gate status: PASS, RETAKE_REQUIRED, or REJECTED_NOT_ONION"
    )
    passed: bool = Field(..., description="True if image passed quality screening, False otherwise")
    reasons: List[str] = Field(
        default_factory=list,
        description="Explicit list of quality rejection reason codes (e.g. IMAGE_TOO_BLURRY, NOT_AN_ONION)"
    )
    metrics: QualityGateMetrics = Field(..., description="Calculated objective quality metrics")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable user feedback to guide image retake"
    )


class PipelineTimings(BaseModel):
    image_decode_time_ms: float = Field(default=0.0, ge=0.0, description="Measured time to decode image bytes")
    preprocessing_time_ms: float = Field(default=0.0, ge=0.0, description="Measured time for preprocessing pipeline")
    quality_gate_time_ms: float = Field(..., ge=0.0, description="Measured execution time of quality gate in ms")
    model_time_ms: float = Field(default=0.0, ge=0.0, description="Measured execution time of vision model in ms")
    aggregation_time_ms: float = Field(default=0.0, ge=0.0, description="Measured batch aggregation duration in ms")
    grading_time_ms: float = Field(default=0.0, ge=0.0, description="Measured grading policy calculation duration in ms")
    persistence_time_ms: float = Field(default=0.0, ge=0.0, description="Measured database persistence duration in ms")
    total_pipeline_time_ms: float = Field(..., ge=0.0, description="Measured total end-to-end pipeline time in ms")
    vision_time_ms: float = Field(default=0.0, ge=0.0, description="Legacy alias for model_time_ms")


class PipelineResult(BaseModel):
    """Complete end-to-end result returned by the InspectionPipeline orchestrator."""

    status: Literal["SUCCESS", "RETAKE_REQUIRED", "REJECTED_NOT_ONION", "REVIEW_REQUIRED", "MODEL_UNAVAILABLE", "PIPELINE_ERROR"] = Field(
        ...,
        description=(
            "Pipeline execution status. REVIEW_REQUIRED indicates the image passed "
            "quality screening and the model ran, but classified below its accepted "
            "confidence threshold; unlike the other terminal states, vision_result is "
            "present and carries the model's explicit per-result status and confidence."
        )
    )
    request_id: str = Field(..., description="Unique request tracing ID")
    quality_gate: QualityGateResult = Field(..., description="Quality Gate screening result")
    vision_result: Optional[VisionResult] = Field(
        default=None,
        description="Vision model output. MUST BE None if quality_gate.passed is False."
    )
    timings: PipelineTimings = Field(..., description="Real measured execution duration metrics")
    error_message: Optional[str] = Field(default=None, description="Error message if pipeline status is ERROR")
