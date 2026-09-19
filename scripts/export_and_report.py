import os
import shutil
import time
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import onnxruntime as ort

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_OUTPUT_DIR = BASE_DIR / "backend" / "models"
PUBLIC_MODEL_DIR = BASE_DIR / "public" / "models"
MODEL_NOTES_PATH = BASE_DIR / "MODEL_NOTES.md"
VAL_DIR = BASE_DIR / "backend" / "dataset_classification" / "val"
TRAIN_DIR = BASE_DIR / "backend" / "dataset_classification" / "train"

classes = ["disease", "healthy", "rotten", "sprouted"]
IMGSZ = 224

def main():
    print("Loading trained PyTorch model...")
    pt_path = MODEL_OUTPUT_DIR / "onion_classifier.pt"
    model = YOLO(str(pt_path))

    print("Exporting model to ONNX...")
    exported_onnx = model.export(format="onnx", imgsz=IMGSZ, dynamic=False, opset=12)
    print(f"Exported to: {exported_onnx}")

    target_onnx_backend = MODEL_OUTPUT_DIR / "onion_yolov8.onnx"
    target_onnx_public = PUBLIC_MODEL_DIR / "onion_yolov8.onnx"
    PUBLIC_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(str(exported_onnx), target_onnx_backend)
    shutil.copy2(str(exported_onnx), target_onnx_public)
    print(f"Copied ONNX to {target_onnx_backend}")
    print(f"Copied ONNX to {target_onnx_public}")

    onnx_size_mb = round(os.path.getsize(target_onnx_public) / (1024 * 1024), 2)
    print(f"ONNX Size: {onnx_size_mb} MB")

    # Validate with onnxruntime
    session = ort.InferenceSession(str(target_onnx_public), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    output_name = session.get_outputs()[0].name
    output_shape = session.get_outputs()[0].shape
    print(f"ONNX validation: Input '{input_name}' {input_shape} -> Output '{output_name}' {output_shape}")

    # Run validation & compute metrics
    train_counts = {c: len(list((TRAIN_DIR / c).glob("*.jpg"))) if (TRAIN_DIR / c).exists() else 0 for c in classes}
    val_counts = {c: len(list((VAL_DIR / c).glob("*.jpg"))) if (VAL_DIR / c).exists() else 0 for c in classes}
    total_train = sum(train_counts.values())
    total_val = sum(val_counts.values())

    matrix = np.zeros((4, 4), dtype=int)
    latencies = []

    print("Evaluating validation dataset with ONNX Runtime...")
    from PIL import Image

    # Standard ImageNet normalization:
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 3, 1, 1)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1)

    for true_idx, c in enumerate(classes):
        c_dir = VAL_DIR / c
        if not c_dir.exists():
            continue
        for img_p in c_dir.glob("*.jpg"):
            with Image.open(img_p) as img:
                img_rgb = img.convert("RGB").resize((IMGSZ, IMGSZ), Image.Resampling.BILINEAR)
                arr = np.array(img_rgb, dtype=np.float32) / 255.0  # (224, 224, 3)
                arr = np.transpose(arr, (2, 0, 1))  # (3, 224, 224)
                arr = np.expand_dims(arr, 0)  # (1, 3, 224, 224)
                arr = (arr - mean) / std

            t0 = time.perf_counter()
            out = session.run([output_name], {input_name: arr})[0]
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

            pred_idx = int(np.argmax(out[0]))
            matrix[true_idx, pred_idx] += 1

    avg_latency_ms = round(float(np.mean(latencies)), 2)
    p95_latency_ms = round(float(np.percentile(latencies, 95)), 2)

    per_class_metrics = {}
    for i, c in enumerate(classes):
        tp = matrix[i, i]
        fp = int(np.sum(matrix[:, i]) - tp)
        fn = int(np.sum(matrix[i, :]) - tp)
        total = int(np.sum(matrix[i, :]))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
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

    print(f"Overall Accuracy: {overall_accuracy * 100:.2f}% ({total_correct}/{total_samples})")
    print(f"Average CPU Latency: {avg_latency_ms} ms (P95: {p95_latency_ms} ms)")
    for c, m in per_class_metrics.items():
        print(f"  {c:<10}: Precision={m['precision']:.4f}, Recall={m['recall']:.4f}, F1={m['f1']:.4f}")

    matrix_rows = "\n".join([
        f"| {classes[i]} | " + " | ".join(str(matrix[i, j]) for j in range(4)) + " |"
        for i in range(4)
    ])

    notes_content = f"""# S.P.O.T. Model Card & Empirical Validation Report

## 1. Overview & Architecture
- **Model Architecture**: Lightweight YOLO Classification CNN (`yolo11n-cls` backbone)
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

    print(f"\nCreated {MODEL_NOTES_PATH}")

if __name__ == "__main__":
    main()
