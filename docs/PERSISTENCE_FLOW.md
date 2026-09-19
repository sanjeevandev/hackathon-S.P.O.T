# PERSISTENCE FLOW — S.P.O.T.

**Date**: September 4, 2026  
**Status**: IMPLEMENTED & TESTED  

---

## 1. Inspection Persistence Lifecycle

```
Image Input / File Upload
          │
          ▼
   Quality Gate Screening
          │
    ┌─────┴──────────────────────────────┐
    │                                    │
 [FAIL]                               [PASS]
    │                                    │
    ▼                                    ▼
Return Quality Gate Rejection      VisionModel Inference
(Persists status="FAILED")                │
                                         ▼
                               Batch Intelligence Aggregation
                                         │
                                         ▼
                               Grading Policy Evaluation
                                         │
                                         ▼
                        InspectionRepository Transaction (Atomic)
                                         │
 ┌───────────────────────────────────────┼───────────────────────────────────────┐
 │                                       │                                       │
 ▼                                       ▼                                       ▼
Save Batch Record                Save Inspection & Image            Save Detections & Defect Predictions
 │                                       │                                       │
 └───────────────────────────────────────┼───────────────────────────────────────┘
                                         │
                                         ▼
                             Save Grading Result
                                         │
                                         ▼
                             Append Audit Event (SHA-256 Chain)
                                         │
                                         ▼
                             Database Commit / Session Close
```

---

## 2. Transaction Boundaries & Rollback Safety

All database write operations within `InspectionRepository.save_inspection_result` execute inside a single atomic database transaction. If any entity persistence operation fails:
1. `db.rollback()` is executed automatically.
2. No partially persisted records or orphan records remain in the database.
3. Errors are logged and returned as structured API errors without corrupting historical records.

---

## 3. History Retrieval Endpoints

- `GET /api/v1/inspections`: Returns listing of inspections with filtering support (`batch_id`, `status`, `limit`).
- `GET /api/v1/inspections/{inspection_id}`: Returns complete detail of an inspection including model version, grading profile, image quality metrics, detected onions, defect probabilities, and lot grade evaluation.
