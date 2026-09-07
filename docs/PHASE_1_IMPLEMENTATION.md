# PHASE 1 IMPLEMENTATION REPORT — S.P.O.T. (Smart Procurement Onion Transparency)

**Date**: September 4, 2026  
**Status**: PHASE 1 COMPLETE  
**Problem Statement**: SIH 2026 PS 26031 — AI-Based Mobile Application for Onion Quality Assessment & Grading  

---

## 1. What Was Implemented

In Phase 1, we established a type-safe, modular AI vision abstraction layer and image quality gate:

1. **AI Abstraction Layer (`backend/ai/base.py`)**: Defined an abstract `VisionModel` interface that decouples all high-level application endpoints from specific vision model implementations.
2. **Typed Schemas (`backend/ai/schemas.py`)**: Created Pydantic models for `ImageInput`, `OnionDetection`, `DefectProbabilities`, `SizeEstimate`, `EvidenceRegion`, and `VisionResult`. Removed all unbacked physical properties (moisture %, firmness %, internal rot %).
3. **Deterministic Development Mock (`backend/ai/mock_model.py`)**: Built `DevelopmentMockVisionModel` as a pure test double returning fixed synthetic detections. Uses no random numbers or pseudo-random heuristics. Explicitly flags `source = "development_mock"`.
4. **Model Registry & Production Protection (`backend/ai/registry.py`)**: Implemented `get_vision_model()`. In production mode (`SPOT_ENV=production`), requesting a mock or operating without a registered real model raises `ProductionModelUnavailableError`. Silently falling back to mock models in production is impossible.
5. **Image Quality Gate (`backend/pipeline/quality_gate.py`)**: Developed deterministic image quality evaluation measuring:
   - Resolution validation (minimum 320x240 pixels)
   - Blur score calculation (Laplacian variance threshold)
   - Exposure analysis (brightness min 40.0, max 225.0)
   - Contrast check (intensity standard deviation >= 20.0)
6. **Pipeline Orchestrator (`backend/pipeline/pipeline.py`)**: Built `InspectionPipeline`. If the Quality Gate returns `RETAKE_REQUIRED` (`passed=False`), the Vision Model `analyze()` method is **never executed**.
7. **FastAPI Endpoints (`backend/main.py`)**: Updated `/api/v1/inspect` and `/api/v1/analyze-onion` to use `InspectionPipeline` and return typed structured responses.
8. **Automated Unit & Integration Tests (`tests/`)**: Implemented 16 test cases covering schema validation, mock determinism, production mode mock protection, image quality gate rejection, quality failure preventing model execution, and measured pipeline timings.

---

## 2. AI Abstraction Design

The application depends exclusively on the abstract `VisionModel` contract:

```python
class VisionModel(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str: pass

    @property
    @abstractmethod
    def model_version(self) -> str: pass

    @property
    @abstractmethod
    def source(self) -> Literal["development_mock", "real_model"]: pass

    @abstractmethod
    def analyze(self, image_input: ImageInput, image_bytes: bytes) -> VisionResult: pass
```

---

## 3. VisionResult Structure

```json
{
  "request_id": "REQ-8812A",
  "model_name": "DevelopmentMockVisionModel",
  "model_version": "0.1.0-test",
  "source": "development_mock",
  "processing_time_ms": 1.25,
  "onions": [
    {
      "onion_id": "MOCK-DETECTION-01",
      "bbox": [64, 48, 256, 192],
      "detection_confidence": 0.90,
      "defect_probabilities": {
        "damage": 0.0,
        "rot": 0.0,
        "sprouting": 0.0
      },
      "size_estimate": {
        "status": "UNAVAILABLE",
        "estimated_diameter_mm": null,
        "calibration_method": null,
        "confidence": 0.0
      },
      "evidence_regions": []
    }
  ],
  "overall_confidence": 0.875,
  "status": "SUCCESS"
}
```

---

## 4. Mock Model Purpose & Rules

- **DevelopmentMockVisionModel** is strictly a **test double** for validating pipeline mechanics.
- It returns 2 fixed, synthetic detections with `source = "development_mock"`.
- It does **NOT** use `random.Random`, fake hashes, or pseudo-random heuristics.
- It is **NEVER** presented as a real AI model.

---

## 5. Quality Gate Methodology

The `ImageQualityGate` screens images before inference using OpenCV / Pillow matrix processing:

1. **Resolution**: `width >= 320` and `height >= 240` (replaces with `IMAGE_RESOLUTION_TOO_LOW`).
2. **Blur Detection**: Laplacian variance $V_{lap} = \text{var}(\nabla^2 I_{gray})$. Rejection if $V_{lap} < 50.0$ (`IMAGE_TOO_BLURRY`).
3. **Brightness**: $\mu = \text{mean}(I_{gray})$. Rejection if $\mu < 40.0$ (`IMAGE_TOO_DARK`) or $\mu > 225.0$ (`IMAGE_TOO_BRIGHT`).
4. **Contrast**: $\sigma = \text{std}(I_{gray})$. Rejection if $\sigma < 20.0$ (`IMAGE_LOW_CONTRAST`).

---

## 6. Threshold Configuration (`backend/pipeline/config.py`)

```python
class QualityGateConfig(BaseModel):
    minimum_width: int = 320
    minimum_height: int = 240
    blur_threshold: float = 50.0
    brightness_min: float = 40.0
    brightness_max: float = 225.0
    contrast_threshold: float = 20.0
```

> **Note**: These values are initial development heuristics and must later be empirically calibrated against the real APMC onion dataset.

---

## 7. Pipeline Execution Flow

```
[Raw Image Upload]
       │
       ▼
[Image Quality Gate Evaluation]
       │
       ├── (passed == False) ──▶ [Status: RETAKE_REQUIRED, vision_result: None]
       │                               (VisionModel.analyze() is NOT executed)
       ▼ (passed == True)
[Model Registry Resolution]
       │
       ├── (SPOT_ENV == 'production' & No Real Model) ──▶ [Status: MODEL_UNAVAILABLE, Error: ProductionModelUnavailableError]
       │
       ▼ (Model Available)
[VisionModel.analyze()] ──▶ [Status: SUCCESS, PipelineResult]
```

---

## 8. Production vs Development Model Behaviour

- **Development Mode (`SPOT_ENV=development`)**: `get_vision_model()` provides `DevelopmentMockVisionModel` if no real model is requested.
- **Production Mode (`SPOT_ENV=production`)**: `get_vision_model()` checks registered `real_model` runners. If no real model is registered, or if a mock model is requested, it raises `ProductionModelUnavailableError`. **Silent fallbacks to mock models in production are impossible.**

---

## 9. Test Coverage & Execution Metrics

Executed test suite via `python3 -m pytest -v tests/`:

- `tests/test_ai_contracts.py` (4 tests) — PASSED
- `tests/test_model_registry.py` (4 tests) — PASSED
- `tests/test_quality_gate.py` (5 tests) — PASSED
- `tests/test_pipeline.py` (3 tests) — PASSED

**Total**: 16 Passed, 0 Failed (Execution time: 0.82 seconds).

---

## 10. Known Limitations

1. No real neural network model binary (YOLO11 / ONNX runner) is included yet (scheduled for Phase 2).
2. Size calibration currently returns `status = "UNAVAILABLE"` (optical calibration scheduled for Phase 4).
3. Quality Gate thresholds are initial dev heuristics requiring dataset calibration.

---

## 11. Exact Next Step for Phase 2

**PHASE 2 — REAL MODEL INTEGRATION & BENCHMARK FRAMEWORK**
1. Implement real vision model runner wrappers (YOLO11 / ONNX runtime integration).
2. Build quantitative benchmark harness evaluating candidate models on precision, recall, mAP50, mAP50-95, F1, confusion matrix, latency, and model size.
3. Register the production model candidate with `register_vision_model("yolo11n-onion", YOLO11VisionModel)`.
