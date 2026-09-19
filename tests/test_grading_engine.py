"""Unit tests for GradingPolicyEngine rule evaluation, profile non-official claims, and dynamic thresholding."""

import pytest
from backend.grading.schemas import GradingRequest, LotPercentages, WeightDistribution, GradingProfile
from backend.grading.grading_engine import GradingPolicyEngine
from backend.grading.profiles import get_grading_profile, list_grading_profiles, register_grading_profile


def test_prototype_profile_is_clearly_marked_non_official():
    """Verify default grading profile is explicitly marked EXPERIMENTAL and NOT_OFFICIAL."""
    profile = get_grading_profile("prototype-procurement-v1")
    assert profile.status == "EXPERIMENTAL"
    assert profile.official_status == "NOT_OFFICIAL"
    assert profile.source == "PROJECT_DEFINED"
    assert "Not an official government certification" in profile.disclaimer


def test_government_and_nafed_claims_are_not_generated():
    """Verify registered profile names, disclaimers, and explanations omit official government/NAFED/AGMARK claims."""
    profiles = list_grading_profiles()
    for prof in profiles:
        assert "NAFED" not in prof.profile_name
        assert "AGMARK" not in prof.profile_name
        assert "APEDA" not in prof.profile_name
        assert prof.official_status == "NOT_OFFICIAL"


def test_thresholds_come_only_from_profile_configuration():
    """Verify that changing threshold values in a GradingProfile dynamically alters engine decision output."""
    pct = LotPercentages(healthy_pct=80.0, damaged_pct=5.0, rotten_pct=4.0, sprouted_pct=2.0, undersized_pct=9.0)
    w_dist = WeightDistribution(
        is_weight_estimated=False, weight_source="UNAVAILABLE",
        grade_a_weight_percentage=80.0, grade_urs_weight_percentage=14.0, rejected_weight_percentage=6.0
    )

    # Standard default profile has rot_max_tolerance_pct = 5.0 -> rot=4.0% PASSES
    req_default = GradingRequest(batch_id="B-DYN-1", profile_id="prototype-procurement-v1", percentages=pct, weight_distribution=w_dist)
    res_default = GradingPolicyEngine.evaluate(req_default)
    assert res_default.final_prototype_grade == "Grade-A"

    # Custom strict profile with rot_max_tolerance_pct = 3.0 -> rot=4.0% REJECTS
    strict_profile = GradingProfile(
        profile_id="custom-strict-test",
        profile_name="Custom Strict Test Profile",
        version="1.0.0",
        rot_max_tolerance_pct=3.0
    )
    register_grading_profile(strict_profile)

    req_strict = GradingRequest(batch_id="B-DYN-2", profile_id="custom-strict-test", percentages=pct, weight_distribution=w_dist)
    res_strict = GradingPolicyEngine.evaluate(req_strict)
    assert res_strict.final_prototype_grade == "Grade-C"
    assert "RULE_ROT_TOLERANCE_EXCEEDED" in res_strict.rules_triggered


def test_grade_a_qualification():
    """Verify high healthy percentage qualifies for Grade-A lot status."""
    pct = LotPercentages(healthy_pct=92.0, damaged_pct=3.0, rotten_pct=1.0, sprouted_pct=2.0, undersized_pct=2.0)
    w_dist = WeightDistribution(
        is_weight_estimated=True, weight_source="PROPORTIONAL_SAMPLE_ESTIMATE",
        total_batch_weight_kg=100.0, grade_a_weight_kg=92.0, grade_urs_weight_kg=5.0, rejected_weight_kg=3.0,
        grade_a_weight_percentage=92.0, grade_urs_weight_percentage=5.0, rejected_weight_percentage=3.0
    )
    req = GradingRequest(batch_id="BATCH-A", profile_id="prototype-procurement-v1", percentages=pct, weight_distribution=w_dist, inspection_confidence=0.92)

    res = GradingPolicyEngine.evaluate(req)

    assert res.final_prototype_grade == "Grade-A"
    assert res.review_status == "ACCEPTED"
    assert res.review_reason is None
    assert "RULE_GRADE_A_QUALIFIED" in res.rules_triggered
    assert res.quality_score > 90.0


def test_low_confidence_triggers_review_required_with_reason():
    """Verify low inspection confidence populates review_reason and triggers REVIEW_REQUIRED."""
    pct = LotPercentages(healthy_pct=85.0, damaged_pct=10.0, rotten_pct=1.0, sprouted_pct=2.0, undersized_pct=2.0)
    w_dist = WeightDistribution(
        is_weight_estimated=False, weight_source="UNAVAILABLE",
        grade_a_weight_percentage=85.0, grade_urs_weight_percentage=12.0, rejected_weight_percentage=3.0
    )
    req = GradingRequest(batch_id="BATCH-CONF", profile_id="prototype-procurement-v1", percentages=pct, weight_distribution=w_dist, inspection_confidence=0.60)

    res = GradingPolicyEngine.evaluate(req)

    assert res.review_status == "REVIEW_REQUIRED"
    assert res.review_reason is not None
    assert any("below profile minimum threshold" in r for r in res.review_reason)
