# API CONTRACT — S.P.O.T. (Smart Procurement Onion Transparency)

**Date**: September 4, 2026  
**Version**: 2.0.0 (Modular Pipeline REST Contract)  

---

## 1. Overview & Protocol Guidelines

- **Base URL**: `/api/v1`
- **Content Type**: `application/json` (Multipart for image uploads)
- **Error Handling**: Standard HTTP status codes (`400`, `422`, `404`, `500`) with structured error details:
  ```json
  {
    "error_code": "IMAGE_QUALITY_FAILED",
    "message": "Image failed quality gate evaluation",
    "details": {
      "rejection_reasons": ["IMAGE_TOO_BLURRY"],
      "blur_score": 42.1
    }
  }
  ```

---

## 2. API Endpoints Specification

### 2.1. Image Quality Gate
Evaluates raw image for blur, lighting, framing, and minimum onion visibility.

- **Endpoint**: `POST /api/v1/quality-check`
- **Content-Type**: `multipart/form-data`
- **Request Parameters**:
  - `file`: `UploadFile` (Required image file)
  - `min_onion_count`: `int` (Query, optional, default: `1`)
- **Response (`200 OK`)**:
  ```json
  {
    "status": "PASS",
    "is_usable": true,
    "rejection_reasons": [],
    "metrics": {
      "blur_score": 184.5,
      "brightness": 128.2,
      "contrast": 64.0,
      "detected_rough_count": 18
    },
    "recommendation": "Image quality is optimal for AI inspection."
  }
  ```
- **Response (`422 Unprocessable Entity - RETAKE_REQUIRED`)**:
  ```json
  {
    "status": "RETAKE_REQUIRED",
    "is_usable": false,
    "rejection_reasons": ["IMAGE_TOO_BLURRY", "EXCESSIVE_DARKNESS"],
    "metrics": {
      "blur_score": 38.2,
      "brightness": 41.0,
      "contrast": 18.5,
      "detected_rough_count": 2
    },
    "recommendation": "Retake photo under brighter illumination with steady camera focus."
  }
  ```

---

### 2.2. AI Vision Inspection Endpoint
Performs modular object detection, multi-label defect scoring, and size estimation.

- **Endpoint**: `POST /api/v1/inspect`
- **Content-Type**: `multipart/form-data`
- **Request Parameters**:
  - `file`: `UploadFile` (Required)
  - `batch_id`: `str` (Form, optional)
  - `center_id`: `str` (Form, default: `"APMC-NASHIK-CENTER-01"`)
  - `model_version`: `str` (Form, default: `"development-mock-v1"`)
- **Response (`200 OK`)**:
  ```json
  {
    "inspection_id": "INSP-2026-9901A",
    "batch_id": "BATCH-MH-2026-8812",
    "center_id": "APMC-NASHIK-CENTER-01",
    "timestamp": "2026-09-04T12:19:23Z",
    "model_version": "DevelopmentMockVisionModel-v1.0",
    "total_onions_detected": 15,
    "coverage_percentage": 82.5,
    "onions": [
      {
        "onion_id": "ONION-01",
        "bbox": [120, 80, 240, 200],
        "detection_confidence": 0.94,
        "defect_probabilities": {
          "damage": 0.05,
          "rot": 0.02,
          "sprout": 0.01,
          "undersized": 0.00
        },
        "size_estimate_mm": null,
        "size_status": "SIZE_ESTIMATE_UNAVAILABLE",
        "primary_defect": "HEALTHY"
      }
    ],
    "model_confidence": 0.932,
    "inspection_confidence": 0.895,
    "review_status": "ACCEPTED"
  }
  ```

---

### 2.3. Batch Aggregation
Aggregates detections across single or multiple inspection images for a batch lot.

- **Endpoint**: `POST /api/v1/batches/{batch_id}/aggregate`
- **Request Body**:
  ```json
  {
    "inspection_ids": ["INSP-2026-9901A", "INSP-2026-9901B"],
    "declared_total_weight_kg": 100.0
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "batch_id": "BATCH-MH-2026-8812",
    "total_images_processed": 2,
    "total_onions_detected": 32,
    "counts": {
      "healthy": 22,
      "damaged": 4,
      "rotten": 2,
      "sprouted": 1,
      "undersized": 3
    },
    "percentages": {
      "healthy_pct": 68.75,
      "damaged_pct": 12.5,
      "rotten_pct": 6.25,
      "sprouted_pct": 3.125,
      "undersized_pct": 9.375
    },
    "estimated_weight_distribution": {
      "total_weight_kg": 100.0,
      "healthy_weight_kg": 68.75,
      "urs_weight_kg": 21.88,
      "rejected_weight_kg": 9.37
    }
  }
  ```

---

### 2.4. Grading Policy Engine Endpoint
Evaluates aggregated batch metrics against a specific versioned `GradingProfile`.

- **Endpoint**: `POST /api/v1/grade`
- **Request Body**:
  ```json
  {
    "batch_id": "BATCH-MH-2026-8812",
    "profile_id": "sih-2026-urs-v1",
    "healthy_pct": 68.75,
    "damaged_pct": 12.5,
    "rotten_pct": 6.25,
    "sprouted_pct": 3.125,
    "undersized_pct": 9.375,
    "inspection_confidence": 0.895
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "batch_id": "BATCH-MH-2026-8812",
    "profile_id": "sih-2026-urs-v1",
    "profile_version": "1.1.0",
    "grade_a_percentage": 68.75,
    "grade_urs_percentage": 21.88,
    "rejected_percentage": 9.37,
    "quality_score": 76.5,
    "final_prototype_grade": "Grade-URS",
    "review_status": "ACCEPTED",
    "explanation": "Grade A percentage (68.75%) is below the 70.0% threshold. Lot satisfies Under Relaxed Specifications (URS) criteria.",
    "rules_triggered": [
      "RULE_GRADE_A_UNDER_THRESHOLD",
      "RULE_URS_QUALIFIED"
    ]
  }
  ```

---

### 2.5. Digital Report Generation Endpoint
Retrieves the digital inspection report for persistent batch results.

- **Endpoint**: `GET /api/v1/reports/{inspection_id}`
- **Query Parameters**: `format` (`json` | `pdf`)
- **Response (`200 OK`)**:
  ```json
  {
    "report_title": "S.P.O.T. QUALITY INSPECTION REPORT",
    "inspection_id": "INSP-2026-9901A",
    "batch_id": "BATCH-MH-2026-8812",
    "timestamp": "2026-09-04T12:19:23Z",
    "supplier": {
      "supplier_id": "F-8812",
      "name": "Ramesh Patil",
      "location": "Nashik APMC"
    },
    "metrics": {
      "total_onions": 32,
      "grade_a_pct": 68.75,
      "urs_pct": 21.88,
      "rejected_pct": 9.37,
      "quality_score": 76.5,
      "final_grade": "Grade-URS",
      "inspection_confidence": 89.5,
      "review_status": "ACCEPTED"
    },
    "rationale": "Grade A percentage (68.75%) is below 70.0% threshold. Meets URS criteria.",
    "provenance": {
      "model_version": "DevelopmentMockVisionModel-v1.0",
      "grading_profile_version": "sih-2026-urs-v1.1.0"
    },
    "limitations": [
      "Inspection covers visible outer bulb characteristics only.",
      "Internal rot cannot be detected from RGB photography.",
      "Size estimate is uncalibrated."
    ]
  }
  ```

---

### 2.6. Grading Profile Management
- `GET /api/v1/profiles`: List available grading profiles.
- `POST /api/v1/profiles`: Register a new grading profile version.

---

### 2.7. Audit & History Endpoint
- `GET /api/v1/inspections`: Retrieve inspection history with filter params (`batch_id`, `supplier_id`, `date_from`, `date_to`, `review_status`).
