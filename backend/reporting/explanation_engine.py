"""Deterministic, rule-based Explanation Engine.

Generates transparent, mathematically consistent explanations for lot grading results.
DO NOT use LLM or non-deterministic generators.
"""

from typing import List, Optional
from backend.contracts.schemas import Explanation, BatchStatistics, GradingPresentation


class ExplanationEngine:
    """Deterministic generator for inspection grade explanations and disclaimers."""

    MANDATORY_LIMITATIONS = [
        "Assessment is derived strictly from captured sample images (sampling status: SAMPLE_ONLY).",
        "Standard RGB surface imaging cannot detect hidden internal decay, rot, or internal sprouting.",
        "Onion bulb diameter measurement requires physical spatial calibration; uncalibrated images return size as UNAVAILABLE.",
        "Prototype grading profile. Not an official government certification or statutory grading standard."
    ]

    @classmethod
    def generate(
        self,
        status: str,
        batch_stats: BatchStatistics,
        grading: Optional[GradingPresentation] = None,
        review_status: str = "NOT_REVIEWED",
        review_reasons: Optional[List[str]] = None
    ) -> Explanation:
        primary_factors: List[str] = []
        supporting_factors: List[str] = []
        review_msg: Optional[str] = None

        if status == "RETAKE_REQUIRED":
            headline = "Grade Withheld: Image Retake Required"
            primary_factors.append("Image failed quality gate screening criteria (blur, brightness, or resolution threshold).")
            primary_factors.append("Visual evidence insufficient for reliable bulb classification.")
            review_msg = "Please retake the image under adequate lighting and steady focus."

        elif status == "MODEL_UNAVAILABLE":
            headline = "Grade Withheld: Vision Model Unavailable"
            primary_factors.append("Production vision model checkpoint is currently offline or unreachable.")
            primary_factors.append("Mock fallback is disabled in production environment.")
            review_msg = "System administrators must restore vision model service."

        elif status == "FAILED":
            headline = "Grade Withheld: Inspection Execution Failed"
            primary_factors.append("An unrecoverable system exception occurred during inspection pipeline execution.")

        elif review_status == "REVIEW_REQUIRED":
            headline = f"Provisional {grading.prototype_grade if grading else 'Grade-C'}: Human Review Required"
            if grading:
                primary_factors.append(f"Grade-A proportion: {grading.grade_a_percent:.1f}%")
                primary_factors.append(f"Under-Sized & Defect proportion: {grading.urs_percent:.1f}%")
            if review_reasons:
                for r in review_reasons:
                    primary_factors.append(f"Review Trigger: {r}")
            review_msg = "Discrepancy or low confidence detected. APMC Inspector manual sign-off required prior to settlement."
            supporting_factors.append(f"Analyzed {batch_stats.total_analyzed_onions} bulbs across sample images.")

        else:
            grade_str = grading.prototype_grade if grading and grading.prototype_grade else "Grade-C"
            headline = f"Prototype {grade_str} — Inspection Complete"
            if grading:
                primary_factors.append(f"Visible Grade-A percentage: {grading.grade_a_percent:.1f}%")
                primary_factors.append(f"Under-Sized / Defect percentage: {grading.urs_percent:.1f}%")
                supporting_factors.append(f"Commercial Quality Score: {grading.quality_score:.1f}/100")
            supporting_factors.append(f"Healthy bulbs: {batch_stats.healthy_count}/{batch_stats.total_analyzed_onions}")
            if batch_stats.damaged_count > 0:
                supporting_factors.append(f"Damaged bulbs: {batch_stats.damaged_count}")
            if batch_stats.rotten_count > 0:
                supporting_factors.append(f"Rotten bulbs: {batch_stats.rotten_count}")
            if batch_stats.sprouted_count > 0:
                supporting_factors.append(f"Sprouted bulbs: {batch_stats.sprouted_count}")

        return Explanation(
            headline=headline,
            primary_factors=primary_factors,
            supporting_factors=supporting_factors,
            review_message=review_msg,
            limitations=self.MANDATORY_LIMITATIONS
        )
