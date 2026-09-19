import json
import datetime
from typing import Dict, Any, List, Tuple

class AnnotationValidator:
    """Quality control & validation engine for human multi-label defect annotations."""

    @staticmethod
    def validate_record(record: Dict[str, Any]) -> Tuple[bool, List[str], str]:
        """Validates an annotation record against schema rules & logical integrity constraints.

        Returns:
            (is_valid, error_messages, review_status)
        """
        errors = []
        review_status = record.get("review_status", "VERIFIED")

        # 1. Required Top-Level Keys
        required_keys = [
            "annotation_id", "image_id", "dataset_version", "annotation_version",
            "annotator_id", "semantic_attributes", "multi_label_defects",
            "size_assessment", "evidence_regions", "annotation_confidence", "created_at"
        ]
        for key in required_keys:
            if key not in record:
                errors.append(f"Missing required field: {key}")

        if errors:
            return False, errors, "NEEDS_REVIEW"

        defects = record["multi_label_defects"]
        healthy = defects.get("healthy", False)
        damage = defects.get("damage", False)
        rot = defects.get("rot", False)
        sprout = defects.get("sprout", False)
        uncertain = defects.get("uncertain", False)

        # 2. Contradictory Label Check (Healthy = True AND Defect = True)
        if healthy and (damage or rot or sprout):
            errors.append("Contradictory labels: 'healthy' is True while defect flags are also True.")
            review_status = "NEEDS_REVIEW"

        # 3. No Label Marked Check (Neither healthy, defect, nor uncertain marked)
        if not healthy and not damage and not rot and not sprout and not uncertain:
            errors.append("Unspecified condition: neither 'healthy', defect flags, nor 'uncertain' is marked True.")
            review_status = "NEEDS_REVIEW"


        # 4. Size Reference & Diameter Rule
        size_info = record.get("size_assessment", {})
        if not size_info.get("size_reference_available", False):
            if size_info.get("estimated_diameter_mm") is not None:
                errors.append("Invalid diameter: estimated_diameter_mm must be null when size_reference_available is False.")
                review_status = "NEEDS_REVIEW"
            if size_info.get("undersized_status") != "UNAVAILABLE":
                errors.append("Invalid undersized_status: must be 'UNAVAILABLE' when size_reference_available is False.")
                review_status = "NEEDS_REVIEW"

        # 5. Evidence Region Coordinate Checks
        regions = record.get("evidence_regions", [])
        for idx, reg in enumerate(regions):
            bbox = reg.get("coordinates", [])
            if reg.get("region_format") == "BOUNDING_BOX":
                if len(bbox) != 4:
                    errors.append(f"Region {idx}: Bounding box coordinates must have 4 values [x1, y1, x2, y2].")
                    review_status = "NEEDS_REVIEW"
                else:
                    x1, y1, x2, y2 = bbox
                    if not (0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0):
                        errors.append(f"Region {idx}: Bounding box coordinates out of normalized bounds [0, 1].")
                        review_status = "NEEDS_REVIEW"

        is_valid = len(errors) == 0
        return is_valid, errors, review_status
