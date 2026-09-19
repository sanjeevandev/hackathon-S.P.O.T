"""
S.P.O.T. SIH 2026 — Train 4-Class Onion YOLO Classification Model & Export to ONNX
==================================================================================
Trains a lightweight YOLO classification model on the 4-class Roboflow onion dataset
(healthy, disease, rotten, sprouted) and exports it to ONNX format for browser WebAssembly
edge inference and backend inference.

Outputs:
- backend/models/onion_classifier.pt
- backend/models/onion_yolov8.onnx
- public/models/onion_yolov8.onnx
- MODEL_NOTES.md
"""

import os
import sys
import time
import json
import shutil
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(PROJECT_ROOT, "backend", "dataset_classification")
MODEL_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "backend", "models")
PUBLIC_MODEL_DIR = os.path.join(PROJECT_ROOT, "public", "models")
MODEL_NOTES_PATH = os.path.join(PROJECT_ROOT, "MODEL_NOTES.md")

EPOCHS = 2
IMGSZ = 224
BATCH = 32
FRACTION = 0.35
SEED = 42


def main():
    print("=" * 70)
    print("S.P.O.T. 4-Class YOLO Onion Model Training & ONNX Export")
    print("=" * 70)

    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset not found at {DATASET_DIR}")
        sys.exit(1)

    classes = ["disease", "healthy", "rotten", "sprouted"]
    train_counts = {c: len(os.listdir(os.path.join(DATASET_DIR, "train", c))) for c in classes}
    val_counts = {c: len(os.listdir(os.path.join(DATASET_DIR, "val", c))) for c in classes}

    print(f"\n[1/5] Dataset verified:")
    total_train = sum(train_counts.values())
    total_val = sum(val_counts.values())
    for c in classes:
        print(f"  - {c:<10}: train={train_counts[c]:<5} val={val_counts[c]:<5}")
    print(f"  Total: train={total_train}, val={total_val}")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    os.makedirs(PUBLIC_MODEL_DIR, exist_ok=True)

    # ---- Step 2: Initialize & Train Model ----
    print(f"\n[2/5] Training YOLO classification model on CPU (epochs={EPOCHS}, fraction={FRACTION}, batch={BATCH}, imgsz={IMGSZ})...")
    
    # Load pretrained YOLO classification model (e.g. yolo11n-cls.pt or yolov8n-cls.pt)
    base_model_file = "yolo11n-cls.pt" if os.path.exists("yolo11n-cls.pt") else "yolov8n-cls.pt"
    model = YOLO(base_model_file)

    train_start = time.time()
    train_results = model.train(
        data=DATASET_DIR,
        epochs=EPOCHS,
        fraction=FRACTION,
        imgsz=IMGSZ,
        batch=BATCH,
        device="cpu",
        workers=2,
        seed=SEED,
        project=os.path.join(PROJECT_ROOT, "runs", "classify"),
        name="onion_4class",
        exist_ok=True,
        verbose=True
    )
    train_duration = round(time.time() - train_start, 2)
    print(f"  Training completed in {train_duration}s")

    # ---- Step 3: Validate Model ----
    print(f"\n[3/5] Validating model on validation dataset...")
    val_results = model.val(data=DATASET_DIR, imgsz=IMGSZ, batch=BATCH, device="cpu")
    
    top1_acc = float(val_results.top1) if hasattr(val_results, "top1") else 0.0
    top5_acc = float(val_results.top5) if hasattr(val_results, "top5") else 0.0
    model_classes = model.names if hasattr(model, "names") else {i: c for i, c in enumerate(classes)}
    print(f"  Model classes mapping: {model_classes}")
    print(f"  Validation Top-1 Accuracy: {top1_acc:.4f}")

    # Copy best weights to backend/models/onion_classifier.pt
    best_pt_path = getattr(model.trainer, "best", None)
    if not best_pt_path or not os.path.exists(str(best_pt_path)):
        best_pt_path = os.path.join(PROJECT_ROOT, "runs", "classify", "onion_4class", "weights", "best.pt")
    
    target_pt = os.path.join(MODEL_OUTPUT_DIR, "onion_classifier.pt")
    if os.path.exists(str(best_pt_path)):
        shutil.copy2(str(best_pt_path), target_pt)
        print(f"  Saved best PyTorch weights to {target_pt}")

    # Reload best model for export & detailed evaluation
    best_model = YOLO(target_pt)

    # ---- Step 4: Detailed Per-Class Evaluation & Confusion Matrix ----
    print(f"\n[4/5] Computing per-class accuracy and confusion matrix...")
    matrix = np.zeros((4, 4), dtype=int)
    latencies = []

    # Map name to index
    name_to_idx = {v: k for k, v in best_model.names.items()}

    for true_idx, true_name in best_model.names.items():
        val_cls_dir = os.path.join(DATASET_DIR, "val", true_name)
        if not os.path.exists(val_cls_dir):
            continue
        for img_name in os.listdir(val_cls_dir):
            img_path = os.path.join(val_cls_dir, img_name)
            
            t0 = time.perf_counter()
            pred = best_model.predict(img_path, imgsz=IMGSZ, device="cpu", verbose=False)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

            if pred and len(pred) > 0 and pred[0].probs is not None:
                pred_idx = int(pred[0].probs.top1)
                matrix[true_idx, pred_idx] += 1

    avg_latency_ms = round(float(np.mean(latencies)), 2) if latencies else 0.0
    p95_latency_ms = round(float(np.percentile(latencies, 95)), 2) if latencies else 0.0

    per_class_metrics = {}
    for i, c in best_model.names.items():
        tp = matrix[i, i]
        fp = int(np.sum(matrix[:, i]) - tp)
        fn = int(np.sum(matrix[i, :]) - tp)
        total = int(np.sum(matrix[i, :]))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        per_class_metrics[c] = {
            "samples": total,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "true_positives": int(tp),
            "false_positives": fp,
            "false_negatives": fn
        }

    total_samples = int(np.sum(matrix))
    total_correct = int(np.trace(matrix))
    overall_accuracy = round(total_correct / total_samples, 4) if total_samples > 0 else 0.0

    print(f"  Overall Accuracy: {overall_accuracy:.4f} ({total_correct}/{total_samples})")
    print(f"  Average CPU Latency: {avg_latency_ms} ms (P95: {p95_latency_ms} ms)")
    for c, m in per_class_metrics.items():
        print(f"    - {c:<10}: Precision={m['precision']:.4f}, Recall={m['recall']:.4f}, F1={m['f1']:.4f}")

    # ---- Step 5: Export Model to ONNX ----
    print(f"\n[5/5] Exporting model to ONNX format...")
    onnx_file_path = best_model.export(format="onnx", imgsz=IMGSZ, dynamic=False, opset=12)
    print(f"  Exported ONNX model to: {onnx_file_path}")

    # Copy to both public/models/onion_yolov8.onnx and backend/models/onion_yolov8.onnx
    target_onnx_backend = os.path.join(MODEL_OUTPUT_DIR, "onion_yolov8.onnx")
    target_onnx_public = os.path.join(PUBLIC_MODEL_DIR, "onion_yolov8.onnx")

    shutil.copy2(str(onnx_file_path), target_onnx_backend)
    shutil.copy2(str(onnx_file_path), target_onnx_public)
    print(f"  Copied ONNX model to {target_onnx_backend}")
    print(f"  Copied ONNX model to {target_onnx_public}")

    onnx_size_mb = round(os.path.getsize(target_onnx_public) / (1024 * 1024), 2)
    print(f"  ONNX File Size: {onnx_size_mb} MB")

    # Validate ONNX model with onnxruntime
    try:
        import onnxruntime as ort
        session = ort.InferenceSession(target_onnx_public, providers=["CPUExecutionProvider"])
        input_name = session.get_inputs()[0].name
        input_shape = session.get_inputs()[0].shape
        output_name = session.get_outputs()[0].name
        output_shape = session.get_outputs()[0].shape
        print(f"  ONNX Runtime validation: Input '{input_name}' {input_shape} -> Output '{output_name}' {output_shape}")
        
        # Test inference with dummy tensor
        dummy_input = np.random.randn(1, 3, IMGSZ, IMGSZ).astype(np.float32)
        ort_out = session.run([output_name], {input_name: dummy_input})
        print(f"  ONNX Test Output shape: {ort_out[0].shape}, Sample output: {ort_out[0]}")
    except Exception as e:
        print(f"  Notice on onnxruntime test: {e}")

    # ---- Generate MODEL_NOTES.md ----
    matrix_rows = "\n".join([
        f"| {classes[i]} | " + " | ".join(str(matrix[i, j]) for j in range(4)) + " |"
        for i in range(4)
    ])

    notes_content = f"""# S.P.O.T. Model Card & Empirical Validation Report

## 1. Overview & Architecture
- **Model Architecture**: Lightweight YOLO Classification CNN (`yolo11n-cls` / `yolov8n-cls` backbone)
- **Task**: 4-Class Onion Defect Classification (`disease`, `healthy`, `rotten`, `sprouted`)
- **Input Dimension**: `(1, 3, 224, 224)` RGB Float32 Normalized Tensor (ImageNet Mean/Std: `[0.485, 0.456, 0.406]`, `[0.229, 0.224, 0.225]`)
- **Output Dimension**: `(1, 4)` Class Logits / Probabilities
- **Class Index Mapping**:
  - `0`: `disease`
  - `1`: `healthy`
  - `2`: `rotten`
  - `3`: `sprouted`
- **Deployment Artifacts**:
  - PyTorch Checkpoint: `backend/models/onion_classifier.pt`
  - ONNX WebAssembly Model: `public/models/onion_yolov8.onnx` ({onnx_size_mb} MB)
  - Backend ONNX Model: `backend/models/onion_yolov8.onnx`

---

## 2. Dataset Distribution (Roboflow Onion Dataset v1)
Source dataset: `mayank-eltkz/onion-vi5f2-e2gt1` (12-class bounding-box dataset mapped and cropped with 10% bounding padding).

| Class Name | Training Crops | Validation Crops | Total Crops |
| :--- | :--- | :--- | :--- |
| **healthy** | {train_counts['healthy']} | {val_counts['healthy']} | {train_counts['healthy'] + val_counts['healthy']} |
| **disease** | {train_counts['disease']} | {val_counts['disease']} | {train_counts['disease'] + val_counts['disease']} |
| **rotten** | {train_counts['rotten']} | {val_counts['rotten']} | {train_counts['rotten'] + val_counts['rotten']} |
| **sprouted** | {train_counts['sprouted']} | {val_counts['sprouted']} | {train_counts['sprouted'] + val_counts['sprouted']} |
| **TOTAL** | **{total_train}** | **{total_val}** | **{total_train + total_val}** |

---

## 3. Empirical Performance Metrics (Evaluated on Validation Set)

- **Overall Top-1 Accuracy**: **{overall_accuracy * 100:.2f}%** ({total_correct} / {total_samples} samples correct)
- **Validation Top-1 Metric**: **{top1_acc * 100:.2f}%**
- **Average CPU Inference Latency**: **{avg_latency_ms} ms** (P95: {p95_latency_ms} ms)
- **Model Size on Disk**: **{onnx_size_mb} MB**

### Per-Class Evaluation

| Class | Samples | Precision | Recall | F1-Score | TP | FP | FN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **disease** | {per_class_metrics['disease']['samples']} | {per_class_metrics['disease']['precision']:.4f} | {per_class_metrics['disease']['recall']:.4f} | {per_class_metrics['disease']['f1']:.4f} | {per_class_metrics['disease']['true_positives']} | {per_class_metrics['disease']['false_positives']} | {per_class_metrics['disease']['false_negatives']} |
| **healthy** | {per_class_metrics['healthy']['samples']} | {per_class_metrics['healthy']['precision']:.4f} | {per_class_metrics['healthy']['recall']:.4f} | {per_class_metrics['healthy']['f1']:.4f} | {per_class_metrics['healthy']['true_positives']} | {per_class_metrics['healthy']['false_positives']} | {per_class_metrics['healthy']['false_negatives']} |
| **rotten** | {per_class_metrics['rotten']['samples']} | {per_class_metrics['rotten']['precision']:.4f} | {per_class_metrics['rotten']['recall']:.4f} | {per_class_metrics['rotten']['f1']:.4f} | {per_class_metrics['rotten']['true_positives']} | {per_class_metrics['rotten']['false_positives']} | {per_class_metrics['rotten']['false_negatives']} |
| **sprouted** | {per_class_metrics['sprouted']['samples']} | {per_class_metrics['sprouted']['precision']:.4f} | {per_class_metrics['sprouted']['recall']:.4f} | {per_class_metrics['sprouted']['f1']:.4f} | {per_class_metrics['sprouted']['true_positives']} | {per_class_metrics['sprouted']['false_positives']} | {per_class_metrics['sprouted']['false_negatives']} |

### Confusion Matrix (Rows: Ground Truth, Columns: Predicted)

| True \\ Pred | disease | healthy | rotten | sprouted |
| :--- | :--- | :--- | :--- | :--- |
{matrix_rows}

---

## 4. Hardware Calibration & Execution Environment
- **Inference Runtime**: ONNX Runtime Web (Wasm / WebGL) in Web Worker on Mobile Clients; ONNX Runtime / PyTorch on FastAPI server.
- **Physical Size Calibration**: Standard optical calibration ratio $D_{{mm}} = D_{{px}} \\times 0.38$ with $\\text{{Undersized}} < 45.0\\text{{mm}}$ threshold.
- **Tamper Protection**: Every analysis produces a SHA-256 integrity hash:
  $$\\text{{Hash}} = \\text{{SHA256}}(\\text{{batch\\_id}} : \\text{{overall\\_grade}} : \\text{{confidence}} : \\text{{timestamp}})$$
"""

    with open(MODEL_NOTES_PATH, "w", encoding="utf-8") as f:
        f.write(notes_content.strip() + "\n")

    print(f"\n✅ Created {MODEL_NOTES_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
