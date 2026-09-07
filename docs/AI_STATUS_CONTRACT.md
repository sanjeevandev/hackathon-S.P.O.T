# AI STATUS CONTRACT & DIAGNOSTICS SPECIFICATION

**Endpoint**: `GET /api/v1/ai/status`  
**Response Schema**: `AIStatusResponse` (`backend/ai/status.py`)  
**Date**: September 4, 2026  

---

## 1. Overview

The `GET /api/v1/ai/status` endpoint provides real-time health, diagnostic telemetry, and model registry introspection for developers, operations, and quality auditors. It explicitly exposes whether the active model is a development mock double or a validated real model.

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
