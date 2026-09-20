# AI STATUS CONTRACT & DIAGNOSTICS SPECIFICATION

**Endpoint**: `GET /api/v1/ai/status`  
**Response Schema**: `AIStatusResponse` (`backend/ai/status.py`)  
**Date**: September 4, 2026  

---

## 1. Overview

The `GET /api/v1/ai/status` endpoint provides real-time health, diagnostic telemetry, and model registry introspection for developers, operations, and quality auditors. It explicitly exposes whether the active model is a development mock double or a validated real model.

> **Arena update (2026-09-20):** the active real model is `YOLO26n-cls-pilot`
> (binary healthy/defective classifier), checkpoint
> `artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.pt`, `source: real_model`.
> Low-confidence handling uses the **pre-existing grading path**: the classifier
> reports the model's top-1 confidence in `VisionResult.overall_confidence`, the
> grading engine compares it against `GradingProfile.confidence_min_threshold`
> (default 0.70) and flags `REVIEW_REQUIRED`. No additional status was added on
> top of this flow. See `docs/AI_ARCHITECTURE_AND_EVALUATION.md` for the full
> architecture and evaluation methodology.

---

## 2. API Contract Schema

```json
{
  "available": true,
  "model_name": "DevelopmentMockVisionModel",
  "model_version": "1.0.0-mock",
  "source": "development_mock",
  "loaded": true,
  "runtime": "PyTorch / CPU (Mock Double)",
  "capabilities": [
    "object_detection",
    "damage_classification",
    "rot_classification",
    "sprouting_classification"
  ],
  "preprocessing_version": "image-preprocess-v1",
  "status": "READY",
  "last_successful_inference": "2026-09-04T10:55:00.123456+00:00",
  "last_inference_duration_ms": 14.5,
  "environment": "development"
}
```

---

## 3. Field Definitions & Valid Values

| Field | Type | Description | Valid Values |
| :--- | :--- | :--- | :--- |
| `available` | boolean | True if an active model can perform inference | `true`, `false` |
| `model_name` | string | Identifier of active vision model class | e.g. `DevelopmentMockVisionModel`, `YOLO11OnionDetector` |
| `model_version` | string | Semantic version of active model build | e.g. `1.0.0-mock`, `1.2.0-yolo11n` |
| `source` | string | Explicit model provenance flag | `"development_mock"`, `"real_model"` |
| `loaded` | boolean | Memory status of model weights and runtime | `true`, `false` |
| `runtime` | string | Execution device hardware / engine | e.g. `PyTorch / CPU (Mock Double)`, `CUDA / ONNX` |
| `capabilities` | string[] | List of supported CV tasks | `object_detection`, `damage_classification`, etc. |
| `preprocessing_version` | string | Image contract version | `"image-preprocess-v1"` |
| `status` | string | Overall engine status | `"READY"`, `"NOT_CONFIGURED"`, `"UNAVAILABLE"`, `"ERROR"` |
| `last_successful_inference`| ISO string | UTC timestamp of last completed inference | Nullable ISO 8601 string |
| `last_inference_duration_ms`| float | Measured vision duration in ms | Nullable float >= 0.0 |
| `environment` | string | Active system environment | `"development"`, `"production"` |

---

## 4. Production Security Rules

- In production (`SPOT_ENV=production`), if no real model is registered, the endpoint returns `available: false`, `source: "real_model"`, `status: "UNAVAILABLE"`.
- Production mode **NEVER** silently falls back to `"development_mock"`.
- The real-model registry entry (`YOLO26ClassifierModel`) verifies at least once per
  process that `best.pt` exists **and** loads as a binary (healthy/defective)
  classifier. A present-but-unusable checkpoint (e.g. a 4-class model placed at the
  binary path) is not advertised or selected, so a bad checkpoint cannot silently
  masquerade as the real model.

## 5. Vision & Pipeline Status Semantics

| Surface | Status | Meaning |
| :--- | :--- | :--- |
| `VisionResult.status` | `SUCCESS` | A valid binary classification was produced; confidence is carried in `overall_confidence` |
| `VisionResult.status` | `NO_VALID_DETECTIONS` | No usable classification probabilities / unknown class label |
| `VisionResult.status` | `MODEL_UNAVAILABLE` / `ERROR` | Weights/runtime failure or generic error, with `error_message` |
| `PipelineResult.status` | `SUCCESS` | Image passed the gate and the model produced a valid classification (even a low-confidence one) |

**Confidence → review is a grading-engine responsibility, not a new status:** the
classifier returns the model's own top-1 confidence; `GradingPolicyEngine` compares
it against `GradingProfile.confidence_min_threshold` (default `0.70`) and flags
`review_status = REVIEW_REQUIRED` with an explanation. This is persisted on the
inspection record and surfaced via the canonical inspection result. There is no
separate `VisionResult`/`PipelineResult` low-confidence status by design — one
threshold, one source of truth.
