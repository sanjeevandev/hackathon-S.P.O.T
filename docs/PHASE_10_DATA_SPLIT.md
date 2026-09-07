# S.P.O.T. Phase 10 Data Split & Curation Strategy

## 1. Executive Data Curation Summary

- **Total Audited Dataset Size**: 16,300 images
- **Bulb Images (Target Scope)**: 12,260 images (75.22%)
- **Leaf Images (Out-of-Scope Validation Data)**: 4,040 images (24.78%)
- **Grouping Strategy**: Union-Find Disjoint Set Cluster Partitioning (28 exact duplicate hash groups + 276 near-duplicate pairs + sequential burst windows of 20 images).
- **Leakage-Safe Capture Clusters**: 571 independent capture clusters.

---

## 2. Partition Summary Table

| Partition | Scope | Sample Count | % of Scope | Leakage Protection Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **TRAIN** | Bulb Quality | 8,580 | 70.0% | Entire capture clusters isolated to train set |
| **VALIDATION** | Bulb Quality | 1,830 | 14.9% | Held-out capture clusters (0 duplicate overlap) |
| **TEST** | Baseline Eval | 1,850 | 15.1% | Strictly held-out test capture clusters |
| **OUT_OF_SCOPE** | Subject Validation | 4,040 | 100% (Leaf) | Isolated for future Bulb vs Leaf classifier |

---

## 3. Semantic Attribute Inventory

Each item in the curated manifest maps directly to 4 semantic dimensions without altering source files:

1. **Organ**: `BULB` (12,260) | `LEAF` (4,040)
2. **Health**: `HEALTHY` (8,220) | `UNHEALTHY` (4,040)
3. **Color**: `RED` (6,030) | `WHITE` (6,030) | `N/A` (4,040 leaf)
4. **Arrangement**: `SINGLE` (10,060) | `MULTIPLE` (6,240)

---

## 4. Verification & Lineage

The data split manifest is stored at `artifacts/ml/split_manifest.json` and tied reproducibly to dataset manifest `artifacts/ml/dataset_version.json` (Checksum: `cfd9e8b75205be3253cabf0ec59bcece02ddf4e641cd12dd17171b5e6cd667d4`).
