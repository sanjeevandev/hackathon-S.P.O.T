# S.P.O.T. — Training Handoff for Antogravity's Machine

**Date:** 2026-09-19
**Goal:** produce the real `YOLO26n-cls` **binary** checkpoint (Healthy/Defective)
plus its ONNX export and honest metrics, so integration can be verified.

## Why this can't run in the sandbox
The Arena sandbox has no GPU (2 CPU, ~3.8 GB RAM) and the Roboflow dataset is
network-blocked there. The onion dataset (`artifacts/ml/yolo_cls_dataset_v1.tgz`
or the Roboflow source) exists **on Antogravity's machine only**. Training must
be executed there; integration/verification happens in this repo.

## What to run (on the training machine, with the dataset present)
```bash
cd hackathon-S.P.O.T
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/prepare_yolo_cls_dataset.py   # if not already prepared
.venv/bin/python scripts/train_yolo26_cls.py           # trains to artifacts/ml/experiments/yolo26n_cls_pilot_v1/
```

## Deliverables to commit back to this repo
1. **`backend/models/onion_classifier.pt`** — replace the current 4-class
   prototype with the trained **binary** classifier. The registry's
   `YOLO26ClassifierModel` expects two classes, order is read directly from the
   checkpoint `names`, so either `{0: healthy, 1: defective}` or the reverse is
   fine — the loader maps by name.

2. **The trained YOLO26 checkpoint** at
   `artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.pt`
   (a copy of #1 is acceptable if only one will be kept).

3. **ONNX export** with static input shape `[1, 3, 224, 224]`:
   ```python
   from ultralytics import YOLO
   m = YOLO("path/to/best.pt")
   m.export(format="onnx", imgsz=224, dynamic=False, opset=12)
   ```
   Commit `best.onnx` next to `best.pt`.

4. **One calibration image** — a single, straight-on shot of one onion bulb on a
   neutral background, taken at the same distance the app expects (used to
   confirm the pipeline end-to-end; do not fabricate a size reference).

5. **Honest macro metrics** — commit the script's own output JSON:
   - validation **macro-F1 / accuracy / per-class precision & recall** for
     Healthy and Defective (no "94.74% on 19 images" style claims — the script
     must print the real numbers computed by `model.val(...)`).
   - the number of training/validation samples actually used.
   - any class-imbalance note (healthy vs defective counts).

## What happens after the checkpoint lands
Once #1 is committed, `backend/ai/registry.py` will automatically route
`/api/v1/inspect` and `/api/v1/ai/status` to the real model — no further code
change is required. (The integration seam was already wired and verified with a
placeholder checkpoint in commit `68ad434`.)

## Verification checklist (run on any machine with the checkpoint)
```bash
cd hackathon-S.P.O.T
.venv/bin/python -m pytest -q          # all green
.venv/bin/python - <<'PY'
from ultralytics import YOLO
m = YOLO("backend/models/onion_classifier.pt")
print(m.names)   # expect exactly {0:..., 1:...} two classes
PY
```
