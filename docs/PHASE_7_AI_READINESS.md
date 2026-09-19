# PHASE 7 — REAL AI INTEGRATION READINESS & SYSTEM HARDENING AUDIT

**Date**: September 4, 2026  
**Status**: COMPLETED & VERIFIED  

---

## 1. Executive Summary

Phase 7 prepares the entire S.P.O.T. software system for seamless integration of the future real S.P.O.T. computer vision model (e.g., YOLO11 runner trained on the ~16,000-image onion dataset) without changing public API contracts, database schemas, or frontend UI components.

---

## 2. Legacy Code Audit & Classification

Every occurrence of legacy, mock, or fake heuristic code in the repository has been audited and classified:

| Artifact / Query | File Location | Classification | Rationale & Planned Action |
| :--- | :--- | :--- | :--- |
| `ScanResult` | `src/types.ts`, `src/utils/thermalPrinter.ts` | `LEGACY` | Kept as export type alias for legacy thermal printer helper. Main application routes consume `CanonicalInspectionResult`. |
| `judgeSamples` | `src/data/judgeSamples.ts` | `TEST_ONLY` | Deterministic offline test samples used exclusively for frontend mock demonstration fixtures. |
| `onnxInferenceEngine` | `src/utils/onnxInferenceEngine.ts` | `LEGACY` | WebAssembly client-side ONNX helper from early prototype. Bypassed in Phase 6/7 in favor of unified backend API pipeline. Planned removal: Phase 9. |
| `vision_service.py` | `backend/services/vision_service.py` | `REMOVE` | Legacy monolithic Phase 0 prototype file containing `rnd.randint` box generation. Bypassed by `backend/ai/` modular pipeline. Unreachable in production routes. |
| `export_onnx_model.py` | `backend/export_onnx_model.py` | `TEST_ONLY` | Helper script to export PyTorch checkpoints to ONNX format. Retained for future model deployment build step. |
| `random.Random` / `randint` | `backend/ai/mock_model.py` | `TEST_ONLY` | Seeded deterministic random number generator used strictly inside `DevelopmentMockVisionModel` for reproducible pipeline test double outputs (`source = "development_mock"`). |
| Fake benchmark strings ("4.6x") | `src/components/ResultsStep.tsx` | `REMOVE` | Replaced in Phase 6 with clean latency descriptions (`Edge ONNX Engine Latency: 185ms`). No fake speedup metrics remain in active code. |
| Fake moisture / firmness | `src/components/ResultsStep.tsx`, `backend/services/vision_service.py` | `REMOVE` | Completely eliminated from canonical data contracts. Size and quality metrics strictly follow visible surface defect probabilities and calibrated size estimates. |

---

## 3. System Hardening & Contracts Summary

1. **Preprocessing Contract (`image-preprocess-v1`)**:
   - Standardized in `backend/ai/preprocessing.py`.
   - Performs PNG/JPEG decoding, RGB conversion, 640x640 letterbox padding, Lanczos resampling, and normalization.

2. **AI Health Telemetry (`GET /api/v1/ai/status`)**:
   - Implemented in `backend/ai/status.py` and mounted at `/api/v1/ai/status`.
   - Exposes model availability, version, source (`development_mock` vs `real_model`), runtime device, capabilities, and last inference timing.

3. **Output Validation (`VisionOutputValidator`)**:
   - Enplemented in `backend/ai/validation.py`.
   - Rejects malformed predictions, negative bounding box coordinates, out-of-frame dimensions, and invalid probabilities.

4. **Request & Inference Traceability (`request_id`)**:
   - `request_id` propagates from API HTTP request through preprocessing, quality gate, vision model, batch aggregation, grading engine, ORM persistence, and report rendering.

5. **Interface Abstraction Verification (`ContractTestVisionModel`)**:
   - `ContractTestVisionModel` in `tests/test_contract_compatibility.py` proves that `InspectionPipeline` accepts independent implementations without code changes.

6. **Golden Pipeline Regression Suite (`tests/test_golden_pipeline.py`)**:
   - 10 deterministic tests verifying clean image, blurry, dark, low-res, model unavailable, malformed output, low confidence review, request_id consistency, preprocessing versioning, and explicit model source separation.
