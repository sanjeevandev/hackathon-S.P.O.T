# DATABASE ARCHITECTURE — S.P.O.T.

**Date**: September 4, 2026  
**Status**: IMPLEMENTED & TESTED (Phase 4 Database Normalization)  
**Problem Statement**: SIH 2026 PS 26031 — AI-Based Mobile Application for Onion Quality Assessment & Grading  

---

## 1. Audit of Legacy Database Scaffolding

### Starting Technology & Table Analysis
- **Database Engine**: Raw `sqlite3` connecting to `krishi_database.db`.
- **Legacy Table**: `grading_sessions` (flat 24-column table).
- **Identified Deficiencies**:
  1. Flat single-table structure lacking relational normalization (images, detections, defect probabilities, model versions, grading profiles, and audit events were squeezed into a single row).
  2. Contained legacy unbacked physical attributes (`moisture_level`, `firmness_rating`, `shelf_life_days`, `farmer_recommendation`).
  3. Lacked model version tracking (`model_version_id`), grading profile versioning (`grading_profile_id`), image metadata, and append-only audit trail.
  4. Lacked ORM data-access abstraction layer (raw SQL strings scattered in legacy helper functions).

### Migration & Compatibility Policy
- The legacy `grading_sessions` table is retained as a read-only historical fallback.
- The new application uses SQLAlchemy 2.0 ORM under `backend/db/` with 13 normalized entities supporting both SQLite and PostgreSQL.

---

## 2. Normalized Entity Relationship Design

```
[User] (1) ─────── (N) [Inspection] (1) ─────── (1) [Batch] (1) ─────── (0..1) [Supplier]
                          │                           │
                          │                           └── (0..1) [ProcurementCenter]
                          │
                          ├── (1) ─────── (N) [InspectionImage]
                          │                       │
                          │                       └── (1) ─────── (N) [OnionDetection]
                          │                                               │
                          │                                               └── (1) ─────── (1) [DefectPrediction]
                          │
                          ├── (N) ─────── (1) [ModelVersion]
                          │
                          ├── (N) ─────── (1) [GradingProfileModel]
                          │
                          ├── (1) ─────── (1) [GradingResultModel]
                          │
                          ├── (1) ─────── (N) [Report]
                          │
                          └── (1) ─────── (N) [AuditEvent] (Append-only Cryptographic Chain)
```

---

## 3. Entity Specification

1. **`users` (`User`)**: Basic user identity (`id`, `name`, `role`, `is_active`, `created_at`, `updated_at`). Roles: `INSPECTOR`, `BUYER`, `SELLER`, `ADMIN`.
2. **`suppliers` (`Supplier`)**: Procurement suppliers (`id`, `name`, `contact_reference`, `location_reference`, `is_active`).
3. **`procurement_centers` (`ProcurementCenter`)**: APMC procurement yards (`id`, `name`, `location`, `is_active`).
4. **`batches` (`Batch`)**: Physical procurement lots (`id`, `batch_code`, `supplier_id`, `procurement_center_id`, `declared_weight_kg`, `weight_source`, `sampling_status`).
5. **`model_versions` (`ModelVersion`)**: Vision model tracking (`id`, `model_id`, `model_name`, `model_version`, `source`, `framework`, `weights_reference`, `dataset_version`, `is_active`).
6. **`grading_profiles` (`GradingProfileModel`)**: Commercial grading policies (`id`, `profile_id`, `profile_name`, `version`, `status`, `official_status`, `source`, `disclaimer`, `rules_json`, `is_active`).
7. **`inspections` (`Inspection`)**: Inspection runs (`id`, `batch_id`, `inspector_id`, `model_version_id`, `started_at`, `completed_at`, `status`, `inspection_confidence`, `review_status`, `review_reason`).
8. **`inspection_images` (`InspectionImage`)**: Uploaded image metadata (`id`, `inspection_id`, `image_reference`, `original_filename`, `mime_type`, `width`, `height`, `quality_status`, `quality_metrics_json`).
9. **`onion_detections` (`OnionDetectionModel`)**: Per-bulb detections (`id`, `inspection_image_id`, `external_onion_id`, `bbox_json`, `detection_confidence`, `size_status`, `estimated_diameter_mm`, `size_confidence`).
10. **`defect_predictions` (`DefectPrediction`)**: Defect probabilities (`id`, `onion_detection_id`, `damage_probability`, `rot_probability`, `sprout_probability`).
11. **`grading_results` (`GradingResultModel`)**: Evaluated lot grades (`id`, `inspection_id`, `grading_profile_id`, `quality_score`, `grade`, `grade_a_percent`, `urs_percent`, `healthy_percent`, `damaged_percent`, `rotten_percent`, `sprouted_percent`, `undersized_percent`, `review_status`, `review_reason_json`, `sampling_status`, `explanation`, `rules_triggered_json`).
12. **`reports` (`Report`)**: Report references (`id`, `inspection_id`, `report_reference`, `report_type`, `generated_at`).
13. **`audit_events` (`AuditEvent`)**: Immutable append-only audit trail (`id`, `event_id`, `entity_type`, `entity_id`, `event_type`, `actor_id`, `timestamp`, `payload_json`, `previous_event_hash`, `event_hash`).

---

## 4. Reproducibility & Audit Trail Security

Every inspection record maintains explicit foreign key references to:
- The exact `ModelVersion` used during inference.
- The exact `GradingProfileModel` evaluated during policy scoring.
- The cryptographic `AuditEvent` SHA-256 chain (`event_hash` computed over `previous_event_hash + timestamp + entity_type + entity_id + event_type + payload`).

Historical inspections retain their original model version and grading profile version permanently. Modifying active model checkpoints or grading profile defaults does NOT alter historical inspection records.
