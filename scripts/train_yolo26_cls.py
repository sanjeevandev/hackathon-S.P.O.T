"""
S.P.O.T. Phase 3 — Train YOLO26n-cls on Pilot Dataset
======================================================
Fine-tunes YOLO26n-cls (ImageNet-pretrained, officially released by Ultralytics in Jan 2026)
on the 99-sample binary pilot dataset using transfer learning on CPU.

Output: artifacts/ml/experiments/yolo26n_cls_pilot_v1/
"""

import datetime
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "yolo_cls_dataset_v1")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "experiments", "yolo26n_cls_pilot_v1")
BASELINE_METRICS_PATH = os.path.join(PROJECT_ROOT, "artifacts", "ml", "baseline_metrics.json")

# Training hyperparameters — tuned for tiny dataset + CPU
EPOCHS = 50
IMGSZ = 224
BATCH = 8       # Small batch for 80 training images
LR0 = 0.001
FREEZE = 10     # Freeze first 10 backbone layers (transfer learning)
PATIENCE = 15   # Early stopping patience
SEED = 42


def main():
    print("=" * 70)
    print("S.P.O.T. Phase 3 — Train YOLO26n-cls")
    print("=" * 70)

    # Verify dataset exists
    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset not found at {DATASET_DIR}")
        print("   Run scripts/prepare_yolo_cls_dataset.py first")
        sys.exit(1)

    train_healthy = len(os.listdir(os.path.join(DATASET_DIR, "train", "healthy")))
    train_defective = len(os.listdir(os.path.join(DATASET_DIR, "train", "defective")))
    val_healthy = len(os.listdir(os.path.join(DATASET_DIR, "val", "healthy")))
    val_defective = len(os.listdir(os.path.join(DATASET_DIR, "val", "defective")))

    print(f"\n[1/4] Dataset verified:")
    print(f"  Train: {train_healthy} healthy + {train_defective} defective = {train_healthy + train_defective}")
    print(f"  Val:   {val_healthy} healthy + {val_defective} defective = {val_healthy + val_defective}")

    # ---- Step 2: Load pretrained model and train ----
    print(f"\n[2/4] Loading YOLO26n-cls pretrained model...")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ ultralytics not installed. Run: .venv/bin/pip install ultralytics")
        sys.exit(1)

    model = YOLO("yolo26n-cls.pt")  # Official YOLO26 classification model
    print(f"  Model loaded: yolo26n-cls.pt")
    print(f"  Training config: epochs={EPOCHS}, imgsz={IMGSZ}, batch={BATCH}, lr0={LR0}, freeze={FREEZE}")
    print(f"  Device: CPU (or CUDA if available)")

    train_start = time.time()

    results = model.train(
        data=DATASET_DIR,
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        lr0=LR0,
        freeze=FREEZE,
        patience=PATIENCE,
        seed=SEED,
        device="cpu",
        workers=2,
        project=os.path.dirname(OUTPUT_DIR),
        name="yolo26n_cls_pilot_v1",
        exist_ok=True,
        verbose=True,
        # Augmentation — tuned for small dataset
        augment=True,
        hsv_h=0.02,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=45.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        flipud=0.2,
        erasing=0.1,
    )

    train_time = time.time() - train_start
    print(f"\n  Training completed in {train_time:.1f}s")

    # ---- Step 3: Evaluate on validation set ----
    print(f"\n[3/4] Evaluating on validation set...")

    eval_start = time.time()
    val_results = model.val(data=DATASET_DIR, imgsz=IMGSZ, batch=BATCH, device="cpu")
    eval_time = time.time() - eval_start

    # Extract metrics
    top1_acc = float(val_results.top1) if hasattr(val_results, 'top1') else None
    top5_acc = float(val_results.top5) if hasattr(val_results, 'top5') else None

    # Measure inference latency
    print(f"\n  Measuring inference latency...")
    import torch
    from PIL import Image

    latencies = []
    test_images_dir = os.path.join(DATASET_DIR, "val", "healthy")
    test_images = os.listdir(test_images_dir)[:5]

    for img_name in test_images:
        img_path = os.path.join(test_images_dir, img_name)
        t0 = time.perf_counter()
        _ = model.predict(img_path, imgsz=IMGSZ, device="cpu", verbose=False)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    # Get model file size
    best_model_path = os.path.join(OUTPUT_DIR, "weights", "best.pt")
    if not os.path.exists(best_model_path):
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for f in files:
                if f == "best.pt":
                    best_model_path = os.path.join(root, f)
                    break

    model_size_bytes = os.path.getsize(best_model_path) if os.path.exists(best_model_path) else 0
    model_size_mb = round(model_size_bytes / (1024 * 1024), 2)

    # Run per-class analysis on validation set
    print(f"\n  Running per-class predictions on validation set...")
    tp = {"healthy": 0, "defective": 0}
    fp = {"healthy": 0, "defective": 0}
    fn = {"healthy": 0, "defective": 0}
    total_correct = 0
    total_samples = 0

    for cls in ["healthy", "defective"]:
        cls_dir = os.path.join(DATASET_DIR, "val", cls)
        for img_name in os.listdir(cls_dir):
            img_path = os.path.join(cls_dir, img_name)
            preds = model.predict(img_path, imgsz=IMGSZ, device="cpu", verbose=False)
            if preds and len(preds) > 0:
                pred_cls_idx = int(preds[0].probs.top1)
                pred_cls = preds[0].names[pred_cls_idx]
            else:
                pred_cls = "unknown"

            total_samples += 1
            if pred_cls == cls:
                total_correct += 1
                tp[cls] += 1
            else:
                fp[pred_cls] = fp.get(pred_cls, 0) + 1
                fn[cls] += 1

    # Compute per-class metrics
    per_class_metrics = {}
    for cls in ["healthy", "defective"]:
        precision = tp[cls] / (tp[cls] + fp[cls]) if (tp[cls] + fp[cls]) > 0 else 0
        recall = tp[cls] / (tp[cls] + fn[cls]) if (tp[cls] + fn[cls]) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        per_class_metrics[cls] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "true_positives": tp[cls],
            "false_positives": fp[cls],
            "false_negatives": fn[cls],
        }

    accuracy = total_correct / total_samples if total_samples > 0 else 0
    macro_precision = sum(m["precision"] for m in per_class_metrics.values()) / len(per_class_metrics)
    macro_recall = sum(m["recall"] for m in per_class_metrics.values()) / len(per_class_metrics)
    macro_f1 = sum(m["f1"] for m in per_class_metrics.values()) / len(per_class_metrics)

    print(f"\n  Results:")
    print(f"    Accuracy:    {accuracy:.4f}")
    print(f"    Macro P:     {macro_precision:.4f}")
    print(f"    Macro R:     {macro_recall:.4f}")
    print(f"    Macro F1:    {macro_f1:.4f}")
    print(f"    Defect Recall: {per_class_metrics['defective']['recall']:.4f}")
    print(f"    Latency:     {avg_latency:.1f}ms (avg), {min_latency:.1f}ms (min), {max_latency:.1f}ms (max)")
    print(f"    Model size:  {model_size_mb} MB")

    # ---- Step 4: Save experiment results and comparison ----
    print(f"\n[4/4] Saving experiment results...")

    # Load ResNet18 baseline for comparison
    baseline = {}
    if os.path.exists(BASELINE_METRICS_PATH):
        with open(BASELINE_METRICS_PATH, "r") as f:
            baseline = json.load(f)

    experiment_results = {
        "experiment_name": "YOLO26n-cls Pilot Binary Classification",
        "experiment_id": "yolo26n-cls-pilot-v1",
        "model_name": "YOLO26n-cls",
        "model_version": "1.0.0-pilot",
        "source": "real_model",
        "task": "binary_classification",
        "classes": ["healthy", "defective"],
        "dataset": {
            "name": "SPOT-PILOT-YOLO-CLS-V1",
            "train_samples": train_healthy + train_defective,
            "val_samples": val_healthy + val_defective,
            "total_usable": train_healthy + train_defective + val_healthy + val_defective,
        },
        "training": {
            "epochs_configured": EPOCHS,
            "imgsz": IMGSZ,
            "batch_size": BATCH,
            "lr0": LR0,
            "frozen_layers": FREEZE,
            "patience": PATIENCE,
            "device": "cpu",
            "training_time_seconds": round(train_time, 2),
            "seed": SEED,
            "transfer_learning": True,
            "pretrained_on": "ImageNet",
        },
        "metrics": {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(macro_precision, 4),
            "macro_recall": round(macro_recall, 4),
            "macro_f1": round(macro_f1, 4),
            "top1_accuracy": top1_acc,
            "top5_accuracy": top5_acc,
            "per_class": per_class_metrics,
        },
        "inference": {
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": round(min_latency, 2),
            "max_latency_ms": round(max_latency, 2),
            "device": "cpu",
            "imgsz": IMGSZ,
        },
        "model_file": {
            "best_checkpoint": best_model_path,
            "size_bytes": model_size_bytes,
            "size_mb": model_size_mb,
        },
        "comparison_vs_baseline": {
            "baseline_model": baseline.get("model_name", "ResNet18 Baseline Classifier"),
            "note": "ResNet18 baseline was trained on 74-dim feature vectors (tabular MLP), not raw images. Architecturally different from YOLO26 CNN. Comparison is directional only.",
            "baseline_accuracy": baseline.get("accuracy"),
            "baseline_f1": baseline.get("f1_score"),
            "baseline_unhealthy_recall": baseline.get("recall_unhealthy"),
            "baseline_model_size_mb": baseline.get("model_size_mb"),
            "baseline_latency_ms": baseline.get("avg_inference_latency_ms"),
            "yolo26_accuracy": round(accuracy, 4),
            "yolo26_f1": round(macro_f1, 4),
            "yolo26_defect_recall": per_class_metrics["defective"]["recall"],
            "yolo26_model_size_mb": model_size_mb,
            "yolo26_latency_ms": round(avg_latency, 2),
        },
        "limitations": [
            "Trained on 80 images (small pilot dataset)",
            "Single annotator labels — no IAA validation",
            "CPU training",
            "Binary classification (healthy vs defective) — preserves fine-grained labels in pilot_v1 dataset",
            "Metrics on 19-sample validation set have expected sample variance",
            "Transfer learning used (ImageNet pretrained YOLO26 backbone)",
        ],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results_path = os.path.join(OUTPUT_DIR, "experiment_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(experiment_results, f, indent=2)

    print(f"  ✅ Saved experiment_results.json")

    # Print comparison table
    print(f"\n{'=' * 70}")
    print(f"PHASE 3 COMPLETE — MODEL COMPARISON")
    print(f"{'=' * 70}")
    print(f"{'Metric':<25} {'ResNet18 (baseline)':<22} {'YOLO26n-cls (new)':<22}")
    print(f"{'-'*25} {'-'*22} {'-'*22}")
    print(f"{'Architecture':<25} {'Tabular MLP (74-dim)':<22} {'CNN (224x224 images)':<22}")
    print(f"{'Accuracy':<25} {str(baseline.get('accuracy', 'N/A')):<22} {accuracy:<22.4f}")
    print(f"{'F1':<25} {str(baseline.get('f1_score', 'N/A')):<22} {macro_f1:<22.4f}")
    print(f"{'Defect/Unhealthy Recall':<25} {str(baseline.get('recall_unhealthy', 'N/A')):<22} {per_class_metrics['defective']['recall']:<22.4f}")
    print(f"{'Model Size':<25} {str(baseline.get('model_size_mb', 'N/A')) + ' MB':<22} {str(model_size_mb) + ' MB':<22}")
    print(f"{'Inference Latency':<25} {str(baseline.get('avg_inference_latency_ms', 'N/A')) + ' ms':<22} {str(round(avg_latency, 1)) + ' ms':<22}")
    print(f"{'Training Data':<25} {'8580 feature vectors':<22} {'80 images':<22}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
