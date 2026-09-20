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
> `VisionResult.status` gained a **`LOW_CONFIDENCE`** value, and
> `PipelineResult.status` gained **`REVIEW_REQUIRED`** (the pipeline-level mirror of a
> low-confidence classification). See `docs/EVALUATION_AND_BENCHMARK.md` for the
> held-out evaluation methodology and results.

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
| `VisionResult.status` | `SUCCESS` | Classified above the model's accepted confidence threshold |
| `VisionResult.status` | `LOW_CONFIDENCE` | Classified but below the threshold; detections and confidence are preserved for review |
| `VisionResult.status` | `NO_VALID_DETECTIONS` | No usable classification probabilities / unknown class label |
| `VisionResult.status` | `MODEL_UNAVAILABLE` / `ERROR` | Weights/runtime failure or generic error, with `error_message` |
| `PipelineResult.status` | `REVIEW_REQUIRED` | Pipeline mirror of `LOW_CONFIDENCE`; `vision_result` is **present** so callers see the explicit per-model status, confidence, and detections |
| `PipelineResult.status` | `REJECTED_NOT_ONION` | Pipeline mirror of `NO_VALID_DETECTIONS` (image passed the gate but produced no valid class) |

The binary classifier's default accept threshold is `0.60`
(`YOLO26ClassifierModel.DEFAULT_MIN_ACCEPT_CONFIDENCE`). This threshold is runtime
policy — not an accuracy statistic — and can be tuned per deployment.
