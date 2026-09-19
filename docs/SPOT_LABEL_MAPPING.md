# S.P.O.T. Label Taxonomy Compatibility Matrix

## 1. Executive Summary

This document evaluates the compatibility between the real dataset's discovered classes and the official S.P.O.T. target quality inspection requirements.

### Target S.P.O.T. Quality Concepts:
1. **Healthy**: Prime quality bulb with clean skin, intact neck, no disease or decay.
2. **Damaged**: Physical cuts, mechanical abrasion, skin peeling, or bruising.
3. **Rotten**: Fungal/bacterial rot, soft rot, black mold, or internal decay.
4. **Sprouted**: Internal or external green shoot emergence.
5. **Undersized**: Below standard market diameter classification.

---

## 2. Taxonomy Mapping Table

| Dataset Label | S.P.O.T. Concept | Mapping Status | Evidence | Confidence | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `2. Bulb/1. Healthy/1. Red Onion/*` | Healthy (Red) | Direct Match | Directory path explicit label | HIGH | Meets S.P.O.T. Healthy Red category |
| `2. Bulb/1. Healthy/2. White Onion/*` | Healthy (White) | Direct Match | Directory path explicit label | HIGH | Meets S.P.O.T. Healthy White category |
| `2. Bulb/2. Unhealthy/1. Red Onion/*` | Damaged / Rotten / Sprouted / Undersized | Collapsed / Generic | Merged under generic `Unhealthy` label | MEDIUM | Dataset does NOT differentiate specific defect types |
| `2. Bulb/2. Unhealthy/2. White Onion/*` | Damaged / Rotten / Sprouted / Undersized | Collapsed / Generic | Merged under generic `Unhealthy` label | MEDIUM | Dataset does NOT differentiate specific defect types |
| `1. Leaves/*` | Leaf Foliage | Out of Scope | Plant leaves before harvesting | N/A | Tagged `OUT_OF_SCOPE_FOR_BULB_GRADING` |

---

## 3. Discrepancy & Gap Analysis

1. **Defect Sub-Type Loss**:
   - The real dataset aggregates all onion bulb flaws (rot, physical cuts, sprouting, mold) into a single binary label: `2. Unhealthy`.
   - **Impact**: Multi-class fine-grained defect diagnosis (e.g. distinguishing Rotten vs Sprouted vs Damaged) requires either secondary fine-grained defect annotation or training a binary/hierarchical classifier first (`Healthy` vs `Unhealthy`).

2. **Size Estimation (Undersized Concept)**:
   - No millimeter/pixel size calibrations or bounding box references exist in the current image-level dataset.
   - **Impact**: Determining "Undersized" requires camera distance calibration or reference bounding scale markers in future capture pipelines.
