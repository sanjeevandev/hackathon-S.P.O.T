# S.P.O.T. Model Card & Empirical Validation Report

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
  - ONNX WebAssembly Model: `public/models/onion_yolov8.onnx` (5.89 MB)
  - Backend ONNX Model: `backend/models/onion_yolov8.onnx`

---

## 2. Dataset Distribution (Roboflow Onion Dataset v1)
Source dataset: `mayank-eltkz/onion-vi5f2-e2gt1` (12-class bounding-box dataset mapped and cropped with 10% bounding padding).

| Class Name | Training Crops | Validation Crops | Total Crops |
| :--- | :--- | :--- | :--- |
| **healthy** | 7500 | 697 | 8197 |
| **disease** | 1299 | 202 | 1501 |
| **rotten** | 1178 | 109 | 1287 |
| **sprouted** | 1167 | 93 | 1260 |
| **TOTAL** | **11144** | **1101** | **12245** |

---

## 3. Empirical Performance Metrics (Evaluated on Validation Set)

- **Overall Top-1 Accuracy**: **63.49%** (699 / 1101 samples correct)
- **Average CPU Inference Latency**: **2.83 ms** (P95: 3.67 ms)
- **Model Size on Disk**: **5.89 MB**

### Per-Class Evaluation

| Class | Samples | Precision | Recall | F1-Score | TP | FP | FN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **disease** | 202 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 202 |
| **healthy** | 697 | 0.6342 | 1.0000 | 0.7762 | 697 | 402 | 0 |
| **rotten** | 109 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 109 |
| **sprouted** | 93 | 1.0000 | 0.0215 | 0.0421 | 2 | 0 | 91 |

### Confusion Matrix (Rows: Ground Truth, Columns: Predicted)

| True \ Pred | disease | healthy | rotten | sprouted |
| :--- | :--- | :--- | :--- | :--- |
| disease | 0 | 202 | 0 | 0 |
| healthy | 0 | 697 | 0 | 0 |
| rotten | 0 | 109 | 0 | 0 |
| sprouted | 0 | 91 | 0 | 2 |

---

## 4. Hardware Calibration & Execution Environment
- **Inference Runtime**: ONNX Runtime Web (Wasm / WebGL) in Web Worker on Mobile Clients; ONNX Runtime / PyTorch on FastAPI server.
- **Physical Size Calibration**: Standard optical calibration ratio $D_{mm} = D_{px} \times 0.38$ with $\text{Undersized} < 45.0\text{mm}$ threshold.
- **Tamper Protection**: Every analysis produces a SHA-256 integrity hash:
  $$\text{Hash} = \text{SHA256}(\text{batch\_id} : \text{overall\_grade} : \text{confidence} : \text{timestamp})$$
