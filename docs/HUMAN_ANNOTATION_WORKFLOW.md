# S.P.O.T. Human Defect Annotation Workstation User Manual

## 1. Introduction & Access Control

This manual guides human agronomists and quality inspectors using the S.P.O.T. Internal Annotation Workstation.

> [!WARNING]
> This is an internal agronomic data collection workstation. Access is restricted to authorized domain experts.

---

## 2. Step-by-Step Labeling Protocol

1. **Launch Queue**: Load your assigned 1,000-image queue.
2. **Inspect Image**: Zoom and inspect outer tunic, neck, basal plate, and surface scales for physical flaws.
3. **Select Multi-Label Conditions**:
   - **Healthy**: Check if bulb has dry intact tunic, tight neck, and zero decay/damage.
   - **Damaged**: Check if mechanical cuts, cracks, bruises, or crushing injuries are visible.
   - **Rotten**: Check if fungal mold (black/grey spores), soft rot decay, or wet soft spots are present.
   - **Sprouted**: Check if green foliage shoots emerge from the neck.
   - **Undersized**: Leave as `UNAVAILABLE` unless a calibrated scale marker is visible.
4. **Mark Uncertainty (If Ambiguous)**:
   - If lighting or occlusion makes a defect uncertain, check `UNCERTAIN` and select `uncertainty_reason` (e.g. *Ambiguous rot lesion vs dirt smudge*).
5. **Draw Evidence Region (Optional)**:
   - Click and drag a bounding box over the defect region if clearly identifiable.
6. **Assign Confidence & Save**:
   - Select Confidence (`HIGH`, `MEDIUM`, or `LOW`).
   - Click **Save & Next**.

---

## 3. Separation of Test Agreement vs Real Agreement

- **Test Fixture Agreement**: Used during software unit testing only.
- **Real-World Agreement**: Calculated automatically once 100 double-annotated images are independently completed by Annotator A and Annotator B.
