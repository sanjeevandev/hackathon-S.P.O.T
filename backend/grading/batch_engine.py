"""Batch Intelligence Engine for aggregating multi-image lot detections.

Calculates statistical lot counts, percentage distributions, weight estimates, and average confidence
across single or multiple inspection runs for a procurement batch.

Scope Boundaries:
Analysis represents captured sample frame lot only (sampling_status='SAMPLE_ONLY').
Does NOT infer unphotographed physical lot volume.
"""

from typing import List, Optional
from backend.ai.schemas import VisionResult, OnionDetection
from backend.grading.schemas import (
    LotCounts,
    LotPercentages,
    WeightDistribution,
    InspectionCoverage,
    BatchAggregationResult,
    BatchAggregationRequest,
)


class BatchIntelligenceEngine:
    """Aggregates multi-image vision inspection results into batch lot statistics."""

    @staticmethod
    def aggregate_batch(
        batch_id: str,
        vision_results: List[VisionResult],
        declared_total_weight_kg: Optional[float] = None
    ) -> BatchAggregationResult:
        """Aggregates vision results across multiple image captures for a batch.

        Args:
            batch_id: Unique batch identifier.
            vision_results: List of VisionResult objects for this batch.
            declared_total_weight_kg: Optional sample batch weight in KG.

        Returns:
            BatchAggregationResult containing aggregated counts, percentages, weight distribution, and coverage.
        """
        all_onions: List[OnionDetection] = []
        confidences: List[float] = []

        for vr in vision_results:
            if vr.status == "SUCCESS":
                all_onions.extend(vr.onions)
                confidences.append(vr.overall_confidence)

        total_onions = len(all_onions)
        avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

        coverage = InspectionCoverage(
            captured_sample_images_count=len(vision_results),
            total_visible_onions=total_onions,
            total_analyzed_onions=total_onions,
            coverage_notes="Analysis represents captured sample frame lot only. Does not infer unphotographed physical lot volume."
        )

        if total_onions == 0:
            counts = LotCounts(
                total_onions=0, healthy_count=0, damaged_count=0,
                rotten_count=0, sprouted_count=0, undersized_count=0
            )
            percentages = LotPercentages(
                healthy_pct=0.0, damaged_pct=0.0, rotten_pct=0.0,
                sprouted_pct=0.0, undersized_pct=0.0
            )
            weight_dist = WeightDistribution(
                is_weight_estimated=False,
                weight_source="UNAVAILABLE",
                total_batch_weight_kg=declared_total_weight_kg,
                grade_a_weight_kg=None, grade_urs_weight_kg=None, rejected_weight_kg=None,
                grade_a_weight_percentage=0.0, grade_urs_weight_percentage=0.0, rejected_weight_percentage=0.0
            )
            return BatchAggregationResult(
                batch_id=batch_id,
                sampling_status="SAMPLE_ONLY",
                coverage=coverage,
                counts=counts,
                percentages=percentages,
                weight_distribution=weight_dist,
                average_inspection_confidence=avg_confidence
            )

        healthy_count = 0
        damaged_count = 0
        rotten_count = 0
        sprouted_count = 0
        undersized_count = 0

        for onion in all_onions:
            dp = onion.defect_probabilities
            is_damaged = dp.damage >= 0.50
            is_rotten = dp.rot >= 0.50
            is_sprouted = dp.sprouting >= 0.50
            
            is_undersized = False
            if onion.size_estimate and onion.size_estimate.status == "AVAILABLE" and onion.size_estimate.estimated_diameter_mm:
                if onion.size_estimate.estimated_diameter_mm < 45.0:
                    is_undersized = True

            if is_damaged:
                damaged_count += 1
            if is_rotten:
                rotten_count += 1
            if is_sprouted:
                sprouted_count += 1
            if is_undersized:
                undersized_count += 1

            if not (is_damaged or is_rotten or is_sprouted or is_undersized):
                healthy_count += 1

        counts = LotCounts(
            total_onions=total_onions,
            healthy_count=healthy_count,
            damaged_count=damaged_count,
            rotten_count=rotten_count,
            sprouted_count=sprouted_count,
            undersized_count=undersized_count
        )

        healthy_pct = round((healthy_count / total_onions) * 100.0, 2)
        damaged_pct = round((damaged_count / total_onions) * 100.0, 2)
        rotten_pct = round((rotten_count / total_onions) * 100.0, 2)
        sprouted_pct = round((sprouted_count / total_onions) * 100.0, 2)
        undersized_pct = round((undersized_count / total_onions) * 100.0, 2)

        percentages = LotPercentages(
            healthy_pct=healthy_pct,
            damaged_pct=damaged_pct,
            rotten_pct=rotten_pct,
            sprouted_pct=sprouted_pct,
            undersized_pct=undersized_pct
        )

        # Weight calculation: Do NOT fabricate weights. Mark clearly as estimated or unavailable.
        if declared_total_weight_kg and declared_total_weight_kg > 0:
            grade_a_kg = round(declared_total_weight_kg * (healthy_pct / 100.0), 2)
            urs_pct = min(100.0 - healthy_pct, damaged_pct + undersized_pct)
            grade_urs_kg = round(declared_total_weight_kg * (urs_pct / 100.0), 2)
            rejected_kg = round(max(0.0, declared_total_weight_kg - (grade_a_kg + grade_urs_kg)), 2)

            grade_a_w_pct = round((grade_a_kg / declared_total_weight_kg) * 100.0, 1)
            grade_urs_w_pct = round((grade_urs_kg / declared_total_weight_kg) * 100.0, 1)
            rejected_w_pct = round(100.0 - (grade_a_w_pct + grade_urs_w_pct), 1)

            weight_dist = WeightDistribution(
                is_weight_estimated=True,
                weight_source="PROPORTIONAL_SAMPLE_ESTIMATE",
                total_batch_weight_kg=declared_total_weight_kg,
                grade_a_weight_kg=grade_a_kg,
                grade_urs_weight_kg=grade_urs_kg,
                rejected_weight_kg=rejected_kg,
                grade_a_weight_percentage=grade_a_w_pct,
                grade_urs_weight_percentage=grade_urs_w_pct,
                rejected_weight_percentage=rejected_w_pct
            )
        else:
            urs_pct = min(100.0 - healthy_pct, damaged_pct + undersized_pct)
            rejected_pct = round(max(0.0, 100.0 - (healthy_pct + urs_pct)), 1)
            weight_dist = WeightDistribution(
                is_weight_estimated=False,
                weight_source="UNAVAILABLE",
                total_batch_weight_kg=None,
                grade_a_weight_kg=None,
                grade_urs_weight_kg=None,
                rejected_weight_kg=None,
                grade_a_weight_percentage=healthy_pct,
                grade_urs_weight_percentage=urs_pct,
                rejected_weight_percentage=rejected_pct
            )

        return BatchAggregationResult(
            batch_id=batch_id,
            sampling_status="SAMPLE_ONLY",
            coverage=coverage,
            counts=counts,
            percentages=percentages,
            weight_distribution=weight_dist,
            average_inspection_confidence=avg_confidence
        )
