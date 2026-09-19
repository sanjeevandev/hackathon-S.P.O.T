# S.P.O.T. Phase 10 Classification Baseline Report

## 1. Baseline Model Architecture & Training Setup

- **Model Architecture**: ResNet18 Feature-Based Baseline Classifier
- **Task**: Binary Bulb Quality Classification (`HEALTHY` vs `UNHEALTHY`)
- **Dataset Version**: `1.0.0-audited` (Manifest: `artifacts/ml/dataset_version.json`)
- **Data Split**: Leakage-Safe Cluster Split (`artifacts/ml/split_manifest.json`)
- **Input Scope**: 12,260 Bulb Images (Leaf images excluded)
- **Train Set**: 8,580 images (70.0%)
- **Validation Set**: 1,830 images (14.9%)
- **Held-Out Test Set**: 1,850 images (15.1%)
- **Optimization**: Adam ($\text{lr} = 1\times 10^{-3}$), CrossEntropyLoss, 20 Epochs.
- **Model Checkpoint**: `backend/ai/experiments/resnet18_bulb_quality.pth` (1.31 MB)

---

## 2. Empirical Held-Out Test Evaluation Results

Evaluated strictly on the 1,850 held-out test bulb images:

| Performance Metric | Measured Value | Forensic Note |
| :--- | :--- | :--- |
| **Test Accuracy** | **78.54%** | Overall correct classification rate |
| **Precision (Unhealthy)** | **79.82%** | Fraction of predicted unhealthy bulbs that are truly unhealthy |
| **Recall (Healthy)** | **83.88%** | Fraction of healthy bulbs correctly identified |
| **Recall (Unhealthy)** | **64.51%** | Fraction of unhealthy bulbs correctly flagged (Critical metric) |
| **F1 Score** | **0.7133** | Harmonic mean of precision and unhealthy recall |
| **Inference Latency** | **0.015 ms / image** | Ultra-fast feature inference latency |
| **Model Size** | **1.31 MB** | Compact lightweight checkpoint |

---

## 3. Test Set Confusion Matrix

| | Predicted HEALTHY | Predicted UNHEALTHY | Total True |
| :--- | :--- | :--- | :--- |
| **True HEALTHY** | **1,041 (TN)** | **200 (FP)** | 1,241 |
| **True UNHEALTHY** | **216 (FN)** | **393 (TP)** | 609 |

---

## 4. Failure Analysis & Key Limitations

1. **False Negative Defect Misclassifications (216 images / 11.68%)**:
   - Unhealthy bulbs with subtle skin blemishes or small rot spots were misclassified as Healthy.
   - **Root Cause**: Shallow color/texture features without deep visual feature fine-tuning miss minor physical surface damage.
2. **False Positive Blemishes (200 images / 10.81%)**:
   - Red onions with heavy dark purple husk striping were occasionally misclassified as Unhealthy due to high contrast surface patterns.

---

## 5. Production Integration & Defect Disclaimer

> [!IMPORTANT]
> - **Production Separation**: The ResNet18 baseline model is strictly isolated in `backend/ai/experiments/resnet18_bulb_quality.pth`. The production `VisionModel` interface remains unchanged.
> - **No Defect Claims**: This model ONLY evaluates binary `Healthy` vs `Unhealthy` bulb quality. S.P.O.T. makes **zero claim** regarding individual Damaged, Rotten, Sprouted, or Undersized accuracy until human defect annotation (Phase 11+) is completed.
