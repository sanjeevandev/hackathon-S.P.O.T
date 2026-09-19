# S.P.O.T. Multi-Label Defect Annotation Schema Specification

## 1. Overview & Specification Standards

- **Schema Version**: `0.1.0`
- **Source Dataset Version**: `1.0.0-audited`
- **Labeling Paradigm**: **Multi-Label Supervision** (`MULTI_LABEL_ALLOWED = TRUE`)
- **Primary Concepts**: `Healthy` (reference), `Damaged`, `Rotten`, `Sprouted`, `Undersized`.
- **Localization Support**: Optional evidence regions (`bounding_box` or `polygon`).

---

## 2. Canonical JSON Annotation Record Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SPOTOnionDefectAnnotationRecord",
  "type": "object",
  "required": [
    "annotation_id",
    "image_id",
    "dataset_version",
    "annotation_version",
    "annotator_id",
    "semantic_attributes",
    "multi_label_defects",
    "size_assessment",
    "evidence_regions",
    "annotation_confidence",
    "review_status",
    "created_at"
  ],
  "properties": {
    "annotation_id": { "type": "string", "example": "ANN-000101" },
    "image_id": { "type": "string", "example": "New Onion - Copy/2. Bulb/2. Unhealthy/1. Red Onion/1. Single/Onion12261.jpg" },
    "dataset_version": { "type": "string", "example": "1.0.0-audited" },
    "annotation_version": { "type": "string", "example": "0.1.0" },
    "annotator_id": { "type": "string", "example": "HUMAN_EXPERT_01" },
    "semantic_attributes": {
      "type": "object",
      "required": ["organ", "color", "arrangement"],
      "properties": {
        "organ": { "type": "string", "enum": ["BULB", "LEAF"] },
        "color": { "type": "string", "enum": ["RED", "WHITE", "UNSPECIFIED"] },
        "arrangement": { "type": "string", "enum": ["SINGLE", "MULTIPLE"] }
      }
    },
    "multi_label_defects": {
      "type": "object",
      "required": ["healthy", "damage", "rot", "sprout"],
      "properties": {
        "healthy": { "type": "boolean" },
        "damage": { "type": "boolean" },
        "rot": { "type": "boolean" },
        "sprout": { "type": "boolean" }
      }
    },
    "size_assessment": {
      "type": "object",
      "required": ["undersized_status", "size_reference_available", "estimated_diameter_mm", "measurement_method"],
      "properties": {
        "undersized_status": { "type": "string", "enum": ["TRUE", "FALSE", "UNAVAILABLE"] },
        "size_reference_available": { "type": "boolean" },
        "estimated_diameter_mm": { "type": ["number", "null"] },
        "measurement_method": { "type": "string", "enum": ["CALIBRATED_SCALE", "PIXEL_REFERENCE", "UNAVAILABLE"] }
      }
    },
    "evidence_regions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["region_id", "defect_type", "region_format", "coordinates"],
        "properties": {
          "region_id": { "type": "string" },
          "defect_type": { "type": "string", "enum": ["DAMAGE", "ROT", "SPROUT", "OTHER"] },
          "region_format": { "type": "string", "enum": ["BOUNDING_BOX", "POLYGON"] },
          "coordinates": { "type": "array" }
        }
      }
    },
    "annotation_confidence": { "type": "string", "enum": ["HIGH", "MEDIUM", "LOW"] },
    "review_status": { "type": "string", "enum": ["VERIFIED", "NEEDS_REVIEW", "ADJUDICATED", "PENDING"] },
    "notes": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" }
  }
}
```

---

## 3. Size Handling Rules

- If no physical millimeter calibration scale marker is present in the capture environment:
  - `size_reference_available = false`
  - `estimated_diameter_mm = null`
  - `measurement_method = "UNAVAILABLE"`
  - `undersized_status = "UNAVAILABLE"`
- Estimating diameter solely from uncalibrated camera zoom is strictly prohibited.
