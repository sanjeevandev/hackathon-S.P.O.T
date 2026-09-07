"""Canonical Inspection Result and Evidence Presentation Contracts."""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class EvidenceRegion(BaseModel):
    """Detailed visual evidence sub-region within an onion bounding box."""
    defect_type: str = Field(..., description="Defect type label (e.g. DAMAGE, ROT, SPROUTING)")
    coordinates: List[int] = Field(..., description="[ymin, xmin, ymax, xmax] relative pixel box within crop")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score for region")
    region_reference: Optional[str] = Field(default=None, description="Local or object-storage reference to cropped region image")


class OnionResult(BaseModel):
    """Canonical presentation model for individual onion bulb evidence."""
    onion_id: str = Field(..., description="Unique onion identifier within image/batch")
    bounding_box: List[int] = Field(..., description="[ymin, xmin, ymax, xmax] bounding box in full frame")
    mask_reference: Optional[str] = Field(default=None, description="Segmentation mask reference if present")
    detection_confidence: float = Field(..., ge=0.0, le=1.0)
    defect_probabilities: Dict[str, float] = Field(..., description="Map of defect types to probabilities")
    size_estimate: Dict[str, Optional[Any]] = Field(..., description="Size diameter mm, status, and confidence")
    evidence_regions: List[EvidenceRegion] = Field(default_factory=list)
    final_status: str = Field(..., description="Individual classification: HEALTHY, DAMAGED, ROTTEN, SPROUTED, UNDERSIZED")


class BatchStatistics(BaseModel):
    """Canonical batch-level aggregate count and percentage summary."""
    total_visible_onions: int = Field(..., ge=0)
    total_analyzed_onions: int = Field(..., ge=0)
    healthy_count: int = Field(..., ge=0)
    damaged_count: int = Field(..., ge=0)
    rotten_count: int = Field(..., ge=0)
    sprouted_count: int = Field(..., ge=0)
    undersized_count: int = Field(..., ge=0)
    healthy_percentage: float = Field(..., ge=0.0, le=100.0)
    damaged_percentage: float = Field(..., ge=0.0, le=100.0)
    rotten_percentage: float = Field(..., ge=0.0, le=100.0)
    sprouted_percentage: float = Field(..., ge=0.0, le=100.0)
    undersized_percentage: float = Field(..., ge=0.0, le=100.0)


class Coverage(BaseModel):
    """Inspection sample coverage tracking."""
    captured_sample_images_count: int = Field(..., ge=0)
    total_visible_onions: int = Field(..., ge=0)
    total_analyzed_onions: int = Field(..., ge=0)
    sampling_status: str = Field(default="SAMPLE_ONLY", description="Always SAMPLE_ONLY unless verified full-lot census")
    coverage_notes: str = Field(default="Inspection metrics are derived solely from captured sample images.")


class GradingPresentation(BaseModel):
    """Canonical presentation of lot grading results."""
    quality_score: Optional[float] = Field(default=None, description="0-100 commercial score. None if RETAKE_REQUIRED or MODEL_UNAVAILABLE")
    prototype_grade: Optional[str] = Field(default=None, description="Grade-A, Grade-URS, Grade-C. Suppressed if RETAKE_REQUIRED or MODEL_UNAVAILABLE")
    grade_a_percent: float = Field(..., ge=0.0, le=100.0)
    urs_percent: float = Field(..., ge=0.0, le=100.0)
    review_status: str = Field(..., description="ACCEPTED, REVIEW_REQUIRED, RETAKE_REQUIRED")
    review_reason: List[str] = Field(default_factory=list)
    inspection_confidence: float = Field(..., ge=0.0, le=1.0)
    grading_profile_id: str = Field(...)
    grading_profile_version: str = Field(...)


class Explanation(BaseModel):
    """Deterministic, transparent breakdown of grading policy evaluation."""
    headline: str = Field(..., description="Clear grade summary headline")
    primary_factors: List[str] = Field(..., description="Primary numerical factors driving grade determination")
    supporting_factors: List[str] = Field(default_factory=list, description="Secondary factors or quality metrics")
    review_message: Optional[str] = Field(default=None, description="Human review guidance if review_status is REVIEW_REQUIRED")
    limitations: List[str] = Field(..., description="Mandatory legal and physical inspection disclaimers")


class ModelInformation(BaseModel):
    """Model version traceability contract."""
    model_id: str
    model_name: str
    model_version: str
    source: str = Field(..., description="development_mock or real_model")


class GradingProfileInformation(BaseModel):
    """Grading profile policy metadata contract."""
    profile_id: str
    profile_name: str
    version: str
    status: str = Field(..., description="EXPERIMENTAL")
    official_status: str = Field(..., description="NOT_OFFICIAL")
    disclaimer: str


class CanonicalInspectionResult(BaseModel):
    """Complete, unified data contract for frontend consumption."""
    inspection_id: str
    batch_id: str
    status: Literal["COMPLETE", "RETAKE_REQUIRED", "REVIEW_REQUIRED", "MODEL_UNAVAILABLE", "FAILED"]
    sampling_status: str = Field(default="SAMPLE_ONLY")
    image_quality: Dict[str, Any] = Field(..., description="Image quality gate status and summary metrics")
    coverage: Coverage
    onions: List[OnionResult] = Field(default_factory=list)
    batch_statistics: BatchStatistics
    grading: Optional[GradingPresentation] = Field(default=None)
    explanation: Explanation
    confidence: float = Field(..., ge=0.0, le=1.0)
    review: Dict[str, Any] = Field(..., description="review_status and review_reason")
    model: ModelInformation
    grading_profile: GradingProfileInformation
    report_reference: Optional[str] = Field(default=None)
