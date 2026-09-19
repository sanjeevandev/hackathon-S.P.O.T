# SYSTEM ARCHITECTURE — S.P.O.T. (Smart Procurement Onion Transparency)

**Date**: September 4, 2026  
**Status**: Target Engineering Architecture (Phase 0 Specification)  
**Problem Statement**: SIH 2026 PS 26031 — AI-Based Mobile Application for Onion Quality Assessment & Grading  

---

## 1. End-to-End System Processing Pipeline

Every inspection must follow this strictly sequential pipeline contract. No step may be bypassed, fake-simulated in UI components, or hard-coded.

```
Mobile App / Device Interface
              │
              ▼
    Image Capture / Upload
              │
              ▼
    Image Quality Gate ──────────▶ [RETAKE_REQUIRED] (Blur / Exposure / Darkness / Framing / Overlap)
              │ (PASS)
              ▼
    AI Vision Service (Abstract VisionModel Interface)
              │
              ▼
     Onion Detection (Bounding Boxes / Coordinates / Confidence)
              │
              ▼
     Defect Analysis (Multi-Label Probabilities: Damage, Rot, Sprouting, Undersized)
              │
              ▼
      Size Analysis (Pixel-to-mm Calibration OR SIZE_ESTIMATE_UNAVAILABLE)
              │
              ▼
    Evidence & Confidence Aggregation
              │
              ▼
    Batch Aggregation & Statistical Lot Analysis
              │
              ▼
    Grading Policy Engine (Versioned Grading Profiles & Rule Evaluations)
              │
              ▼
  Grade Allocation (Grade A %, URS %, Quality Score, Final Prototype Grade)
              │
              ▼
    Digital Inspection Report Generation
              │
              ▼
  Relational Database Persistence & Immutable Audit Trail
```

---

## 2. System Contract & Module Boundaries

### Module 1: Image Quality Gate Engine
- **Input**: Raw RGB Image Buffer (Bytes / Base64), Metadata (resolution, device orientation).
- **Processing**:
  - Blur score calculation (Laplacian variance threshold).
  - Exposure & illumination check (histogram analysis for darkness or overexposure clipping).
  - Minimum usable onion count check (minimum detected objects threshold).
  - Framing and border occlusion check.
- **Output**:
  - `status`: `PASS` or `RETAKE_REQUIRED`
  - `rejection_reasons`: List of failures (e.g. `["IMAGE_TOO_BLURRY", "UNDEREXPOSED_LIGHTING"]`)
  - `quality_metrics`: `{ blur_score: float, brightness: float, contrast: float }`

### Module 2: AI Vision Service Abstraction Layer
- **Input**: Validated RGB Image (`Image Quality Gate` == `PASS`).
- **Interface**: `VisionModel`
  ```python
  class VisionModel(ABC):
      @abstractmethod
      def analyze(self, image_bytes: bytes) -> VisionResult:
          pass
  ```
- **Implementations**:
  - `DevelopmentMockVisionModel`: Explicitly named development double for pipeline integration testing (must NEVER be passed off as production AI).
  - `YOLO11VisionModel` / `ONNXEdgeVisionModel`: Production model candidate wrappers evaluated against validation metrics (precision, recall, mAP50, mAP50-95, latency).

### Module 3: Defect Analysis Engine (Multi-Label Defect Representation)
An onion is **not** forced into a single mutually-exclusive defect class. An onion bulb can simultaneously exhibit multiple defect flags.

- **Output Entity (`OnionDetection`)**:
  - `onion_id`: Unique string identifier within inspection
  - `bbox`: `[x1, y1, x2, y2]` coordinates in normalized or pixel space
  - `damage_probability`: `float` (0.0 to 1.0) — surface cracks, skin cuts, mechanical bruising
  - `rot_probability`: `float` (0.0 to 1.0) — visible surface moisture rot, mold, bacterial decay
  - `sprout_probability`: `float` (0.0 to 1.0) — neck shoot growth / active sprouting
  - `size_estimate_mm`: `Optional[float]` — diameter in mm if calibrated
  - `size_class`: `UNDERSIZED | STANDARD | OVERSIZED | UNCALIBRATED`
  - `detection_confidence`: `float` (0.0 to 1.0)
  - `evidence_regions`: Bounding boxes / masks around identified defect loci

### Module 4: Calibrated Size Measurement Module
- **Rules**:
  - If a calibrated reference object (e.g., standard marker or ArUco reference) is detected and camera parameters are known:
    `Diameter (mm) = (Pixel Width * Reference Scale Factor)`
  - If no reference object is present:
    `size_estimate_mm = None` and `size_status = "SIZE_ESTIMATE_UNAVAILABLE"`
  - **Forbidden**: Inventing fixed arbitrary multiplier scalars (such as `pixel_span * 0.38`) without physical reference.

### Module 5: Uncertainty & Review Decision Engine
- **Uncertainty Trigger Conditions**:
  - Model detection confidence below configurable threshold (e.g. `< 0.70`).
  - Severe onion overlap/occlusion percentage exceeding limit (`> 40%`).
  - Ambiguous defect probabilities (e.g., rot probability between 0.40 and 0.60).
  - Uncalibrated size measurement when size rules are strict.
  - Image quality parameters borderline.
- **Output Status**: `REVIEW_REQUIRED`
- **Rule**: Never force a confident Grade A or URS result when evidence is ambiguous.

### Module 6: Model Confidence vs Inspection Confidence
- **Model Confidence**: Pure statistical confidence score produced by the neural network backend for object detection and classification (e.g., bounding box detection probability).
- **Inspection Confidence**: Composite reliability score combining:
  - Image quality score (blur, lighting, contrast)
  - Frame coverage & onion separation
  - Detection confidence average & variance
  - Size calibration availability
  - Defect classification certainty
- **Equation Concept**:
  `Inspection Confidence = (Quality Score * 0.25) + (Avg Model Confidence * 0.35) + (Calibration Factor * 0.20) + (Separation Factor * 0.20)`

### Module 7: Grading Policy Engine (`GradingProfile`)
Separates AI physical measurements from commercial procurement policies.

- **Configurable `GradingProfile` Schema**:
  - `profile_id`: String (e.g., `"SIH-2026-STANDARD-PROTOTYPE"`)
  - `profile_name`: Human-readable name
  - `version`: Version string (e.g., `"1.0.0"`)
  - `grade_a_min_percentage`: Minimum Grade A % required for Lot Grade A (e.g. 70.0%)
  - `urs_max_defect_tolerance`: Max allowable defects under Under-Relaxed Specifications
  - `undersized_threshold_mm`: Physical diameter boundary (e.g. 45.0 mm)
  - `rejection_rules`: Conditions for immediate lot rejection (e.g. Rot count > 5%)
- **Rule**: Grading thresholds must NOT be scattered across frontend TypeScript or backend service routines.

---

## 3. Relational Database Architecture

The persistence model is fully normalized across 13 core entities:

```
[users] ──┐
          ├──▶ [batches] ──┬──▶ [inspections] ──┬──▶ [inspection_images]
[suppliers] ┘              │                    ├──▶ [onion_detections] ──▶ [defect_predictions]
                           │                    ├──▶ [grading_results]
[procurement_centers] ─────┘                    ├──▶ [reports]
                                                └──▶ [audit_events]

[grading_profiles] ─────────────────────────────┐
[model_versions]   ─────────────────────────────┴──▶ [inspections]
```

### Core Entities Description
1. `users`: Inspector and officer credentials, roles, APMC assignments.
2. `suppliers`: Farmer and trader profile data.
3. `procurement_centers`: Location, depot ID, district, state.
4. `batches`: Lot identifier, declared weight (KG), arrival timestamp.
5. `inspections`: Individual inspection runs linking batch, model version, and grading profile version.
6. `inspection_images`: Raw and processed image metadata, storage paths, quality gate results.
7. `onion_detections`: Individual detected onion bulbs with bounding box coordinates.
8. `defect_predictions`: Multi-label defect probabilities per detected bulb.
9. `grading_results`: Aggregated metrics (Grade A %, URS %, Rejected %, Quality Score, Final Grade).
10. `grading_profiles`: Versioned rules engine configurations.
11. `model_versions`: Registry of deployed model checkpoints, evaluation metrics, and weights hash.
12. `reports`: Generated PDF / JSON digital inspection certificates.
13. `audit_events`: Immutable security and dispute log events.

---

## 4. Reproducibility Contract

Every inspection result generated by S.P.O.T. must be 100% reproducible.

$$ \text{Final Result} = \mathcal{F}\left(\text{Image Buffer}, \text{Model Version } V_m, \text{Model Output } O_m, \text{Grading Profile } P_g\right) $$

Given the identical:
1. `Image Buffer`
2. `Model Version` (e.g., `yolo11n-onion-v1.2.0`)
3. `Raw Model Output` (Bounding boxes & defect probabilities)
4. `Grading Profile Version` (e.g., `profile-sih-2026-v1`)

The system **must** re-compute the exact same Grade A %, URS %, Quality Score, Final Prototype Grade, and Explanation.

---

## 5. Digital Inspection Report Contract

The generated S.P.O.T. Quality Inspection Report must include:

```
================================================================================
                     S.P.O.T. QUALITY INSPECTION REPORT
================================================================================
Batch ID: BATCH-MH-2026-0891                 Inspection Timestamp: 2026-09-04 12:19
Supplier: Ramesh Patil (Farmer ID: F-8812)   Procurement Location: APMC Nashik Hub
--------------------------------------------------------------------------------
Total Onions Detected: 24                    Inspection Coverage: 85% Frame Area
--------------------------------------------------------------------------------
COUNT BREAKDOWN:
  - Healthy (Grade A Candidate): 16
  - Damaged: 2
  - Rotten: 1
  - Sprouted: 2
  - Undersized (<45mm): 3
--------------------------------------------------------------------------------
PERCENTAGE & GRADE SUMMARY:
  - Grade A Percentage: 66.7%
  - URS Percentage: 20.8%
  - Quality Score: 78 / 100
  - Final Prototype Grade: Grade-URS (Under Relaxed Specifications)
  - Inspection Confidence: 91.4% (Model Conf: 94.2%, Quality: PASS)
  - Review Status: ACCEPTED
--------------------------------------------------------------------------------
DECISION RATIONALE:
  "Grade A percentage (66.7%) is below the 70.0% threshold for Grade-A certification.
   Lot meets URS Criteria (Grade A + URS = 87.5% >= 75.0%). Rot count is within 5% tolerance."
--------------------------------------------------------------------------------
PROVENANCE METADATA:
  Model Version: onion-yolov8n-v1.0.4 [Hash: e3b0c442...]
  Grading Profile Version: sih-2026-urs-v1.1
--------------------------------------------------------------------------------
LIMITATIONS & DISCLAIMER:
  * Inspection covers visible outer surface bulb characteristics only.
  * Internal bulb rot cannot be determined from standard RGB photography.
  * Size measurements are estimated based on pixel geometry; formal optical calibration required.
  * Prototype decision system for SIH 2026 demonstration; non-certified for statutory trade.
================================================================================
```
