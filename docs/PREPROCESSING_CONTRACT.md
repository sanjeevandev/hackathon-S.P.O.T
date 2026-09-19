# PREPROCESSING CONTRACT

**Contract Version**: `image-preprocess-v1`  
**Status**: ACTIVE & VERSIONED  
**Date**: September 4, 2026  

---

## 1. Overview

The S.P.O.T. vision system enforces a single, versioned preprocessing pipeline (`image-preprocess-v1`) implemented in `backend/ai/preprocessing.py`. This contract guarantees identical image formatting, color spaces, resizing, padding, and normalizations across development mocks, contract test models, and production vision models (e.g. YOLO11 runners).

---

## 2. Specification Standards

| Step | Parameter | Specification / Standard | Rationale |
| :--- | :--- | :--- | :--- |
| **Decoding** | PIL Image.open | JPEG / PNG / WEBP byte stream verification | Rejects corrupted byte payloads immediately |
| **Color Space** | `RGB` | 3-channel RGB (0-255 uint8) | Eliminates alpha-channel/grayscale ambiguity |
| **Geometry** | Aspect-Preserved Letterbox | Target dimensions `640 x 640` with `(114, 114, 114)` gray padding | Prevents aspect ratio distortion of spherical onion bulbs |
| **Resampling** | Lanczos (`Image.Resampling.LANCZOS`) | High-fidelity downsampling / upsampling | Preserves micro-surface defect textures (scuffs, fungal rot) |
| **Normalization** | `[0.0, 1.0]` tensor input ready | Floating point pixel values normalized by `255.0` | Matches standardized PyTorch/ONNX model input norms |

---

## 3. Preprocessing Metadata Contract

Every execution of the preprocessor returns a `PreprocessingResult` payload:

```json
{
  "preprocessing_version": "image-preprocess-v1",
  "original_width": 1280,
  "original_height": 720,
  "target_width": 640,
  "target_height": 640,
  "color_space": "RGB",
  "channels": 3,
  "decode_time_ms": 1.45,
  "preprocessing_time_ms": 4.12
}
```

---

## 4. Versioning Policy

- Changes to target dimensions, padding color, or normalization scale require bumping `PREPROCESSING_VERSION` (e.g., `image-preprocess-v2`).
- Production vision model weights are pinned to a specific preprocessing version to ensure inferencing consistency.
