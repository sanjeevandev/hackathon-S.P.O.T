# PHASE 6 — MOBILE INSPECTION UI ARCHITECTURE

**Date**: September 4, 2026  
**Status**: IMPLEMENTED  

---

## 1. Overview & Navigation Workflow

The S.P.O.T. Mobile Inspection UI is built using React 18, Vite, and TypeScript. It strictly mirrors the operational workflow of agricultural procurement officers at APMC yards:

```
HOME (/home)
  └── NEW INSPECTION (/inspection/new)
        └── CAPTURE / UPLOAD (/inspection/:id/capture)
              └── ANALYSIS STEP (/inspection/:id/analyzing)
                    ├── RESULT SCREEN (/inspection/:id/result)
                    │     ├── EVIDENCE OVERLAY (/inspection/:id/evidence)
                    │     └── DIGITAL QUALITY REPORT (/inspection/:id/report)
                    └── HISTORY VIEW (/history & /history/:id)
```

---

## 2. Component Structure & Responsibilities

1. **`src/App.tsx`**: Active route state manager (`home`, `new_inspection`, `capture`, `analyzing`, `result`, `evidence`, `report`, `history`).
2. **`src/components/HomeStep.tsx`**: Operational dashboard launcher with direct links to "New Inspection" and "View History".
3. **`src/components/NewInspectionStep.tsx`**: Metadata form collecting batch ID, supplier, procurement center, declared weight, and explicit `sampling_status = "SAMPLE_ONLY"`.
4. **`src/components/CaptureStep.tsx`**: Live WebRTC camera stream and image file upload picker with optimum lighting and framing guidelines.
5. **`src/components/AnalyzingStep.tsx`**: Step-state progress indicator executing pipeline calls (`/api/v1/inspect` -> `GET /api/v1/inspections/{id}/result`) without fake percentages. Discloses development model source.
6. **`src/components/ResultStep.tsx`**: Consumes `CanonicalInspectionResult`. Renders prototype grade, commercial quality score, defect distribution, review flags, and explanation factors. Handles `RETAKE_REQUIRED` and `MODEL_UNAVAILABLE` error states.
7. **`src/components/EvidenceStep.tsx`**: Interactive bounding box visualizer and per-onion defect inspector displaying probabilities, size metrics, and visual sub-region locations.
8. **`src/components/ReportStep.tsx`**: Digital Quality Inspection Report viewer consuming `GET /api/v1/inspections/{id}/report`.
9. **`src/components/HistoryStep.tsx`**: Stored inspection list and historical result viewer. Loads persisted canonical results without rerunning AI inference.

---

## 3. Frontend API Client Layer (`src/api/`)

- `src/api/client.ts`: Standard fetch wrapper managing error handling and `VITE_API_URL`.
- `src/api/inspections.ts`:
  - `uploadInspectionImage(file, centerId, batchId)`
  - `getCanonicalResult(inspectionId)`
  - `getInspectionHistory(batchId, limit)`
- `src/api/reports.ts`:
  - `getInspectionReport(inspectionId)`
  - `getInspectionReportHtmlUrl(inspectionId)`
  - `generateInspectionReport(inspectionId)`

---

## 4. Development Model Disclosure & Realism Constraints

- Whenever `model.source === "development_mock"`, the UI displays: `"Development inference — not production AI"`.
- All user-facing references to "certificate" have been removed and renamed to **"Digital Quality Inspection Report"**.
- Fake internal physical properties (e.g. moisture/firmness) and fake speedup claims have been completely scrubbed from frontend code.
