"""Typed Pydantic schemas for Batch Intelligence and Grading Policy Engine.

Decouples commercial procurement policy rules from vision model perception outputs.
All calculations are deterministic, reproducible, and rule-driven.
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class LotCounts(BaseModel):
    total_onions: int = Field(..., ge=0, description="Total count of detected onion bulbs across sample images")
    healthy_count: int = Field(..., ge=0, description="Count of healthy candidate onions")
    damaged_count: int = Field(..., ge=0, description="Count of onions with mechanical surface damage")
    rotten_count: int = Field(..., ge=0, description="Count of onions exhibiting moisture or fungal rot")
    sprouted_count: int = Field(..., ge=0, description="Count of onions exhibiting neck shoot sprouting")
    undersized_count: int = Field(..., ge=0, description="Count of undersized onions (< 45mm diameter)")


class LotPercentages(BaseModel):
    healthy_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of healthy onions")
    damaged_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of damaged onions")
    rotten_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of rotten onions")
    sprouted_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of sprouted onions")
    undersized_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of undersized onions")


class WeightDistribution(BaseModel):
    is_weight_estimated: bool = Field(..., description="True if weight allocation is an estimate from sample count")
    weight_source: Literal["PROPORTIONAL_SAMPLE_ESTIMATE", "SCALE_HARDWARE_SYNC", "UNAVAILABLE"] = Field(...)
    total_batch_weight_kg: Optional[float] = Field(default=None, ge=0.0, description="Declared or scale-synced batch weight in KG")
    grade_a_weight_kg: Optional[float] = Field(default=None, ge=0.0, description="Estimated Grade-A portion weight in KG")
    grade_urs_weight_kg: Optional[float] = Field(default=None, ge=0.0, description="Estimated Grade-URS portion weight in KG")
    rejected_weight_kg: Optional[float] = Field(default=None, ge=0.0, description="Estimated Rejected portion weight in KG")
    grade_a_weight_percentage: float = Field(..., ge=0.0, le=100.0)
    grade_urs_weight_percentage: float = Field(..., ge=0.0, le=100.0)
    rejected_weight_percentage: float = Field(..., ge=0.0, le=100.0)


class InspectionCoverage(BaseModel):
    captured_sample_images_count: int = Field(..., ge=0, description="Number of sample images analyzed")
    total_visible_onions: int = Field(..., ge=0, description="Total onion bulbs visible in sample frames")
    total_analyzed_onions: int = Field(..., ge=0, description="Total onion bulbs successfully analyzed")
    coverage_notes: str = Field(
        default="Analysis represents captured sample frame lot only. Does not infer unphotographed physical lot volume.",
        description="Explicit coverage scope boundary statement"
    )


class BatchAggregationRequest(BaseModel):
    batch_id: str = Field(..., description="Unique batch identifier")
    inspection_ids: List[str] = Field(default_factory=list, description="List of inspection IDs in this batch")
    declared_total_weight_kg: Optional[float] = Field(default=None, ge=0.1, description="Optional sample batch weight in KG")


class BatchAggregationResult(BaseModel):
    batch_id: str
    sampling_status: Literal["SAMPLE_ONLY", "PARTIAL_BATCH", "FULL_BATCH"] = Field(
        default="SAMPLE_ONLY",
        description="Sampling scope status indicator. Defaults strictly to SAMPLE_ONLY."
    )
    coverage: InspectionCoverage
    counts: LotCounts
    percentages: LotPercentages
    weight_distribution: WeightDistribution
    average_inspection_confidence: float = Field(..., ge=0.0, le=1.0)


class GradingProfile(BaseModel):
    """Configurable commercial procurement grading profile."""
    profile_id: str = Field(..., description="Unique profile identifier (e.g. prototype-procurement-v1)")
    profile_name: str = Field(..., description="Experimental human readable profile name")
    version: str = Field(..., description="Semantic version string")
    status: Literal["EXPERIMENTAL", "VALIDATED", "DEPRECATED"] = Field(
        default="EXPERIMENTAL",
        description="Development status flag"
    )
    official_status: Literal["NOT_OFFICIAL", "OFFICIAL_STANDARDIZED"] = Field(
        default="NOT_OFFICIAL",
        description="Explicit indicator that profile is non-official"
    )
    source: Literal["PROJECT_DEFINED", "OFFICIAL_AUTHORITATIVE"] = Field(
        default="PROJECT_DEFINED",
        description="Source of policy rules"
    )
    source_reference: Optional[str] = Field(
        default="Development baseline heuristic. Not validated against statutory trade standards.",
        description="Reference documentation source"
    )
    created_at: str = Field(default="2026-09-04", description="ISO creation timestamp")
    effective_at: str = Field(default="2026-09-04", description="ISO effective timestamp")
    grade_a_min_pct: float = Field(default=70.0, ge=0.0, le=100.0, description="Minimum Grade A % for Grade-A lot status")
    urs_min_combined_pct: float = Field(default=75.0, ge=0.0, le=100.0, description="Minimum (Grade A + URS %) for URS lot status")
    rot_max_tolerance_pct: float = Field(default=5.0, ge=0.0, le=100.0, description="Maximum allowable rot % before lot rejection")
    sprout_max_tolerance_pct: float = Field(default=10.0, ge=0.0, le=100.0, description="Maximum allowable sprout % before lot rejection")
    rot_review_threshold_pct: float = Field(default=3.0, ge=0.0, le=100.0, description="Rot % threshold triggering manual review")
    undersized_threshold_mm: float = Field(default=45.0, ge=0.0, description="Diameter boundary threshold in mm")
    confidence_min_threshold: float = Field(default=0.70, ge=0.0, le=1.0, description="Minimum inspection confidence before flagging REVIEW_REQUIRED")
    
    # Penalty coefficients for quality score formula
    penalty_rot_coeff: float = Field(default=2.0, ge=0.0)
    penalty_sprout_coeff: float = Field(default=1.5, ge=0.0)
    penalty_damaged_coeff: float = Field(default=0.8, ge=0.0)
    penalty_undersized_coeff: float = Field(default=0.5, ge=0.0)

    rules: Dict[str, Any] = Field(
        default_factory=lambda: {
            "rot_rejection": "RULE_ROT_TOLERANCE_EXCEEDED",
            "sprout_rejection": "RULE_SPROUT_TOLERANCE_EXCEEDED",
            "grade_a": "RULE_GRADE_A_QUALIFIED",
            "grade_urs": "RULE_GRADE_URS_QUALIFIED",
            "low_confidence": "RULE_CONFIDENCE_BELOW_THRESHOLD",
            "borderline_rot": "RULE_BORDERLINE_ROT_DETECTED",
        },
        description="Configurable rule code map"
    )
    disclaimer: str = Field(
        default="Prototype grading profile. Not an official government certification or statutory grading standard.",
        description="Mandatory non-official disclaimer"
    )


class GradingRequest(BaseModel):
    batch_id: str = Field(..., description="Batch identifier")
    profile_id: Optional[str] = Field(default="prototype-procurement-v1", description="Grading profile ID to apply")
    percentages: LotPercentages
    weight_distribution: WeightDistribution
    inspection_confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    sampling_status: Literal["SAMPLE_ONLY", "PARTIAL_BATCH", "FULL_BATCH"] = Field(
        default="SAMPLE_ONLY",
        description="Sampling status indicator"
    )


class GradingResult(BaseModel):
    """Output generated by the GradingPolicyEngine."""
    batch_id: str
    profile_id: str
    profile_version: str
    status: Literal["EXPERIMENTAL", "VALIDATED", "DEPRECATED"] = Field(default="EXPERIMENTAL")
    official_status: Literal["NOT_OFFICIAL", "OFFICIAL_STANDARDIZED"] = Field(default="NOT_OFFICIAL")
    sampling_status: Literal["SAMPLE_ONLY", "PARTIAL_BATCH", "FULL_BATCH"] = Field(default="SAMPLE_ONLY")
    grade_a_percentage: float = Field(..., ge=0.0, le=100.0)
    grade_urs_percentage: float = Field(..., ge=0.0, le=100.0)
    rejected_percentage: float = Field(..., ge=0.0, le=100.0)
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Quality Score (0-100)")
    final_prototype_grade: Literal["Grade-A", "Grade-URS", "Grade-C"] = Field(..., description="Final Prototype Grade")
    review_status: Literal["ACCEPTED", "REVIEW_REQUIRED"] = Field(..., description="Review status flag")
    review_reason: Optional[List[str]] = Field(default=None, description="Detailed list of review requirement reasons")
    explanation: str = Field(..., description="Human-readable decision explanation")
    rules_triggered: List[str] = Field(default_factory=list, description="List of rule codes triggered")
    disclaimer: str = Field(
        default="Prototype grading profile. Not an official government certification or statutory grading standard.",
        description="Mandatory disclaimer"
    )
