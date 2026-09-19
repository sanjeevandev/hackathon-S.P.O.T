# S.P.O.T. Phase 13 — Real Human Annotation Pilot Status

## 1. Executive Summary
Phase 13 manages the **real human multi-label defect annotation process** on the 100-image pilot dataset selected during Phase 12A.

- **No Automated / ResNet18 / YOLO26 Labeling**: All ground truth annotations are recorded by human annotators.
- **Multi-Label Schema**: Healthy, Damaged, Rotten, Sprouted, Undersized, Uncertain.
- **Physical Size Rule**: `Undersized = UNAVAILABLE` unless calibrated physical measurement reference is available.
- **Pilot First Strategy**: Initial 10-image batch review before full 100-image completion.
- **Double Annotation**: Independent labeling by Annotator A & Annotator B without label copying.

---

## 2. Current Annotation Metrics

| Metric | Value |
| :--- | :--- |
| **Total Pilot Images** | 100 |
| **Human Annotations Completed** | 0 |
| **Remaining Images** | 100 |
| **Needs Review** | 0 |
| **Adjudicated** | 0 |
| **Damage Count** | 0 |
| **Rot Count** | 0 |
| **Sprout Count** | 0 |
| **Undersized Count** | 0 |
| **Uncertain Count** | 0 |

---

## 3. Workstation Architecture & Status Lifecycle
```
[UNLABELED] -> (Annotator Input) -> [IN_PROGRESS] -> (Submit) -> [COMPLETE]
                                                         |
                                                  (Validation Error)
                                                         v
                                                  [NEEDS_REVIEW] -> (Adjudication) -> [ADJUDICATED]
```
