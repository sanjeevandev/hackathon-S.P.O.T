# S.P.O.T. — Held-out Evaluation & Benchmark Methodology

Companion to `MODEL_NOTES.md`. This file defines **how** the old vs new model
comparison is produced and reproduced. It records no hard-coded benchmark results —
metrics are always computed at runtime by `scripts/evaluate_models.py`.

## 1. Why a held-out set (and why it is not committed)

The Arena binary model was tuned on a 99-image pilot pool (80 train / 19 val),
and the legacy 4-class model on the `Onion Leaves and Bulb Dataset` archive.
Neither pool's image files are present in this repository.

A valid comparison therefore requires images that are in **neither** pool. The
evaluation set is *externally gathered* and deliberately **not committed** (repo
size conventions); only its ground-truth manifest (labels + SHA-256) is committed,
so results are reproducible on a machine that has the images.

## 2. The two models compared (identical images, identical scoring)

| Model checkpoint | Classes | Serves | Binary mapping used for scoring |
| :--- | :--- | :--- | :--- |
| `artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.pt` | `{0: defective, 1: healthy}` | `/api/v1/inspect` | native |
| `backend/models/onion_classifier.pt` | `{0: disease, 1: healthy, 2: rotten, 3: sprouted}` | `/api/v1/analyze-onion` | `{disease, rotten, sprouted} → defective` |

Both are scored on the *same* held-out images at `imgsz=224` on CPU, top-1
prediction, with ground truth reduced to `healthy` / `defective`.

## 3. Held-out set layout

```
artifacts/ml/v1_eval/
  manifest.csv         # committed: filename, subdir_note, class, source_note, checksum_sha256
  images/              # NOT committed: the actual images (place here on the eval machine)
```

`manifest.csv` is produced by `scripts/make_eval_manifest.py` from a labelled
directory:

- `images/healthy/*` and `images/defective/*` (subdirectory mode), or
- flat files prefixed `healthy_` / `defective_` (flat mode).

## 4. Leakage prevention (enforced, aborts on violation)

Before any scoring, `scripts/evaluate_models.py` asserts that **no** evaluation
image matches committed identifiers:

1. basename/path against `artifacts/ml/split_manifest.json`
   `train/val/test/leaf_filenames` (the legacy archive split);
2. stem/basename against the pilot annotation manifest (`image_id`s) and the
   committed `defect_annotations/records/*.json`.
3. Every ground-truth label must be exactly `healthy` or `defective`; anything
   else is an error, never a prediction.
4. Every manifest row's SHA-256 must match the image actually on disk before
   scoring (protects against swapped/relabelled inputs).

## 5. Reproducing the benchmark

```bash
# 1. Prepare labels + checksums from your held-out folder (generates only, never scores):
.venv/bin/python scripts/make_eval_manifest.py \
    --images /path/to/heldout \
    --manifest artifacts/ml/v1_eval/manifest.csv \
    --mode dirs \
    --source-note "independently gathered public onion-bulb images"

# 2. Score BOTH models on the SAME images:
.venv/bin/python scripts/evaluate_models.py \
    --images /path/to/heldout \
    --manifest artifacts/ml/v1_eval/manifest.csv \
    --out artifacts/ml/v1_eval/results.json
```

`scripts/evaluate_models.py` prints and writes, per model: accuracy, per-class
precision/recall/F1, confusion matrix, healthy recall, defective recall, false
positives, false negatives, mean & p95 CPU latency, and on-disk size. Nothing is
hard-coded; if the images or manifest change, the output changes.

## 6. Interpretation rules

- The **7-image exploratory smoke set** (`/home/user/eval-imgs`) is **preliminary
  only**: it is a smoke test for the harness, not a generalization claim.
- The **19-image pilot validation** (from `experiment_results.json`) is a
  **validation-set** number, not held-out evidence.
- Treat both accordingly; the labelled held-out manifest is the authoritative
  evaluation once populated with images.
