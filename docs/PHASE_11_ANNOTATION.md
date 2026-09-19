# S.P.O.T. Phase 11 Human Defect Annotation Infrastructure Report

## 1. Executive Overview

Phase 11 establishes the end-to-end infrastructure, annotation tool, schema validator, double-annotation engine, and quality verification suite required for fine-grained multi-label onion defect supervision.

### Core Architectural Principles:
1. **No Invented Defect Labels**: Ground-truth labels for `Damaged`, `Rotten`, `Sprouted`, and `Undersized` are derived **exclusively** through human expert annotation.
2. **Multi-Label Paradigm**: Independent binary flags (`damage`, `rot`, `sprout`) + size assessment (`undersized`).
3. **Preservation of Baseline**: Baseline ResNet18 (`SPOT-Baseline-001`) remains isolated in `backend/ai/experiments/`. Production `DevelopmentMockVisionModel` remains active and unchanged.
4. **Leakage-Group Preserved Subset**: A 1,000-image stratified annotation subset is curated from the 12,260 bulb dataset preserving all capture clusters.

---

## 2. Stratified 1,000-Image Annotation Pool

| Stratum Dimension | Category | Image Count | % of Pool | Cluster Count |
| :--- | :--- | :--- | :--- | :--- |
| **Bulb Color** | Red Onion | 500 | 50.0% | 184 clusters |
| | White Onion | 500 | 50.0% | 182 clusters |
| **Arrangement** | Single Bulb | 500 | 50.0% | 210 clusters |
| | Multiple Bulbs | 500 | 50.0% | 156 clusters |
| **Audit Health Tag** | Healthy | 500 | 50.0% | 200 clusters |
| | Unhealthy | 500 | 50.0% | 166 clusters |

---

## 3. Data Quality Engine & Contradiction Resolution

The validation engine (`backend/ai/annotation/validator.py`) runs automated checks on every recorded annotation:

1. **Contradiction Flagging**:
   - `healthy = true` AND (`damage = true` OR `rot = true` OR `sprout = true`): Automatically flagged as `NEEDS_REVIEW`.
2. **Size Reference Check**:
   - If `size_reference_available = false`, sets `estimated_diameter_mm = null` and `undersized_status = "UNAVAILABLE"`.
3. **Bounding Box Coordinate Validation**:
   - Verifies bounding box coordinates $[x_1, y_1, x_2, y_2]$ satisfy $0 \le x_1 < x_2 \le 1.0$ and $0 \le y_1 < y_2 \le 1.0$.

---

## 4. Annotation Artifacts Summary

All outputs are preserved in `artifacts/ml/defect_annotations/`:

- `annotation_manifest.json`: Manifest of 1,000 stratified target images & metadata.
- `annotation_distribution.json`: Multi-label defect statistics.
- `agreement_report.json`: Inter-annotator agreement metrics ($\kappa$ and % agreement) on 100 double-annotated images.
- `quality_report.json`: Quality check summary and flagged contradiction records.
