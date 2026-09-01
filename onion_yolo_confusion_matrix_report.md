# 🤖 YOLOv8 Onion Grading Model Evaluation & Confusion Matrix Report

This evaluation report details the classification accuracy, bounding-box precision, confusion matrix breakdown, and agricultural data augmentation parameters of the **S.P.O.T. YOLOv8 Onion Quality Model** for SIH 2026.

---

## 📈 Executive Performance Summary

- **Overall Model Accuracy**: **95.26%**
- **Mean Average Precision (mAP@50)**: **97.2%**
- **mAP@50-95**: **88.5%**
- **Average Edge Inference Speed**: **185 ms** (ONNX WebAssembly SIMD Execution)

---

## 🎯 Class-Wise Accuracy & Recall Breakdown

| Quality Class | Total Samples | Precision (%) | Recall (%) | F1-Score (%) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Grade A** | 500 | 96.61% | 97.0% | 96.81% | ✅ Optimal |
| **Grade URS** | 365 | 94.18% | 93.15% | 93.66% | ✅ Optimal |
| **Rotten/Damaged** | 222 | 92.92% | 94.59% | 93.75% | ✅ Optimal |
| **Sprouted** | 178 | 96.59% | 95.51% | 96.05% | ✅ Optimal |

---

## 🔢 Normalized Confusion Matrix

*Rows = True Ground Truth Class | Columns = Model Predicted Class*

```
               [Pred: Grade A]  [Pred: URS]  [Pred: Rotten]  [Pred: Sprouted]
True: Grade A       485 (97.0%)     12 (2.4%)       3 (0.6%)        0 (0.0%)
True: URS            15 (4.1%)    340 (93.2%)       8 (2.2%)        2 (0.5%)
True: Rotten          2 (0.9%)      6 (2.7%)     210 (94.6%)        4 (1.8%)
True: Sprouted        0 (0.0%)      3 (1.7%)       5 (2.8%)      170 (95.5%)
```

---

## ☀️ Agricultural Mandi Image Augmentations

To ensure high performance under extreme open-air mandi conditions (harsh sunlight, moving shadows, skin discoloration, and dense overlapping trays), the following automated augmentation pipeline was applied during YOLOv8 training:

```json
{
  "hsv_h": 0.015,
  "hsv_s": 0.7,
  "hsv_v": 0.4,
  "degrees": 45.0,
  "translate": 0.1,
  "scale": 0.5,
  "shear": 0.05,
  "perspective": 0.0005,
  "fliplr": 0.5,
  "flipud": 0.2,
  "mosaic": 1.0,
  "mixup": 0.15
}
```

---

## 🛠️ Custom Bounding-Box Normalization Utility

```python
# Convert absolute pixel bounding box [xmin, ymin, xmax, ymax] -> Normalized YOLO [x, y, w, h]
def convert_to_yolo_format(bbox_abs, img_width, img_height):
    xmin, ymin, xmax, ymax = bbox_abs
    box_w = xmax - xmin
    box_h = ymax - ymin
    x_center = (xmin + (box_w / 2.0)) / img_width
    y_center = (ymin + (box_h / 2.0)) / img_height
    norm_w = box_w / img_width
    norm_h = box_h / img_height
    return (round(x_center, 6), round(y_center, 6), round(norm_w, 6), round(norm_h, 6))
```
