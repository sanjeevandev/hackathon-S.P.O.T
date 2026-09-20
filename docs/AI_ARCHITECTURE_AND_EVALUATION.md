# S.P.O.T. — AI Architecture & Evaluation

Single source of truth for the AI pipeline's current architecture, model
inventory, confidence/review handling, held-out evaluation methodology, and
measured results.

**Distinction rule (applies to this whole document):** numbers reported as
*MEASURED* were computed from the committed checkpoints/scripts in this repo;
anything not independently verified is labelled *NOT VERIFIABLE* or
*ASSUMPTION*.

---

## 1. Current AI architecture

Two independent PyTorch classification flows coexist:

```
POST /api/v1/inspect            POST /api/v1/analyze-onion
        │                               │
        ▼                               ▼
backend.pipeline.InspectionPipeline  backend.services.vision_service.AIVisionService
  (Quality Gate → VisionModel)         (HSV heuristic → OpenCV contours → YOLO)
        │                               │
        ▼                               ▼
backend.ai.yolo_cls_model.           backend/models/onion_classifier.pt
YOLO26ClassifierModel                (4-class: disease, healthy,
 (binary: defective, healthy)         rotten, sprouted)
        │
        ▼
artifacts/ml/experiments/
yolo26n_cls_pilot_v1/weights/best.pt
```

| Flow | Model | Classes (measured from checkpoint) | Code path |
| :--- | :--- | :--- | :--- |
| `/api/v1/inspect` | Arena binary YOLO26n-cls | `{0: defective, 1: healthy}` | `backend/ai/yolo_cls_model.py` (via `backend/ai/registry.py` / `backend/pipeline/pipeline.py`) |
| `/api/v1/analyze-onion` | Legacy 4-class YOLO | `{0: disease, 1: healthy, 2: rotten, 3: sprouted}` | `backend/services/vision_service.py` |

`GET /api/v1/ai/status` reports which model the registry resolves
(`YOLO26n-cls-pilot`, `source: real_model` in development and production).

### Confidence → review (single source of truth, no extra status)

Low-confidence handling uses the **pre-existing grading path** end to end:

1. `YOLO26ClassifierModel.analyze` returns the model's own top-1 probability in
   `VisionResult.overall_confidence` (`probs.top1conf`), always
   `status=SUCCESS` for a valid binary prediction.
2. `backend/main.py` builds a `GradingRequest(inspection_confidence=overall_confidence)`.
3. `GradingPolicyEngine.evaluate` compares that against the active profile's
   `confidence_min_threshold` (**default 0.70**) and flags
   `review_status=REVIEW_REQUIRED` with reason
   `"Inspection confidence (...) is below profile minimum threshold (...)"`.
4. The review status is persisted via `InspectionRepository` and returned through
   the canonical inspection result (`/api/v1/inspections/{id}/result`), where the
   frontend surfaces it.

There is **no additional `LOW_CONFIDENCE` status** on `VisionResult` or
`PipelineResult` — the grading engine is the single authority for the threshold
and the review decision. This is covered by tests
(`tests/test_grading_engine.py::test_low_confidence_triggers_review_required_with_reason`
and `tests/test_yolo26_classifier.py::test_low_confidence_flows_to_grading_review_required`).

### Failure handling (hardened, no mock fallback)

- Missing checkpoint → `RuntimeError`; registry never advertises the model.
- Non-binary checkpoint (e.g. a 4-class placed at the binary path) → `ValueError`
  at load; the registry skips the model entirely (validated once per process).
- Unreadable image bytes / inference exception → `VisionResult.status=ERROR` with
  an `error_message`.
- Empty classification / unknown class → `NO_VALID_DETECTIONS`.
- The pipeline maps load-time `ValueError` to `MODEL_UNAVAILABLE`.
- **The production path never falls back to `DevelopmentMockVisionModel`**: the
  mock is only reachable in development when no real model is available, and its
  results are always labelled `source=development_mock`.

---

## 2. Model inventory & purposes

| File | Purpose | Status |
| :--- | :--- | :--- |
| `artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.pt` | Binary classifier, active for `/inspect` and `/ai/status`. | **Runtime, active** |
| `artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.onnx` | ONNX export of the same binary model. | **Export-only** (see §5) |
| `artifacts/ml/experiments/yolo26n_cls_pilot_v1/experiment_results.json` | Training-run report (split, training time, validation metrics). | Record; **not** real-world evidence |
| `backend/models/onion_classifier.pt` | 4-class classifier, active for `/analyze-onion`. | **Runtime, active** |
| `backend/models/onion_classifier.onnx` | ONNX export of the 4-class model. | **Export-only** |
| `backend/models/onion_yolov8.onnx` | Copy of the 4-class ONNX, referenced by `public/sw.js` + export scripts. | **Export-only** |

Sizes (bytes on disk, measured): `best.pt` 3,186,754 · `best.onnx` 6,160,819 ·
`onion_classifier.pt` 3,191,042 · `onion_classifier.onnx` 6,171,093 ·
`onion_yolov8.onnx` 6,171,093.

---

## 3. Datasets

- **Binary pilot (Arena model).** `scripts/create_pilot_100.py` +
  `scripts/prepare_yolo_cls_dataset.py` build `artifacts/ml/yolo_cls_dataset_v1/`
  (binary `train/`+`val/`) from the pilot annotations; `scripts/train_yolo26_cls.py`
  trained at `imgsz=224, seed=42` on **80 train / 19 val** of a 99-image pool.
  Recorded in `experiment_results.json`. Image files are **not committed**.
- **Legacy archive.** `artifacts/ml/dataset_version.json` documents the source
  archive (`Onion Leaves and Bulb Dataset.zip`, SHA-256 `cfd9e8b7…667d4`,
  16,300 images); `artifacts/ml/split_manifest.json` partitions 12,260 bulbs into
  **8,580 train / 1,830 val / 1,850 test** (seed 42, 4,040 leaf excluded, 437
  leakage groups held together). Images are **not committed**.

---

## 4. Held-out evaluation methodology

- **Fixed set:** `evaluation/v1_eval/` — **committed** images
  (`images/healthy/`, `images/defective/`) + ground-truth `manifest.csv`
  (`filename`, `subdir_note`, `scene`, `class`, `source_note`, `checksum_sha256`).
  The images are **15 public web onion photos not present in either model's
  training/validation pools** (10 healthy, 5 defective). Labels are
  **search-query / source-page-title assigned at collection time** — *not
  pixel-annotated*, no inter-annotator agreement. This is the stated limitation,
  not hidden.
- **Scene grouping (metadata only, never used for scoring):** `single_bulb` (9
  images: 4 healthy + 5 defective) vs `multi_bulb_scene` (6 images, all healthy).
  Both models are trained/documented for **single-bulb** classification; accuracy
  is reported for the full set *and* per subgroup without filtering or
  relabelling. (ASSUMPTION, documented — not a metric.)
- **Binary-collapse for the old model:** its 4 output classes are mapped
  `{disease, rotten, sprouted} → defective`, `healthy → healthy`, scored on the
  top-1 prediction — exactly the same reduction applied to the new model.
- **Leakage check (enforced by the script):** every eval image is checked against
  `split_manifest.json` train/val/test filenames and pilot annotation IDs; any
  overlap aborts. Every label must be `healthy`/`defective` and every SHA-256 must
  match the on-disk bytes. **Result: PASS.**
- **No cherry-picking:** every image in the manifest is scored regardless of how
  it affects either model; nothing is re-run to favor Arena.

### Reproduction

```bash
.venv/bin/python scripts/evaluate_models.py \
    --images evaluation/v1_eval/images \
    --manifest evaluation/v1_eval/manifest.csv \
    --out evaluation/v1_eval/results.json
```

---

## 5. Measured benchmark (15-image held-out set, CPU, imgsz=224)

MEASURED 2026-09-20 with `scripts/evaluate_models.py` on the committed set.
**Arena does NOT win overall — this is reported as-is, not massaged.**

| Metric | Legacy 4-class | Arena binary |
| :--- | ---: | ---: |
| Accuracy (15) | **0.7333** | **0.5333** |
| Healthy precision | 0.75 | 1.00 |
| Healthy recall | **0.90** | 0.30 |
| Defective precision | 0.6667 | 0.4167 |
| Defective recall | 0.40 | **1.00** |
| F1 (healthy) | 0.8182 | 0.4615 |
| F1 (defective) | 0.50 | 0.5882 |
| FP (defective class) | 1 | 7 |
| FN (defective class) | 3 | 0 |
| Mean latency | 24.83 ms | 23.95 ms |
| P95 latency | 61.46 ms | 55.0 ms |
| Model size | 3.04 MB | 3.04 MB |

Confusion (rows = ground truth; columns = predicted):

| Model | healthy→healthy | healthy→defective | defective→healthy | defective→defective |
| :--- | ---: | ---: | ---: | ---: |
| Legacy 4-class | 9 | 1 | 3 | 2 |
| Arena binary | 3 | 7 | 0 | 5 |

**Subgroup accuracy (single-bulb, n=9 — the models' documented task):**
Arena **0.8889** (8/9) vs legacy **0.6667** (6/9) — Arena is *more* accurate
single-bulb.
**Subgroup accuracy (multi-bulb scenes, n=6 healthy-only):** legacy **0.8333**
(5/6) vs Arena **0.0** (0/6) — the binary model labels every multi-bulb scene
defective, which is what drags its overall accuracy down.

(These subgroup numbers are computed by the script from per-image results; they
are measured, not hand-written.)

### Reading of the result (facts, not spin)

- Arena's **defective recall is 1.0** (it never misses rot), and on the
  **single-bulb** subset — the documented task — Arena is actually *more*
  accurate than legacy (0.8889 vs 0.6667).
- But Arena over-predicts `defective` on fresh, **multi-bulb** scenes
  (7 false positives total, 6 of them pile/bunch shots, 1 fresh single bulb),
  collapsing its overall accuracy to 0.5333.
- Legacy is more accurate overall (0.7333) but misses 3 of 5 rotten onions
  (defective recall 0.40).
- These are genuine, opposing trade-offs on a **15-image, weakly-labelled** set.
  Neither number is a robust real-world accuracy estimate; do not generalize
  from it.

---

## 6. ONNX status (`best.onnx`)

MEASURED 2026-09-20: using ultralytics' own classification preprocessing
(`classify_transforms(size=224)`: PIL RGB → resize shortest-edge 224 (bilinear) →
center-crop 224×224 → `ToTensor` [0,1] → no normalization; defaults
`mean=(0,0,0)`, `std=(1,1,1)`), `best.onnx` produces **bit-identical softmax**
outputs to `best.pt` on all 15 held-out images (`max|prob diff| = 0.000000`).

- **ONNX input:** `images` `[1,3,224,224] float32` → **output:** `output0` `[1,2]`.
- **Correct preprocessing is load-bearing:** feeding a naively distorted
  (non-aspect-preserving) resize causes the ONNX top-1 to disagree with PyTorch on
  2 of 7 exploratory images. This is an artifact of preprocessing, not of the
  export.

**Deployment decision:** `best.onnx` is a **verified, faithful export** but
remains **export-only**. The server `/inspect` path runs PyTorch (`best.pt`); no
ONNX Runtime loader is wired in, and there is no measured operational need to add
one on the current CPU-only deployment. The export is retained for
deployment-portability (mobile/edge where PyTorch is too heavy), documented, not
forced into the application.

---

## 7. Known limitations

1. Held-out set is **15 images, weakly labelled** (query/title assignment, no
   pixel annotation, no IAA). Results are directional, not production evidence.
2. Binary model cannot distinguish damage/rot/sprouting; all defect mass maps to
   `damage` (`rot`/`sprouting` always 0.0 on the `/inspect` path).
3. No size estimation exists (`SizeEstimate.status=UNAVAILABLE`); the graded
   "undersized" bucket needs `<45 mm` optical calibration that is not implemented.
4. Pilot training data (99 images) and the legacy archive images are absent from
   the repo, so **training/validation metrics cannot be independently reproduced
   here** (`experiment_results.json` 1.0 on 19 val images is a validation number,
   not real-world evidence).
5. `/analyze-onion` (4-class) flow is preserved but not modernized.

---

## 8. Exact reproduction commands

```bash
# deps
python -m venv .venv && .venv/bin/pip install -r requirements.txt

# benchmarks: held-out old-vs-new
.venv/bin/python scripts/evaluate_models.py \
    --images evaluation/v1_eval/images \
    --manifest evaluation/v1_eval/manifest.csv \
    --out evaluation/v1_eval/results.json

# (re)generate a manifest from a labelled directory
.venv/bin/python scripts/make_eval_manifest.py \
    --images evaluation/v1_eval/images \
    --manifest evaluation/v1_eval/manifest.csv \
    --mode dirs --source-note "..."

# tests / build / server
.venv/bin/python -m pytest -q -rs
npm run build
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Companion docs:** `MODEL_NOTES.md` (model card), `docs/AI_STATUS_CONTRACT.md`
((status contract & confidence flow).
