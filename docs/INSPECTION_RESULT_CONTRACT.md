# CANONICAL INSPECTION RESULT CONTRACT — S.P.O.T.

**Date**: September 4, 2026  
**Status**: IMPLEMENTED (Phase 5 Canonical Presentation Contract)  

---

## 1. Executive Summary

This document specifies the single canonical data contract (`CanonicalInspectionResult`) produced by the S.P.O.T. backend for consumption by mobile and web client interfaces. Frontend clients MUST consume this backend contract directly and MUST NOT duplicate grading calculations, lot statistics aggregation, or defect scoring locally.

---

## 2. Schema Specification

```json
{
  "inspection_id": "INSP-REQ-98F12A04",
  "batch_id": "BATCH-2026-NASHIK-01",
  "status": "COMPLETE",
  "sampling_status": "SAMPLE_ONLY",
  "image_quality": {
    "quality_status": "PASS",
    "metrics": {
      "blur_score": 245.5,
      "brightness": 128.0,
      "contrast": 64.2,
      "width": 1920,
      "height": 1080
    }
  },
  "coverage": {
    "captured_sample_images_count": 1,
    "total_visible_onions": 3,
    "total_analyzed_onions": 3,
    "sampling_status": "SAMPLE_ONLY",
    "coverage_notes": "Inspection metrics are derived solely from captured sample images."
  },
  "onions": [
    {
      "onion_id": "O1",
      "bounding_box": [120, 200, 340, 420],
      "mask_reference": null,
      "detection_confidence": 0.94,
      "defect_probabilities": {
        "damage": 0.05,
        "rot": 0.02,
        "sprouting": 0.0
      },
      "size_estimate": {
        "estimated_diameter_mm": null,
        "status": "UNAVAILABLE",
        "confidence": 0.0
      },
      "evidence_regions": [],
      "final_status": "HEALTHY"
    }
  ],
  "batch_statistics": {
    "total_visible_onions": 3,
    "total_analyzed_onions": 3,
    "healthy_count": 3,
    "damaged_count": 0,
    "rotten_count": 0,
    "sprouted_count": 0,
    "undersized_count": 0,
    "healthy_percentage": 100.0,
    "damaged_percentage": 0.0,
    "rotten_percentage": 0.0,
    "sprouted_percentage": 0.0,
    "undersized_percentage": 0.0
  },
  "grading": {
    "quality_score": 100.0,
    "prototype_grade": "Grade-A",
    "grade_a_percent": 100.0,
    "urs_percent": 0.0,
    "review_status": "ACCEPTED",
    "review_reason": [],
    "inspection_confidence": 0.94,
    "grading_profile_id": "prototype-procurement-v1",
    "grading_profile_version": "1.1.0-dev"
  },
  "explanation": {
    "headline": "Prototype Grade-A — Inspection Complete",
    "primary_factors": [
      "Visible Grade-A percentage: 100.0%",
      "Under-Sized / Defect percentage: 0.0%"
    ],
    "supporting_factors": [
      "Commercial Quality Score: 100.0/100",
      "Healthy bulbs: 3/3"
    ],
    "review_message": null,
    "limitations": [
      "Assessment is derived strictly from captured sample images (sampling status: SAMPLE_ONLY).",
      "Standard RGB surface imaging cannot detect hidden internal decay, rot, or internal sprouting.",
      "Onion bulb diameter measurement requires physical spatial calibration; uncalibrated images return size as UNAVAILABLE.",
      "Prototype grading profile. Not an official government certification or statutory grading standard."
    ]
  },
  "confidence": 0.94,
  "review": {
    "review_status": "ACCEPTED",
    "review_reason": ""
  },
  "model": {
    "model_id": "DevelopmentMockVisionModel",
    "model_name": "Dev Mock Pipeline",
    "model_version": "0.1.0-mock",
    "source": "development_mock"
  },
  "grading_profile": {
    "profile_id": "prototype-procurement-v1",
    "profile_name": "Experimental Procurement Profile",
    "version": "1.1.0-dev",
    "status": "EXPERIMENTAL",
    "official_status": "NOT_OFFICIAL",
    "disclaimer": "Prototype grading profile. Not an official government certification or statutory grading standard."
  },
  "report_reference": "/reports/RPT-A8B9C0D1.json"
}
```

---

## 3. Status Rules for Presentation

1. **`RETAKE_REQUIRED`**:
   - `grading` field object suppresses `quality_score` and `prototype_grade` (set to `null`).
   - `explanation.headline` displays `"Grade Withheld: Image Retake Required"`.
2. **`MODEL_UNAVAILABLE`**:
   - `grading` field suppresses grade.
   - `explanation.headline` displays `"Grade Withheld: Vision Model Unavailable"`.
3. **`REVIEW_REQUIRED`**:
   - `grading.prototype_grade` displays provisional grade.
   - `explanation.headline` displays `"Provisional Grade-A: Human Review Required"`.
   - `explanation.review_message` contains human reviewer instructions.
