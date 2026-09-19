# S.P.O.T. Phase 9 Forensic Audit Report & Scorecard

## 1. Executive Forensic Audit Findings

- **Dataset Identifier**: `Image Dataset of Red and White Onion Bulbs and Leaves`
- **Source Path Verified**: `/run/media/sanjeeva/New Volume1/ONION IQ/Image Dataset of Red and White Onion Bulbs and Lea`
- **Archive Path Verified**: `/run/media/sanjeeva/New Volume1/ONION IQ/Image Dataset of Red and White Onion Bulbs and Lea/Onion Leaves and Bulb Dataset.zip`
- **Dataset Checksum SHA-256**: `cfd9e8b75205be3253cabf0ec59bcece02ddf4e641cd12dd17171b5e6cd667d4`
- **Total Files**: 16,300
- **Total Images**: 16,300 (100% JPG)
- **Valid Images**: 16,300 (100%)
- **Corrupt Images**: 0 (0%)
- **Non-Image Files**: 0 (0%)

---

## 2. Quantitative Summary Metrics

| Metric Category | Discovered Value | Forensic Note |
| :--- | :--- | :--- |
| **Total Bulb Images** | 12,260 (75.22%) | Relevant for post-harvest S.P.O.T. quality grading |
| **Total Leaf Images** | 4,040 (24.78%) | Out of scope for post-harvest bulb quality grading |
| **Single-Object Images** | 10,060 (61.72%) | Clean isolated specimens |
| **Multi-Object Images** | 6,240 (38.28%) | Multiple specimens in field of view |
| **Exact Cryptographic Duplicates** | 28 groups / 57 files | 29 redundant duplicate images |
| **Perceptual Near-Duplicates** | 276 image pairs | dhash Hamming distance $\le 3$ |
| **Resolution Types** | 1024x768 (71.01%), 576x768 (28.99%) | Uniform resolution pairs |
| **Mean Blur Score (Laplacian)** | 433.47 (Std: 1038.11) | 7,727 images $\text{blur} < 100$ (soft focus) |
| **Mean Brightness** | 125.66 / 255 | Well-exposed lighting conditions |

---

## 3. Dataset Quality Scorecard

| Assessment Dimension | Qualitative Rating | Concrete Evidence |
| :--- | :--- | :--- |
| **Dataset Completeness** | **EXCELLENT** | 16,300 intact images, 0 corrupt files, clean ZIP packaging. |
| **Annotation Completeness** | **MODERATE** | Folder-level classification labels present; 0 bounding boxes or segmentation masks. |
| **Class Balance** | **FAIR** | Strong healthy bulb count (8,220); minority unhealthy bulb count (4,040). Imbalance ratio 2.03:1. |
| **Image Quality** | **GOOD** | Clear color rendition, good exposure; ~47% soft-focus images due to macro depth-of-field. |
| **Duplicate Risk** | **LOW** | Only 29 exact duplicate files out of 16,300 (0.178%). |
| **Leakage Risk** | **HIGH** | Sequential frame series require Group-based splitting to prevent validation leakage. |
| **Defect Coverage** | **COARSE** | Generic `Unhealthy` label used; no individual rot/sprout sub-labels. |
| **Variety Coverage** | **EXCELLENT** | Dual color representation (Red and White onions) across single and multi-bulb setups. |
| **Bulb/Leaf Separation** | **EXCELLENT** | Explicit top-level directory separation (`1. Leaves` vs `2. Bulb`). |
| **Suitability for S.P.O.T.** | **HIGH (for Classification)** | Excellent foundation for binary and multi-task bulb quality classification models. |
