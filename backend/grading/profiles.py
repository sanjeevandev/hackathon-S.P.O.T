"""Grading Profiles Registry & Configuration Loader.

Manages commercial grading policies separately from AI vision perception code.
All default profiles are explicitly marked EXPERIMENTAL and NOT_OFFICIAL.
"""

from typing import Dict, List, Optional
from backend.grading.schemas import GradingProfile

# Experimental Default Procurement Profile
DEFAULT_PROFILE = GradingProfile(
    profile_id="prototype-procurement-v1",
    profile_name="Experimental Prototype Procurement Profile",
    version="1.1.0-dev",
    status="EXPERIMENTAL",
    official_status="NOT_OFFICIAL",
    source="PROJECT_DEFINED",
    source_reference="Development baseline heuristic. Not validated against statutory trade standards.",
    created_at="2026-09-04",
    effective_at="2026-09-04",
    grade_a_min_pct=70.0,
    urs_min_combined_pct=75.0,
    rot_max_tolerance_pct=5.0,
    sprout_max_tolerance_pct=10.0,
    rot_review_threshold_pct=3.0,
    undersized_threshold_mm=45.0,
    confidence_min_threshold=0.70,
    penalty_rot_coeff=2.0,
    penalty_sprout_coeff=1.5,
    penalty_damaged_coeff=0.8,
    penalty_undersized_coeff=0.5,
    disclaimer="Prototype grading profile. Not an official government certification or statutory grading standard."
)

# Experimental Strict Export Baseline Profile
STRICT_EXPORT_PROFILE = GradingProfile(
    profile_id="prototype-export-strict-v1",
    profile_name="Experimental Prototype Export Baseline Profile",
    version="1.0.0-dev",
    status="EXPERIMENTAL",
    official_status="NOT_OFFICIAL",
    source="PROJECT_DEFINED",
    source_reference="Experimental baseline heuristic for high-quality lot screening. Not validated.",
    created_at="2026-09-04",
    effective_at="2026-09-04",
    grade_a_min_pct=90.0,
    urs_min_combined_pct=95.0,
    rot_max_tolerance_pct=1.0,
    sprout_max_tolerance_pct=2.0,
    rot_review_threshold_pct=0.5,
    undersized_threshold_mm=50.0,
    confidence_min_threshold=0.85,
    penalty_rot_coeff=3.0,
    penalty_sprout_coeff=2.0,
    penalty_damaged_coeff=1.0,
    penalty_undersized_coeff=0.8,
    disclaimer="Prototype grading profile. Not an official government certification or statutory grading standard."
)

_PROFILES_REGISTRY: Dict[str, GradingProfile] = {
    DEFAULT_PROFILE.profile_id: DEFAULT_PROFILE,
    STRICT_EXPORT_PROFILE.profile_id: STRICT_EXPORT_PROFILE,
}


def register_grading_profile(profile: GradingProfile) -> None:
    """Register a new or updated GradingProfile."""
    _PROFILES_REGISTRY[profile.profile_id] = profile


def get_grading_profile(profile_id: str = "prototype-procurement-v1") -> GradingProfile:
    """Retrieve a GradingProfile by ID. Fallback to DEFAULT_PROFILE if not found."""
    return _PROFILES_REGISTRY.get(profile_id, DEFAULT_PROFILE)


def list_grading_profiles() -> List[GradingProfile]:
    """List all registered GradingProfiles."""
    return list(_PROFILES_REGISTRY.values())
