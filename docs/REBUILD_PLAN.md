# REBUILD PLAN — S.P.O.T. (Smart Procurement Onion Transparency)

**Date**: September 4, 2026  
**Strategy**: Modular, Evidence-Driven 12-Phase System Rebuild  

---

## Executive Principles

1. **Defensified Engineering**: No hardcoded fake metrics, fake edge benchmarks, or fake bounding boxes.
2. **Phase 0 Gate**: Complete repository audit, target architecture, and API contracts before pipeline execution.
3. **Decoupled Business Logic**: Separate AI computer vision perception from commercial grading policy rules.
4. **Honest Limitations**: State physical limits (e.g. RGB camera cannot sense internal rot; uncalibrated pixel sizes are returned as `SIZE_ESTIMATE_UNAVAILABLE`).
5. **Reproducibility**: Every inspection result is traceable through `Image` + `Model Version` + `Model Output` + `Grading Profile Version` = `Final Grade`.

---

## Development Roadmap & Phase Sequence

```
  Phase 0: Repository Audit & Architecture Contracts (CURRENT PHASE)
    │
    ▼
  Phase 1: AI Abstraction Layer, Pipeline Skeleton & Image Quality Gate
    │
    ▼
  Phase 2: Real Model Integration & Vision Candidate Benchmark Framework
    │
    ▼
  Phase 3: Multi-Label Defect Evidence Engine
    │
    ▼
  Phase 4: Optical Size Calibration Module
    │
    ▼
  Phase 5: Batch Intelligence & Multi-Image Aggregation
    │
    ▼
  Phase 6: Configurable Grading Policy Engine (`GradingProfile`)
    │
    ▼
  Phase 7: Relational Database Schema & Immutable Audit Trail
    │
    ▼
  Phase 8: Backend REST API Infrastructure
    │
    ▼
  Phase 9: Mobile UX / Frontend Client Alignment
    │
    ▼
  Phase 10: Digital Inspection Report Generator
    │
    ▼
  Phase 11: Comprehensive Automated Testing Suite
    │
    ▼
  Phase 12: Performance Polish, Mobile Optimization & Verification
```

---

## Phase Breakdown & Deliverables

### PHASE 0: Repository Audit & Contracts (Completed)
- **Deliverables**:
  - `docs/CODEBASE_AUDIT.md`: Complete repository inspection & tech debt identification.
  - `docs/SYSTEM_ARCHITECTURE.md`: Pipeline specifications, contracts, and module boundaries.
  - `docs/API_CONTRACT.md`: Typed REST endpoint schemas.
  - `docs/REBUILD_PLAN.md`: Execution roadmap.

### PHASE 1: AI Abstraction & Image Quality Gate
- **Deliverables**:
  - Abstract `VisionModel` interface in Python (`backend/ai/base.py`).
  - Explicit `DevelopmentMockVisionModel` for pipeline testing.
  - `ImageQualityGate` service evaluating blur score (Laplacian variance), darkness/exposure, and framing.
  - Rejection handler returning `RETAKE_REQUIRED` with explicit error codes.

### PHASE 2: Real Model Integration & Benchmark Protocol
- **Deliverables**:
  - Model evaluation harness supporting YOLO11, YOLO26, segmentation variants, lightweight classification models.
  - Quantitative benchmark runner computing precision, recall, mAP50, mAP50-95, F1, confusion matrix, latency, and model size.
  - Model registry loader for checkpoint execution.

### PHASE 3: Defect Evidence Engine
- **Deliverables**:
  - Multi-label defect output parser.
  - Independent defect scoring for damage, rot, sprouting, and undersized status.
  - Spatial bounding box & evidence region extractor.

### PHASE 4: Size Calibration Module
- **Deliverables**:
  - Pixel-to-millimeter reference target detector.
  - Fallback logic returning `SIZE_ESTIMATE_UNAVAILABLE` when uncalibrated.

### PHASE 5: Batch Intelligence Engine
- **Deliverables**:
  - Multi-image inspection aggregator.
  - Statistical lot sampling and weight distribution estimators.

### PHASE 6: Grading Policy Engine
- **Deliverables**:
  - Decoupled `GradingPolicyEngine` class.
  - JSON profile schema loader (`GradingProfile`) supporting versioned rule sets.

### PHASE 7: Relational Persistence Layer
- **Deliverables**:
  - Normalized SQLite schema migration script (`backend/db/schema.py`).
  - ORM / SQL query layers for 13 entities (`users`, `batches`, `inspections`, `detections`, etc.).

### PHASE 8: Backend REST API Refactor
- **Deliverables**:
  - Refactored FastAPI application routes conforming to `docs/API_CONTRACT.md`.
  - Request validation schemas & error response handlers.

### PHASE 9: Mobile UX Alignment
- **Deliverables**:
  - Mobile UI step updates (`CameraStep`, `QualityGateStep`, `EvidenceStep`, `ResultsStep`, `ReportStep`).
  - Alignment of frontend state with backend contracts (no local fake overrides).

### PHASE 10: Digital Report Generator
- **Deliverables**:
  - Backend PDF/JSON report generation pipeline.
  - QR verification code & provenance hash signature embedded in report.

### PHASE 11: Testing Suite
- **Deliverables**:
  - `tests/test_image_quality_gate.py`
  - `tests/test_grading_engine.py`
  - `tests/test_pipeline.py`
  - `tests/test_api.py`

### PHASE 12: Final Polish & Verification
- **Deliverables**:
  - End-to-end verification report.
  - Performance audit (< 1500ms target pipeline execution).

---

## Dataset Handling Guidelines (Step 17)

When real onion datasets become available:
1. Conduct complete dataset audit (class distribution, annotation audit, duplicate detection, image quality analysis).
2. Establish explicit Train / Validation / Test split strategy (prevent data leakage across batches/farms).
3. Select final AI model strictly based on empirical evaluation benchmark results, never popularity claims.
