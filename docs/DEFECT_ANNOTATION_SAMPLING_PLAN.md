# S.P.O.T. Defect Human Annotation Sampling Plan

## 1. Sampling Objective

Rather than attempting unguided manual annotation across all 4,040 `Unhealthy` bulb images simultaneously, this plan establishes a stratified random sampling strategy to create a high-value 1,000-image human gold-standard benchmark.

---

## 2. Stratification Matrix

The 1,000 sampling budget is stratified across key environmental & physical axes to guarantee representative defect coverage:

| Stratum Dimension | Category | Stratum Proportion | Sample Target Count |
| :--- | :--- | :--- | :--- |
| **Bulb Color** | Red Onion | 50.0% | 500 images |
| | White Onion | 50.0% | 500 images |
| **Arrangement** | Single Bulb | 50.0% | 500 images |
| | Multiple Bulbs | 50.0% | 500 images |
| **Focus Quality** | High Clarity ($\text{blur} \ge 200$) | 70.0% | 700 images |
| | Soft Focus ($\text{blur} < 200$) | 30.0% | 300 images |

---

## 3. Human Annotation Export Format Schema

Human annotators will record multi-label annotations using the following standardized JSON/CSV schema:

```json
{
  "image_id": "Onion12261.jpg",
  "source_filename": "New Onion - Copy/2. Bulb/2. Unhealthy/1. Red Onion/1. Single/Onion12261.jpg",
  "onion_type": "RED",
  "arrangement": "SINGLE",
  "quality_binary": "UNHEALTHY",
  "defects": {
    "damaged": true,
    "rotten": true,
    "sprouted": false,
    "undersized": false
  },
  "annotator_id": "HUMAN_EXPERT_01",
  "annotation_status": "COMPLETED",
  "notes": "Severe mechanical laceration on upper hemisphere with black Aspergillus mold present."
}
```
