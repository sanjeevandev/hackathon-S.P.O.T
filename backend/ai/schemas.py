"""Typed Pydantic schemas for the AI Vision abstraction layer.

Supported defects conform to SIH 2026 PS 26031 visible surface defect requirements:
- damage (mechanical cracks, cuts, bruises)
- rot (surface wet rot, fungal decay)
- sprouting (neck growth)

Size estimation is tracked separately via SizeEstimate and defaults to status='UNAVAILABLE'
until physical optical reference calibration is implemented.
No fake physical properties (moisture %, firmness %, internal rot %) are present.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ImageInput(BaseModel):
    image_id: str = Field(..., description="Unique image identifier")
    width: int = Field(..., ge=1, description="Image width in pixels")
    height: int = Field(..., ge=1, description="Image height in pixels")
    mime_type: str = Field(default="image/jpeg", description="MIME type of the input image")
    file_reference: Optional[str] = Field(default=None, description="Path or URL reference to raw image file")


class DefectProbabilities(BaseModel):
    damage: float = Field(default=0.0, ge=0.0, le=1.0, description="Probability of mechanical damage/cracks")
    rot: float = Field(default=0.0, ge=0.0, le=1.0, description="Probability of surface moisture/fungal rot")
    sprouting: float = Field(default=0.0, ge=0.0, le=1.0, description="Probability of neck shoot sprouting")


class SizeEstimate(BaseModel):
    status: Literal["AVAILABLE", "UNAVAILABLE", "UNCALIBRATED"] = Field(
        default="UNAVAILABLE",
        description="Status of size calibration"
    )
    estimated_diameter_mm: Optional[float] = Field(
        default=None,
        description="Estimated bulb diameter in mm if calibrated, otherwise None"
    )
    calibration_method: Optional[str] = Field(
        default=None,
        description="Method used for pixel-to-mm calibration"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Confidence in size estimation"
    )


class EvidenceRegion(BaseModel):
    type: str = Field(..., description="Type of evidence locus (e.g., sprout_tip, rot_patch, damage_scuff)")
    coordinates: List[int] = Field(..., description="[x1, y1, x2, y2] bounding box coordinates of evidence region")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for evidence region")


class OnionDetection(BaseModel):
    onion_id: str = Field(..., description="Unique ID for detected onion within the image frame")
    bbox: List[int] = Field(..., description="[x1, y1, x2, y2] bounding box coordinates in pixels")
    detection_confidence: float = Field(..., ge=0.0, le=1.0, description="Object detection confidence score")
    defect_probabilities: DefectProbabilities = Field(default_factory=DefectProbabilities)
    size_estimate: SizeEstimate = Field(default_factory=SizeEstimate)
    evidence_regions: List[EvidenceRegion] = Field(default_factory=list)


class VisionResult(BaseModel):
    request_id: str = Field(..., description="Unique request tracing identifier")
    model_name: str = Field(..., description="Name of the vision model used")
    model_version: str = Field(..., description="Version of the vision model used")
    source: Literal["development_mock", "real_model"] = Field(
        ...,
        description="Explicit source indicator: 'development_mock' or 'real_model'"
    )
    processing_time_ms: float = Field(..., ge=0.0, description="Measured model inference duration in milliseconds")
    onions: List[OnionDetection] = Field(default_factory=list, description="List of detected onion bulbs")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score across detections")
    status: Literal["SUCCESS", "NO_VALID_DETECTIONS", "MODEL_UNAVAILABLE", "ERROR"] = Field(
        ...,
        description="Status of vision inference step"
    )
    error_message: Optional[str] = Field(default=None, description="Detailed error message if status is ERROR")
