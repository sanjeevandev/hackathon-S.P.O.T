# S.P.O.T. Phase 12 Human Annotation Workstation Architecture & Specification

## 1. Executive Summary & Strict Disclaimers

> [!IMPORTANT]
> - **Synthetic Agreement Disclaimer**: The 95.0% inter-annotator agreement and Cohen's Kappa 0.90 reported during Phase 11 software testing were **pipeline test fixtures ONLY**. They do NOT represent real-world human annotation agreement. Real-world agreement is marked **`NOT_AVAILABLE`** until human domain experts complete double-annotation tasks.
> - **Internal Workstation Isolation**: The human annotation workstation is an **INTERNAL AGRI-INSPECTOR TOOL**. It is strictly segregated from the public procurement user workflow and is not exposed to normal users.
> - **Zero Model Auto-Labeling**: The workstation does NOT use the ResNet18 baseline (`SPOT-Baseline-001`) to automatically generate defect labels. Defect labels are derived exclusively from human visual inspection.

---

## 2. Work Queue & Stratification Preservation

The workstation loads the stratified 1,000-image annotation manifest (`artifacts/ml/defect_annotations/annotation_manifest.json`) created in Phase 11.

- **Queue Partitioning**: 1,000 bulb images stratified across 8 color/arrangement/quality strata.
- **Leakage Protection**: All 571 capture clusters from Phase 10 remain intact.
- **Item State Lifecycle**:
  `UNLABELED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETE` $\rightarrow$ (`NEEDS_REVIEW` / `ADJUDICATED`)

---

## 3. Workstation Interface Specifications

| UI Component | Functionality | Rule / Constraint |
| :--- | :--- | :--- |
| **Image Viewer** | High-resolution zoom/pan of bulb specimen | Read-only; source file is NEVER modified |
| **Multi-Label Toggles** | Checkboxes for `Healthy`, `Damaged`, `Rotten`, `Sprouted`, `Undersized` | Multi-label enabled (`MULTI_LABEL_ALLOWED = TRUE`) |
| **Undersized Handling** | Size assessment dropdown (`UNAVAILABLE` by default) | Must NOT infer size without calibrated scale |
| **Uncertainty Mark** | Mark `UNCERTAIN` + select `uncertainty_reason` | Prevents forced binary labels on ambiguous samples |
| **Evidence Regions** | Draw bounding boxes or polygons over defect areas | Optional; stored separately under `evidence_regions` |
| **Confidence Level** | Select `HIGH`, `MEDIUM`, or `LOW` confidence | Recorded for every annotation record |
| **Navigation & Progress** | Previous / Next / Save buttons + Progress Counter | Shows exact completed count (e.g. 0 / 1000) |

---

## 4. Double Annotation & Independent Adjudication

1. **Independent Dual Assignment**: Exactly 100 images from the verification subset are assigned to Annotator A and Annotator B independently. Annotator B NEVER views or inherits Annotator A's entries.
2. **Disagreement Adjudication**: When Annotator A and B disagree on a defect label, the record is routed to `NEEDS_REVIEW` and resolved by a Senior Adjudicator. Initial records are preserved; final decisions are saved with `review_status = "ADJUDICATED"`.
