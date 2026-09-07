# S.P.O.T. PHASE 6 FRONTEND AUDIT

**Date**: September 4, 2026  
**Status**: AUDITED  

---

## 1. Existing Frontend Stack & Tech Audit

- **Framework**: React 18 + Vite + TypeScript.
- **Styling**: Tailwind CSS with custom theme colors (`#F7F5F0` warm background, `#0F281E` dark forest text, `#2D5A27` green accents).
- **Internationalization**: `react-i18n` (EN, HI, TA, MR).
- **Icons**: `lucide-react`.

---

## 2. Existing Component & Screen Structure

- `src/App.tsx`: Main navigation container managing active step state (`language`, `camera`, `results`, `history`, `admin`).
- `src/components/CameraStep.tsx`: Web camera stream capture & gallery image file picker.
- `src/components/ResultsStep.tsx`: Inspection outcome display. Currently contains legacy hardcoded fallback metrics, benchmark logs, and fake moisture/firmness properties.
- `src/components/HistoryStep.tsx`: Inspection history list view.
- `src/components/BoundingBoxCanvas.tsx`: HTML5 Canvas overlay for bounding boxes. Currently contains hardcoded fallback bounding boxes when empty.
- `src/components/VerifyStep.tsx`: QR verification / digital quality inspection report lookup screen.

---

## 3. Legacy / Hardcoded Code & Discrepancy Audit

1. **Terminology Violations**:
   - `ResultsStep.tsx` and `VerifyStep.tsx` refer to "Certificate", "Quality Certificate", or "Certificate Verification".
   - MUST be renamed across all UI screens to **"Digital Quality Inspection Report"** / **"Digital Quality Report"**.
2. **Fake Physical Metrics & Benchmarks**:
   - `types.ts` contains `moisture`, `firmness`, `shelfLife`, `edgeLatencyMs`, `serverLatencyMs`, `benchmarkLog`, "4.6x faster".
   - Physical internal rot or internal moisture cannot be measured by ordinary RGB surface imaging and must be completely removed/isolated.
3. **Hardcoded Fallback Data**:
   - `BoundingBoxCanvas.tsx` generates hardcoded fallback boxes (`BOX-01`, `BOX-02`, `BOX-03`).
   - `JUDGE_DEMO_SAMPLES` in `src/data/judgeSamples.ts` contains hardcoded static results.
4. **Backend API Integration Gap**:
   - The frontend currently performs client-side heuristic processing in `CameraStep.tsx` or uses mock `ScanResult` structs instead of consuming the canonical backend contract `GET /api/v1/inspections/{id}/result`.

---

## 4. Phase 6 Refactoring Plan

1. **Frontend API Client (`src/api/`)**:
   - `src/api/client.ts`: Base fetch wrapper supporting `VITE_API_URL` (default `http://localhost:8000`).
   - `src/api/inspections.ts`: Calls `/api/v1/inspect`, `/api/v1/inspections/{id}/result`, `/api/v1/inspections`.
   - `src/api/reports.ts`: Calls `/api/v1/inspections/{id}/report` (JSON/HTML).
2. **Types (`src/types.ts`)**:
   - Import backend contract schemas (`CanonicalInspectionResult`, `OnionResult`, `BatchStatistics`, `GradingPresentation`, `Explanation`, `InspectionReport`).
3. **Refactored Screens**:
   - `/home` -> `HomeStep.tsx`
   - `/inspection/new` -> `NewInspectionStep.tsx`
   - `/inspection/:id/capture` -> `CaptureStep.tsx`
   - `/inspection/:id/analyzing` -> `AnalyzingStep.tsx`
   - `/inspection/:id/result` -> `ResultStep.tsx`
   - `/inspection/:id/evidence` -> `EvidenceStep.tsx`
   - `/inspection/:id/report` -> `ReportStep.tsx`
   - `/history` & `/history/:id` -> `HistoryStep.tsx` & `HistoryDetailStep.tsx`
4. **Strict Realism & Terminology Compliance**:
   - Rename all user-facing occurrences of "Certificate" to "Digital Quality Inspection Report".
   - Highlight model source (`Development Mock Pipeline` / `development_mock`).
   - Display `RETAKE_REQUIRED`, `REVIEW_REQUIRED`, and `MODEL_UNAVAILABLE` error states explicitly without fake fallbacks.
