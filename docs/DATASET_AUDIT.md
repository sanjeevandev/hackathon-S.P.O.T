# DATASET AUDIT & PRE-GATE SPECIFICATION — S.P.O.T.

**Date**: September 4, 2026  
**Status**: PRE-GATE AUDIT (DATASET_NOT_AVAILABLE)  
**Problem Statement**: SIH 2026 PS 26031 — AI-Based Mobile Application for Onion Quality Assessment & Grading  

---

## 1. Dataset Location & Availability Status

- **Configured Dataset Directory**: `/home/sanjeeva/ONION HACKATHON/backend/dataset` (Configurable via `SPOT_DATASET_DIR` or `--dataset-dir`).
- **Audit Execution Result**:
  - `status`: `DATASET_NOT_AVAILABLE`
  - `total_images`: `0`
  - `message`: Target directory exists on local disk but contains no image files (`.jpg`, `.png`, `.jpeg`, `.webp`).
- **Policy**: Per Phase 2 Pre-Gate rules, we **do not fabricate** dataset statistics or accuracy numbers. The dataset audit tool `scripts/audit_dataset.py` has been built and verified. Once the ~16,000-image dataset is mounted, the automated audit script will execute the full statistical inventory.

---

## 2. Expected Dataset Directory Structure & Annotation Formats

To run the automated audit, the dataset should be organized in one of the following standard layouts:

### Option A: YOLO Format (Recommended for Object Detection)
```
dataset/
├── dataset.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

### Option B: COCO Format (Recommended for Instance Segmentation)
```
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── annotations/
    ├── instances_train.json
    ├── instances_val.json
    └── instances_test.json
```

---

## 3. Command to Execute Automated Dataset Audit

Once the dataset files are mounted, execute:

```bash
# Using environment variable
export SPOT_DATASET_DIR=/path/to/16k_onion_dataset
python3 scripts/audit_dataset.py

# OR using explicit CLI parameter
python3 scripts/audit_dataset.py --dataset-dir /path/to/16k_onion_dataset --output-dir artifacts/dataset_audit
```

This generates:
- `artifacts/dataset_audit/dataset_summary.json`
- `artifacts/dataset_audit/dataset_summary.csv`

---

## 4. Defect Taxonomy Mapping Protocol

When annotations are analyzed, dataset class labels must be mapped to the official SIH 2026 visible defect taxonomy:

| Raw Dataset Class / Terminology | Official S.P.O.T. Taxonomy Class | Processing Type |
| :--- | :--- | :--- |
| `grade_a` / `healthy` / `fresh` | **Healthy (Grade A Candidate)** | Object Detection |
| `damaged` / `crack` / `bruise` | **Damaged** | Multi-Label Defect Probability |
| `rotten` / `rot` / `fungus` | **Rotten** | Multi-Label Defect Probability |
| `sprouted` / `shoot` / `neck_sprout` | **Sprouted** | Multi-Label Defect Probability |
| `undersized` / `<45mm` | **Undersized** | Calibrated Diameter Measurement (or `SIZE_ESTIMATE_UNAVAILABLE`) |

---

## 5. Multi-Onion Analysis Protocol

The audit tool calculates:
- Images containing single onions vs multiple onions vs overlapping lots.
- Distribution of onion counts per image (min, max, median, mean).
- Average bounding box area relative to image frame size (coverage %).

---

## 6. Leakage-Resistant Data Split Strategy

Random 70/15/15 splitting across images is strictly forbidden to prevent data leakage (visually identical onions from the same capture session appearing in both training and test sets).

**Group-Based Partitioning Rules**:
1. **Primary Grouping Key**: Capture session / farm origin / supplier batch ID.
2. **Perceptual Hashing**: Images belonging to the same `dhash` near-duplicate cluster must reside within the **same** partition (Train, Val, or Test).
3. **Partition Allocation**:
   - **Train Set (70%)**: Model weight optimization.
   - **Validation Set (15%)**: Hyperparameter tuning & early stopping.
   - **Test Set (15%)**: Final benchmark evaluation report (held-out, never used during training).

---

## 7. Model Task Decision Framework

Model architecture selection will be driven by the annotation format identified during dataset execution:

| Annotation Support Found | Recommended Vision Task | Justification |
| :--- | :--- | :--- |
| Bounding Boxes (`YOLO_TXT` / `VOC_XML`) | **Object Detection & Multi-Label Defect Scoring** | Enables locating individual onion bulbs and estimating spatial defect loci. |
| Polygon Masks (`COCO_JSON`) | **Instance Segmentation (YOLO-Seg)** | Provides exact pixel boundaries for bulb area and diameter estimation without background noise. |
| Folder-Based Classification | **Multi-Label Image Classification** | Whole-frame lot classification. |

---

## 8. Candidate Model Benchmark Plan

Candidate models evaluated in Phase 2:
1. **YOLO11 Small / Nano (`yolo11n`, `yolo11s`)**
2. **YOLO26 Small / Nano**
3. **Lightweight Segmentation Variants (YOLOv8-Seg / YOLO11-Seg)**

### Benchmark Metrics Protocol
All models will be evaluated under identical conditions on the **held-out Test Set**:
- **Precision (P)** & **Recall (R)**
- **mAP@50** & **mAP@50-95**
- **F1 Score** per class
- **Confusion Matrix**
- **Inference Latency** (measured in ms on target CPU/Edge device)
- **Model Binary Size** (MB)

No model will be declared "best" prior to empirical benchmark execution.

---

## 9. Reality Check & Anti-Fabrication Mandate

- **No Transferred Claims**: Academic research accuracy papers or published YOLO benchmarks cannot be cited as S.P.O.T. system accuracy.
- **System Accuracy Formula**:
  $$\text{S.P.O.T. Accuracy} = \text{Our Dataset} + \text{Our Held-Out Test Set} + \text{Our Evaluation Protocol}$$

---

## 10. Existing Fake AI Cleanup Audit Report

An audit for legacy fabricated AI code revealed:

1. **`backend/services/vision_service.py`**:
   - Contains `import random` and `rnd = random.Random(seed)` generating fake bounding boxes.
   - *Status*: Superseded by `InspectionPipeline` in `backend/main.py`. The legacy file remains uncalled by API routes.
2. **`backend/export_onnx_model.py`**:
   - Generates fake binary bytes (`os.urandom(65536)`) disguised as an ONNX model export.
   - *Status*: Standalone script, not called in production API paths.
3. **`src/utils/onnxInferenceEngine.ts` & `src/components/ResultsStep.tsx`**:
   - Contain hardcoded speedup strings (`"🚀 Speedup: 4.6x Faster"`).
   - *Status*: Client-side UI mock leftovers. Will be aligned during Phase 9 (Mobile UX).
