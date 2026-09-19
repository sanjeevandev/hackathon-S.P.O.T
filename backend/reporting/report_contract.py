"""Structured Inspection Report Contract and Model."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.contracts.schemas import CanonicalInspectionResult


class InspectionReport(BaseModel):
    """Canonical structured digital inspection report data model."""

    report_id: str = Field(..., description="Unique report identifier")
    report_version: int = Field(default=1, ge=1, description="Report revision number")
    inspection_id: str = Field(..., description="Referenced inspection identifier")
    batch_id: str = Field(..., description="Referenced procurement batch code")
    generated_at: str = Field(..., description="ISO 8601 timestamp of report generation")
    batch_metadata: Dict[str, Any] = Field(default_factory=dict)
    sampling: Dict[str, Any] = Field(default_factory=dict)
    image_quality: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    grading: Optional[Dict[str, Any]] = Field(default=None)
    explanation: Dict[str, Any] = Field(default_factory=dict)
    model_information: Dict[str, Any] = Field(default_factory=dict)
    grading_profile_information: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = Field(
        default="Prototype grading profile. Not an official government certification or statutory grading standard."
    )
    limitations: List[str] = Field(default_factory=list)

    @classmethod
    def from_canonical_result(
        cls,
        report_id: str,
        result: CanonicalInspectionResult,
        report_version: int = 1
    ) -> "InspectionReport":
        """Constructs a structured report directly from a canonical inspection result."""
        return cls(
            report_id=report_id,
            report_version=report_version,
            inspection_id=result.inspection_id,
            batch_id=result.batch_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            batch_metadata={
                "batch_id": result.batch_id,
                "inspection_status": result.status,
                "confidence": result.confidence
            },
            sampling=result.coverage.model_dump(),
            image_quality=result.image_quality,
            statistics=result.batch_statistics.model_dump(),
            grading=result.grading.model_dump() if result.grading else None,
            explanation=result.explanation.model_dump(),
            model_information=result.model.model_dump(),
            grading_profile_information=result.grading_profile.model_dump(),
            disclaimer=result.grading_profile.disclaimer,
            limitations=result.explanation.limitations
        )
