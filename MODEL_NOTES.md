# S.P.O.T. Model Card & Empirical Evaluation

Python-agnostic, measured documentation of every committed model artifact. Only
numbers that were actually computed from the committed checkpoints are reported as
**MEASURED**; everything else is labelled **ASSUMPTION / NOT VERIFIABLE**.

> **Status (2026-09-20):** rewritten after the Arena binary-model integration.
> The previous version of this file described only the legacy 4-class ONNX model.

---

## 1. Model inventory (committed artifacts)

| File | Task | Classes (measured from checkpoint) | Size (bytes) | Runtime role |
| :--- | :--- | :--- | ---: | :--- |
| `artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.pt` | Binary onion classification (whole image) | `{0: defective, 1: healthy}` | 3,186,754 (≈3.04 MB) | **Active.** Loaded by `backend/ai/yolo_cls_model.py` (PyTorch, CPU) for `/api/v1/inspect` and `/api/v1/ai/status`. |
| `artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.onnx` | Same binary model, ONNX runtime export | `{0: defective, 1: healthy}` | 6,160,819 (≈5.88 MB) | **Export-only.** No loader imports it; see §3. |
| `backend/models/onion_classifier.pt` | 4-class onion defect classification | `{0: disease, 1: healthy, 2: rotten, 3: sprouted}` | 3,191,042 (≈3.04 MB) | **Active (legacy flow).** Loaded by `backend/services/vision_service.py` for `/api/v1/analyze-onion`. |
| `backend/models/onion_classifier.onnx` | Same 4-class model, ONNX export | 4-class (see above) | 6,171,093 | **Export-only.** |
| `backend/models/onion_yolov8.onnx` | 4-class ONNX (copy of `onion_classifier.onnx`) | 4-class | 6,171,093 | **Export-only.** Referenced by `public/sw.js` (offline PWA asset) and `scripts/export_and_report.py`. |

MEASURED class names and sizes were read directly from each checkpoint at
evaluation time; the old `script-generated` sizes in `artifacts/ml/*.json` may
round differently.

### 1.1 The two inference flows (why both models still exist)

- **`/api/v1/inspect`** → `backend.ai` pipeline → `YOLO26ClassifierModel` →
  **`best.pt`** (binary). The product's primary inspection flow.
- **`/api/v1/analyze-onion`** → `backend.services.vision_service.AIVisionService` →
  **`onion_classifier.pt`** (4-class) with the OpenCV contour/heuristic pre-stage.
  The earlier PWA results flow; not wired to the new binary runner.

The binary model **replaces** the 4-class model for `/inspect` only. It does **not**
replace `/analyze-onion`, which still depends on the 4-class checkpoint. **Do not
delete `onion_classifier.pt`/`/analyze-onion`** without first migrating that flow —
no such migration is part of the Arena changes.

### 1.2 `experiment_results.json`

`artifacts/ml/experiments/yolo26n_cls_pilot_v1/experiment_results.json` is the
**training-run report** written by `scripts/train_yolo26_cls.py` on Antogravity's
machine. It records: train/val split **80/19** of a 99-image binary pilot dataset,
and reports **1.0 top-1 accuracy / macro-F1 on those 19 validation samples**
(9 healthy + 10 defective), plus a 22.44 ms average training-machine CPU latency.

> **These are validation-set metrics produced by the same image pool used to tune
> the model — NOT a held-out benchmark.** They are not evidence of real-world
> accuracy and are not used as such anywhere in this repository.

---

## 2. Training & evaluation data — exact split and leakage analysis

**The image files themselves are NOT committed to this repository.** Only annotation
records, manifests, and the resulting checkpoints are committed. Therefore the
training/validation images (and the held-out images used here) **cannot be
freely regenerated from this repo alone**.

- **Binary pilot (new model).** `scripts/create_pilot_100.py` +
  `scripts/prepare_yolo_cls_dataset.py` build
  `artifacts/ml/yolo_cls_dataset_v1/` (binary `train/` + `val/`) from the pilot
  annotations. `scripts/train_yolo26_cls.py` trained at **imgsz=224, seed 42** on
  **80 train / 19 val**; the `experiment_results.json` above is that run's output.
  - `artifacts/ml/defect_annotations/annotation_manifest.json` lists 1000 sampled
    IDs; only 4 annotation `records/*.json` are committed (peer side-effects only),
    of which 99 had a usable image at training time (`total_usable: 99`).
- **Legacy source archive (old model).** `artifacts/ml/dataset_version.json`
  documents the source archive `Onion Leaves and Bulb Dataset.zip` (SHA-256
  `cfd9e8b7…667d4`, 1,608,618,402 bytes), **16,300 images** (12,260 bulb,
  4,040 leaf; 8,220 healthy / 4,040 unhealthy bulbs).
  - `artifacts/ml/split_manifest.json` (`split_version: 1.0.0-grouped`, seed 42)
    partitions the **12,260 bulb images** into **8,580 train / 1,830 val /
    1,850 test**, excluding 4,040 out-of-scope leaf images, with 437
    leakage-group siblings kept together per group.
  - The **1,850 held-out test filenames** are enumerated in
    `artifacts/ml/split_manifest.json#/test_filenames`; the **1,830 val
    filenames** in `#/val_filenames`. Filenames are archive-relative paths
    (e.g. `New Onion - Copy/2. Bulb/1. Healthy/2. White Onion/1. Single/Onion08291.jpg`).

### 2.1 Held-out evaluation set used for the old-vs-new benchmark

The benchmark (see §4) uses **independently gathered public onion-bulb images that
are absent from this repository** and therefore **outside both models' training and
validation pools**:

- `artifacts/ml/v1_eval/manifest.csv` — the ground-truth manifest
  (`filename`, `subdir_note`, `class`, `source_note`, `checksum_sha256`),
  generated by `scripts/make_eval_manifest.py` with computed SHA-256. The images
  themselves are **not committed** (per repo size conventions); they are placed in
  `artifacts/ml/v1_eval/images/` on the evaluation machine and verified by checksum
  before scoring.
- Labels are **two-class** (`healthy` / `defective`). For the 4-class model the
  benchmark maps `{disease, rotten, sprouted} → defective` and scores the
  top-1 prediction.
- To (re)generate the manifest from a labelled local directory (which also
  recomputes the checksums): `scripts/make_eval_manifest.py`.
- **No image in the manifest appears in `split_manifest.json` (legacy) or in any
  committed pilot record.** This is asserted by `scripts/evaluate_models.py`
  (leakage check) and must pass before metrics print.

Leakage-prevention rules, enforced by the script:
1. Every eval image is checked against legacy `train/val/test` filenames and pilot
   record IDs; any overlap aborts.
2. Every eval image label must be `healthy` or `defective`; unknown labels are
   errors, not predictions.
3. Scoring is computed at runtime from the images actually present; **no results
   are hard-coded**.

---

## 3. ONNX artifacts: why export-only

Although this repo historically ran an ONNX classifier in the mobile PWA
(`public/sw.js` references `onion_yolov8.onnx`, and the original frontend had an
ONNX WebAssembly inference worker), **no backend module loads `best.onnx` or
`onion_classifier.onnx` at runtime** (verified by static analysis over
`backend/**/*.py`). The `/inspect` flow uses PyTorch (`best.pt`); `/analyze-onion`
uses PyTorch (`onion_classifier.pt`).

Measured ONNX metadata (read directly from the exported files):

| File | Input shape | Output shape | Class labels (metadata) |
| :--- | :--- | :--- | :--- |
| `best.onnx` | `(1,3,224,224)` | `(1,2)` | `{0: defective, 1: healthy}` |
| `onion_classifier.onnx` | `(1,3,224,224)` | `(1,4)` | `{0: disease, 1: healthy, 2: rotten, 3: sprouted}` |
| `onion_yolov8.onnx` | `(1,3,224,224)` | `(1,4)` | 4-class |

**Decision:** the ONNX artifacts remain **export artifacts** for
deployment-portability/offline-PWA prototyping. They are *not* wired into the
current server inference path: on the current CPU-only deployment the PyTorch
checkpoint already serves `/inspect`, and there is no profiling evidence that
moving to ONNX Runtime would change latency meaningfully enough to justify a
second runtime path + its packaging cost. If a future deployment targets
ONNX-the-only-runtime (e.g. no PyTorch in the image), `best.onnx` has metadata and
I/O consistent with serving `224×224` classification directly — but that integration
does not exist yet and is **not claimed** here.

---

## 4. Old vs new — measured comparison (same held-out images, CPU)

The comparison below is **measured on the 7-image exploratory smoke set only** and is
reported for completeness. It is **preliminary and must not be treated as a
generalization claim** — 7 images is not a statistically meaningful sample. A proper
held-out benchmark with a larger manifest is produced by
`scripts/evaluate_models.py` (see §5), and its output is the authoritative number.

| Metric | Legacy 4-class (`onion_classifier.pt`) | Arena binary (`best.pt`) |
| :--- | ---: | ---: |
| Classes | disease / healthy / rotten / sprouted | defective / healthy |
| Accuracy (7 images) | 5 / 7 = **0.714** | 6 / 7 = **0.857** |
| Healthy correctly classified | 4 / 4 | 3 / 4 (1 fresh-on-table → defective) |
| Defective correctly classified | 0 / 3 | 3 / 3 |
| Confusion (healthy→healthy, healthy→defective) | 4, 0 | 3, 1 |
| Confusion (defective→defective, defective→healthy) | 0, 3 (collapsed to healthy) | 3, 0 |
| CPU inference latency, mean | 34.21 ms | 20.03 ms |
| CPU inference latency, p95 | 105.7 ms | 46.48 ms |
| Model size | 3.04 MB | 3.04 MB |

MEASURED, CPU-only, `imgsz=224`, cold-per-image `predict()` latency. The old 4-class
model's poor defective recall is consistent with its own (legacy) validation note
below — it collapses most bulbs to `healthy`.

### 4.1 Legacy model validation metrics (archive-reported, not re-verified here)

The following table is copied from the archive's own training notes (the 4-class
ONNX evaluation). The source images are absent from this repo, so these numbers
**cannot be independently re-verified from the current repository**:

| Class | Samples | Precision | Recall | F1 |
| :--- | :--- | :--- | :--- | :--- |
| disease | 202 | 0.0000 | 0.0000 | 0.0000 |
| healthy | 697 | 0.6342 | 1.0000 | 0.7762 |
| rotten | 109 | 0.0000 | 0.0000 | 0.0000 |
| sprouted | 93 | 1.0000 | 0.0215 | 0.0421 |
| **Overall top-1** | 1101 | — | **63.49%** | — |

### 4.2 New model pilot validation metrics (Antogravity training run)

From `experiment_results.json` (19 val images — **validation set, not held-out**):

- Top-1 **1.0**, macro precision/recall/F1 **1.0**; healthy 9/9, defective 10/10.
- Train machine latencies: min 8.53 / avg 22.44 / max 75.02 ms.
- **Caveat (recorded in the file):** small pilot (80 train), single annotator,
  no inter-annotator agreement, CPU training. DO NOT cite as real-world accuracy.

---

## 5. Reproducing the benchmark later

```bash
# From a checkout of this branch, with a venv that has requirements.txt installed:
.venv/bin/python scripts/evaluate_models.py --images dir/with/heldout/images \
  --manifest artifacts/ml/v1_eval/manifest.csv \
  --out artifacts/ml/v1_eval/results.json
```

The script:
1. Verifies each manifest image exists and its SHA-256 matches (protects against
   swapped/relabelled inputs).
2. Runs the **leakage check** against legacy split manifests and pilot records.
3. Scores **both** `best.pt` (binary) and `onion_classifier.pt` (4-class, mapped
   to binary) on the **same** images.
4. Prints a factual comparison: per-model accuracy, per-class precision/recall/F1,
   confusion matrix, healthy/defective recall, false positives/false negatives,
   mean & p95 CPU latency, and on-disk size.
5. Writes `--out` JSON. **Nothing is hard-coded**; metrics are computed at runtime
   from the images actually present.

---

## 6. Known limitations

- Binary classification **cannot** distinguish damage / rot / sprouting —
  `DefectProbabilities.rot` and `.sprouting` are always `0.0` on the `/inspect`
  flow; all defect mass is mapped to `damage`. This is an explicit design
  contract, not a defect.
- No inter-annotator agreement (IAA) is recorded for the pilot labels.
- No physical size estimation exists (`SizeEstimate.status == UNAVAILABLE`); the
  graded **undersized** bucket requires an `<45 mm` optical calibration that is
  not implemented.
- Model performance beyond the 7-image smoke set and the 19-image pilot
  validation set is **not verifiable from the current repository**.
