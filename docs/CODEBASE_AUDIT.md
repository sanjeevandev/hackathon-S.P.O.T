# CODEBASE AUDIT — S.P.O.T. (Smart Procurement Onion Transparency)

**Date**: September 4, 2026  
**Auditor**: Principal Software Architect & Engineering Team  
**Scope**: Smart India Hackathon 2026 — Problem Statement 26031 Prototype Rebuild  

---

## 1. Current Architecture Overview

The existing codebase is structured as a two-tier Web application:

1. **Frontend (`/src`)**: React 18 + Vite + TypeScript single-page app styled with Tailwind CSS v4. It manages step-based UI flow (`language`, `camera`, `results`, `history`, `admin`), uses WebSockets/WebRTC/WebSerial stubs, and attempts in-browser ONNX inference via `onnxruntime-web`.
2. **Backend (`/backend`)**: Python FastAPI server providing REST endpoints for image submission, session listing, status updates (dispute flagging), and SQLite persistence.

```
┌─────────────────────────────────────────────────────────┐
│                 React 18 Frontend UI                    │
│   (Camera Step, Results Step, History, Admin Dashboard) │
└───────────────────────────┬─────────────────────────────┘
                            │
            ┌───────────────┴──────────────┐
            ▼                              ▼
 ┌──────────────────────┐      ┌─────────────────────────┐
 │   FastAPI Backend    │      │  ONNX Edge Fallback     │
 │  (vision_service.py) │      │ (onnxInferenceEngine.ts)│
 └──────────┬───────────┘      └─────────────────────────┘
            ▼
 ┌──────────────────────┐
 │  SQLite Database     │
 │ (krishi_database.db) │
 └──────────────────────┘
```

---

## 2. Current Tech Stack

| Category | Component / Dependency | Current Usage / Status |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18.3.1, TypeScript 5.6.2, Vite 5.4.10 | Active & functional build system |
| **UI Styling** | Tailwind CSS v4.3.3, Lucide React 1.38.0 | Styled components and custom dashboards |
| **Edge AI Runtime** | `onnxruntime-web` 1.29.0 | Configured with WASM/WebGL providers; currently falls back to hardcoded static results when `.onnx` binary is missing |
| **Backend Framework** | FastAPI 0.110.0, Uvicorn, Pydantic | Operates REST API on port 8000 |
| **Image Processing** | Pillow (PIL) 10.2.0 | Simple PIL open & RGB sample color calculation |
| **Database** | SQLite3 (`krishi_database.db`) | Single flat table `grading_sessions` |
| **Reporting / Export** | `jspdf`, `html2canvas`, `html2pdf.js` | Client-side DOM PDF rendering |

---

## 3. Current Data Flow

```
[User Camera / File Upload]
           │
           ▼
[FastAPI /api/v1/analyze-onion OR Edge Inference]
           │
           ▼
[AIVisionService.process_onion_image]
 ├─ Reads bytes & samples RGB
 ├─ Uses random seed (image bytes sum) to manufacture 12–28 bounding boxes
 ├─ Calculates pseudo millimeter sizes: (box_w + box_h)/2 * 0.38
 ├─ Evaluates < 45mm threshold & assigns defect tags
 └─ Summarizes Grade A %, URS %, Rejected %
           │
           ▼
[SQLite log_grading_session] -> Stores in flat 'grading_sessions' table
           │
           ▼
[Response JSON to Frontend UI] -> Rendered in Recharts & HTML cards
```

---

## 4. Existing AI & Database Flows

### AI Flow Analysis
- **Backend (`backend/services/vision_service.py`)**:
  - The function `run_yolov8_opencv_inference` claims to run YOLOv8, but actually uses `random.Random(seed)` based on image bytes sum.
  - It generates arbitrary bounding box coordinates (`rnd.randint(10, width-80)`), assigns mock defect labels (`grade_a`, `sprouted`, `rotten`, `damaged`, `undersized`), and computes percentages from synthetic counters.
  - It asserts moisture levels (e.g. "82% Ideal") and firmness ratings from RGB color averages, which is scientifically invalid for ordinary RGB camera images without spectroscopic/hyperspectral sensors.
- **Frontend (`src/utils/onnxInferenceEngine.ts`)**:
  - Catches missing ONNX files and returns 5 static hardcoded bounding boxes (`ONION-01` to `ONION-05`), static 62.5% Grade A percentage, and prints fake edge benchmark logs ("🚀 Speedup: 4.6x Faster").

### Database Flow Analysis
- **Backend (`backend/database.py`)**:
  - Operates a single table `grading_sessions` with 24 flat columns.
  - Missing normalized entities for Users, Procurement Centers, Suppliers, Batches, Onion Detections, Grading Profiles, Model Versions, and Audit Logs.

---

## 5. Audit Findings & Known Defects

| Area | Defect / Anti-Pattern Description | Severity | Rebuild Action |
| :--- | :--- | :--- | :--- |
| **AI Fabrications** | Bounding boxes and defect classes generated using `random.Random()`. Hardcoded fallback arrays in browser ONNX module. | **CRITICAL** | Replace with modular `VisionModel` interface and explicit `DevelopmentMockVisionModel`. |
| **False Claims** | Moisture %, firmness ratings, and internal-rot claims derived from ordinary RGB camera photos. | **CRITICAL** | Remove unbacked physical claims. Limit output strictly to visible surface features and state physical limits clearly. |
| **Image Quality** | No blur check, exposure check, framing validation, or minimum onion count check before analysis. | **HIGH** | Implement `Image Quality Gate` that returns `RETAKE_REQUIRED` for blurry/dark images. |
| **Uncalibrated Size** | Diameter mm calculated by multiplying pixel width by fixed arbitrary scalar `0.38` without reference objects or optical calibration. | **HIGH** | Return `SIZE_ESTIMATE_UNAVAILABLE` until pixel-to-mm optical calibration flow is implemented. |
| **Missing Uncertainty** | Low-confidence detections or ambiguous images forced into Grade A/URS/C without review flags. | **HIGH** | Implement `REVIEW_REQUIRED` state for low confidence, severe overlap, or quality issues. |
| **Coupled Logic** | Grading rules (e.g. `>= 70% Grade A`) hardcoded inside Python vision functions and React components. | **MEDIUM** | Extract into decoupled `GradingPolicyEngine` using versioned `GradingProfile` rules. |
| **Flat Database** | Single table without relations, audit trails, model versioning, or multi-image batch support. | **MEDIUM** | Design normalized relational schema (`users`, `batches`, `inspections`, `detections`, etc.). |
| **Security Risks** | Open CORS (`*`), unauthenticated API endpoints, unvalidated file upload limits. | **MEDIUM** | Implement strict CORS, input validation, and API authentication primitives. |

---

## 6. What Should Be Preserved vs Replaced vs Removed

### A. What Will Be Preserved (Reused)
1. **Frontend Architecture Foundation**: React 18 + Vite + TypeScript project structure.
2. **Camera Access Primitives**: MediaStream capture logic in `CameraStep.tsx`.
3. **Hardware Stubs**: Serial scale interface helper (`webSerialScale.ts`) and thermal printing utility (`thermalPrinter.ts`).
4. **Base Design System & Icons**: Lucide React icons, Tailwind utility styling foundation.

### B. What Will Be Replaced
1. **`vision_service.py`**: Replaced by a cleanly abstracted AI Vision Service interface and explicit pipeline runners.
2. **`onnxInferenceEngine.ts`**: Replaced by an abstract `VisionModel` interface client.
3. **Database Schema (`database.py`)**: Replaced by a multi-entity relational schema (SQLite / PostgreSQL ready).
4. **Grading Logic**: Extracted out of frontend and backend vision scripts into a pure `GradingPolicyEngine`.

### C. What Will Be Removed
1. **`rnd.randint()` Bounding Box Fabrication**: All code generating fake bounding boxes disguised as YOLO outputs.
2. **Hardcoded Moisture & Firmness Assumptions**: Unbacked physical attribute calculations from RGB images.
3. **Synthetic Edge Benchmark Logs**: Fabricated latency comparison strings.
4. **Hardcoded Judge Demo Mock Overrides**: Fake demo payloads claiming 100% export quality without actual model inference.

---

## 7. Audit Conclusion & Roadmap

The current repository provides a working Vite/React frontend shell and FastAPI backend scaffolding, but relies on fabricated AI logic and hardcoded mock statistics.

**Phase 0 Mandate**: Stop building visual UI mockups. Define the rigorous System Architecture, API Contracts, AI Abstractions, and Rebuild Plan before executing pipeline implementation.
