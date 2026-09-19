# BATCH INTELLIGENCE & GRADING POLICY FOUNDATION — S.P.O.T.

**Date**: September 4, 2026  
**Status**: CORRECTIONS APPLIED & TESTED (Phase 2 Correction)  
**Problem Statement**: SIH 2026 PS 26031 — AI-Based Mobile Application for Onion Quality Assessment & Grading  

---

## 1. Overview & Non-Official Disclaimers

The Batch Intelligence and Grading Policy system provides a **data-independent commercial decision foundation**. All default grading profiles are explicitly marked `status = "EXPERIMENTAL"` and `official_status = "NOT_OFFICIAL"`. No government, NAFED, AGMARK, or APEDA certification claims are made.

> **Mandatory Disclaimer**:  
> *"Prototype grading profile. Not an official government certification or statutory grading standard."*

---

## 2. Experimental Grading Profiles (`backend/grading/profiles.py`)

1. **`prototype-procurement-v1`** (*Experimental Prototype Procurement Profile*):
   - `grade_a_min_pct`: 70.0%
   - `urs_min_combined_pct`: 75.0%
   - `rot_max_tolerance_pct`: 5.0%
   - `sprout_max_tolerance_pct`: 10.0%
   - `rot_review_threshold_pct`: 3.0%
   - `confidence_min_threshold`: 0.70
2. **`prototype-export-strict-v1`** (*Experimental Prototype Export Baseline Profile*):
   - `grade_a_min_pct`: 90.0%
   - `urs_min_combined_pct`: 95.0%
   - `rot_max_tolerance_pct`: 1.0%
   - `sprout_max_tolerance_pct`: 2.0%

---

## 3. Dynamic Thresholding & No Magic Numbers

The `GradingPolicyEngine` does not contain scattered magic numbers. Every threshold, tolerance, penalty weight coefficient, and rule code is resolved dynamically from the active `GradingProfile`:

- **Penalty coefficients**: `penalty_rot_coeff` (default 2.0), `penalty_sprout_coeff` (default 1.5), `penalty_damaged_coeff` (default 0.8), `penalty_undersized_coeff` (default 0.5).
- **Rule codes**: `profile.rules["rot_rejection"]`, `profile.rules["grade_a"]`, etc.

---

## 4. Inspection Coverage & Non-Fabricated Weight Allocation

- **`sampling_status`**: Defaults strictly to `"SAMPLE_ONLY"`.
- **`coverage` (`InspectionCoverage`)**:
  - `captured_sample_images_count`: Number of sample frames analyzed.
  - `total_visible_onions`: Total bulbs visible in analyzed frames.
  - `total_analyzed_onions`: Total bulbs successfully processed.
  - `coverage_notes`: *"Analysis represents captured sample frame lot only. Does not infer unphotographed physical lot volume."*
- **Non-Fabricated Weight Allocation**:
  - If no scale weight is provided (`declared_total_weight_kg = None`): Weight fields return `None` with `weight_source = "UNAVAILABLE"` and `is_weight_estimated = False`.
  - If scale weight is provided: Weight is calculated as a sample proportion and explicitly labeled `weight_source = "PROPORTIONAL_SAMPLE_ESTIMATE"` and `is_weight_estimated = True`.

---

## 5. Review Reasons

When `review_status == "REVIEW_REQUIRED"`, `review_reason` provides an explicit list of triggered human inspector review conditions (e.g. low inspection confidence or borderline rot detection).

---

## 6. Test Verification & Execution Metrics

Executed test suite via `python3 -m pytest -v tests/`:

- **Total Tests Executed**: 24
- **Total Tests Passed**: 24 (100%)
- **Total Tests Failed**: 0
- **Execution Duration**: 0.82 seconds
