"""Grading Policy Engine for S.P.O.T.

Decoupled commercial procurement policy evaluator.
Applies versioned GradingProfile rules to batch lot percentages and quality scores.

No magic numbers: All penalty coefficients and thresholds are dynamically resolved from GradingProfile.
"""

from typing import List, Optional
from backend.grading.schemas import GradingRequest, GradingResult, LotPercentages
from backend.grading.profiles import get_grading_profile, GradingProfile


class GradingPolicyEngine:
    """Evaluates lot inspection metrics against policy rules to produce prototype lot grades."""

    @staticmethod
    def evaluate(request: GradingRequest) -> GradingResult:
        """Evaluates a GradingRequest against the requested or default GradingProfile.

        Args:
            request: GradingRequest containing batch percentages, weight distribution, and confidence.

        Returns:
            GradingResult containing calculated Quality Score, prototype grade, review status, and explanation.
        """
        profile: GradingProfile = get_grading_profile(request.profile_id or "prototype-procurement-v1")
        pct: LotPercentages = request.percentages

        # 1. Quality Score Calculation (Penalty coefficients resolved entirely from GradingProfile)
        penalty = (
            (profile.penalty_rot_coeff * pct.rotten_pct) +
            (profile.penalty_sprout_coeff * pct.sprouted_pct) +
            (profile.penalty_damaged_coeff * pct.damaged_pct) +
            (profile.penalty_undersized_coeff * pct.undersized_pct)
        )
        quality_score = round(max(0.0, min(100.0, 100.0 - penalty)), 1)

        rules_triggered: List[str] = []
        explanations: List[str] = []
        final_grade: str = "Grade-C"

        # 2. Rule Evaluation (Thresholds resolved entirely from GradingProfile)
        rot_exceeded = pct.rotten_pct > profile.rot_max_tolerance_pct
        sprout_exceeded = pct.sprouted_pct > profile.sprout_max_tolerance_pct

        if rot_exceeded:
            rule_code = profile.rules.get("rot_rejection", "RULE_ROT_TOLERANCE_EXCEEDED")
            rules_triggered.append(rule_code)
            explanations.append(
                f"Rot percentage ({pct.rotten_pct}%) exceeds profile tolerance ({profile.rot_max_tolerance_pct}%)."
            )

        if sprout_exceeded:
            rule_code = profile.rules.get("sprout_rejection", "RULE_SPROUT_TOLERANCE_EXCEEDED")
            rules_triggered.append(rule_code)
            explanations.append(
                f"Sprout percentage ({pct.sprouted_pct}%) exceeds profile tolerance ({profile.sprout_max_tolerance_pct}%)."
            )

        if not (rot_exceeded or sprout_exceeded):
            if pct.healthy_pct >= profile.grade_a_min_pct:
                final_grade = "Grade-A"
                rule_code = profile.rules.get("grade_a", "RULE_GRADE_A_QUALIFIED")
                rules_triggered.append(rule_code)
                explanations.append(
                    f"Healthy onion percentage ({pct.healthy_pct}%) satisfies Grade-A profile requirement ({profile.grade_a_min_pct}%)."
                )
            else:
                combined_usable = pct.healthy_pct + pct.damaged_pct + pct.undersized_pct
                if combined_usable >= profile.urs_min_combined_pct:
                    final_grade = "Grade-URS"
                    rule_code = profile.rules.get("grade_urs", "RULE_GRADE_URS_QUALIFIED")
                    rules_triggered.append(rule_code)
                    explanations.append(
                        f"Usable onion percentage ({combined_usable:.1f}%) qualifies under URS buffer scheme requirement ({profile.urs_min_combined_pct}%)."
                    )
                else:
                    final_grade = "Grade-C"
                    rule_code = profile.rules.get("defect_excessive", "RULE_DEFECT_EXCESSIVE")
                    rules_triggered.append(rule_code)
                    explanations.append(
                        f"Defect levels are too high ({100.0 - combined_usable:.1f}% unusable). Lot rejected."
                    )

        # 3. Review Status Evaluation (Thresholds resolved entirely from GradingProfile)
        review_status = "ACCEPTED"
        review_reasons: List[str] = []

        if request.inspection_confidence < profile.confidence_min_threshold:
            review_status = "REVIEW_REQUIRED"
            rule_code = profile.rules.get("low_confidence", "RULE_CONFIDENCE_BELOW_THRESHOLD")
            rules_triggered.append(rule_code)
            reason = f"Inspection confidence ({request.inspection_confidence}) is below profile minimum threshold ({profile.confidence_min_threshold})."
            review_reasons.append(reason)
            explanations.append(reason)

        if pct.rotten_pct > profile.rot_review_threshold_pct:
            review_status = "REVIEW_REQUIRED"
            rule_code = profile.rules.get("borderline_rot", "RULE_BORDERLINE_ROT_DETECTED")
            rules_triggered.append(rule_code)
            reason = f"Rot percentage ({pct.rotten_pct}%) exceeds review threshold ({profile.rot_review_threshold_pct}%)."
            review_reasons.append(reason)
            explanations.append(reason)

        explanation_str = " ".join(explanations)

        return GradingResult(
            batch_id=request.batch_id,
            profile_id=profile.profile_id,
            profile_version=profile.version,
            status=profile.status,
            official_status=profile.official_status,
            sampling_status=request.sampling_status,
            grade_a_percentage=request.weight_distribution.grade_a_weight_percentage,
            grade_urs_percentage=request.weight_distribution.grade_urs_weight_percentage,
            rejected_percentage=request.weight_distribution.rejected_weight_percentage,
            quality_score=quality_score,
            final_prototype_grade=final_grade,
            review_status=review_status,
            review_reason=review_reasons if review_reasons else None,
            explanation=explanation_str,
            rules_triggered=rules_triggered,
            disclaimer=profile.disclaimer
        )
